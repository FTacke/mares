"""G2-A (geographic bands) and G2-B (geographically constrained force layout), and the register of the figures.

What is secured: five geographic steps, no ego lines, exactly the confirmed ties (none added, none hidden), the geography of every
contact kept in both layouts, deterministic and independent of the hash seed, any number of contacts and any distribution; and the
division of the figures into core / supplementary / diagnostic with reproducible clean and analysis profiles.
"""

from __future__ import annotations

import math
import os
import subprocess
import sys

import pytest
from matplotlib.collections import LineCollection, PathCollection
from matplotlib.text import Text

import network_v0_fixtures as fx
from mares.core import ids
from mares.network_v0.analysis import AnalysisParams, survey_status
from mares.network_v0.build import build_network
from mares.network_v0.figures import design, geo_network, geo_zones, registry
from mares.network_v0.figures.common import contact_views
from mares.network_v0.figures.registry import FigureContext, FigureOptions
from mares.network_v0.figures.style import rc, save_figure
from mares.network_v0.geo import GeoCategory
from mares.network_v0.package import read_package

PARAMS = AnalysisParams()
PLACES = {
    GeoCategory.LOCAL: ("Marburg", "DEU"),
    GeoCategory.LOCAL_REGION: ("Nähe Marburg", "DEU"),
    GeoCategory.GERMANY_OTHER: ("Berlin", "DEU"),
    GeoCategory.EUROPE_OTHER: ("Wien", "AUT"),
    GeoCategory.OUTSIDE_EUROPE: ("Bogotá", "COL"),
}
ZONE_ORDER = list(PLACES)


def _dataset(tmp_path, zones, groups=None, n=None):
    """Contacts with the given residence zones (a list, one per contact) and cliques ``groups`` = {id: [contact numbers]}."""
    n = n or len(zones)
    rows = fx.contact_rows(n, 8)
    for row, zone in zip(rows, zones):
        city, country = ("", "") if zone is GeoCategory.UNKNOWN else PLACES[zone]
        row.update(residence_city=city, residence_country_iso3=country)
    group_rows, member_rows = [], []
    for group_id, numbers in (groups or {}).items():
        group_rows.append(fx.group(group_id))
        member_rows += fx.members(group_id, [f"A{k:02d}" for k in numbers])
    return read_package(fx.build_package(tmp_path / "p", contacts=rows, groups=group_rows, memberships=member_rows, review_items=[]))


def _make(dataset):
    network = build_network(dataset)
    return network, survey_status(dataset, network)


def _pilot_like(tmp_path):
    """22 contacts, 41 confirmed ties (28 + 10 + 3 from three cliques); the contacts of a clique live in several zones."""
    L, R, G, E, O = (GeoCategory.LOCAL, GeoCategory.LOCAL_REGION, GeoCategory.GERMANY_OTHER, GeoCategory.EUROPE_OTHER, GeoCategory.OUTSIDE_EUROPE)
    zones = [L, L, R, G, G, E, O, O,  # G1: A01-A08, over all five steps
             L, G, G, O, L,  # G2: A09-A13
             G, E, L,  # G3: A14-A16
             L, G, G, L, O, G]  # six contacts without a confirmed tie
    groups = {"G1": list(range(1, 9)), "G2": list(range(9, 14)), "G3": list(range(14, 17))}
    return _dataset(tmp_path, zones, groups)


def _texts(fig):
    return [t.get_text() for t in fig.findobj(Text) if t.get_text()]


def _lines(fig):
    return {c.get_label(): c for c in fig.axes[0].collections if isinstance(c, LineCollection)}


def _nodes(fig):
    return max((c for c in fig.axes[0].collections if isinstance(c, PathCollection)), key=lambda c: len(c.get_offsets()))


def _tie_count(fig):
    lines = _lines(fig)
    return sum(len(lines[k].get_segments()) for k in ("ties_between", "ties_within") if k in lines)


# ------------------------------------------------------------------ the fixtures themselves -------------------------


def test_the_pilot_like_case_has_22_contacts_41_ties_and_cliques_across_zones(tmp_path):
    dataset = _pilot_like(tmp_path)
    network, _ = _make(dataset)
    views = contact_views(dataset, PARAMS)
    assert len(dataset.contacts) == 22 and len(network.positive_ties) == 41
    zone = {v.contact_id: v.geo for v in views}
    assert len({zone[c] for c in network.confirmed_groups[0][1]}) == 5  # a social sub-network over all five geographic steps
    assert {v.geo for v in views} == set(ZONE_ORDER)


# ------------------------------------------------------------------ G2-A: bands -------------------------------------


def test_bands_layout_has_five_bands_in_order_each_as_wide_as_its_contacts_need(tmp_path):
    dataset = _pilot_like(tmp_path)
    network, _ = _make(dataset)
    views = contact_views(dataset, PARAMS)
    layout = geo_network.bands_layout(views, geo_zones.structure_order(network))
    assert [b.category for b in layout.bands] == ZONE_ORDER
    width = {b.category: b.x1 - b.x0 for b in layout.bands}
    assert width[GeoCategory.LOCAL_REGION] < width[GeoCategory.GERMANY_OTHER]  # one contact: a narrow band, no empty area
    assert abs(width[GeoCategory.EUROPE_OTHER] - width[GeoCategory.LOCAL_REGION]) < 1e-9
    assert all(layout.bands[i].x1 < layout.bands[i + 1].x0 for i in range(4))  # separate, in order
    by_id = {v.contact_id: v for v in views}
    for band in layout.bands:
        for contact in band.members:
            x, y = layout.positions[contact]
            assert by_id[contact].geo is band.category and band.x0 < x < band.x1 and 0 < y < layout.height
    points = list(layout.positions.values())
    assert min(math.dist(p, q) for i, p in enumerate(points) for q in points[i + 1 :]) > 0.45
    assert {c for b in layout.bands for c in b.members} == set(by_id)  # nobody lost, nobody twice


def test_bands_figure_has_no_ego_and_exactly_the_confirmed_ties(tmp_path):
    dataset = _pilot_like(tmp_path)
    network, status = _make(dataset)
    fig = geo_network.geographic_bands_figure(dataset, status, PARAMS, network=network)
    lines = _lines(fig)
    assert "ego_lines" not in lines and set(lines) == {"ties_between", "ties_within"}
    assert _tie_count(fig) == len(network.positive_ties) == 41
    assert len(_nodes(fig).get_offsets()) == 22
    assert "EGO" not in _texts(fig)  # ego is not part of this graph
    zone = {v.contact_id: v.geo for v in contact_views(dataset, PARAMS)}
    within, between = geo_zones.classify_ties(network, contact_views(dataset, PARAMS))
    assert len(lines["ties_between"].get_segments()) == len(between) > 0 and len(lines["ties_within"].get_segments()) == len(within) > 0
    assert all(zone[a] is zone[b] for a, b in within) and all(zone[a] is not zone[b] for a, b in between)


def test_the_highlight_changes_only_the_look_of_the_ties(tmp_path):
    dataset = _pilot_like(tmp_path)
    network, status = _make(dataset)
    segments = {}
    for highlight in ("between", "within", None):
        for build in (geo_network.geographic_bands_figure, geo_network.geographic_radial_figure):
            fig = build(dataset, status, PARAMS, network=network, highlight=highlight)
            lines = _lines(fig)
            segments.setdefault(build.__name__, set()).add(tuple(sorted(repr(s.round(6).tolist()) for c in lines.values() for s in c.get_segments())))
            if highlight == "between":
                assert lines["ties_between"].get_linewidths()[0] > lines["ties_within"].get_linewidths()[0]
                assert lines["ties_between"].get_zorder() > lines["ties_within"].get_zorder()
            if highlight == "within":
                assert lines["ties_within"].get_linewidths()[0] > lines["ties_between"].get_linewidths()[0]
    assert all(len(s) == 1 for s in segments.values())  # the same segments in every emphasis
    with pytest.raises(ValueError):
        geo_network.geographic_bands_figure(dataset, status, PARAMS, network=network, highlight="strong")


# ------------------------------------------------------------------ G2-B: radial force layout ----------------------


def _radius(position):
    return math.hypot(position[0] / geo_network.ASPECT, position[1])


def test_radial_layout_keeps_the_geography_of_every_contact(tmp_path):
    dataset = _pilot_like(tmp_path)
    network, _ = _make(dataset)
    views = contact_views(dataset, PARAMS)
    layout = geo_network.radial_layout(views, network)
    zone = {v.contact_id: v.geo for v in views}
    ring = {r.category: r for r in layout.zones}
    assert [r.category for r in layout.zones] == ZONE_ORDER and all(layout.zones[i].centre < layout.zones[i + 1].centre for i in range(4))
    window = geo_network.RING_STEP * geo_network.WINDOW + 1e-6
    for contact, position in layout.positions.items():
        assert abs(_radius(position) - ring[zone[contact]].centre) <= window, contact  # the radius stays in the window of its zone
        assert ring[zone[contact]].inner - 1e-6 <= _radius(position) <= ring[zone[contact]].outer + 1e-6
    # the zones keep their order: the mean radius of a zone grows with the step
    means = [sum(_radius(layout.positions[c]) for c in r.members) / len(r.members) for r in layout.zones if r.members]
    assert means == sorted(means)
    assert set(layout.positions) == set(zone)


def test_radial_layout_leaves_the_sector_for_the_zone_names_free(tmp_path):
    dataset = _pilot_like(tmp_path)
    network, _ = _make(dataset)
    layout = geo_network.radial_layout(contact_views(dataset, PARAMS), network)
    for x, y in layout.positions.values():
        angle = math.degrees(math.atan2(y, x / geo_network.ASPECT)) % 360
        assert abs(angle - 90.0) >= geo_network.GAP_DEG - 0.5  # nobody stands where the names are written


def test_radial_layout_keeps_social_sub_networks_together_better_than_a_random_order(tmp_path):
    dataset = _pilot_like(tmp_path)
    network, _ = _make(dataset)
    views = contact_views(dataset, PARAMS)
    within, between = geo_zones.classify_ties(network, views)
    radial = geo_network.measure_ab(geo_network.radial_layout(views, network).positions, network, within, between)
    assert radial.group_compactness is not None and radial.group_compactness < 0.6  # members of a group stand closer than contacts in general
    assert radial.min_node_distance > 0.2  # no contacts on top of each other


def test_radial_figure_has_ego_only_as_a_point_of_reference(tmp_path):
    dataset = _pilot_like(tmp_path)
    network, status = _make(dataset)
    fig = geo_network.geographic_radial_figure(dataset, status, PARAMS, network=network)
    lines = _lines(fig)
    assert "ego_lines" not in lines and _tie_count(fig) == 41 == len(network.positive_ties)
    ego = [c for c in fig.axes[0].collections if isinstance(c, PathCollection) and len(c.get_offsets()) == 1]
    assert any(tuple(c.get_offsets()[0]) == (0.0, 0.0) for c in ego)  # the reference point in the centre ...
    for collection in lines.values():  # ... that no line touches
        assert all((0.0, 0.0) not in [tuple(p) for p in segment] for segment in collection.get_segments())
    texts = _texts(fig)
    assert "EGO" in texts and sum(1 for t in texts if ids.is_contact_id(t)) == 22
    names = " ".join(texts)
    for zone in ("Marburg", "Region Marburg", "übriges Deutschland", "übriges Europa", "außerhalb Europas"):
        assert zone in names


def test_radial_layout_is_deterministic_and_independent_of_the_hash_seed(tmp_path):
    dataset = _pilot_like(tmp_path)
    network, _ = _make(dataset)
    views = contact_views(dataset, PARAMS)
    first = geo_network.radial_layout(views, network)
    assert first.positions == geo_network.radial_layout(views, network).positions
    outputs = set()
    for seed in ("1", "2", "3"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        script = _PROBE.format(tests=os.path.dirname(os.path.abspath(__file__)), tmp=str(tmp_path / f"seed{seed}"))
        (tmp_path / f"seed{seed}").mkdir()
        outputs.add(subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=env, check=True).stdout)
    assert len(outputs) == 1


_PROBE = """
import sys
from pathlib import Path
sys.path.insert(0, {tests!r})
import test_network_v0_geo_network as t
root = Path({tmp!r})
dataset = t._pilot_like(root)
network, status = t._make(dataset)
from mares.network_v0.figures import geo_network
from mares.network_v0.figures.common import contact_views
views = contact_views(dataset, t.PARAMS)
layout = geo_network.radial_layout(views, network)
print(sorted((k, round(v[0], 9), round(v[1], 9)) for k, v in layout.positions.items()), layout.start)
bands = geo_network.bands_layout(views, t.geo_zones.structure_order(network))
print(sorted((k, round(v[0], 9), round(v[1], 9)) for k, v in bands.positions.items()))
"""


# ------------------------------------------------------------------ generalisation ---------------------------------


CASES = {
    "only_local": lambda: [GeoCategory.LOCAL] * 7,
    "only_transcontinental": lambda: [GeoCategory.OUTSIDE_EUROPE] * 6,
    "very_unequal": lambda: [GeoCategory.LOCAL] * 30 + [GeoCategory.EUROPE_OTHER],
    "all_zones": lambda: ZONE_ORDER * 4,
    "one_contact": lambda: [GeoCategory.EUROPE_OTHER],
    "unknown_residences": lambda: [GeoCategory.LOCAL, GeoCategory.UNKNOWN, GeoCategory.UNKNOWN, GeoCategory.OUTSIDE_EUROPE],
}


@pytest.mark.parametrize("case", sorted(CASES))
def test_both_variants_build_for_unusual_distributions(tmp_path, case):
    zones = CASES[case]()
    n = len(zones)
    groups = {"G1": list(range(1, min(n, 5) + 1))} if n >= 3 else None
    dataset = _dataset(tmp_path, zones, groups)
    network, status = _make(dataset)
    for build in (geo_network.geographic_bands_figure, geo_network.geographic_radial_figure):
        fig = build(dataset, status, PARAMS, network=network)
        assert len(_nodes(fig).get_offsets()) == n
        assert _tie_count(fig) == len(network.positive_ties)
    views = contact_views(dataset, PARAMS)
    radial = geo_network.radial_layout(views, network)
    assert set(radial.positions) == {v.contact_id for v in views}
    if case == "unknown_residences":
        assert radial.zones[-1].category is GeoCategory.UNKNOWN and len(radial.zones[-1].members) == 2  # not guessed into a step, not dropped
        assert "Wohnort nicht zuordenbar" in " ".join(_texts(geo_network.geographic_radial_figure(dataset, status, PARAMS, network=network)))
    if case == "very_unequal":
        bands = geo_network.bands_layout(views, geo_zones.structure_order(network))
        widths = {b.category: b.x1 - b.x0 for b in bands.bands}
        assert widths[GeoCategory.EUROPE_OTHER] < widths[GeoCategory.LOCAL]  # a single person does not open a large empty area


@pytest.mark.parametrize("n", [1, 2, 3, 40, 100])
def test_both_variants_build_for_any_number_of_contacts(tmp_path, n):
    zones = [ZONE_ORDER[i % 5] for i in range(n)]
    groups = {"G1": [1, 2, 3, 4], "G2": [3, 4, 5]} if n >= 5 else None  # overlapping groups across zones
    dataset = _dataset(tmp_path, zones, groups)
    network, status = _make(dataset)
    for build in (geo_network.geographic_bands_figure, geo_network.geographic_radial_figure):
        fig = build(dataset, status, PARAMS, network=network)
        assert len(_nodes(fig).get_offsets()) == n
    layout = geo_network.radial_layout(contact_views(dataset, PARAMS), network)
    points = list(layout.positions.values())
    if len(points) > 1:
        assert min(math.dist(p, q) for i, p in enumerate(points) for q in points[i + 1 :]) > 0.25


def test_attributes_and_data_are_unchanged_by_the_figures(tmp_path):
    dataset = _pilot_like(tmp_path)
    network, status = _make(dataset)
    before = ([(c.contact_id, dict(c.text)) for c in dataset.contacts], [t.pair for t in network.ties])
    geo_network.geographic_bands_figure(dataset, status, PARAMS, network=network)
    geo_network.geographic_radial_figure(dataset, status, PARAMS, network=network)
    geo_network.geographic_ab_comparison_figure(dataset, status, PARAMS, network=network)
    assert ([(c.contact_id, dict(c.text)) for c in dataset.contacts], [t.pair for t in network.ties]) == before


def test_the_reference_place_is_configurable_in_g2(tmp_path):
    zones = [GeoCategory.LOCAL] * 3 + [GeoCategory.OUTSIDE_EUROPE] * 2
    rows = fx.contact_rows(5)
    for row, zone in zip(rows, zones):
        city, country = PLACES[zone]
        row.update(residence_city="Gießen" if zone is GeoCategory.LOCAL else city, residence_country_iso3=country)
    dataset = read_package(fx.build_package(tmp_path / "p", contacts=rows))
    network, status = _make(dataset)
    giessen = AnalysisParams(local_places=("Gießen",))
    texts = " ".join(_texts(geo_network.geographic_radial_figure(dataset, status, giessen, network=network)))
    assert "Gießen" in texts and "Marburg" not in texts.replace("Region Marburg", "")  # the first zone carries the configured name


# ------------------------------------------------------------------ comparison figure -------------------------------


def test_the_comparison_has_both_variants_and_measures_on_the_same_ties(tmp_path):
    dataset = _pilot_like(tmp_path)
    network, status = _make(dataset)
    fig = geo_network.geographic_ab_comparison_figure(dataset, status, PARAMS, network=network)
    joined = " ".join(_texts(fig))
    for expected in ("G2-A", "G2-B", "Kreuzungen", "Gruppenkompaktheit", "Knotenabstand"):
        assert expected in joined
    views = contact_views(dataset, PARAMS)
    within, between = geo_zones.classify_ties(network, views)
    for layout in (geo_network.bands_layout(views, geo_zones.structure_order(network)), geo_network.radial_layout(views, network)):
        measures = geo_network.measure_ab(layout.positions, network, within, between)
        assert measures.between_ties == len(between) and measures.crossings >= 0


# ------------------------------------------------------------------ profiles: reduced and full -----------------------


def test_clean_g2_is_reduced_and_the_analysis_profile_keeps_the_notes(tmp_path):
    dataset = _pilot_like(tmp_path)
    network, status = _make(dataset)
    for build in (geo_network.geographic_bands_figure, geo_network.geographic_radial_figure):
        clean = " ".join(_texts(build(dataset, status, PARAMS, network=network)))
        analysis = " ".join(_texts(build(dataset, status, PARAMS, network=network, profile="analysis")))
        assert len(clean) < len(analysis) * 0.6
        assert "MARES · 0000-1 · vorläufig" in clean and "UNREVIEWED" in analysis
        assert "keine Entfernungen" in clean and "Integration" in analysis and "Integration" not in clean
        assert "Ego ist nicht Teil" in analysis


# ------------------------------------------------------------------ the register ------------------------------------


def test_the_figures_are_divided_into_core_supplementary_and_diagnostic():
    by_tier = {tier: {s.stem for s in registry.SPECS if s.tier == tier} for tier in registry.TIERS}
    assert by_tier["core"] == {"fig_B3_ego_netzwerk", "fig_G2b_geografisches_kraftlayout", "fig_P1_distanz_und_naehe", "fig_P2_sprachliche_praktiken"}
    assert {"fig_A_ego_naehe_wohnort", "fig_B1_netzwerkstruktur", "fig_B2_netzwerkstruktur_gruppen", "fig_G1_geografische_zonen", "fig_G2a_geografische_baender",
            "fig_P3_einbettung_und_kommunikation", "fig_C_geografisches_profil", "fig_D1_sprachprofil", "fig_D2_ego_sprachmodus",
            "fig_E_deskriptive_uebersicht"} == by_tier["supplementary"]
    assert {"fig_B0_layoutvergleich", "fig_B3_0_layoutvergleich", "fig_G2_0_variantenvergleich", "fig_G2_1_vergleich_a_b", "fig_G2_geografisches_beziehungsnetz"} == by_tier["diagnostic"]
    assert sum(len(v) for v in by_tier.values()) == len(registry.SPECS) == len({s.stem for s in registry.SPECS})  # every figure in exactly one tier
    assert all(not s.profiles for s in registry.SPECS if s.tier == "diagnostic") and all(s.profiles for s in registry.SPECS if s.tier != "diagnostic")
    assert [s.stem for s in registry.SPECS if s.candidate] == ["fig_G2b_geografisches_kraftlayout"]  # one candidate, the decision is the project lead's
    assert [s.stem for s in registry.SPECS if s.legacy] == ["fig_G2_geografisches_beziehungsnetz"]
    with pytest.raises(ValueError):
        registry.FigureSpec("x", "gallery", lambda c, p: None)


def test_every_figure_has_a_register_entry_with_question_and_limits():
    index = registry.figure_index(FigureOptions(), ("svg",))
    assert set(index["figures"]) == {s.stem for s in registry.SPECS} and set(index["tiers"]) == set(registry.TIERS)
    for stem, entry in index["figures"].items():
        assert entry["title"] != stem and entry["question"] and entry["limits"] and entry["tier"] in registry.TIERS, stem
    g2b = index["figures"]["fig_G2b_geografisches_kraftlayout"]
    assert g2b["candidate"] and "Kilometer" in " ".join(g2b["limits"]) and "Ego ist nicht Teil" in " ".join(g2b["limits"])
    assert index["figures"]["fig_G2_geografisches_beziehungsnetz"]["legacy"]
    assert set(g2b["files"]) == {"clean", "analysis"} and g2b["files"]["analysis"].startswith("figures/analysis/core/")
    assert set(index["figures"]["fig_B0_layoutvergleich"]["files"]) == {"standard"}


def test_the_register_carries_the_full_provenance_the_clean_figures_only_hint_at(tmp_path):
    dataset = _pilot_like(tmp_path)
    network, status = _make(dataset)
    index = registry.figure_index(FigureOptions(), ("svg",), status)
    assert index["provenance"]["source_label"] == "0000-1" and "UNREVIEWED" in str(index["provenance"])
    assert "figures_index" not in str(index["provenance"])


def _context(dataset, network, status):
    from mares.network_v0.figures import ego_network
    from mares.network_v0.figures import network as network_figures

    return FigureContext(dataset, status, PARAMS, network, network_figures.build_structure(network), ego_network.build_ego_structure(network))


def test_every_figure_builds_in_every_profile_and_clean_is_shorter_than_analysis(tmp_path):
    dataset = _pilot_like(tmp_path)
    network, status = _make(dataset)
    context = _context(dataset, network, status)
    for spec in registry.SPECS:
        clean = spec.build(context, "clean")
        texts = " ".join(_texts(clean))
        assert texts and ("vorläufig" in texts or "UNREVIEWED" in texts), spec.stem
        if spec.profiles:
            analysis = " ".join(_texts(spec.build(context, "analysis")))
            assert len(texts) <= len(analysis), spec.stem
            assert "MARES · 0000-1 · vorläufig" in texts and "Quelle 0000-1" not in texts, spec.stem  # the short mark in clean
            title = max((t for t in clean.texts if t.get_fontsize() == design.TITLE_PT), key=lambda t: len(t.get_text())).get_text()
            assert len(title) < 70 and ":" not in title, (spec.stem, title)


def test_every_figure_is_reproducible_byte_for_byte_in_both_profiles(tmp_path):
    dataset = _pilot_like(tmp_path)
    network, status = _make(dataset)
    digests = []
    for run in ("one", "two"):
        context = _context(dataset, network, status)
        out = {}
        for spec in registry.SPECS:
            for profile in ("clean", "analysis") if spec.profiles else ("clean",):
                with rc():
                    save_figure(spec.build(context, profile), tmp_path / f"{run}_{profile}_{spec.stem}", ("svg", "png"))
                out[(profile, spec.stem)] = [(tmp_path / f"{run}_{profile}_{spec.stem}.{ext}").read_bytes() for ext in ("svg", "png")]
        digests.append(out)
    assert digests[0] == digests[1]


def test_the_analysis_profile_keeps_the_earlier_wording_of_the_older_figures(tmp_path):
    dataset = _pilot_like(tmp_path)
    network, status = _make(dataset)
    context = _context(dataset, network, status)
    for stem, phrase in (("fig_A_ego_naehe_wohnort", "Egozentriertes Netzwerk"), ("fig_C_geografisches_profil", "Geografisches Netzwerkprofil"),
                         ("fig_D1_sprachprofil", "Sprachliches Netzwerkprofil"), ("fig_E_deskriptive_uebersicht", "Deskriptive Übersicht"),
                         ("fig_B1_netzwerkstruktur", "Netzwerkstruktur der erhobenen Beziehungen")):
        spec = registry.spec_for(stem)
        assert phrase in " ".join(_texts(spec.build(context, "analysis"))), stem
        assert phrase not in " ".join(_texts(spec.build(context, "clean"))), stem
