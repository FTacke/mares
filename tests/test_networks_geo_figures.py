"""Figures G1 and G2: where the contacts live relative to ego, in ordered steps.

They show the residence *category* (Marburg, Region Marburg, übriges Deutschland, übriges Europa, außerhalb Europas), they are no maps,
and they add no tie. B1-B3 stay as they are.
"""

from __future__ import annotations

import math
import os
import subprocess
import sys

import pytest
from matplotlib.collections import LineCollection, PathCollection
from matplotlib.text import Text

import network_fixtures as fx
from mares.core import ids
from mares.networks.analysis import AnalysisParams, survey_status
from mares.networks.build import build_network
from mares.networks.figures import ego_network, geo_zones
from mares.networks.figures import network as netfig
from mares.networks.figures.common import contact_views
from mares.networks.figures.style import GEO_COLORS, rc, save_figure
from mares.networks.geo import GeoCategory
from mares.networks.package import read_package

PARAMS = AnalysisParams()
# residence of the first contacts: (city, country) -> the category the contact must land in
RESIDENCES = [
    ("Marburg", "DEU", GeoCategory.LOCAL),
    ("Nähe Marburg", "DEU", GeoCategory.LOCAL_REGION),
    ("Berlin", "DEU", GeoCategory.GERMANY_OTHER),
    ("Lima", "PER", GeoCategory.OUTSIDE_EUROPE),
    ("Marburg", "DEU", GeoCategory.LOCAL),
    ("Region Marburg", "DEU", GeoCategory.LOCAL_REGION),
    ("Marburg an der Lahn", "DEU", GeoCategory.GERMANY_OTHER),  # "Marburg" only when stated exactly
    ("Wien", "AUT", GeoCategory.EUROPE_OTHER),
]


def _dataset(tmp_path, n=12, residences=RESIDENCES, with_groups=True):
    rows = fx.contact_rows(n, 8)
    for row, (city, country, _) in zip(rows, residences):
        row.update(residence_city=city, residence_country_iso3=country)
    g, m = fx.standard_groups() if with_groups else ([], [])
    if n < 11:
        m = [x for x in m if int(x["contact_id"][1:]) <= n]
        g = [x for x in g if any(y["group_id"] == x["group_id"] for y in m)]
    return read_package(fx.build_package(tmp_path / "p", contacts=rows, groups=g, memberships=m, review_items=[]))


def _make(dataset):
    network = build_network(dataset)
    return network, survey_status(dataset, network)


def _texts(fig):
    return [t.get_text() for t in fig.findobj(Text) if t.get_text()]


def _collections(fig, kind):
    return [c for c in fig.axes[0].collections if isinstance(c, kind)]


def _order(network):
    return geo_zones.structure_order(network)


# ------------------------------------------------------------------ categories ----------------------------


def test_contacts_land_in_the_four_geographic_categories(tmp_path):
    dataset = _dataset(tmp_path)
    views = {v.contact_id: v for v in contact_views(dataset, PARAMS)}
    for index, (_, _, expected) in enumerate(RESIDENCES, 1):
        assert views[f"A{index:02d}"].geo is expected, index
    assert GeoCategory.LOCAL_REGION is not GeoCategory.LOCAL  # Region Marburg is a category of its own
    assert GeoCategory.LOCAL_REGION is not GeoCategory.GERMANY_OTHER


def test_rings_follow_the_order_marburg_region_germany_europe_outside_and_hold_the_right_contacts(tmp_path):
    dataset = _dataset(tmp_path)
    network, _ = _make(dataset)
    views = contact_views(dataset, PARAMS)
    layout = geo_zones.ring_layout(views, _order(network))
    assert [b.category for b in layout.bands] == list(geo_zones.ZONES)  # five zones, near to far
    assert all(layout.bands[i].outer <= layout.bands[i + 1].inner + 1e-9 for i in range(4))  # nested, not overlapping
    by_id = {v.contact_id: v for v in views}
    for band in layout.bands:
        for contact in band.members:
            assert by_id[contact].geo is band.category
            radius = math.hypot(*layout.positions[contact])
            assert band.inner < radius < band.outer, (contact, band.category)
    assert {c for b in layout.bands for c in b.members} == set(by_id)  # nobody lost, nobody twice
    region = next(b for b in layout.bands if b.category is GeoCategory.LOCAL_REGION)
    assert set(region.members) == {"A02", "A06"}


def test_an_empty_zone_stays_visible_and_unknown_residences_get_their_own_band(tmp_path):
    dataset = _dataset(tmp_path, n=2, residences=[("Marburg", "DEU", None), ("Berlin", "DEU", None)], with_groups=False)
    views = contact_views(dataset, PARAMS)
    layout = geo_zones.ring_layout(views, list(sorted(v.contact_id for v in views)))
    assert [b.category for b in layout.bands][:5] == list(geo_zones.ZONES)
    assert next(b for b in layout.bands if b.category is GeoCategory.OUTSIDE_EUROPE).members == ()  # empty, still drawn
    # a residence without a country is neither guessed into a zone nor dropped
    rows = fx.contact_rows(6)
    rows[0].update(residence_city="", residence_country_iso3="")
    unknown = read_package(fx.build_package(tmp_path / "q", contacts=rows))
    layout = geo_zones.ring_layout(contact_views(unknown, PARAMS), [f"A{i:02d}" for i in range(1, 7)])
    assert layout.bands[-1].category is GeoCategory.UNKNOWN and layout.bands[-1].members == ("A01",)
    assert len(layout.bands) == 6


def test_band_layout_places_contacts_in_their_band(tmp_path):
    dataset = _dataset(tmp_path)
    network, _ = _make(dataset)
    views = contact_views(dataset, PARAMS)
    layout = geo_zones.band_layout(views, _order(network))
    by_id = {v.contact_id: v for v in views}
    assert [box[0] for box in layout.boxes] == list(geo_zones.ZONES)
    for category, x0, x1, y0, y1, members in layout.boxes:
        for contact in members:
            x, y = layout.positions[contact]
            assert by_id[contact].geo is category and x0 < x < x1 and y0 < y < y1
    assert all(layout.boxes[i][2] < layout.boxes[i + 1][1] for i in range(4))  # the bands are separate and in order


def test_contacts_never_overlap_in_any_layout(tmp_path):
    for n in (12, 40, 100):
        dataset = _dataset(tmp_path / str(n), n=n, residences=[(c, k, g) for c, k, g in RESIDENCES] * 8, with_groups=n >= 11)
        network, _ = _make(dataset)
        views = contact_views(dataset, PARAMS)
        for layout in (geo_zones.ring_layout(views, _order(network)), geo_zones.ring_layout(views, even=True), geo_zones.band_layout(views, _order(network))):
            points = list(layout.positions.values())
            nearest = min(math.dist(p, q) for i, p in enumerate(points) for q in points[i + 1 :])
            assert nearest > 0.45, (n, nearest)


# ------------------------------------------------------------------ G1 --------------------------------


def test_g1_shows_every_contact_once_in_its_zone_colour_and_no_ties(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    fig = geo_zones.geographic_zones_figure(dataset, status, PARAMS, network=network)
    assert _collections(fig, LineCollection) == []  # no ties in G1
    texts = _texts(fig)
    assert sum(1 for t in texts if t.startswith("A") and len(t) == 3) == 12 and "EGO" in texts
    joined = " ".join(texts)
    for zone in ("Marburg", "Region Marburg", "übriges Deutschland", "übriges Europa", "außerhalb Europas"):
        assert zone in joined
    circles = [p for p in fig.axes[0].patches if type(p).__name__ == "Circle"]
    node_colours = [tuple(p.get_facecolor()[:3]) for p in circles if p.get_radius() < 0.3]
    expected = [tuple(int(GEO_COLORS[g][i : i + 2], 16) / 255 for i in (1, 3, 5)) for _, _, g in RESIDENCES]
    for colour in expected:  # every category that occurs is drawn in its colour
        assert any(all(abs(a - b) < 1e-6 for a, b in zip(colour, drawn)) for drawn in node_colours)


@pytest.mark.parametrize("figure", ["g1", "g2b", "g2a"])
def test_the_figures_say_what_they_are_not(tmp_path, figure):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    if figure == "g1":
        fig = geo_zones.geographic_zones_figure(dataset, status, PARAMS, network=network, profile="analysis")
    else:
        fig = geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network, variant="bands" if figure == "g2b" else "rings", profile="analysis")
    joined = " ".join(_texts(fig))
    for expected in ("keine Karte", "Entfernungsmaß", "Abbildung A", "Netzwerk-Layout", "UNREVIEWED"):
        assert expected in joined, (figure, expected)
    assert "Prüfhinweis" not in joined and "communit" not in joined.lower()
    if figure != "g1":
        assert "heißt nicht, dass die Kontakte sozial getrennt sind" in joined
        assert "nicht „kennen sich nicht“" in joined  # unknown pairs stay unknown


# ------------------------------------------------------------------ G2 --------------------------------


@pytest.mark.parametrize("variant", ["bands", "rings"])
def test_g2_draws_exactly_the_confirmed_ties_and_one_ego_line_per_contact(tmp_path, variant):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    fig = geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network, variant=variant)
    lines = {c.get_label(): c for c in _collections(fig, LineCollection)}
    ego_lines, between, within = lines["ego_lines"], lines["ties_between"], lines["ties_within"]
    assert len(ego_lines.get_segments()) == 12
    nodes = max(_collections(fig, PathCollection), key=lambda c: len(c.get_offsets()))
    names = sorted((c.contact_id for c in dataset.contacts), key=ids.contact_number)
    at = {tuple(round(float(v), 6) for v in xy): name for xy, name in zip(nodes.get_offsets(), names)}

    def pairs(collection):
        out = []
        for a, b in collection.get_segments():
            out.append(frozenset((at[tuple(round(float(v), 6) for v in a)], at[tuple(round(float(v), 6) for v in b)])))
        return out

    drawn = pairs(between) + pairs(within)
    expected = [frozenset(t.pair) for t in network.positive_ties]
    assert len(drawn) == len(set(drawn)) == len(expected) == 9  # none lost, none invented, none twice
    assert set(drawn) == set(expected)
    zone = {v.contact_id: v.geo for v in contact_views(dataset, PARAMS)}
    assert all(len({zone[c] for c in pair}) == 1 for pair in pairs(within))  # within = the same zone
    assert all(len({zone[c] for c in pair}) == 2 for pair in pairs(between))  # between = two zones


def test_g2_classifies_the_ties_by_zone(tmp_path):
    dataset = _dataset(tmp_path)
    network, _ = _make(dataset)
    views = contact_views(dataset, PARAMS)
    within, between = geo_zones.classify_ties(network, views)
    assert len(within) + len(between) == len(network.positive_ties)
    assert not set(within) & set(between)
    zone = {v.contact_id: v.geo for v in views}
    assert all(zone[a] is zone[b] for a, b in within) and all(zone[a] is not zone[b] for a, b in between)
    assert ("A01", "A02") in between and ("A03", "A04") in between  # Marburg-Region and Germany-abroad pairs cross zones


def test_g2_without_ego_lines_and_without_any_tie(tmp_path):
    dataset = _dataset(tmp_path, n=5, with_groups=False, residences=RESIDENCES[:5])
    network, status = _make(dataset)
    assert network.ties == ()
    fig = geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network, ego_lines=False, profile="analysis")
    assert _collections(fig, LineCollection) == []
    assert "0 bestätigte" in " ".join(_texts(fig))


def test_unknown_variant_is_refused(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    with pytest.raises(ValueError):
        geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network, variant="map")


# ------------------------------------------------------------------ stability --------------------------


@pytest.mark.parametrize("n", [1, 2, 3, 40, 100])
def test_g1_and_g2_build_for_any_number_of_contacts(tmp_path, n):
    dataset = _dataset(tmp_path, n=n, residences=[(c, k, g) for c, k, g in RESIDENCES] * 13, with_groups=n >= 11)
    network, status = _make(dataset)
    geo_zones.geographic_zones_figure(dataset, status, PARAMS, network=network)
    for variant in ("bands", "rings"):
        geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network, variant=variant)
    geo_zones.geographic_variants_figure(dataset, status, PARAMS, network=network)


def test_the_geographic_figures_are_reproducible_byte_for_byte(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    digests = []
    for run in ("one", "two"):
        figures = {
            "g1": geo_zones.geographic_zones_figure(dataset, status, PARAMS, network=network),
            "g2": geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network),
            "g2a": geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network, variant="rings"),
            "v": geo_zones.geographic_variants_figure(dataset, status, PARAMS, network=network),
        }
        out = []
        for name, fig in sorted(figures.items()):
            with rc():
                save_figure(fig, tmp_path / f"{run}_{name}", ("svg", "png", "pdf"))
            out += [(tmp_path / f"{run}_{name}.{ext}").read_bytes() for ext in ("svg", "png", "pdf")]
        digests.append(out)
    assert digests[0] == digests[1]


_PROBE = """
from mares.networks.figures import geo_zones
from mares.networks.figures.common import ContactView
from mares.networks.geo import GeoCategory
cats = [GeoCategory.LOCAL, GeoCategory.LOCAL_REGION, GeoCategory.GERMANY_OTHER, GeoCategory.EUROPE_OTHER, GeoCategory.OUTSIDE_EUROPE]
views = [ContactView(f"A{i:02d}", cats[i % 4], ("Ort" + str(i % 3)), "DEU", None, "DEU", (), None, ()) for i in range(1, 15)]
order = [f"A{i:02d}" for i in (3, 9, 1, 14, 5, 7, 2, 12, 4, 10, 8, 13, 6, 11)]
rings = geo_zones.ring_layout(views, order)
even = geo_zones.ring_layout(views, even=True)
bands = geo_zones.band_layout(views, order)
for layout in (rings, even, bands):
    print(sorted((k, round(v[0], 9), round(v[1], 9)) for k, v in layout.positions.items()))
"""


def test_the_layouts_do_not_depend_on_the_process_hash_seed():
    outputs = set()
    for seed in ("1", "2", "3"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        outputs.add(subprocess.run([sys.executable, "-c", _PROBE], capture_output=True, text=True, env=env, check=True).stdout)
    assert len(outputs) == 1


def test_the_structure_order_is_a_stable_circular_order_of_all_contacts(tmp_path):
    dataset = _dataset(tmp_path)
    network, _ = _make(dataset)
    first = geo_zones.structure_order(network)
    assert first == geo_zones.structure_order(network)
    assert sorted(first, key=ids.contact_number) == sorted(network.contact_ids, key=ids.contact_number)
    # the contacts of one clique stay next to each other
    positions = {c: i for i, c in enumerate(first)}
    clique = [positions[c] for c in ("A01", "A02", "A03", "A04")]
    assert max(clique) - min(clique) <= 6


def test_the_existing_figures_are_not_changed_by_building_the_geographic_ones(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)

    def existing(stem):
        figs = {
            "b1": netfig.network_structure_figure(dataset, status, PARAMS, network=network),
            "b2": netfig.network_structure_figure(dataset, status, PARAMS, network=network, show_groups=True),
            "b3": ego_network.ego_network_figure(dataset, status, PARAMS, network=network),
        }
        out = {}
        for name, fig in figs.items():
            with rc():
                save_figure(fig, tmp_path / f"{stem}_{name}", ("svg", "png"))
            out[name] = [(tmp_path / f"{stem}_{name}.{ext}").read_bytes() for ext in ("svg", "png")]
        return out

    before = existing("before")
    geo_zones.geographic_zones_figure(dataset, status, PARAMS, network=network)
    geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network)
    geo_zones.geographic_variants_figure(dataset, status, PARAMS, network=network)
    assert existing("after") == before


def test_geographic_figures_keep_the_status_stamp_and_use_only_ids(tmp_path):
    def with_text(rows):
        rows[0]["birth_country_source"] = "Freitext-Herkunft"
        rows[1]["review_flags"] = "SECRET_FLAG"

    rows = fx.contact_rows(12, 8)
    with_text(rows)
    dataset = read_package(fx.build_package(tmp_path / "p", contacts=rows, groups=fx.standard_groups()[0], memberships=fx.standard_groups()[1],
                                            review_items=[{"review_id": "R1", "priority": "x", "reference": "A03", "field": "f",
                                                           "description": "VERTRAULICHE NOTIZ", "recommended_action": "x"}]))
    network, status = _make(dataset)
    for fig in (geo_zones.geographic_zones_figure(dataset, status, PARAMS, network=network, profile="analysis"),
                geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network, profile="analysis")):
        joined = " ".join(_texts(fig))
        assert "Quelle 0000-1" in joined and "UNREVIEWED" in joined
        for forbidden in ("VERTRAULICHE", "Freitext-Herkunft", "SECRET_FLAG"):
            assert forbidden not in joined
