"""network_v1 standard figures: the fixed set, file names, scientific rules visible in the drawing."""

from __future__ import annotations

import math

import pytest
from matplotlib.patches import PathPatch
from matplotlib.text import Text

from mares.network_v0.figures.style import rc
from mares.network_v1 import codes
from mares.network_v1.case import read_case
from mares.network_v1.figures import FIGURES, expected_files, render
from mares.network_v1.figures.base import Context, file_name
from mares.network_v1.figures.networks import g1_layout, g2, g3_layout, intruders
from mares.network_v1.testcases import synthetic_source
from mares.network_v1.validate import validate
from network_v1_fixtures import copy_002, read_rows, write_rows


def context(folder):
    case = read_case(folder)
    return Context(case, validate(case).derived)


@pytest.fixture(scope="module")
def ctx():
    return context(synthetic_source())


def test_exactly_eight_standard_figures():
    assert [s.code for s in FIGURES] == ["G1", "G2", "P1", "P2", "P3", "P4", "P5", "G3"]


def test_file_names_are_stable_and_ascii():
    assert file_name("001_test_v0_fictionalized", "G1", "persoenliches_netz", "png") == "001_test_v0_fictionalized_G1_persoenliches_netz.png"
    with pytest.raises(ValueError):
        file_name("001", "G1", "persönliches netz", "png")
    assert all(n.isascii() for n in expected_files("002_test_synthetic", ("png", "svg")))


def test_render_writes_only_the_eight_files_and_is_reproducible(ctx, tmp_path):
    first = render(ctx, tmp_path / "a")
    second = render(ctx, tmp_path / "b")
    names = sorted(p.name for p in (tmp_path / "a").iterdir())
    assert names == sorted(expected_files(ctx.code, ("png",)))
    assert all(e["status"] == "rendered" for e in first)
    for name in names:
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()
    assert [e["files"] for e in first] == [e["files"] for e in second]


def test_g1_radius_is_the_recorded_closeness(ctx):
    positions = g1_layout(ctx)
    for c in ctx.case.contacts:
        value = codes.closeness_value(c.closeness)
        if value is not None:
            assert math.hypot(*positions[c.id]) == pytest.approx(value)
    assert math.hypot(*positions["A22"]) > 4  # no recorded closeness: outside the rings, never on one


def test_g1_layout_is_deterministic(ctx):
    assert g1_layout(ctx) == g1_layout(ctx)


def test_g2_draws_confirmed_ties_only_and_no_ego(ctx):
    with rc():
        figure = g2(ctx)
    ax = figure.axes[0]
    texts = [t.get_text() for t in ax.findobj(Text)]
    assert not any("Ego" == t for t in texts)
    ties = [p for p in ax.patches if isinstance(p, PathPatch) and p.get_gid() == "tie"]
    assert len(ties) == len(ctx.derived.confirmed_edges) == 35  # one line per confirmed pair, no ego lines


def test_g3_keeps_non_members_out_of_group_outlines(ctx):
    assert intruders(ctx, g3_layout(ctx)) == []


def test_no_labels_of_persons_in_any_figure(tmp_path):
    case = copy_002(tmp_path)
    rows = read_rows(case, "contacts.csv")
    for i, row in enumerate(rows):
        row["label"] = f"Pseudonym-Xq{i:02d}"
    write_rows(case, "contacts.csv", rows)
    named = context(case)
    for spec in FIGURES:
        with rc():
            figure = spec.draw(named)
        texts = " ".join(t.get_text() for t in figure.findobj(Text))
        assert "Pseudonym-Xq" not in texts, spec.code
        assert "TESTFALL 002* · SYNTHETISCH" in texts  # case badge on every figure
        assert "MARES · network_v1 · 32 Kontakte · 5 Gruppen" in texts  # the same footer on every figure


def test_coverage_is_stated_on_network_figures(ctx):
    for spec in FIGURES:
        if spec.code in ("G2", "G3"):  # G1 shows no ties, so it states no coverage
            with rc():
                texts = " ".join(t.get_text() for t in spec.draw(ctx).findobj(Text))
            assert "unbekannt 454" in texts, spec.code


def test_a_figure_without_data_is_skipped_with_a_reason(tmp_path):
    case = copy_002(tmp_path)
    write_rows(case, "groups.csv", [], ["group_id", "label", "connection_status", "belonging", "comment"])
    write_rows(case, "group_memberships.csv", [], ["group_id", "contact_id"])
    rows = [r for r in read_rows(case, "alter_connections.csv") if r["source"] == ""]
    write_rows(case, "alter_connections.csv", rows)
    entries = {e["code"]: e for e in render(context(case), tmp_path / "out")}
    assert entries["G3"]["status"] == "skipped" and entries["G3"]["reason"] and not entries["G3"]["files"]
    assert not list((tmp_path / "out").glob("*G3*"))
    assert entries["G1"]["status"] == "rendered"


def test_svg_is_optional(ctx, tmp_path):
    render(ctx, tmp_path, ("png", "svg"))
    assert len(list(tmp_path.glob("*.svg"))) == 8
    with pytest.raises(ValueError):
        render(ctx, tmp_path, ("pdf",))
