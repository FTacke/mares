"""Figure B3: the personal network including ego -- one more perspective, not a different dataset.

B3 must show exactly: one ego node, one ego line per contact, and the confirmed alter-alter ties and no other.
B1 and B2 (the alter-alter network without ego) and the ego rings of figure A stay as they are.
"""

from __future__ import annotations

import math
import os
import subprocess
import sys

import pytest
from matplotlib.collections import LineCollection, PathCollection

import network_v0_fixtures as fx
from mares.core import ids
from mares.network_v0.analysis import AnalysisParams, descriptive_tables, survey_status
from mares.network_v0.build import build_network
from mares.network_v0.figures import ego_layouts, layouts
from mares.network_v0.figures import ego_network as b3
from mares.network_v0.figures import network as netfig
from mares.network_v0.figures.ego_network import EGO_LINE_COLOR
from mares.network_v0.figures.style import GEO_COLORS, INK, rc, save_figure
from mares.network_v0.figures.network import TIE_COLOR
from mares.network_v0.package import read_package

PARAMS = AnalysisParams()


def _dataset(tmp_path, n=12, with_groups=True):
    rows = fx.contact_rows(n, 8)
    g, m = fx.standard_groups() if with_groups else ([], [])
    if n < 11:
        m = [x for x in m if int(x["contact_id"][1:]) <= n]
        g = [x for x in g if any(y["group_id"] == x["group_id"] for y in m)]
    return read_package(fx.build_package(tmp_path / "p", contacts=rows, groups=g, memberships=m, review_items=[]))


def _b3(dataset, **kwargs):
    network = build_network(dataset)
    status = survey_status(dataset, network)
    return b3.ego_network_figure(dataset, status, PARAMS, network=network, **kwargs), network


def _line_collections(fig):
    return [c for c in fig.axes[0].collections if isinstance(c, LineCollection)]


def _scatters(fig):
    return [c for c in fig.axes[0].collections if isinstance(c, PathCollection)]


def _texts(fig):
    return [t.get_text() for t in fig.findobj(lambda a: hasattr(a, "get_text")) if t.get_text()]


def test_b3_has_one_ego_one_ego_line_per_contact_and_the_confirmed_ties_only(tmp_path):
    dataset = _dataset(tmp_path)
    fig, network = _b3(dataset)
    ego_lines, alter_lines = sorted(_line_collections(fig), key=lambda c: c.get_zorder())
    n = len(dataset.contacts)
    assert len(ego_lines.get_segments()) == n == 12  # one ego-alter line per contact
    assert len(alter_lines.get_segments()) == len(network.positive_ties) == 9  # exactly the confirmed ties
    contact_nodes, ego_node = sorted(_scatters(fig), key=lambda c: len(c.get_offsets()), reverse=True)
    assert len(contact_nodes.get_offsets()) == n and len(ego_node.get_offsets()) == 1  # exactly one ego

    ego_xy = tuple(map(float, ego_node.get_offsets()[0]))
    contact_xy = {tuple(map(float, p)) for p in contact_nodes.get_offsets()}
    assert all(tuple(map(float, seg[0])) == ego_xy and tuple(map(float, seg[1])) in contact_xy for seg in ego_lines.get_segments())
    assert len({tuple(map(float, seg[1])) for seg in ego_lines.get_segments()}) == n  # no contact twice, none missing
    ties = {frozenset((tuple(map(float, s[0])), tuple(map(float, s[1])))) for s in alter_lines.get_segments()}
    assert len(ties) == 9  # no duplicate
    assert not any(ego_xy in tie for tie in ties)  # no alter-alter line touches ego


def test_the_two_kinds_of_line_are_visibly_different(tmp_path):
    fig, _ = _b3(_dataset(tmp_path), profile="analysis")
    ego_lines, alter_lines = sorted(_line_collections(fig), key=lambda c: c.get_zorder())
    assert ego_lines.get_zorder() < alter_lines.get_zorder()  # surveyed ties lie above the membership lines
    assert ego_lines.get_linewidths()[0] < alter_lines.get_linewidths()[0]
    assert ego_lines.get_colors().tolist() != alter_lines.get_colors().tolist()
    texts = " ".join(_texts(fig))
    assert "Ego – Kontakt" in texts and "Kontakt – Kontakt" in texts and "Zugehörigkeit zum" in texts
    assert EGO_LINE_COLOR != TIE_COLOR


def test_alter_positions_and_colours_are_those_of_b1_and_b2(tmp_path):
    dataset = _dataset(tmp_path)
    network = build_network(dataset)
    status = survey_status(dataset, network)
    b1 = netfig.network_structure_figure(dataset, status, PARAMS, network=network)
    fig, _ = _b3(dataset)
    contacts_b1 = max(_scatters(b1), key=lambda c: len(c.get_offsets()))
    contacts_b3 = max(_scatters(fig), key=lambda c: len(c.get_offsets()))
    # B3 re-frames the axes to include ego, so compare the *data* positions, not pixels
    assert [tuple(map(float, p)) for p in contacts_b1.get_offsets()] == [tuple(map(float, p)) for p in contacts_b3.get_offsets()]
    assert contacts_b1.get_facecolors().tolist() == contacts_b3.get_facecolors().tolist()  # the same residence colours
    alter_b1 = _line_collections(b1)[0].get_segments()
    alter_b3 = max(_line_collections(fig), key=lambda c: c.get_zorder()).get_segments()
    assert [s.tolist() for s in alter_b1] == [s.tolist() for s in alter_b3]


def test_ego_is_dark_and_has_no_residence_category(tmp_path):
    fig, _ = _b3(_dataset(tmp_path), profile="analysis")
    ego_node = min(_scatters(fig), key=lambda c: len(c.get_offsets()))
    colour = tuple(ego_node.get_facecolors()[0][:3])
    assert all(colour != tuple(int(v[i : i + 2], 16) / 255 for i in (1, 3, 5)) for v in GEO_COLORS.values())
    texts = _texts(fig)
    assert "EGO" in texts
    legend = " ".join(texts)
    assert "Ego (befragte Person)" in legend and "Kontakte nach Wohnort" in legend


def test_b3_never_adds_a_tie_and_the_network_stays_without_ego(tmp_path):
    dataset = _dataset(tmp_path)
    network = build_network(dataset)
    assert "EGO" not in network.contact_ids and not ids.is_contact_id("EGO")
    before = [(t.pair, t.state, t.basis, t.group_ids) for t in network.ties]
    status = survey_status(dataset, network)
    b3.ego_network_figure(dataset, status, PARAMS, network=network)
    assert [(t.pair, t.state, t.basis, t.group_ids) for t in network.ties] == before
    assert all("EGO" not in t.pair for t in network.ties)
    tables = {t.key: t for t in descriptive_tables(dataset, network, PARAMS)}
    assert "structure" not in tables  # coverage not established: no structure measures, and none from a graph with ego


def test_the_footnote_keeps_the_three_dimensions_apart(tmp_path):
    fig, _ = _b3(_dataset(tmp_path), profile="analysis")
    joined = " ".join(_texts(fig))
    for expected in ("Zugehörigkeit zum persönlichen Netzwerk", "nicht erhobene Beziehungen", "misst keine Nähe", "Abbildung A",
                     "keine soziale oder geografische Distanz", "zwangsläufig zusammenhängend", "kein Befund", "ohne Ego (B1, B2)", "UNREVIEWED"):
        assert expected in joined, expected
    assert "communit" not in joined.lower()


def test_b3_shows_the_surveyed_groups_softly_and_can_do_without(tmp_path):
    dataset = _dataset(tmp_path)
    with_groups, network = _b3(dataset, profile="analysis")
    without, _ = _b3(dataset, show_groups=False, profile="analysis")
    polygons = lambda fig: [p for p in fig.axes[0].patches if type(p).__name__ == "Polygon"]
    assert len(polygons(with_groups)) == 2 * len(network.confirmed_groups) and polygons(without) == []
    assert "Erhobene Kontaktgruppen" in " ".join(_texts(with_groups)) and "Erhobene Kontaktgruppen" not in " ".join(_texts(without))
    assert max(p.get_alpha() or 0 for p in polygons(with_groups)) <= 0.5  # soft: they never compete with the lines


def test_b1_and_b2_are_not_changed_by_building_b3(tmp_path):
    dataset = _dataset(tmp_path)
    network = build_network(dataset)
    status = survey_status(dataset, network)

    def bytes_of(show_groups, stem):
        fig = netfig.network_structure_figure(dataset, status, PARAMS, network=network, show_groups=show_groups)
        with rc():
            save_figure(fig, tmp_path / stem, ("svg", "png"))
        return (tmp_path / f"{stem}.svg").read_bytes(), (tmp_path / f"{stem}.png").read_bytes()

    before = (bytes_of(False, "b1a"), bytes_of(True, "b2a"))
    b3.ego_network_figure(dataset, status, PARAMS, network=network)
    b3.ego_layout_comparison_figure(dataset, status, PARAMS, network=network)
    after = (bytes_of(False, "b1b"), bytes_of(True, "b2b"))
    assert before == after


@pytest.mark.parametrize("n", [1, 2, 3, 40, 100])
def test_b3_builds_for_small_and_large_networks(tmp_path, n):
    dataset = _dataset(tmp_path, n=n, with_groups=n >= 11)
    fig, network = _b3(dataset)
    ego_lines = min(_line_collections(fig), key=lambda c: c.get_zorder())
    assert len(ego_lines.get_segments()) == n  # no fixed number of contacts


def test_b3_builds_without_any_confirmed_tie(tmp_path):
    dataset = _dataset(tmp_path, n=5, with_groups=False)
    fig, network = _b3(dataset, profile="analysis")
    assert network.ties == () and len(_line_collections(fig)) == 1  # only the ego lines exist
    assert "0 bestätigte" in " ".join(_texts(fig))


# ------------------------------------------------------------------ layouts --------------------------


def _graph(tmp_path):
    network = build_network(_dataset(tmp_path))
    edges = [t.pair for t in network.positive_ties]
    return layouts.ordered_graph(network.contact_ids, edges), edges, network


def test_every_ego_layout_places_ego_and_all_contacts_deterministically(tmp_path):
    graph, edges, network = _graph(tmp_path)
    for variant in ego_layouts.EGO_VARIANTS:
        first, second = ego_layouts.compute_ego_layout(graph, variant), ego_layouts.compute_ego_layout(graph, variant)
        assert first == second, variant
        assert set(first) == set(network.contact_ids) | {ego_layouts.EGO}
    with pytest.raises(ValueError):
        ego_layouts.compute_ego_layout(graph, "rings")


def test_the_fixed_variant_keeps_the_alter_layout_exactly(tmp_path):
    graph, edges, _ = _graph(tmp_path)
    reference = layouts.compute_layout(graph, layouts.DEFAULT_VARIANT)
    fixed = ego_layouts.compute_ego_layout(graph, "fixed")
    assert {c: p for c, p in fixed.items() if c != ego_layouts.EGO} == reference
    measures = ego_layouts.measure_ego(fixed, edges, reference)
    assert measures.structure_kept == pytest.approx(1.0)
    assert measures.contacts_touched == 0  # no ego line runs through a contact
    other = ego_layouts.measure_ego(ego_layouts.compute_ego_layout(graph, "weighted"), edges, reference)
    assert other.structure_kept < 1.0  # a joint layout necessarily moves the contacts


def test_the_weighted_layout_weighs_ego_ties_less_than_alter_ties(tmp_path):
    graph, edges, _ = _graph(tmp_path)
    naive = ego_layouts.compute_ego_layout(graph, "joint")
    weighted = ego_layouts.compute_ego_layout(graph, "weighted")
    reference = layouts.compute_layout(graph, layouts.DEFAULT_VARIANT)
    assert ego_layouts.measure_ego(weighted, edges, reference).structure_kept > ego_layouts.measure_ego(naive, edges, reference).structure_kept
    assert ego_layouts.EGO_WEIGHT < 1.0 and ego_layouts.EGO_LENGTH > 1.0


def test_ego_sits_near_the_middle_but_not_necessarily_in_it(tmp_path):
    graph, edges, _ = _graph(tmp_path)
    reference = layouts.compute_layout(graph, layouts.DEFAULT_VARIANT)
    for variant in ego_layouts.EGO_VARIANTS:
        positions = ego_layouts.compute_ego_layout(graph, variant)
        assert ego_layouts.measure_ego(positions, edges, reference).ego_offset < 0.35, variant


_PROBE = """
import networkx as nx
from mares.network_v0.figures import ego_layouts, layouts
edges = [("A01", "A02"), ("A01", "A03"), ("A02", "A03"), ("A02", "A04"), ("A03", "A04"),
         ("A04", "A05"), ("A05", "A06"), ("A04", "A06"), ("A06", "A07")]
nodes = {a for e in edges for a in e} | {"A08"}
graph = layouts.ordered_graph(nodes, edges)
for variant in ego_layouts.EGO_VARIANTS:
    pos = ego_layouts.compute_ego_layout(graph, variant)
    print(variant, [(k, round(v[0], 9), round(v[1], 9)) for k, v in sorted(pos.items())])
"""


def test_ego_layouts_do_not_depend_on_the_process_hash_seed():
    outputs = set()
    for seed in ("1", "2", "3"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        outputs.add(subprocess.run([sys.executable, "-c", _PROBE], capture_output=True, text=True, env=env, check=True).stdout)
    assert len(outputs) == 1


def test_b3_labels_do_not_collide(tmp_path):
    fig, _ = _b3(_dataset(tmp_path))
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [t.get_window_extent(renderer) for t in fig.axes[0].texts if t.get_text().startswith("A")]
    assert len(boxes) == 12
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            assert a.x1 <= b.x0 or b.x1 <= a.x0 or a.y1 <= b.y0 or b.y1 <= a.y0, "two id labels overlap"


def test_b3_is_reproducible_byte_for_byte(tmp_path):
    dataset = _dataset(tmp_path)
    digests = []
    for run in ("one", "two"):
        fig, _ = _b3(dataset)
        with rc():
            save_figure(fig, tmp_path / run, ("svg", "png", "pdf"))
        digests.append([(tmp_path / f"{run}.{ext}").read_bytes() for ext in ("svg", "png", "pdf")])
    assert digests[0] == digests[1]
