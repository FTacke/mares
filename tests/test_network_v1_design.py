"""network_v1: coding key of the final survey sheet and the shared design system of the eleven figures."""

from __future__ import annotations

import json
import math
from collections import Counter

import numpy as np
import pytest
from matplotlib.collections import PathCollection
from matplotlib.colors import to_hex
from matplotlib.patches import PathPatch, Polygon
from matplotlib.path import Path as MplPath
from matplotlib.text import Text
from matplotlib.transforms import Bbox

from mares.network_v0.figures.style import rc
from mares.network_v1 import codes
from mares.network_v1.case import read_case
from mares.network_v1.figures import FIGURES
from mares.network_v1.figures import base
from mares.network_v1.figures.base import (
    HEAT_NEUTRAL, RELATION_COLORS, Context, case_badge, draw_legend, heat_cell, heat_fill, relation_entries,
)
from mares.network_v1.figures.matrices import COMMUNICATION_SECTIONS, _matrix_counts, language_rows
from mares.network_v1.figures.networks import (
    G1_SIZE, LABEL_HALF_WIDTH, LEADER_GAP, MISSING_RADIUS, NODE_R_IN, OUTLINE_W, SECTOR_ORDER, display_name, g1, g1_layout, g1_sectors,
    g2, g2_layout, g3, g3_layout, g3_positions, loose_contacts, membership_marked, nested_groups, relation_code, subgroups,
)
from mares.network_v1.places import Area
from mares.network_v1.testcases import synthetic_source
from mares.network_v1.validate import validate
from network_v1_fixtures import copy_002, geo, read_rows, write_rows


def context(folder):
    case = read_case(folder)
    return Context(case, validate(case).derived)


@pytest.fixture(scope="module")
def ctx(tmp_path_factory):
    case = read_case(synthetic_source())
    return Context(case, validate(case).derived, geo(tmp_path_factory.mktemp("geo")))


# ------------------------------------------------------------------------------- coding key (survey sheet) ---
def test_code_lists_follow_the_coding_key_of_the_survey_sheet():
    assert list(codes.RELATION_TYPE.values()) == ["Familie", "Partner:in", "Freund:in", "Bekannte:r", "Professionell / institutionell",
                                                  "Sonstige Beziehung"]
    assert codes.CONTACT_FREQUENCY["1"] == "(Fast) täglich" and codes.CONTACT_FREQUENCY["5"] == "Wenige Male/Jahr oder seltener"
    assert list(codes.FUNCTIONS) == ["1", "2", "3", "4", "5", "0"] and codes.FUNCTIONS["0"] == "Nichts davon"
    assert list(codes.COMMUNICATION_FORMS.values()) == ["Persönlich", "Videoanruf", "Telefonat", "Sprachnachrichten",
                                                        "Textnachrichten / Chat", "Sonstiges"]
    assert list(codes.LANGUAGES.values()) == ["Spanisch", "Deutsch", "Englisch", "Portugiesisch", "Andere Sprache"]
    assert set(codes.GROUP_STATUS) == {"T", "P", "N", "NS"} and list(codes.BELONGING) == ["1", "2", "3", "4", "5"]
    assert set(codes.CONNECTION) == {"1", "0", "?"} and set(codes.MARKERS) == {"NS", "KA", "NA"}


@pytest.mark.parametrize("raw, value", [("1–2", "1.5"), ("2-3", "2.5"), ("3 – 4", "3.5"), ("2,5", "2.5"), ("4", "4")])
def test_closeness_accepts_the_range_notation_of_the_sheet(raw, value):
    cell = codes.read_closeness(raw)
    assert cell.values == (value,) and cell.raw == raw  # the original spelling is kept


@pytest.mark.parametrize("raw", ["1-3", "2-1", "0-1", "4-5"])
def test_closeness_rejects_other_ranges(raw):
    assert codes.read_closeness(raw).error


def test_the_closing_block_is_checked_against_the_tables(tmp_path):
    folder = copy_002(tmp_path)
    meta_path = folder / "data" / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["closing"] = {"n_contacts": 31, "n_groups": 5, "contact_naming": "ended_early", "connections": "complete"}
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    found = {f.code: f.level for f in validate(read_case(folder)).findings}
    assert found["closing_count"] == "warning"  # 31 stated, 32 transcribed
    assert found["closing_reason"] == "note"  # ended early without a reason
    assert found["closing_connections"] == "warning"  # 'complete', but P/NS groups leave pairs unknown
    meta["closing"] = {"contact_naming": "maybe"}
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    assert "closing_value" in {f.code for f in validate(read_case(folder)).errors}


def test_the_closing_block_is_not_required_of_a_test_case(tmp_path):
    folder = copy_002(tmp_path)
    meta_path = folder / "data" / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    del meta["closing"]
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    assert "closing_missing" not in {f.code for f in validate(read_case(folder)).findings}  # test case: not required


def test_explanations_expected_by_the_sheet_are_noted(tmp_path):
    folder = copy_002(tmp_path)
    rows = read_rows(folder, "communication.csv")
    for row in rows:
        if row["contact_id"] == "A14":  # code 6 'Sonstiges' and S
            row["comment"] = ""
    write_rows(folder, "communication.csv", rows)
    notes = [f for f in validate(read_case(folder)).notes if f.code == "comment_expected"]
    assert len(notes) == 1 and "A14" in notes[0].message and "Sonstiges" in notes[0].message and "S" in notes[0].message


# ------------------------------------------------------------------------------------------- design system ---
def test_relation_palette_is_the_agreed_one():
    assert RELATION_COLORS == {"1": "#D55E00", "2": "#CC79A7", "3": "#009E73", "4": "#56B4E9", "5": "#0072B2", "6": "#6B7280"}


def test_relation_legend_has_the_same_order_labels_and_colours_everywhere(ctx):
    entries = relation_entries(ctx.case)  # 002 has no 'Sonstige Beziehung'
    assert [e[1] for e in entries] == list(codes.RELATION_TYPE.values())[:5]
    assert [e[2] for e in entries] == list(RELATION_COLORS.values())[:5]


def _with_relation_types(tmp_path, mapping):
    """A copy of 002 whose relation types are replaced (code -> code, '' = no answer)."""
    case = copy_002(tmp_path / "tree")
    rows = read_rows(case, "contacts.csv")
    for row in rows:
        row["relation_type"] = mapping.get(row["relation_type"], row["relation_type"])
    write_rows(case, "contacts.csv", rows)
    data = read_case(case)
    return Context(data, validate(data).derived, geo(tmp_path))


def test_the_relation_legend_shows_only_the_types_of_the_case_in_the_fixed_order_and_colours(tmp_path):
    ctx = _with_relation_types(tmp_path, {"5": "1"})  # family, partner, friend, acquaintance only
    entries = relation_entries(ctx.case)
    assert [e[1] for e in entries] == ["Familie", "Partner:in", "Freund:in", "Bekannte:r"]
    assert [e[2] for e in entries] == [RELATION_COLORS[c] for c in "1234"]  # a type keeps its colour whatever else occurs
    only = _with_relation_types(tmp_path / "b", {"1": "4", "2": "4", "3": "4", "5": "4"})
    assert relation_entries(only.case) == [("dot", "Bekannte:r", RELATION_COLORS["4"])]


def test_contacts_without_a_valid_relation_type_stay_marked_and_every_figure_renders(tmp_path):
    ctx = _with_relation_types(tmp_path, {"1": "", "2": "NS", "3": "", "4": "KA", "5": ""})
    assert relation_entries(ctx.case) == [("dot", "keine Angabe", None)]  # never put into one of the six types
    for spec in FIGURES:
        if spec.missing(ctx):
            continue
        with rc():
            texts = [t.get_text() for t in spec.draw(ctx).findobj(Text)]
        if "Beziehungstyp" in texts:
            assert "keine Angabe" in texts and not set(codes.RELATION_TYPE.values()) & set(texts), spec.code
    mixed = _with_relation_types(tmp_path / "b", {"2": ""})
    assert [e[1] for e in relation_entries(mixed.case)] == ["Familie", "Freund:in", "Bekannte:r", "Professionell / institutionell",
                                                           "keine Angabe"]


def _main_content(figure):
    """What a figure shows in its main area (inch coordinates): nodes with their colours, texts, lines, patches."""
    ax = figure.axes[0]
    nodes = sorted((tuple(np.round(o, 6)), tuple(np.round(c, 6))) for coll in ax.collections
                   for o, c in zip(coll.get_offsets(), coll.get_facecolors()))
    texts = sorted((t.get_text(), tuple(np.round(t.get_position(), 6))) for t in ax.texts)
    lines = sorted(tuple(np.round(line.get_xydata(), 6).ravel()) for line in ax.lines)
    patches = sorted((type(p).__name__, p.get_gid() or "", tuple(np.round(p.get_facecolor(), 6))) for p in ax.patches)
    return nodes, texts, lines, patches


def test_only_the_relation_legend_changes_never_the_nodes_or_the_drawing(ctx, monkeypatch):
    def all_six(case):
        return [("dot", label, RELATION_COLORS[code]) for code, label in codes.RELATION_TYPE.items()]

    for spec in FIGURES:
        with rc():
            now = spec.draw(ctx)
        with monkeypatch.context() as m:
            m.setattr(base, "relation_entries", all_six)  # the one shared component
            with rc():
                before = spec.draw(ctx)
        assert _main_content(now) == _main_content(before), spec.code  # same nodes, colours, labels, lines
        legend = [t.get_text() for t in now.findobj(Text)]
        if "Beziehungstyp" in legend:
            assert "Sonstige Beziehung" not in legend and "Familie" in legend, spec.code
        assert now.get_figheight() <= before.get_figheight() + 1e-9, spec.code  # the legend never needs more room


def test_a_legend_with_fewer_types_needs_less_room():
    from mares.network_v1.figures.base import _bottom_rows

    four = [("Beziehungstyp", [("dot", label, RELATION_COLORS[c]) for c, label in list(codes.RELATION_TYPE.items())[:4]])]
    six = [("Beziehungstyp", [("dot", label, RELATION_COLORS[c]) for c, label in codes.RELATION_TYPE.items()])]
    width = lambda sections: max(x for row in _bottom_rows(sections, 30.0) for x, _, _ in row)  # noqa: E731
    assert width(four) < width(six)
    assert base.bottom_legend_height(four, 4.0) < base.bottom_legend_height(six, 4.0)


def test_there_are_exactly_two_legend_layouts(ctx):
    with rc():
        figure = base.new_figure(4, 2)
        ax = figure.add_axes((0, 0, 1, 1))
        ax.set_xlim(0, 4)
        ax.set_ylim(0, 2)
        for mode in ("side", "bottom"):
            draw_legend(ax, [("Beziehungstyp", relation_entries(ctx.case))], mode)
        with pytest.raises(ValueError):
            draw_legend(ax, [], "top")


def test_case_badge_comes_from_metadata_and_never_shows_a_name(ctx):
    assert case_badge(ctx) == "TESTFALL 002* · SYNTHETISCH"
    meta = dict(ctx.case.metadata, provenance="v0_derived_fictionalized")
    fictional = Context(type(ctx.case)(ctx.case.folder, meta), ctx.derived)
    assert case_badge(fictional) == "TESTFALL 002* · FIKTIONALISIERT"
    real = dict(ctx.case.metadata, case_code="003_pilot_x", case_type="pilot", provenance="survey")
    assert case_badge(Context(type(ctx.case)(ctx.case.folder, real), ctx.derived)) == "FALL · MARES-003"


def test_every_figure_has_badge_footer_and_at_most_two_notes(ctx):
    for spec in FIGURES:
        with rc():
            figure = spec.draw(ctx)
        texts = [t.get_text() for t in figure.texts]
        assert texts.count("TESTFALL 002* · SYNTHETISCH") == 1, spec.code
        assert "MARES · network_v1 · 32 Kontakte" in texts, spec.code  # one footer: no groups, no quality, no version
        assert texts[0] == base.TITLES[spec.code] and not any(t.startswith(spec.code) for t in texts), spec.code  # no code
        assert len(texts) <= 5, spec.code  # title, badge, footer and at most two notes -- no subtitle
        assert not any("Tabelle" in t for t in texts), spec.code  # no method details in titles and notes


def _node_colors(ax) -> set[str]:
    return {to_hex(c).upper() for coll in ax.collections if isinstance(coll, PathCollection) for c in coll.get_facecolors()}


def test_network_nodes_use_the_relation_colours(ctx):
    expected = {RELATION_COLORS[c.relation_type.value] for c in ctx.case.contacts}
    for draw in (g1, g3):
        with rc():
            ax = draw(ctx).axes[0]
        assert expected <= _node_colors(ax), draw.__name__


def test_g1_draws_four_solid_and_three_dashed_rings(ctx):
    with rc():
        ax = g1(ctx).axes[0]
    rings = [p for p in ax.patches if type(p).__name__ == "Circle" and p.center == (0, 0) and not p.get_fill()]
    radii = sorted(round(p.radius, 2) for p in rings)
    assert [r for r in radii if r <= 4] == [1, 1.5, 2, 2.5, 3, 3.5, 4]


def test_g1_shows_no_contact_contact_ties(ctx):
    with rc():
        figure = g1(ctx)
    ax = figure.axes[0]
    assert not [p for p in ax.patches if isinstance(p, PathPatch)] and not ax.lines
    texts = " ".join(t.get_text() for t in figure.findobj(Text))
    assert "Verbindung" not in texts and "Kontaktpaare" not in texts
    assert "1 sehr nah · 2 nah ·\n3 weniger nah ·\n4 außerhalb der Kreise" in texts and "Zwischenwerte: 1,5 · 2,5 · 3,5" in texts
    assert "Winkelbereiche" not in texts and "Abstand zu Ego" not in texts  # no method note
    assert not [p for p in ax.patches if type(p).__name__ in ("Wedge", "Rectangle", "Polygon")]  # no sector lines or areas


def _angle_share(x: float, y: float) -> float:
    """Position along the ring as a share of the usable arc (0 = just left of the ring numbers, counter-clockwise)."""
    r = math.hypot(x, y)
    wedge = math.atan2(LABEL_HALF_WIDTH, r)
    return ((math.atan2(y, x) - math.pi / 2 - wedge) % (2 * math.pi)) / (2 * math.pi - 2 * wedge)


def test_g1_radius_is_exactly_the_recorded_closeness(ctx):
    for cid, (x, y) in g1_layout(ctx).items():
        value = codes.closeness_value(ctx.case.contact(cid).closeness)
        assert math.hypot(x, y) == pytest.approx(value if value is not None else MISSING_RADIUS), cid


def test_g1_sectors_follow_the_fixed_relation_order(ctx):
    sectors = g1_sectors(ctx)
    assert list(sectors) == list(SECTOR_ORDER)  # all six types (and 'keine Angabe'), also when absent
    bounds = [b for code in SECTOR_ORDER for b in sectors[code]]
    assert bounds == sorted(bounds) and 0 <= bounds[0] and bounds[-1] <= 1
    assert sectors["2"][1] > sectors["2"][0] and sectors["6"][1] == sectors["6"][0]  # 002: one partner, no 'Sonstige'


def test_g1_groups_contacts_of_one_relation_type_on_every_ring(ctx):
    positions = g1_layout(ctx)
    by_ring: dict = {}
    for cid, (x, y) in positions.items():
        by_ring.setdefault(round(math.hypot(x, y), 6), []).append((_angle_share(x, y), SECTOR_ORDER.index(relation_code(ctx, cid))))
    for ring, items in by_ring.items():
        order = [code for _, code in sorted(items)]
        assert order == sorted(order), ring  # along each ring the types follow the sector order, never interleaved
    sectors = g1_sectors(ctx)
    for cid, xy in positions.items():
        f0, f1 = sectors[relation_code(ctx, cid)]
        assert f0 - 0.06 <= _angle_share(*xy) <= f1 + 0.06, cid  # in (or right beside) the sector of its type


def test_g1_layout_does_not_depend_on_the_row_order(ctx, tmp_path):
    folder = copy_002(tmp_path)
    write_rows(folder, "contacts.csv", list(reversed(read_rows(folder, "contacts.csv"))))
    shuffled = g1_layout(context(folder))
    for cid, xy in g1_layout(ctx).items():
        assert shuffled[cid] == pytest.approx(xy), cid


def test_g1_nodes_do_not_overlap_and_leave_the_ring_numbers_free(ctx):
    points = list(g1_layout(ctx).values())
    scale = G1_SIZE / (2 * (MISSING_RADIUS + 0.45))  # inches per layout unit (002 shows the outer arc)
    for i, (x0, y0) in enumerate(points):
        for x1, y1 in points[i + 1:]:
            assert math.hypot(x1 - x0, y1 - y0) * scale >= 2 * NODE_R_IN  # nodes (and their IDs) never overlap
    for value in (1, 2, 3, 4):
        for x, y in points:
            assert math.hypot(x, y - value) * scale > NODE_R_IN + 0.08  # the ring number at (0, value) stays free


# ------------------------------------------------------------------------------------------------------- G2 ---
def test_g2_subgroups_bundle_place_or_country(ctx):
    layout = g2_layout(ctx)
    by_label: dict = {}
    for g in layout.subgroups:
        by_label.setdefault((g.area, g.label), []).append(sorted(g.members))
    by_label = {k: v[0] if len(v) == 1 else v for k, v in by_label.items()}
    assert by_label[(Area.MITTELHESSEN, "Gießen")] == [["A09", "A17"], ["A21"]]  # connected zone and isolated zone
    assert by_label[(Area.OUTSIDE_EUROPE, "Kolumbien")] == ["A01", "A02", "A04", "A30"]  # country abroad, not the city
    assert by_label[(Area.EUROPE_OTHER, "Spanien")] == ["A03", "A31"]
    assert by_label[(Area.MARBURG, None)][0][0] == "A06"  # Marburg: no further subdivision (connected and isolated zone)


def test_g2_single_contact_is_labelled_with_the_place_only(ctx):
    single = [g for g in g2_layout(ctx).subgroups if g.label == "Kassel"]
    assert len(single) == 1 and single[0].label_text == "Kassel" and single[0].members == ["A07"]
    pair = next(g for g in g2_layout(ctx).subgroups if g.label == "Gießen" and len(g.members) == 2)
    assert pair.label_text == "Gießen · 2"


def test_g2_unresolved_residence_without_ties_is_a_note_not_a_region(ctx):
    layout = g2_layout(ctx)
    assert list(layout.bands) == [Area.MARBURG, Area.MITTELHESSEN, Area.GERMANY_OTHER, Area.EUROPE_OTHER, Area.OUTSIDE_EUROPE]
    assert layout.not_shown == ["A22"] and not layout.unplaced and "A22" not in layout.positions
    with rc():
        figure = g2(ctx)
    texts = " ".join(t.get_text() for t in figure.findobj(Text))
    assert "Wohnort nicht zuordenbar: A22." in texts


def test_g2_unresolved_residence_with_a_confirmed_tie_keeps_the_tie(tmp_path):
    folder = copy_002(tmp_path)
    rows = read_rows(folder, "alter_connections.csv")
    for row in rows:
        if {row["contact_a"], row["contact_b"]} == {"A18", "A22"}:
            row["status"] = "1"
    write_rows(folder, "alter_connections.csv", rows)
    ctx_ = context(folder)
    layout = g2_layout(ctx_)
    assert Area.UNRESOLVED not in layout.bands and layout.unplaced == ["A22"] and not layout.not_shown
    assert layout.positions["A22"][1] < layout.zone_bottom  # below the bands, outside the geography
    with rc():
        figure = g2(ctx_)
    ties = [p for p in figure.axes[0].patches if isinstance(p, PathPatch) and p.get_gid() == "tie"]
    assert len(ties) == len(ctx_.derived.confirmed_edges) == 36
    texts = " ".join(t.get_text() for t in figure.findobj(Text))
    assert "zwischen Bereichen · ohne Bereich" in texts and "Wohnort nicht zuordenbar:" in texts


def test_g2_without_unresolved_contacts_has_five_bands(tmp_path):
    folder = copy_002(tmp_path)
    rows = read_rows(folder, "contacts.csv")
    for row in rows:
        if row["contact_id"] == "A22":
            row["residence_place"] = "Marburg"
    write_rows(folder, "contacts.csv", rows)
    layout = g2_layout(context(folder))
    assert list(layout.bands) == [Area.MARBURG, Area.MITTELHESSEN, Area.GERMANY_OTHER, Area.EUROPE_OTHER, Area.OUTSIDE_EUROPE]
    assert not layout.unplaced and not layout.not_shown


def test_g2_subgroup_areas_do_not_overlap(ctx):
    boxes = [g.box() for g in g2_layout(ctx).subgroups]
    for i, (x0, y0, w0, h0) in enumerate(boxes):
        for x1, y1, w1, h1 in boxes[i + 1:]:
            assert x0 + w0 <= x1 + 1e-9 or x1 + w1 <= x0 + 1e-9 or y0 + h0 <= y1 + 1e-9 or y1 + h1 <= y0 + 1e-9


def test_g2_no_tie_runs_through_a_third_node(ctx):
    positions = g2_layout(ctx).positions
    for a, b in ctx.derived.confirmed_edges:
        (x0, y0), (x1, y1) = positions[a], positions[b]
        if math.hypot(x1 - x0, y1 - y0) > 1.5:
            continue  # long ties between areas are curved
        for cid, (x, y) in positions.items():
            if cid in (a, b):
                continue
            t = max(0.0, min(1.0, ((x - x0) * (x1 - x0) + (y - y0) * (y1 - y0)) / ((x1 - x0) ** 2 + (y1 - y0) ** 2)))
            assert math.hypot(x0 + t * (x1 - x0) - x, y0 + t * (y1 - y0) - y) > NODE_R_IN, (a, b, cid)


def test_g2_subgroups_are_geography_only(ctx):
    assert subgroups(ctx, ["A09", "A21"])[Area.MITTELHESSEN][0].members == ["A09", "A21"]  # same place, no tie needed


# ------------------------------------------------------------------------------------------------------- G3 ---
def _scale_dots(ax) -> list:
    return [p for p in ax.patches if (p.get_gid() or "").startswith("scale-")]


def test_g3_is_one_map_with_one_outline_width(ctx):
    with rc():
        figure = g3(ctx)
    assert len([a for a in figure.axes if a.patches or a.collections]) == 2  # the map and the legend, no second panel
    ax = figure.axes[0]
    outlines = {p.get_gid(): p.get_linewidth() for p in ax.patches if isinstance(p, Polygon) and (p.get_gid() or "").startswith("group-")}
    assert set(outlines) == {f"group-{g.id}" for g in ctx.case.groups}
    assert all(w == pytest.approx(OUTLINE_W) for w in outlines.values())  # the width carries no meaning


def test_g3_labels_are_id_name_count_and_the_number(ctx):
    with rc():
        figure = g3(ctx)
    texts = [t.get_text() for t in figure.axes[0].findobj(Text)]
    assert "C01 · Familie in Kolumbien und Spanien (4)" in texts and "C05 · Sprachtandems (3)" in texts
    assert sorted(t for t in texts if t in {"1", "2", "3", "4", "5"}) == sorted(g.belonging.value for g in ctx.case.groups)
    joined = " ".join(texts)
    for word in ("Zugehörigkeit", "Kontakte", "Sehr stark", "Stark", "Mittel", "Wenig", "Überhaupt nicht"):
        assert word not in joined  # no repeated words in the map
    legend = " ".join(t.get_text() for t in figure.findobj(Text))
    assert "Zugehörigkeit: 1 sehr stark – 5 überhaupt nicht" in legend
    assert "Umrandung" not in legend


def test_group_names_drop_test_suffixes_and_long_names_are_shortened_for_display_only():
    assert display_name("Kreis 4 (fiktive Bezeichnung)") == "Kreis 4"
    assert display_name("Tandem (synthetisch)") == "Tandem"
    assert display_name("Verein (Marburg)") == "Verein (Marburg)"  # a real addition stays
    long = "Sehr lange Bezeichnung einer Gruppe mit vielen Wörtern"
    assert display_name(long).endswith("…") and len(display_name(long)) <= 34
    assert display_name("") == "ohne Bezeichnung"


def _label_geometry(ctx_):
    with rc():
        figure = g3(ctx_)
    ax = figure.axes[0]
    figure.canvas.draw()
    boxes = {p.get_gid()[6:]: p.get_extents().transformed(ax.transData.inverted()) for p in ax.patches
             if (p.get_gid() or "").startswith("label-")}
    hulls = {p.get_gid()[6:]: p.get_xy() for p in ax.patches if isinstance(p, Polygon) and (p.get_gid() or "").startswith("group-")}
    leaders = {line.get_gid()[7:]: line.get_xydata() for line in ax.lines if (line.get_gid() or "").startswith("leader-")}
    return boxes, hulls, leaders


def _box_gap(box, hull) -> float:
    return min(math.hypot(x - min(max(x, box.x0), box.x1), y - min(max(y, box.y0), box.y1)) for x, y in hull)


@pytest.mark.parametrize("nested", [False, True])
def test_g3_labels_sit_at_their_group_off_nodes_ties_and_other_labels(ctx, tmp_path, nested):
    ctx_ = ctx
    if nested:  # a group inside another one (as C04 inside C05 and C06 in the fictionalised case)
        folder = copy_002(tmp_path)
        rows = read_rows(folder, "group_memberships.csv")
        write_rows(folder, "group_memberships.csv", rows + [{"group_id": "C06", "contact_id": "A27"}, {"group_id": "C06", "contact_id": "A28"}])
        groups = read_rows(folder, "groups.csv")
        write_rows(folder, "groups.csv", groups + [{**groups[-1], "group_id": "C06", "label": "Tandem (synthetisch)", "belonging": "4"}])
        ctx_ = context(folder)
    boxes, hulls, leaders = _label_geometry(ctx_)
    assert set(boxes) == {g.id for g in ctx_.case.groups}
    positions, _ = g3_positions(ctx_)
    for gid, box in boxes.items():
        inner = Bbox.from_extents(box.x0 + 0.03, box.y0 + 0.03, box.x1 - 0.03, box.y1 - 0.03)  # without the rounded padding
        for x, y in positions.values():
            assert not inner.overlaps(Bbox.from_extents(x - NODE_R_IN, y - NODE_R_IN, x + NODE_R_IN, y + NODE_R_IN)), gid
        for a, b in ctx_.derived.confirmed_edges:
            assert not MplPath([positions[a], positions[b]]).intersects_bbox(inner, filled=False), (gid, a, b)
        for other, obox in boxes.items():
            assert other == gid or not inner.overlaps(obox), (gid, other)
        assert _box_gap(box, hulls[gid]) <= LEADER_GAP + 0.05 or gid in leaders, gid  # at its outline, or tied to it
        if gid in leaders:
            (x0, y0), (x1, y1) = leaders[gid]
            assert math.hypot(x1 - x0, y1 - y0) < 1.0, gid  # a short leader, never across the figure
    close = sum(_box_gap(box, hulls[gid]) <= LEADER_GAP + 0.05 for gid, box in boxes.items())
    assert close >= len(boxes) - 1 - len(nested_groups(ctx_))  # a nested group may need a leader (no free edge)


def test_g3_belonging_scale_marks_exactly_the_recorded_answer(ctx):
    with rc():
        ax = g3(ctx).axes[0]
    dots = _scale_dots(ax)
    filled = [d for d in dots if d.get_gid() == "scale-on"]
    assert len(dots) == 5 * len(ctx.case.groups) and len(filled) == len(ctx.case.groups)


@pytest.mark.parametrize("value", ["1", "3", "5", None])
def test_ordinal_dots_fill_one_position_or_none(value):
    with rc():
        figure = base.new_figure(2, 1)
        ax = figure.add_axes((0, 0, 1, 1))
        base.ordinal_dots(ax, 0.1, 0.5, value)
    dots = sorted(ax.patches, key=lambda p: p.center[0])
    filled = [i + 1 for i, d in enumerate(dots) if d.get_gid() == "scale-on"]
    assert len(dots) == 5 and filled == ([int(value)] if value else [])


def test_g3_missing_belonging_is_named_and_marks_no_dot(tmp_path):
    folder = copy_002(tmp_path)
    rows = read_rows(folder, "groups.csv")
    for row in rows:
        if row["group_id"] == "C05":
            row["belonging"] = "KA"
    write_rows(folder, "groups.csv", rows)
    ctx_ = context(folder)
    with rc():
        figure = g3(ctx_)
    ax = figure.axes[0]
    texts = [t.get_text() for t in ax.findobj(Text)]
    assert "KA" in texts and "5" not in texts  # the kind of missing answer, never a value
    filled = [d for d in _scale_dots(ax) if d.get_gid() == "scale-on"]
    assert len(filled) == len(ctx_.case.groups) - 1
    legend = [t.get_text() for t in figure.findobj(Text)]
    assert "KA = keine Antwort" in legend and "Zugehörigkeit: 1 sehr stark – 5 überhaupt nicht" in legend
    assert not any("NS =" in t or "n. e. =" in t for t in legend)  # only the codes that occur


def test_g3_ties_are_confirmed_pairs_only(ctx):
    with rc():
        ax = g3(ctx).axes[0]
    assert len([p for p in ax.patches if isinstance(p, PathPatch) and p.get_gid() == "tie"]) == 35


def test_g3_sets_contacts_without_group_and_tie_apart(ctx):
    assert loose_contacts(ctx) == ["A23", "A24"]
    assert not set(loose_contacts(ctx)) & set(g3_layout(ctx))


def test_g3_nested_groups_have_no_anchor_and_no_extra_rings(tmp_path):
    folder = copy_002(tmp_path)
    rows = read_rows(folder, "group_memberships.csv")
    rows.append({"group_id": "C05", "contact_id": "A01"})  # A01 now in C01 and C05; new C06 = {A27, A28} lies inside C05
    write_rows(folder, "group_memberships.csv", rows + [{"group_id": "C06", "contact_id": "A27"}, {"group_id": "C06", "contact_id": "A28"}])
    groups = read_rows(folder, "groups.csv")
    groups.append({**groups[-1], "group_id": "C06", "label": "Tandem (synthetisch)", "belonging": "4"})
    write_rows(folder, "groups.csv", groups)
    ctx_ = context(folder)
    assert nested_groups(ctx_) == {"C06"}
    marked = membership_marked(ctx_)
    assert "A01" in marked and "A27" not in marked and "A28" not in marked  # the nested outline already shows it


# ------------------------------------------------------------------------------------------------ matrices ---
def test_point_matrices_have_no_area_column_for_unresolved_residences(ctx):
    for code in ("P1", "P2"):
        spec = next(s for s in FIGURES if s.code == code)
        with rc():
            figure = spec.draw(ctx)
        texts = " ".join(t.get_text() for t in figure.findobj(Text))
        assert "Wohnort nicht zuordenbar: A22." in texts and "nicht\nzuordenbar" not in texts, code


def test_point_matrix_dots_never_overlap(ctx):
    columns = base.area_columns()
    items = [base.Item(f"A{i:02d}", Area.MARBURG, 1.0, None) for i in range(1, 12)]
    rows = base.closeness_rows(False)
    geometry = base.point_geometry(columns, rows, items, 11.5, {}, {}, bracket=True)
    with rc():
        figure = base.new_figure(11.5, geometry.height)
        positions = base.point_matrix(figure.add_axes((0, 0, 1, 1)), 11.5, geometry, columns, rows, items, gaps={}, row_gaps={},
                                      column_counts={})
    points = list(positions.values())
    assert len(points) == 11
    for i, (x0, y0) in enumerate(points):
        for x1, y1 in points[i + 1:]:
            assert math.hypot(x1 - x0, y1 - y0) >= base.SLOT_H - 1e-9


def test_heat_cells_show_counts_only():
    assert heat_cell(0, 5) == ("#FFFFFF", "")  # no mention: empty, white
    assert heat_cell(3, 5) == (heat_fill(0.6), "3")  # a count, no percentage
    assert heat_cell(1, 1) == (HEAT_NEUTRAL, "1")  # n = 1: neutral, never a strong shade
    assert heat_cell(0, 1) == (HEAT_NEUTRAL, "")
    assert heat_cell(0, 0) == ("#FFFFFF", "")


def test_p3_and_p4_share_one_blue_scale(ctx):
    for code in ("P3", "P4"):
        spec = next(s for s in FIGURES if s.code == code)
        with rc():
            ax = spec.draw(ctx).axes[0]
        fills = {to_hex(p.get_facecolor()).upper() for p in ax.patches if p.get_facecolor()[:3] != (1.0, 1.0, 1.0)}
        palette = {to_hex(heat_fill(k / n)).upper() for n in range(2, 12) for k in range(1, n + 1)} | {HEAT_NEUTRAL.upper()}
        assert fills <= palette, code


def test_p3_sections_keep_all_six_forms_without_codes(ctx):
    assert [k for _, keys in COMMUNICATION_SECTIONS for k in keys] == ["1", "2", "3", "4", "5", "6"]
    with rc():
        texts = [t.get_text() for t in next(s for s in FIGURES if s.code == "P3").draw(ctx).findobj(Text)]
    assert "Persönlich" in texts and "Telefonat" in texts and not any(t.startswith("1 · ") for t in texts)


def test_multiple_answers_are_counted_in_every_row_and_missing_answers_apart(ctx):
    def languages(cid):
        b = ctx.case.communication.get(cid)
        return b.languages.values if b and b.languages.recorded else None

    counts, bases, missing = _matrix_counts(ctx, languages)
    assert sum(v for (a, _), v in counts.items() if a is Area.MARBURG) > bases[Area.MARBURG]  # several languages per contact
    assert Area.UNRESOLVED not in bases and Area.UNRESOLVED not in missing


def test_p4_lists_every_named_other_language(ctx, tmp_path):
    rows, keys = language_rows(ctx)
    assert [label for _, label in rows] == ["Spanisch", "Deutsch", "Englisch", "Portugiesisch", "Französisch", "Kichwa"]
    folder = copy_002(tmp_path)
    data = read_rows(folder, "communication.csv")
    for row, name in zip(data[:5], ("Quechua", "Italienisch", "Arabisch", "Polnisch", "Wayuunaiki")):
        row["languages"], row["other_languages"], row["language_use"], row["comment"] = "1, 5", name, "1", "x"
    write_rows(folder, "communication.csv", data)
    labels = [label for _, label in language_rows(context(folder))[0]]
    assert len(labels) == 4 + 7  # no cut-off for named languages


def test_p5_shows_nothing_of_it_only_when_answered(ctx, tmp_path):
    spec = next(s for s in FIGURES if s.code == "P5")
    with rc():
        texts = [t.get_text() for t in spec.draw(ctx).findobj(Text)]
    assert any(t.startswith("Nichts davon") for t in texts)
    folder = copy_002(tmp_path)
    data = read_rows(folder, "contacts.csv")
    for row in data:
        if row["functions"] == "0":
            row["functions"] = "2"
    write_rows(folder, "contacts.csv", data)
    with rc():
        texts = [t.get_text() for t in spec.draw(context(folder)).findobj(Text)]
    assert not any(t.startswith("Nichts davon") for t in texts)
    assert Counter(t for t in texts if t.startswith("keine Angabe"))  # missing answers stay a column of their own



# --------------------------------------------------------------------------------------- editorial standard ---
def _texts(spec, ctx) -> list[str]:
    with rc():
        return [t.get_text() for t in spec.draw(ctx).findobj(Text)]


def test_every_figure_has_its_title_only_one_footer_and_no_subtitle(ctx):
    for spec in FIGURES:
        texts = _texts(spec, ctx)
        assert spec.title == base.TITLES[spec.code] and texts.count(spec.title) == 1, spec.code
        assert not any(t.startswith(f"{spec.code} ·") for t in texts), spec.code
        assert "Gruppen" not in " ".join(t for t in texts if t.startswith("MARES")), spec.code
        assert "Datenqualität" not in " ".join(texts), spec.code


def test_the_reduced_texts_of_every_figure(ctx):
    texts = {spec.code: " ".join(_texts(spec, ctx)) for spec in FIGURES}
    for code in ("G2", "G3"):  # the coverage of pairs stays in the run record, not in the figure
        assert "Kontaktpaare" not in texts[code] and "fehlende Linien" not in texts[code], code
    assert "innerhalb eines Bereichs" in texts["G2"] and "zwischen Bereichen" in texts["G2"]
    assert "gleicher Wohnort / gleiches Wohnland" in texts["G2"] and "(" not in texts["G2"].split("Verbindungen")[1].split("gleicher")[0]
    assert "Kategorien, keine Entfernungen" not in texts["G2"] + texts["P1"]
    assert "gemeinsame Mitgliedschaft" not in texts["G3"] and "der markierte Punkt" not in texts["G3"]
    assert "getrennte Merkmale" not in texts["P1"] and "geordnete Kategorie" not in texts["P2"]
    assert "Mehrfachnennungen möglich." in texts["P5"] and "Funktionsspalten" not in texts["P5"]
    for code in ("P3", "P4"):  # one heat legend
        for part in ("Farbintensität = Anteil im Wohnortbereich (0–100 %)", "Zahl = Kontakte · Mehrfachnennungen möglich",
                     "n = 1: neutral", "n = Kontakte mit Angabe im jeweiligen Wohnortbereich"):
            assert part in texts[code], (code, part)
        assert "„nein“" not in texts[code]
    assert "Mehrfachnennungen möglich; Anteile summieren sich nicht auf 100 %." in texts["P4"]
    for code in ("P1", "P2", "P3", "P4", "G2"):
        assert "Wohnort nicht zuordenbar: A22." in texts[code], code
    assert "Wohnort nicht darstellbar: A22." in texts["X1"]


def test_g1_explains_the_dashed_rings_even_without_intermediate_values(tmp_path):
    folder = copy_002(tmp_path)
    rows = read_rows(folder, "contacts.csv")
    for row in rows:
        if row["closeness"] in ("1,5", "2,5", "3,5", "2-3"):
            row["closeness"] = row["closeness"][0]
    write_rows(folder, "contacts.csv", rows)
    with rc():
        texts = " ".join(t.get_text() for t in g1(context(folder)).findobj(Text))
    assert "Zwischenwerte: 1,5 · 2,5 · 3,5" in texts and "4 außerhalb der Kreise" in texts  # the rings are always drawn


def test_missing_answers_are_named_alike_and_never_counted_as_no(tmp_path):
    folder = copy_002(tmp_path)
    rows = read_rows(folder, "communication.csv")
    rows[0]["communication_forms"] = ""
    write_rows(folder, "communication.csv", rows)
    ctx_ = context(folder)
    p3 = next(s for s in FIGURES if s.code == "P3")
    with rc():
        texts = [t.get_text() for t in p3.draw(ctx_).findobj(Text)]
    assert "keine Angabe" in texts and "ohne Angabe" not in texts
