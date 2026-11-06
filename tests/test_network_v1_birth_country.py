"""G4 and G5 (group map by birth country): fixed country colours, codes in the nodes, G4 = G3's map, G5 = the G3 layout
of the local sub-network (compacted, no geography), one local note, skip reasons and register details."""

from __future__ import annotations

import hashlib
from dataclasses import replace

import numpy as np
import pytest
from matplotlib.colors import to_hex

from mares.core.refs import StorageRef
from mares.network_v0.figures.style import luminance, rc
from mares.network_v1.case import read_case
from mares.network_v1.figures import FIGURES, expected_files
from mares.network_v1.figures.base import MISSING_FILL, RELATION_COLORS, Context
from mares.network_v1.figures.birth_country import (
    COUNTRY_COLORS, EXTENSION, NO_ANSWER_SHORT, NODE_PT_CODE, UNCODED_FILL, g4, g4_missing, g5, g5_details, g5_missing,
    birth_key, countries, country_fill, legend_entries, local_context, local_size, text_color,
)
from mares.network_v1.figures.networks import g3, g3_geometry, g3_layout, group_colors, intruders, structure_parts
from mares.network_v1.places import Area
from mares.network_v1.run import process_case
from mares.network_v1.testcases import SYNTHETIC_CODE, synthetic_source
from mares.network_v1.validate import validate
from mares.networks import cli
from network_v1_fixtures import copy_002, edit, machine, read_rows, roots_for, write_rows

LOCAL = (Area.MARBURG, Area.MITTELHESSEN)


@pytest.fixture
def small(tmp_path):
    """A copy of 002 in which only the members of C01 and C05 live in Marburg: a small local network of two groups that
    share neither a member nor a tie."""
    case = copy_002(tmp_path)
    full = context_of(case)
    keep = set(full.case.members("C01")) | set(full.case.members("C05"))
    rows = read_rows(case, "contacts.csv")
    for row in rows:
        row["residence_place"], row["residence_country"], row["residence_country_iso3"] = (
            ("Marburg", "Deutschland", "DEU") if row["contact_id"] in keep else ("Berlin", "Deutschland", "DEU"))
    write_rows(case, "contacts.csv", rows)
    return context_of(case)
FREQUENT = ("DEU", "COL", "PER", "MEX", "ECU", "CHL", "CUB", "VEN", "ESP", "ARG")


@pytest.fixture(scope="module")
def ctx():
    case = read_case(synthetic_source())
    return Context(case, validate(case).derived)


def context_of(folder) -> Context:
    case = read_case(folder)
    return Context(case, validate(case).derived)


VIEWS = ("gesamt", "lokal")


def draw(ctx_, view):
    with rc():
        return (g4 if view == "gesamt" else g5)(ctx_)


def texts(figure) -> list[str]:
    return [t.get_text() for t in figure.findobj(lambda a: hasattr(a, "get_text") and a.get_text())]


def node_fills(figure) -> dict[str, tuple[str, str]]:
    """Contact ID -> (node colour, code text below the ID), read from the drawn figure."""
    ax = figure.axes[0]
    nodes = [(tuple(np.round(o, 4)), to_hex(c)) for coll in ax.collections for o, c in zip(coll.get_offsets(), coll.get_facecolors())]
    by_pos = {(round(t.get_position()[0], 3), round(t.get_position()[1], 3)): t.get_text() for t in ax.texts}
    out = {}
    for t in ax.texts:
        cid = t.get_text()
        if not (len(cid) == 3 and cid[0] == "A" and cid[1:].isdigit()):
            continue
        x, y = t.get_position()
        fill = next(f for (nx, ny), f in nodes if abs(nx - x) < 1e-3 and abs(ny - (y - 0.033)) < 1e-3)
        out[cid] = (fill, by_pos.get((round(x, 3), round(y - 0.093, 3)), ""))
    return out


# ------------------------------------------------------------------------------------------- colours ---
def test_the_frequent_countries_have_fixed_distinct_colours():
    assert all(code in COUNTRY_COLORS for code in FREQUENT)
    assert len({COUNTRY_COLORS[c] for c in FREQUENT}) == len(FREQUENT)
    assert len(set(COUNTRY_COLORS.values())) == len(COUNTRY_COLORS)
    assert MISSING_FILL not in COUNTRY_COLORS.values() and UNCODED_FILL not in COUNTRY_COLORS.values()
    assert not set(EXTENSION) & set(COUNTRY_COLORS.values())  # a country without fixed colour never looks like a fixed one


def test_a_country_has_the_same_colour_in_every_case(ctx):
    full = countries(ctx)
    few = [c for c in ctx.case.contacts if c.birth_country_iso3 in ("PER", "GBR", "POL")]  # another mix of countries
    other = countries(Context(replace(ctx.case, contacts=few), ctx.derived))
    for c in few:
        assert other.contact_fill(c.id) == full.contact_fill(c.id) == country_fill(c.birth_country_iso3)
    for code in ("PER", "XKX", "NZL"):  # fixed or not: a function of the code alone
        assert country_fill(code) == country_fill(code)
    assert country_fill("NZL") in EXTENSION and country_fill("PER") == COUNTRY_COLORS["PER"]


def test_the_relation_palette_is_untouched():
    assert RELATION_COLORS == {"1": "#D55E00", "2": "#CC79A7", "3": "#009E73", "4": "#56B4E9", "5": "#0072B2", "6": "#6B7280"}


def test_node_text_keeps_enough_contrast_on_every_country_colour():
    def contrast(a, b):
        hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
        return (hi + 0.05) / (lo + 0.05)
    for fill in set(COUNTRY_COLORS.values()) | set(EXTENSION) | {UNCODED_FILL}:
        assert contrast(fill, text_color(fill)) >= 4.5, fill


def test_birth_country_keys(ctx):
    contact = ctx.case.contacts[0]
    assert birth_key(replace(contact, birth_country_iso3="KA", birth_country="")) is None
    assert birth_key(replace(contact, birth_country_iso3="", birth_country="")) is None
    assert birth_key(replace(contact, birth_country_iso3="", birth_country="Atlantis")) == "~Atlantis"  # named, not coded: kept
    assert country_fill(None) is None and country_fill("~Atlantis") == UNCODED_FILL


# -------------------------------------------------------------------------------------------- nodes ---
def test_every_node_shows_its_colour_and_code_in_both_views(ctx):
    for view in VIEWS:
        drawn = node_fills(draw(ctx, view))
        assert drawn
        for cid, (fill, code) in drawn.items():
            iso = ctx.case.contact(cid).birth_country_iso3
            assert fill == country_fill(iso).lower(), (view, cid)
            assert code == iso, (view, cid)


def test_missing_birth_country_is_neutral_and_gets_no_invented_code(tmp_path):
    case = copy_002(tmp_path)
    edit(case, "contacts.csv", "A01", "birth_country_iso3", "KA")
    edit(case, "contacts.csv", "A01", "birth_country", "")
    ctx_ = context_of(case)
    assert ("dot", "keine Angabe", None) in legend_entries(countries(ctx_), ctx_.case.contact_ids)
    fill, code = node_fills(draw(ctx_, "gesamt"))["A01"]
    assert fill == MISSING_FILL.lower() and code == NO_ANSWER_SHORT


def test_the_legend_names_the_countries_that_occur_in_one_fixed_order(ctx):
    cs = countries(ctx)
    local = local_context(ctx)
    total = [e[1] for e in legend_entries(cs, ctx.case.contact_ids)]
    local_entries = [e[1] for e in legend_entries(cs, local.case.contact_ids)]
    assert {e.split(" (")[0] for e in total} == {c.birth_country for c in ctx.case.contacts}
    assert {e.split(" (")[0] for e in local_entries} == {c.birth_country for c in local.case.contacts}
    assert [e for e in total if e in local_entries] == local_entries  # the local legend keeps the order of the total one
    assert total[:2] == ["Deutschland (DEU)", "Kolumbien (COL)"]  # fixed countries first, in their fixed order


# ---------------------------------------------------------------------------------------- the views ---
def test_the_total_view_is_the_group_map_of_g3(ctx):
    with rc():
        reference = g3(ctx).axes[0]
    ax = draw(ctx, "gesamt").axes[0]

    def outlines(a):
        return sorted((p.get_gid(), to_hex(p.get_edgecolor())) for p in a.patches if (p.get_gid() or "").startswith("group-"))
    assert outlines(ax) == outlines(reference)
    assert sum(p.get_gid() == "tie" for p in ax.patches) == len(ctx.derived.confirmed_edges)
    assert g3_geometry(ctx).positions == g3_geometry(ctx, node_r=0.2).positions  # larger nodes do not move them
    assert "Gruppenstruktur nach Geburtsland" in texts(ax.figure)


def test_the_local_view_keeps_only_local_contacts_their_ties_and_groups(ctx):
    local = local_context(ctx)
    keep = {cid for cid in ctx.case.contact_ids if ctx.derived.area(cid) in LOCAL}
    assert set(local.case.contact_ids) == keep
    assert set(local.derived.confirmed_edges) == {e for e in ctx.derived.confirmed_edges if set(e) <= keep}
    assert {g.id for g in local.case.groups} == {g.id for g in ctx.case.groups if set(ctx.case.members(g.id)) & keep}
    for g in local.case.groups:
        assert local.case.members(g.id) == [m for m in ctx.case.members(g.id) if m in keep]
    ax = draw(ctx, "lokal").axes[0]
    assert sum(p.get_gid() == "tie" for p in ax.patches) == len(local.derived.confirmed_edges)
    colors = group_colors(ctx)
    for p in ax.patches:
        if (p.get_gid() or "").startswith("group-"):
            assert to_hex(p.get_edgecolor()) == colors[p.get_gid()[6:]].lower()  # outline colours of the case


def local_geometry(ctx_):
    local = local_context(ctx_)
    node_r = NODE_PT_CODE / 72 / 2
    width, height = local_size(local, node_r)
    return local, node_r, g3_geometry(local, node_r=node_r, width=width, height=height, compact=True)


def test_the_local_view_has_no_geography(ctx):
    figure = draw(ctx, "lokal")
    assert len(figure.axes) == 2  # main area and legend: no map axes
    gids = [p.get_gid() or "" for a in figure.axes for p in a.patches]
    assert not any(g.startswith("zone-") for g in gids)
    shown = set(texts(figure))
    assert not {"Marburg", "Übriges Mittelhessen", "Marburg und Mittelhessen"} & shown


def test_compaction_moves_whole_parts_only(small):
    local = local_context(small)
    plain, packed = g3_layout(local), g3_layout(local, compact=True)
    parts = structure_parts(local, list(plain))
    assert len(parts) >= 2  # the fixture has unconnected local parts
    for part in parts:  # inside a part every node keeps its place relative to the others (up to the common scale)
        a, b = np.array([plain[n] for n in part]), np.array([packed[n] for n in part])
        da, db = a - a[0], b - b[0]
        scale = (np.linalg.norm(db) / np.linalg.norm(da)) if np.linalg.norm(da) > 0 else 1.0
        assert np.allclose(db, da * scale, atol=1e-6)
    gap = lambda pos: min(np.hypot(pos[a][0] - pos[b][0], pos[a][1] - pos[b][1]) for a in parts[0] for b in parts[1])  # noqa: E731
    assert gap(packed) < gap(plain)  # the parts moved together


def test_the_local_layout_is_compact_and_free_of_overlaps(ctx, small):
    for ctx_ in (ctx, small):
        local, node_r, geometry = local_geometry(ctx_)
        pts = list(geometry.positions.values())
        assert min(np.hypot(a[0] - b[0], a[1] - b[1]) for i, a in enumerate(pts) for b in pts[i + 1:]) > 2 * node_r
        assert not intruders(local, {c: xy for c, xy in geometry.positions.items() if c not in geometry.loose})
        for box in geometry.labels.values():
            for x, y in geometry.positions.values():
                assert not (box[0] < x + node_r and x - node_r < box[2] and box[1] < y + node_r and y - node_r < box[3])


def test_no_label_or_node_leaves_the_main_area(ctx, small):
    for ctx_ in (ctx, small):
        local, node_r, geometry = local_geometry(ctx_)
        width, height = local_size(local, node_r)
        for x, y in geometry.positions.values():
            assert node_r <= x <= width - node_r and node_r <= y <= height - node_r
        for box in geometry.labels.values():
            assert box[0] >= 0 and box[2] <= width and box[1] >= 0 and box[3] <= height


def test_the_local_view_tells_local_from_total_members(ctx):
    local = local_context(ctx)
    shown = texts(draw(ctx, "lokal"))
    assert "Lokale Gruppenstruktur nach Geburtsland" in shown
    for g in local.case.groups:
        n, total = len(local.case.members(g.id)), len(ctx.case.members(g.id))
        count = f"({n})" if n == total else f"({n} von {total})"
        assert any(t.startswith(f"{g.id} · ") and t.endswith(count) for t in shown), g.id
    assert any("5 von 7" in t for t in shown)  # 002: C04 has five of seven members in the area


def test_the_local_view_has_exactly_one_short_note(ctx):
    local = local_context(ctx)
    shown = texts(draw(ctx, "lokal"))
    note = f"Lokaler Ausschnitt: {len(local.case.contacts)} von {len(ctx.case.contacts)} Kontakten (Marburg und Mittelhessen)."
    assert note in shown
    assert not any(t.startswith(("Wohnort nicht zuordenbar", "Dargestellt", "Ohne lokale")) or "nicht dargestellt" in t for t in shown)
    assert "MARES · network_v1 · 32 Kontakte" in shown  # the footer counts the whole case


def test_what_the_local_view_leaves_out_is_in_the_register(ctx):
    details = g5_details(ctx)
    local = local_context(ctx)
    assert details["contacts_shown"] == len(local.case.contacts) and details["contacts_total"] == 32
    assert details["unresolved_residence"] == ctx.unresolved()
    assert set(details["groups_without_local_members"]) == {g.id for g in ctx.case.groups} - {g.id for g in local.case.groups}
    assert details["groups_partly_shown"]["C04"] == "5 von 7"
    left_out = {c for ids in details["not_shown_by_area"].values() for c in ids} | set(details["unresolved_residence"])
    assert left_out == set(ctx.case.contact_ids) - set(local.case.contact_ids)


# ----------------------------------------------------------------------------------- skips and output ---
def test_skip_reasons(tmp_path, ctx):
    assert g4_missing(ctx) is None and g5_missing(ctx) is None
    no_groups = Context(replace(ctx.case, groups=[], memberships=[]), ctx.derived)
    assert g4_missing(no_groups) == g5_missing(no_groups) == "keine Gruppen erhoben"
    nobody = Context(replace(ctx.case, contacts=[replace(c, birth_country="", birth_country_iso3="") for c in ctx.case.contacts]),
                     ctx.derived)
    assert g4_missing(nobody) == "kein Geburtsland erhoben"
    case = copy_002(tmp_path)
    for row in read_rows(case, "contacts.csv"):
        edit(case, "contacts.csv", row["contact_id"], "residence_place", "Berlin")
    far = context_of(case)
    assert g4_missing(far) is None and g5_missing(far) == "kein Kontakt mit Wohnort in Marburg oder Mittelhessen"


def test_g4_and_g5_are_standard_figures_in_graphics(tmp_path):
    folders = machine(tmp_path)
    copy_002(folders["intake"])
    roots = roots_for(folders)
    result = process_case(roots, StorageRef("INTAKE", f"network_v1/pilots/{SYNTHETIC_CODE}"), formats=("png", "svg"))
    assert result.status == "COMPLETED"
    graphics = folders["intake"] / "network_v1" / "pilots" / SYNTHETIC_CODE / "graphics"
    names = {p.name for p in graphics.iterdir()}
    assert names == expected_files(SYNTHETIC_CODE, ("png", "svg")) and len(names) == 22
    assert {f"{SYNTHETIC_CODE}_G4_gruppen_geburtsland.png", f"{SYNTHETIC_CODE}_G5_lokale_gruppen_geburtsland.svg"} <= names
    assert not (graphics.parent / "experimental").exists()
    record = result.record
    g5_entry = next(f for f in record["figures"] if f["code"] == "G5")
    assert g5_entry["status"] == "rendered" and g5_entry["details"]["groups_partly_shown"] == {"C04": "5 von 7"}
    index = (folders["workspace"] / "runs" / result.run_id / "figures_index.json").read_text(encoding="utf-8")
    assert '"G4"' in index and '"G5"' in index and "Kolumbien" not in index  # no country names in the register


def test_the_experiment_command_is_gone():
    from mares.network_v1.cli import build_parser
    with pytest.raises(SystemExit):
        build_parser().parse_args(["experiment", "g3-geburtsland", "--root", "INTAKE"])
