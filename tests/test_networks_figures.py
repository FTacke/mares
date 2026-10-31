"""Figures: they build for any contact count, are reproducible byte for byte, show only what is
documented, and print nothing that is not an id, a code or an aggregate."""

from __future__ import annotations

import math

import pytest
from matplotlib.text import Text

import network_fixtures as fx
from mares.networks.analysis import AnalysisParams, survey_status
from mares.networks.build import build_network
from mares.networks.figures import ego, ego_network, geo_zones, geography, language, layouts, overview, perspectives
from mares.networks.figures import network as netfig
from mares.networks.figures.common import contact_views, ego_layout
from mares.networks.figures.style import rc, save_figure
from mares.networks.package import read_package

PARAMS = AnalysisParams()


def _dataset(tmp_path, n=12, with_groups=True, mutate=None):
    rows = fx.contact_rows(n, 8)
    if mutate:
        mutate(rows)
    g, m = fx.standard_groups() if with_groups else ([], [])
    if n < 11:
        m = [x for x in m if int(x["contact_id"][1:]) <= n]
        g = [x for x in g if any(y["group_id"] == x["group_id"] for y in m)]
    return read_package(fx.build_package(tmp_path / "p", contacts=rows, groups=g, memberships=m, review_items=[]))


def _all_figures(dataset):
    network = build_network(dataset)
    status = survey_status(dataset, network)
    structure = netfig.build_structure(network)
    return {
        "A": ego.proximity_figure(dataset, status, PARAMS),
        "B1": netfig.network_structure_figure(dataset, status, PARAMS, network=network, structure=structure),
        "B2": netfig.network_structure_figure(dataset, status, PARAMS, network=network, show_groups=True, structure=structure),
        "B0": netfig.layout_comparison_figure(dataset, status, PARAMS, network=network),
        "C": geography.geography_figure(dataset, status, PARAMS),
        "D1": language.language_profile_figure(dataset, status, PARAMS),
        "D2": ego.language_mode_figure(dataset, status, PARAMS),
        "E": overview.overview_figure(dataset, status, PARAMS),
        "B3": ego_network.ego_network_figure(dataset, status, PARAMS, network=network),
        "B3_0": ego_network.ego_layout_comparison_figure(dataset, status, PARAMS, network=network),
        "G2": geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network),
        "P1": perspectives.distance_closeness_figure(dataset, status, PARAMS, network=network),
        "P2": perspectives.language_groups_figure(dataset, status, PARAMS, network=network),
        "P3": perspectives.geography_communication_figure(dataset, status, PARAMS, network=network),
    }, network


def _texts(figure):
    return [t.get_text() for t in figure.findobj(Text) if t.get_text()]


def test_all_figures_build_for_a_normal_dataset(tmp_path):
    figures, _ = _all_figures(_dataset(tmp_path))
    assert set(figures) == {"A", "B1", "B2", "B0", "B3", "B3_0", "C", "D1", "D2", "E", "G2", "P1", "P2", "P3"}
    for name, figure in figures.items():
        texts = _texts(figure)
        assert any("vorläufig" in t or "UNREVIEWED" in t for t in texts), name  # the status stamp is on every figure (short in the clean profile)
        assert any("0000-1" in t for t in texts), name  # the source label


@pytest.mark.parametrize("n", [1, 2, 3, 40, 120])
def test_figures_build_for_any_number_of_contacts(tmp_path, n):
    dataset = _dataset(tmp_path, n=n, with_groups=n >= 11)
    figures, _ = _all_figures(dataset)
    assert len(figures) == 14


def test_figures_build_without_any_documented_tie_or_geography(tmp_path):
    def unknown_everywhere(rows):
        for row in rows:
            row.update(residence_city="", residence_country_iso3="", language_mode_code="", language_codes="", table_ring_near_value="")

    dataset = _dataset(tmp_path, n=5, with_groups=False, mutate=unknown_everywhere)
    figures, network = _all_figures(dataset)
    assert network.ties == () and len(figures) == 14


def test_figures_are_reproducible_byte_for_byte(tmp_path):
    dataset = _dataset(tmp_path)
    digests = []
    for run in ("one", "two"):
        out = tmp_path / run
        out.mkdir()
        figures, _ = _all_figures(dataset)
        for name, figure in sorted(figures.items()):
            with rc():
                save_figure(figure, out / name, ("svg", "png", "pdf"))
        digests.append({p.name: p.read_bytes() for p in sorted(out.iterdir())})
    assert digests[0].keys() == digests[1].keys() and len(digests[0]) == 42
    for name in digests[0]:
        assert digests[0][name] == digests[1][name], name


def test_files_carry_no_timestamp_or_software_string(tmp_path):
    figures, _ = _all_figures(_dataset(tmp_path))
    with rc():
        save_figure(figures["A"], tmp_path / "a", ("svg", "pdf", "png"))
    svg = (tmp_path / "a.svg").read_text(encoding="utf-8")
    assert "<dc:date>" not in svg and "Matplotlib v" not in svg
    pdf = (tmp_path / "a.pdf").read_bytes()
    assert b"CreationDate" not in pdf and b"Producer" not in pdf


def test_figures_print_only_ids_codes_and_aggregates(tmp_path):
    def with_text(rows):
        rows[0]["birth_country_source"] = "Freitext-Herkunft"
        rows[2]["review_flags"] = "SECRET_FLAG_TEXT"

    groups_, memberships = fx.standard_groups()
    reviews = [{"review_id": "R1", "priority": "high", "reference": "A03", "field": "f", "description": "VERTRAULICHE NOTIZ", "recommended_action": "x"}]
    rows = fx.contact_rows(12, 8)
    with_text(rows)
    dataset = read_package(fx.build_package(tmp_path / "p", contacts=rows, groups=groups_, memberships=memberships, review_items=reviews))
    figures, _ = _all_figures(dataset)
    for name, figure in figures.items():
        joined = " ".join(_texts(figure))
        for forbidden in ("VERTRAULICHE", "Freitext-Herkunft", "SECRET_FLAG", "Gruppe G01"):  # notes, source text, flags, group labels
            assert forbidden not in joined, (name, forbidden)


def test_network_figures_draw_exactly_the_confirmed_ties(tmp_path):
    dataset = _dataset(tmp_path)
    figures, network = _all_figures(dataset)
    for name in ("B1", "B2"):
        axes = figures[name].axes[0]
        lines = [c for c in axes.collections if type(c).__name__ == "LineCollection"]
        assert len(lines) == 1 and len(lines[0].get_segments()) == len(network.positive_ties) == 9, name  # no line from the layout
        texts = " ".join(_texts(figures[name]))
        assert "unbekannt" in texts  # the short hint of the clean profile
        analysis = netfig.network_structure_figure(dataset, survey_status(dataset, network), PARAMS, network=network, show_groups=name == "B2", profile="analysis")
        assert "bestätigte Beziehungen" in " ".join(_texts(analysis))
    # the candidate group A06-A08 has no confirmed tie and so no line in either figure
    assert not [t for t in network.ties if {"A06", "A07", "A08"} & {t.a, t.b}]


def test_b1_and_b2_share_one_layout_and_differ_only_in_the_group_areas(tmp_path):
    dataset = _dataset(tmp_path)
    figures, network = _all_figures(dataset)

    def node_positions(fig):
        scatter = [c for c in fig.axes[0].collections if type(c).__name__ == "PathCollection"][0]
        return [tuple(map(float, row)) for row in scatter.get_offsets()]

    assert node_positions(figures["B1"]) == node_positions(figures["B2"])
    areas = lambda fig: [p for p in fig.axes[0].patches if type(p).__name__ == "Polygon"]
    assert len(areas(figures["B1"])) == 0
    assert len(areas(figures["B2"])) == 2 * len(network.confirmed_groups)  # one fill and one contour per surveyed group
    assert "Erhobene Kontaktgruppen" in " ".join(_texts(figures["B2"]))
    assert "Erhobene Kontaktgruppen" not in " ".join(_texts(figures["B1"]))


def test_groups_are_never_called_communities(tmp_path):
    figures, _ = _all_figures(_dataset(tmp_path))
    for name, figure in figures.items():
        joined = " ".join(_texts(figure)).lower()
        assert "communit" not in joined and "girvan" not in joined, name


def test_no_figure_carries_review_marks(tmp_path):
    def flagged(rows):
        rows[0]["review_flags"] = "SOME_FLAG"
        rows[1]["review_flags"] = "OTHER_FLAG"

    dataset = _dataset(tmp_path, mutate=flagged)
    figures, _ = _all_figures(dataset)
    for name, figure in figures.items():
        joined = " ".join(_texts(figure))
        assert "Prüfhinweis" not in joined and "SOME_FLAG" not in joined and "gestrichelt" not in joined, name
        dashed = [
            artist for artist in figure.findobj()
            if getattr(artist, "get_linestyle", None) and artist.get_linestyle() in ("--", (0, (2.2, 1.6)))
            and type(artist).__name__ == "Circle"
        ]
        assert not dashed, name


def test_a_regional_residence_and_an_ambiguous_birth_country_are_shown_as_such(tmp_path):
    def vague(rows):
        rows[0].update(residence_city="Nähe Marburg", residence_country_iso3="DEU", birth_country_iso3="", birth_country_source="Land A/Land B")

    dataset = _dataset(tmp_path, mutate=vague)
    figures, _ = _all_figures(dataset)
    geo = " ".join(_texts(figures["C"]))
    assert "Region Marburg" in geo and "mehrdeutig" in geo
    assert "Region Marburg" in " ".join(_texts(figures["A"])) + " ".join(_texts(figures["B1"]))
    assert "Land A" not in geo  # the raw statement is not printed; neither country is chosen


def test_layout_variants_are_deterministic_and_use_only_the_ties(tmp_path):
    dataset = _dataset(tmp_path)
    network = build_network(dataset)
    edges = [t.pair for t in network.positive_ties]
    graph = layouts.ordered_graph(network.contact_ids, edges)
    for variant in layouts.VARIANTS:
        first, second = layouts.compute_layout(graph, variant), layouts.compute_layout(graph, variant)
        assert first == second and set(first) == set(network.contact_ids), variant
    assert netfig.build_structure(network, "stress").positions == layouts.compute_layout(graph, "stress")
    with pytest.raises(ValueError):
        layouts.compute_layout(graph, "circular-ring")


def test_the_layout_does_not_depend_on_group_frames_or_attributes(tmp_path):
    """Same ties, different attributes and groups: the same positions."""
    groups_a, members_a = fx.standard_groups()
    base = read_package(fx.build_package(tmp_path / "a", contacts=fx.contact_rows(12, 8), groups=groups_a, memberships=members_a))
    rows = fx.contact_rows(12, 8)
    for row in rows:
        row.update(residence_city="Lima", residence_country_iso3="PER", language_codes="2")
    other_groups = [fx.group("X01"), fx.group("X02"), fx.group("X03")]  # other ids, same ties
    other_members = fx.members("X01", ["A01", "A02", "A03", "A04"]) + fx.members("X02", ["A03", "A04", "A05"]) + fx.members("X03", ["A10", "A11"])
    other = read_package(fx.build_package(tmp_path / "b", contacts=rows, groups=other_groups, memberships=other_members))
    assert netfig.build_structure(build_network(base)).positions == netfig.build_structure(build_network(other)).positions


def test_stress_layout_beats_a_crushed_layout_on_tie_length(tmp_path):
    dataset = _dataset(tmp_path)
    network = build_network(dataset)
    edges = [t.pair for t in network.positive_ties]
    graph = layouts.ordered_graph(network.contact_ids, edges)
    measures = {v: layouts.measure(layouts.compute_layout(graph, v), edges) for v in layouts.VARIANTS}
    assert measures["stress"].tie_share > measures["spring"].tie_share  # components not blown apart
    assert measures["stress"].min_node_distance > 0.3  # nodes do not touch
    assert all(m.crossings >= 0 for m in measures.values())


def test_node_labels_do_not_collide_in_the_network_figure(tmp_path):
    figures, network = _all_figures(_dataset(tmp_path))
    axes = figures["B1"].axes[0]
    labels = [t for t in axes.texts if t.get_text().startswith("A")]
    assert len(labels) == 12
    boxes = []
    figures["B1"].canvas.draw()
    renderer = figures["B1"].canvas.get_renderer()
    for label in labels:
        box = label.get_window_extent(renderer)
        boxes.append((box.x0, box.y0, box.x1, box.y1))
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            assert a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1], "two id labels overlap"


def test_the_network_footnote_states_how_the_ties_were_obtained(tmp_path):
    from mares.networks.curation import Curation, SurveyMethod

    dataset = _dataset(tmp_path)
    network = build_network(dataset)
    asked = survey_status(dataset, network, Curation(survey=SurveyMethod("asked_per_pair", "group_outlines", "all_members_know_each_other", "not_established", "basis")))
    unknown = survey_status(dataset, network)
    figure_asked = netfig.network_structure_figure(dataset, asked, PARAMS, network=network, profile="analysis")
    figure_unknown = netfig.network_structure_figure(dataset, unknown, PARAMS, network=network, profile="analysis")
    assert "im Interview erfragt" in " ".join(_texts(figure_asked)) and "nicht belegt" in " ".join(_texts(figure_asked))
    assert "im Interview erfragt" not in " ".join(_texts(figure_unknown))  # never asserted without a stated basis


def test_ego_layout_radius_depends_on_the_table_value_only(tmp_path):
    def blank_one(rows):
        rows[6]["table_ring_near_value"] = ""

    dataset = _dataset(tmp_path, mutate=blank_one)
    views = contact_views(dataset, PARAMS)
    zones = sorted(dataset.codebook.codes("closeness_1_5"), key=lambda c: -int(c))
    layout = ego_layout(views, zones)
    for view in views:
        x, y = layout.positions[view.contact_id]
        radius = math.hypot(x, y)
        if view.closeness is None:
            assert radius > layout.band_bounds[-1][1]  # outside every zone: never guessed into one
        else:
            inner, outer = layout.band_bounds[zones.index(view.closeness)]
            assert inner < radius < outer, (view.contact_id, view.closeness)
    by_value = {}
    for view in views:
        if view.closeness:
            by_value.setdefault(view.closeness, []).append(math.hypot(*layout.positions[view.contact_id]))
    assert all(max(r) - min(r) < 0.3 for r in by_value.values())  # same value, same band


def test_ego_layout_is_deterministic_and_keeps_nodes_apart(tmp_path):
    dataset = _dataset(tmp_path, n=40, with_groups=False)
    views = contact_views(dataset, PARAMS)
    zones = sorted(dataset.codebook.codes("closeness_1_5"), key=lambda c: -int(c))
    first, second = ego_layout(views, zones), ego_layout(views, zones)
    assert first.positions == second.positions
    points = list(first.positions.values())
    nearest = min(math.dist(p, q) for i, p in enumerate(points) for q in points[i + 1 :])
    assert nearest > 0.45  # discs of radius 0.29 do not overlap much


def test_five_zones_are_labelled_from_the_codebook_and_empty_ones_stay(tmp_path):
    dataset = _dataset(tmp_path, n=3, with_groups=False)
    figures, _ = _all_figures(dataset)
    clean = " ".join(_texts(figures["A"]))
    for meaning in ("überhaupt nicht nah", "eher wenig nah", "mittel", "nah", "sehr nah"):
        assert meaning in clean  # every zone is named, also the empty ones
    assert "keine Kontakte" not in clean and "(n = " not in clean  # the reduced legend has no counts
    analysis = " ".join(_texts(ego.proximity_figure(dataset, survey_status(dataset, build_network(dataset)), PARAMS, profile="analysis")))
    assert "keine Kontakte" in analysis and "Tabellenwert" in analysis


_LAYOUT_PROBE = """
from mares.networks.figures import layouts
edges = [("A01", "A02"), ("A01", "A03"), ("A02", "A03"), ("A02", "A04"), ("A03", "A04"),
         ("A04", "A05"), ("A05", "A06"), ("A04", "A06"), ("A06", "A07")]
nodes = {a for e in edges for a in e} | {"A08"}
graph = layouts.ordered_graph(nodes, edges)
for variant in layouts.VARIANTS:
    pos = layouts.compute_layout(graph, variant)
    print(variant, [(k, round(v[0], 9), round(v[1], 9)) for k, v in sorted(pos.items())])
"""


def test_layouts_do_not_depend_on_the_process_hash_seed():
    """Sets of strings iterate differently in every process; the layouts must not."""
    import os
    import subprocess
    import sys

    outputs = set()
    for seed in ("1", "2", "3", "4"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        result = subprocess.run([sys.executable, "-c", _LAYOUT_PROBE], capture_output=True, text=True, env=env, check=True)
        outputs.add(result.stdout)
    assert len(outputs) == 1
