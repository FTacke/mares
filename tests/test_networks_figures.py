"""Figures: they build for any contact count, are reproducible byte for byte, show only what is
documented, and print nothing that is not an id, a code or an aggregate."""

from __future__ import annotations

import math

import pytest
from matplotlib.text import Text

import network_fixtures as fx
from mares.networks.analysis import AnalysisParams, survey_status
from mares.networks.build import build_network
from mares.networks.figures import ego, geography, groups, language, overview
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
    return {
        "A": ego.proximity_figure(dataset, status, PARAMS),
        "B": groups.group_network_figure(dataset, status, PARAMS, network=network),
        "C": geography.geography_figure(dataset, status, PARAMS),
        "D1": language.language_profile_figure(dataset, status, PARAMS),
        "D2": ego.language_mode_figure(dataset, status, PARAMS),
        "E": overview.overview_figure(dataset, status, PARAMS),
    }, network


def _texts(figure):
    return [t.get_text() for t in figure.findobj(Text) if t.get_text()]


def test_all_figures_build_for_a_normal_dataset(tmp_path):
    figures, _ = _all_figures(_dataset(tmp_path))
    assert set(figures) == {"A", "B", "C", "D1", "D2", "E"}
    for name, figure in figures.items():
        texts = _texts(figure)
        assert any("UNREVIEWED" in t for t in texts), name  # the status stamp is on every figure
        assert any("Quelle 0000-1" in t for t in texts), name


@pytest.mark.parametrize("n", [1, 2, 3, 40, 120])
def test_figures_build_for_any_number_of_contacts(tmp_path, n):
    dataset = _dataset(tmp_path, n=n, with_groups=n >= 11)
    figures, _ = _all_figures(dataset)
    assert len(figures) == 6


def test_figures_build_without_any_documented_tie_or_geography(tmp_path):
    def unknown_everywhere(rows):
        for row in rows:
            row.update(residence_city="", residence_country_iso3="", language_mode_code="", language_codes="", table_ring_near_value="")

    dataset = _dataset(tmp_path, n=5, with_groups=False, mutate=unknown_everywhere)
    figures, network = _all_figures(dataset)
    assert network.ties == () and len(figures) == 6


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
    assert digests[0].keys() == digests[1].keys() and len(digests[0]) == 18
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


def test_group_figure_draws_exactly_the_documented_ties(tmp_path):
    dataset = _dataset(tmp_path)
    figures, network = _all_figures(dataset)
    axes = figures["B"].axes[0]
    assert len(axes.lines) == len(network.positive_ties) == 9
    texts = " ".join(_texts(figures["B"]))
    assert "unbekannt" in texts and "dokumentierte Beziehungen" in texts
    assert "Ohne dokumentierte Beziehung" in texts
    # candidates A06-A08 are drawn without any connection
    assert not [t for t in network.ties if {"A06", "A07", "A08"} & {t.a, t.b}]


def test_group_layout_never_connects_components_and_is_seeded(tmp_path):
    import networkx as nx

    graph = nx.Graph([("A01", "A02"), ("A02", "A03"), ("A03", "A04"), ("A04", "A01"), ("A01", "A03")])
    first, second = groups.component_layout(graph), groups.component_layout(graph)
    assert first == second
    assert groups.component_layout(nx.Graph([("A01", "A02")])) == {"A01": (-0.8, 0.0), "A02": (0.8, 0.0)}


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
    figures, _ = _all_figures(_dataset(tmp_path, n=3, with_groups=False))
    texts = " ".join(_texts(figures["A"]))
    for meaning in ("überhaupt nicht nah", "eher wenig nah", "mittel", "nah", "sehr nah"):
        assert meaning in texts
    assert "keine Kontakte" in texts and "Tabellenwert" in texts


_LAYOUT_PROBE = """
import networkx as nx
from mares.networks.figures.groups import component_layout
edges = [("A01", "A02"), ("A01", "A03"), ("A02", "A03"), ("A02", "A04"), ("A03", "A04"),
         ("A04", "A05"), ("A05", "A06"), ("A04", "A06"), ("A06", "A07")]
nodes = {a for e in edges for a in e}
g = nx.Graph()
g.add_nodes_from(nodes)
g.add_edges_from(edges)
pos = component_layout(g)
print([(k, round(v[0], 9), round(v[1], 9)) for k, v in sorted(pos.items())])
"""


def test_group_layout_does_not_depend_on_the_process_hash_seed():
    """Sets of strings iterate differently in every process; the layout must not."""
    import os
    import subprocess
    import sys

    outputs = set()
    for seed in ("1", "2", "3", "4"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        result = subprocess.run([sys.executable, "-c", _LAYOUT_PROBE], capture_output=True, text=True, env=env, check=True)
        outputs.add(result.stdout)
    assert len(outputs) == 1
