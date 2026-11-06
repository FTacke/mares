"""Experiment G3 by birth country: same group map as G3, birth-country colours, local view, output outside graphics/."""

from __future__ import annotations

import hashlib

import numpy as np
import pytest
from matplotlib.colors import to_hex
from matplotlib.patches import Polygon

from mares.core.refs import StorageRef
from mares.network_v0.figures.style import rc
from mares.network_v1.case import read_case
from mares.network_v1.experiments import G3_BIRTH_DIR, render_g3_birth
from mares.network_v1.figures import FIGURES, expected_files
from mares.network_v1.figures.base import MISSING_FILL, Context
from mares.network_v1.figures.birth_country import (
    EXPERIMENT, OTHER_FILL, OTHER_LABEL, PALETTE, TITLE_LOCAL, TITLE_TOTAL, birth_figure, birth_key, countries, legend_entries,
    local_context,
)
from mares.network_v1.figures.networks import g3, g3_geometry, group_colors
from mares.network_v1.places import Area
from mares.network_v1.run import process_case
from mares.network_v1.testcases import SYNTHETIC_CODE, synthetic_source
from mares.network_v1.validate import validate
from mares.networks import cli
from network_v1_fixtures import copy_002, edit, machine, roots_for

LOCAL = (Area.MARBURG, Area.MITTELHESSEN)


@pytest.fixture(scope="module")
def ctx():
    case = read_case(synthetic_source())
    return Context(case, validate(case).derived)


def draw(ctx_, view, variant):
    with rc():
        return birth_figure(ctx_, view, variant)


def texts(figure) -> list[str]:
    return [t.get_text() for t in figure.findobj(lambda a: hasattr(a, "get_text") and a.get_text())]


def node_fills(figure) -> dict[str, str]:
    """Contact ID -> node colour, read from the drawn figure (the ID text sits on its node)."""
    ax = figure.axes[0]
    nodes = [(tuple(np.round(o, 4)), to_hex(c)) for coll in ax.collections for o, c in zip(coll.get_offsets(), coll.get_facecolors())]
    out = {}
    for t in ax.texts:
        x, y = t.get_position()
        for (nx, ny), fill in nodes:
            if abs(nx - x) < 1e-3 and abs(ny - y - 0) < 0.04 and t.get_text().startswith("A") and len(t.get_text()) == 3:
                out[t.get_text()] = fill
    return out


# --------------------------------------------------------------------------------------------- the data ---
def test_only_the_recorded_birth_country_is_used(ctx):
    for c in ctx.case.contacts:
        assert birth_key(c) == c.birth_country_iso3
    contact = ctx.case.contacts[0]
    from dataclasses import replace
    assert birth_key(replace(contact, birth_country_iso3="KA", birth_country="")) is None
    assert birth_key(replace(contact, birth_country_iso3="", birth_country="")) is None
    assert birth_key(replace(contact, birth_country_iso3="", birth_country="Atlantis")) == "~Atlantis"  # named, not coded: kept


def test_the_palette_has_nine_distinct_colours_without_the_missing_and_grey_fills():
    assert len(set(PALETTE)) == len(PALETTE) == 9
    assert OTHER_FILL not in PALETTE and MISSING_FILL not in PALETTE


def test_colours_follow_the_country_and_are_stable(ctx):
    cs = countries(ctx)
    assert cs == countries(ctx)  # deterministic
    coloured = [k for k in cs.order if cs.fill[k] != OTHER_FILL]
    assert len(set(cs.fill[k] for k in coloured)) == len(coloured) == min(len(cs.order), len(PALETTE))
    grey = [k for k in cs.order if cs.fill[k] == OTHER_FILL]
    assert len(grey) == max(len(cs.order) - len(PALETTE), 0)
    counts = {k: sum(1 for v in cs.of.values() if v == k) for k in cs.order}
    assert min((counts[k] for k in coloured), default=0) >= max((counts[k] for k in grey), default=0)  # frequent first


def test_a_countrys_colour_does_not_depend_on_rows_it_does_not_share(tmp_path):
    """Colour per code where the other countries allow: a country added with a free slot leaves the others as they are."""
    case = copy_002(tmp_path)
    before = countries(Context(read_case(case), validate(read_case(case)).derived))
    edit(case, "contacts.csv", "A23", "birth_country_iso3", "")
    edit(case, "contacts.csv", "A23", "birth_country", "")
    after = countries(Context(read_case(case), validate(read_case(case)).derived))
    same = [k for k in after.order if after.fill[k] != OTHER_FILL and before.fill.get(k) != OTHER_FILL]
    assert all(after.fill[k] == before.fill[k] for k in same)
    assert after.of["A23"] is None


# -------------------------------------------------------------------------------------------- the views ---
def test_the_total_view_is_the_group_map_of_g3(ctx):
    with rc():
        reference = g3(ctx).axes[0]
    for variant in ("kuerzel", "legende"):
        ax = draw(ctx, "gesamt", variant).axes[0]
        ref_outlines = sorted((p.get_gid(), to_hex(p.get_edgecolor())) for p in reference.patches if (p.get_gid() or "").startswith("group-"))
        outlines = sorted((p.get_gid(), to_hex(p.get_edgecolor())) for p in ax.patches if (p.get_gid() or "").startswith("group-"))
        assert outlines == ref_outlines
        assert sum(p.get_gid() == "tie" for p in ax.patches) == len(ctx.derived.confirmed_edges)
    # same positions as G3 in both variants (the larger nodes of variant 1 do not move them)
    assert g3_geometry(ctx).positions == g3_geometry(ctx, node_r=0.2).positions


def test_every_node_shows_its_birth_country_and_both_views_share_the_colours(ctx):
    cs = countries(ctx)
    for view in ("gesamt", "lokal"):
        for variant in ("kuerzel", "legende"):
            fills = node_fills(draw(ctx, view, variant))
            assert fills
            for cid, fill in fills.items():
                expected = cs.contact_fill(cid)
                assert fill == (MISSING_FILL.lower() if expected is None else expected.lower()), (view, variant, cid)


def test_variant_1_writes_the_code_in_the_node_variant_2_does_not(ctx):
    codes = {c.birth_country_iso3 for c in ctx.case.contacts}
    v1 = texts(draw(ctx, "gesamt", "kuerzel"))
    v2 = texts(draw(ctx, "gesamt", "legende"))
    assert codes <= set(v1)
    assert not codes & set(v2)


def test_the_legend_names_only_countries_that_occur(ctx):
    cs = countries(ctx)
    local = local_context(ctx)
    for view, ids in (("gesamt", ctx.case.contact_ids), ("lokal", local.case.contact_ids)):
        entries = legend_entries(cs, ids, "legende")
        named = [e[1] for e in entries if not e[1].startswith(OTHER_LABEL)]
        present = {cs.of[c] for c in ids}
        assert {n for n in named} == {cs.name[k] for k in present if k is not None and cs.fill[k] != OTHER_FILL}
        if any(cs.fill[k] == OTHER_FILL for k in present if k):
            assert any(e[1].startswith(OTHER_LABEL) for e in entries)


def test_missing_birth_country_is_marked(tmp_path):
    case = copy_002(tmp_path)
    edit(case, "contacts.csv", "A01", "birth_country_iso3", "KA")
    edit(case, "contacts.csv", "A01", "birth_country", "")
    c = read_case(case)
    ctx_ = Context(c, validate(c).derived)
    assert ("dot", "keine Angabe", None) in legend_entries(countries(ctx_), c.contact_ids, "kuerzel")
    assert "keine Angabe" in texts(draw(ctx_, "gesamt", "legende"))


def test_the_local_view_keeps_only_local_contacts_their_ties_and_groups(ctx):
    local = local_context(ctx)
    keep = {cid for cid in ctx.case.contact_ids if ctx.derived.area(cid) in LOCAL}
    assert set(local.case.contact_ids) == keep
    assert {e for e in local.derived.confirmed_edges} == {e for e in ctx.derived.confirmed_edges if set(e) <= keep}
    assert {g.id for g in local.case.groups} == {g.id for g in ctx.case.groups if set(ctx.case.members(g.id)) & keep}
    for g in local.case.groups:
        assert local.case.members(g.id) == [m for m in ctx.case.members(g.id) if m in keep]
        full = next(h for h in ctx.case.groups if h.id == g.id)
        assert (g.label, g.belonging) == (full.label, full.belonging)  # original group, original ID
    assert local.case.groups != ctx.case.groups  # 002 has groups without a local member


def test_the_local_view_tells_local_from_total_members(ctx):
    local = local_context(ctx)
    figure = draw(ctx, "lokal", "legende")
    shown = texts(figure)
    assert TITLE_LOCAL in shown
    for g in local.case.groups:
        n, total = len(local.case.members(g.id)), len(ctx.case.members(g.id))
        count = f"({n})" if n == total else f"({n} von {total})"
        assert any(t.startswith(f"{g.id} · ") and t.endswith(count) for t in shown), g.id
    hidden = [g.id for g in ctx.case.groups if g.id not in {h.id for h in local.case.groups}]
    assert any(all(h in t for h in hidden) and "nicht dargestellt" in t for t in shown)
    assert any(t.startswith(f"Dargestellt: {len(local.case.contacts)} von {len(ctx.case.contacts)} Kontakten") for t in shown)
    assert "MARES · network_v1 · 32 Kontakte" in shown  # the footer counts the case


def test_group_outline_colours_are_those_of_g3_in_both_views(ctx):
    colors = group_colors(ctx)
    for view in ("gesamt", "lokal"):
        ax = draw(ctx, view, "kuerzel").axes[0]
        for p in ax.patches:
            if isinstance(p, Polygon) and (p.get_gid() or "").startswith("group-"):
                assert to_hex(p.get_edgecolor()) == colors[p.get_gid()[6:]].lower()


def test_titles(ctx):
    assert TITLE_TOTAL in texts(draw(ctx, "gesamt", "kuerzel"))
    with pytest.raises(ValueError):
        birth_figure(ctx, "regional", "kuerzel")


def test_no_label_box_covers_a_node(ctx):
    for view in ("gesamt", "lokal"):
        view_ctx = local_context(ctx) if view == "lokal" else ctx
        geometry = g3_geometry(view_ctx, node_r=24 / 72 / 2)
        for box in geometry.labels.values():
            for x, y in geometry.positions.values():
                r = 24 / 72 / 2
                assert not (box[0] < x + r and x - r < box[2] and box[1] < y + r and y - r < box[3])


# --------------------------------------------------------------------------------------- output paths ---
def test_the_experiment_writes_only_into_its_own_folder_and_is_no_standard_figure(tmp_path):
    folders = machine(tmp_path)
    copy_002(folders["intake"])
    roots = roots_for(folders)
    ref = StorageRef("INTAKE", f"network_v1/pilots/{SYNTHETIC_CODE}")
    process_case(roots, ref, formats=("png",))
    graphics = folders["intake"] / "network_v1" / "pilots" / SYNTHETIC_CODE / "graphics"
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in graphics.iterdir()}
    result = render_g3_birth(roots, ref)
    assert result.status == "COMPLETED"
    folder = folders["intake"] / "network_v1" / "pilots" / SYNTHETIC_CODE / "/".join(G3_BIRTH_DIR)
    names = {p.name for p in folder.iterdir()}
    assert names == {f"{SYNTHETIC_CODE}_G3_geburtsland_{v}_{w}.{ext}" for v, w in EXPERIMENT for ext in ("png", "svg")}
    assert {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in graphics.iterdir()} == before  # standard set untouched
    assert len(FIGURES) == 9 and not any("geburtsland" in n for n in expected_files(SYNTHETIC_CODE, ("png", "svg")))
    record = (folders["workspace"] / "runs" / result.run_id / "run_record.json").read_text(encoding="utf-8")
    assert '"standard_figure": false' in record
    assert "COL" not in record and "Kolumbien" not in record  # counts only, no countries


def test_a_case_with_validation_errors_gets_no_experimental_figure(tmp_path):
    folders = machine(tmp_path)
    case = copy_002(folders["intake"])
    edit(case, "contacts.csv", "A01", "birth_country_iso3", "XXX")
    result = render_g3_birth(roots_for(folders), StorageRef("INTAKE", f"network_v1/pilots/{SYNTHETIC_CODE}"))
    assert result.status == "FAILED_VALIDATION" and not result.outputs
    assert not (case / G3_BIRTH_DIR[0]).exists()


def test_command_line(tmp_path, capsys):
    folders = machine(tmp_path)
    copy_002(folders["intake"])
    roots = roots_for(folders)
    assert cli.main(["v1", "experiment", "g3-geburtsland", "--root", "INTAKE", "--formats", "png"], roots=roots) == 0
    assert "g3-geburtsland COMPLETED  4 files" in capsys.readouterr().out
