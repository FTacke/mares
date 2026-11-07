"""The matrix figures of network_v1: P1-P5.

* P1 residence area x personal closeness (point matrix)
* P2 residence area x contact frequency (point matrix)
* P3 residence area x communication forms (heat matrix, multiple answers)
* P4 residence area x languages (heat matrix, multiple answers; every named other language is a row of its own)
* P5 relation functions x personal closeness (point matrix; a contact with several functions appears several times)

P1, P2 and P5 share :func:`~.base.point_matrix`, P3 and P4 share :func:`~.base.heat_matrix`. Ordinal codes stay
categories: rows are placed in code order, never on a metric axis. Missing answers are a row or column of their own and
are never counted as 'no'. A contact whose residence is not resolvable is no column: it is named in a note.
"""

from __future__ import annotations

from collections import Counter

from .. import codes
from ..places import Area
from .base import (
    AREA_TINTS, HEAT_LEGEND, MISSING_GAP, MISSING_LABEL, Context, Item, area_columns, area_gaps, closeness_rows, heat_height, heat_matrix, page,
    point_geometry, point_matrix, relation_fill, relation_section,
)

MATRIX_W = 11.5  # main area width of every matrix figure (inches)


def _closeness_key(cell: codes.Cell):
    value = codes.closeness_value(cell)
    return value if value is not None else "missing"


def _area_counts(ctx: Context) -> Counter:
    return Counter(ctx.derived.area(cid) for cid in ctx.resolved())


def _area_point_figure(ctx: Context, *, code: str, y_title: str, rows: list, row_of):
    """P1 and P2: area columns, one dot per resolved contact in the row of its answer."""
    columns = area_columns(ctx.scheme)
    keys = [k for k, _ in columns]
    items = [Item(cid, ctx.derived.area(cid), row_of(ctx.case.contact(cid)), ctx.scheme.fill(ctx.case, cid)) for cid in ctx.resolved()]
    if any(i.row == "missing" for i in items):
        rows = rows + [("missing", MISSING_LABEL)]
    row_gaps = {len(rows) - 1: MISSING_GAP} if rows[-1][0] == "missing" else {}
    gaps = area_gaps(keys)
    geometry = point_geometry(columns, rows, items, MATRIX_W, gaps, row_gaps, bracket=True)
    p = page(ctx, code, main_w=MATRIX_W, main_h=geometry.height, legend="bottom",
             sections=[ctx.scheme.relation_section(ctx.case)], notes=[ctx.unresolved_note()])
    point_matrix(p.main, MATRIX_W, geometry, columns, rows, items, gaps=gaps, row_gaps=row_gaps, column_counts=_area_counts(ctx),
                 tints=AREA_TINTS, y_title=y_title, bracket=ctx.scheme.bracket)
    return p.figure


def p1(ctx: Context):
    return _area_point_figure(
        ctx, code="P1", y_title=ctx.scheme.closeness_title, rows=ctx.scheme.closeness_rows(False), row_of=ctx.scheme.closeness_key)


def p2(ctx: Context):
    return _area_point_figure(
        ctx, code="P2", y_title=ctx.scheme.frequency_title, rows=ctx.scheme.frequency_rows(), row_of=ctx.scheme.frequency_key)


def _matrix_counts(ctx: Context, values_of) -> tuple[Counter, Counter, Counter]:
    """Counts per (area, row) among resolved contacts with a recorded answer; bases and missing answers per area."""
    counts: Counter = Counter()
    bases: Counter = Counter()
    missing: Counter = Counter()
    for cid in ctx.resolved():
        area = ctx.derived.area(cid)
        values = values_of(cid)
        if values is None:
            missing[area] += 1
            continue
        bases[area] += 1
        for v in values:
            counts[(area, v)] += 1
    return counts, bases, missing


def _heat_figure(ctx: Context, *, code: str, sections, values_of, notes: list[str]):
    counts, bases, missing = _matrix_counts(ctx, values_of)
    if ctx.scheme.drop_empty:  # rows without any contact are left out; a section without rows too
        used = {row for (_area, row), n in counts.items() if n}
        sections = [(title, [r for r in rows if r[0] in used]) for title, rows in sections]
        sections = [(title, rows) for title, rows in sections if rows]
    with_missing = any(missing.values())
    height = heat_height(sections, with_missing)
    p = page(ctx, code, main_w=MATRIX_W, main_h=height, legend="bottom", sections=HEAT_LEGEND,
             notes=notes + [ctx.unresolved_note()])
    heat_matrix(p.main, MATRIX_W, height, area_columns(ctx.scheme), sections, counts, bases, missing, bracket=ctx.scheme.bracket)
    return p.figure


# Visual sections of the communication forms (no new categories, no sums; a telephone call is not 'digital').
COMMUNICATION_SECTIONS = (
    ("Persönliche Kommunikation", ("1",)),
    ("Synchron auf Distanz", ("2", "3")),
    ("Asynchron", ("4", "5")),
    ("Weitere Formen", ("6",)),
)


def p3(ctx: Context):
    return _heat_figure(
        ctx, code="P3", sections=ctx.scheme.communication_sections(), values_of=lambda cid: ctx.scheme.forms(ctx.case, cid), notes=[])


def language_rows(ctx: Context) -> tuple[list[tuple[str, str]], dict[str, tuple[str, ...]]]:
    """Rows of P4 and the row keys of every contact, as the scheme of the case defines them."""
    return ctx.scheme.language_rows(ctx.case)


def p4(ctx: Context):
    rows, keys = language_rows(ctx)
    return _heat_figure(
        ctx, code="P4", sections=[(None, rows)], values_of=lambda cid: keys.get(cid),
        notes=["Mehrfachnennungen möglich; Anteile summieren sich nicht auf 100 %."])


FUNCTION_LABELS = {
    "1": "Persönlicher\nRückhalt / Rat", "2": "Gemeinsame\nAktivitäten /\nGespräche", "3": "Praktische Hilfe\nim Alltag",
    "4": "Sprachliche Hilfe /\nÜbersetzung", "5": "Sonstiges", "0": "Nichts davon", "missing": MISSING_LABEL,
}


def p5(ctx: Context):
    scheme = ctx.scheme
    items = []
    for c in ctx.case.contacts:
        row = scheme.closeness_key(c)
        fill = scheme.fill(ctx.case, c.id)
        functions = scheme.functions(c)
        if functions:
            items += [Item(c.id, f, row, fill) for f in functions]
        else:
            items.append(Item(c.id, "missing", row, fill))
    present = {i.column for i in items}
    none = scheme.function_none
    keys = [k for k in scheme.function_keys if not scheme.drop_empty or k in present]
    keys += [k for k in (none, "missing") if k and k in present]
    columns = [(k, scheme.function_label(k)) for k in keys]
    rows = scheme.closeness_rows(any(i.row == "missing" for i in items))
    row_gaps = {len(rows) - 1: MISSING_GAP} if rows[-1][0] == "missing" else {}
    gaps = {keys.index(k): MISSING_GAP for k in (none, "missing") if k and k in keys}
    if none in keys and "missing" in keys:
        gaps[keys.index("missing")] = 0.15
    width = scheme.p5_width or MATRIX_W
    geometry = point_geometry(columns, rows, items, width, gaps, row_gaps, bracket=False)
    p = page(ctx, "P5", main_w=width, main_h=geometry.height, legend="bottom", sections=[scheme.relation_section(ctx.case)],
             notes=["Mehrfachnennungen möglich."])
    point_matrix(p.main, width, geometry, columns, rows, items, gaps=gaps, row_gaps=row_gaps, column_counts=Counter(i.column for i in items),
                 y_title=scheme.closeness_title)
    return p.figure
