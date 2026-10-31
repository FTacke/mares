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
    AREA_TINTS, HEAT_LEGEND, MISSING_GAP, Context, Item, area_columns, area_gaps, closeness_rows, heat_height, heat_matrix, page,
    point_geometry, point_matrix, relation_entries, relation_fill,
)

MATRIX_W = 11.5  # main area width of every matrix figure (inches)


def _closeness_key(cell: codes.Cell):
    value = codes.closeness_value(cell)
    return value if value is not None else "missing"


def _area_counts(ctx: Context) -> Counter:
    return Counter(ctx.derived.area(cid) for cid in ctx.resolved())


def _area_point_figure(ctx: Context, *, title: str, subtitle: str, y_title: str, rows: list, row_of, notes: list[str]):
    """P1 and P2: area columns, one dot per resolved contact in the row of its answer."""
    columns = area_columns()
    keys = [k for k, _ in columns]
    items = [Item(cid, ctx.derived.area(cid), row_of(ctx.case.contact(cid)), relation_fill(ctx.case, cid)) for cid in ctx.resolved()]
    if any(i.row == "missing" for i in items):
        rows = rows + [("missing", "keine Angabe")]
    row_gaps = {len(rows) - 1: MISSING_GAP} if rows[-1][0] == "missing" else {}
    gaps = area_gaps(keys)
    geometry = point_geometry(columns, rows, items, MATRIX_W, gaps, row_gaps, bracket=True)
    p = page(ctx, title, subtitle, main_w=MATRIX_W, main_h=geometry.height, legend="bottom",
             sections=[("Beziehungstyp", relation_entries(ctx.case))], notes=notes + [ctx.unresolved_note()])
    point_matrix(p.main, MATRIX_W, geometry, columns, rows, items, gaps=gaps, row_gaps=row_gaps, column_counts=_area_counts(ctx),
                 tints=AREA_TINTS, y_title=y_title)
    return p.figure


def p1(ctx: Context):
    return _area_point_figure(
        ctx, title="P1 · Wohnortbereich und persönliche Nähe", subtitle="Wie nah stehen Kontakte an verschiedenen Wohnorten?",
        y_title="Persönliche Nähe", rows=closeness_rows(False), row_of=lambda c: _closeness_key(c.closeness),
        notes=["Wohnortbereiche sind Kategorien, keine Entfernungen; persönliche Nähe und Wohnort sind getrennte Merkmale."],
    )


def p2(ctx: Context):
    rows = list(codes.CONTACT_FREQUENCY.items())
    return _area_point_figure(
        ctx, title="P2 · Wohnortbereich und Kontakthäufigkeit", subtitle="Wie häufig besteht Kontakt zu Personen an verschiedenen Wohnorten?",
        y_title="Kontakthäufigkeit", rows=rows,
        row_of=lambda c: c.contact_frequency.value if c.contact_frequency.recorded else "missing",
        notes=["Kontakthäufigkeit ist eine geordnete Kategorie; die Zeilenabstände sind keine gemessenen Zeitabstände."],
    )


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


def _heat_figure(ctx: Context, *, title: str, subtitle: str, sections, values_of, notes: list[str]):
    counts, bases, missing = _matrix_counts(ctx, values_of)
    with_missing = any(missing.values())
    height = heat_height(sections, with_missing)
    p = page(ctx, title, subtitle, main_w=MATRIX_W, main_h=height, legend="bottom", sections=HEAT_LEGEND,
             notes=notes + [ctx.unresolved_note()])
    heat_matrix(p.main, MATRIX_W, height, area_columns(), sections, counts, bases, missing)
    return p.figure


# Visual sections of the communication forms (no new categories, no sums; a telephone call is not 'digital').
COMMUNICATION_SECTIONS = (
    ("Persönliche Kommunikation", ("1",)),
    ("Synchron auf Distanz", ("2", "3")),
    ("Asynchron", ("4", "5")),
    ("Weitere Formen", ("6",)),
)


def p3(ctx: Context):
    def forms(cid):
        b = ctx.case.communication.get(cid)
        return b.forms.values if b is not None and b.forms.recorded else None

    sections = [(title, [(code, codes.COMMUNICATION_FORMS[code]) for code in keys]) for title, keys in COMMUNICATION_SECTIONS]
    return _heat_figure(
        ctx, title="P3 · Kommunikationsformen nach Wohnortbereich", subtitle="Auf welchen Wegen wird mit Kontakten an verschiedenen Wohnorten kommuniziert?",
        sections=sections, values_of=forms,
        notes=["n = Kontakte des Bereichs mit Angabe; fehlende Angaben stehen getrennt und zählen nie als „nein“."],
    )


def language_rows(ctx: Context) -> tuple[list[tuple[str, str]], dict[str, tuple[str, ...]]]:
    """Rows of P4 and the row keys of every contact. Every named other language is a row of its own (most frequent
    first, then alphabetical); code 5 without a name has a row of its own."""
    named: Counter = Counter()
    for b in ctx.case.communication.values():
        if b.other_languages.recorded:
            named.update(b.other_languages.values)
    shown = [name for name, _ in sorted(named.items(), key=lambda kv: (-kv[1], kv[0]))]
    rows = [(code, label) for code, label in codes.LANGUAGES.items() if code != codes.LANGUAGE_OTHER]
    rows += [(f"other:{name}", name) for name in shown]
    keys: dict[str, tuple[str, ...]] = {}
    unnamed = False
    for cid, b in ctx.case.communication.items():
        if not b.languages.recorded:
            continue
        ks = [v for v in b.languages.values if v != codes.LANGUAGE_OTHER]
        if codes.LANGUAGE_OTHER in b.languages.values:
            names = b.other_languages.values if b.other_languages.recorded else ()
            if not names:
                ks.append("other:?")
                unnamed = True
            ks += [f"other:{name}" for name in names]
        keys[cid] = tuple(dict.fromkeys(ks))
    if unnamed:
        rows.append(("other:?", "Andere Sprache (ohne Bezeichnung)"))
    return rows, keys


def p4(ctx: Context):
    rows, keys = language_rows(ctx)
    return _heat_figure(
        ctx, title="P4 · Sprachen nach Wohnortbereich", subtitle="In welchen Sprachen wird mit Kontakten an verschiedenen Wohnorten kommuniziert?",
        sections=[(None, rows)], values_of=lambda cid: keys.get(cid),
        notes=["Mehrsprachige Kontakte zählen in jeder verwendeten Sprache; Anteile summieren sich daher nicht zu 100 %."],
    )


FUNCTION_LABELS = {
    "1": "Persönlicher\nRückhalt / Rat", "2": "Gemeinsame\nAktivitäten /\nGespräche", "3": "Praktische Hilfe\nim Alltag",
    "4": "Sprachliche Hilfe /\nÜbersetzung", "5": "Sonstiges", "0": "Nichts davon", "missing": "keine Angabe",
}


def p5(ctx: Context):
    items = []
    for c in ctx.case.contacts:
        row = _closeness_key(c.closeness)
        fill = relation_fill(ctx.case, c.id)
        if c.functions.recorded:
            items += [Item(c.id, f, row, fill) for f in c.functions.values]
        else:
            items.append(Item(c.id, "missing", row, fill))
    present = {i.column for i in items}
    keys = ["1", "2", "3", "4", "5"] + [k for k in ("0", "missing") if k in present]
    columns = [(k, FUNCTION_LABELS[k]) for k in keys]
    rows = closeness_rows(any(i.row == "missing" for i in items))
    row_gaps = {len(rows) - 1: MISSING_GAP} if rows[-1][0] == "missing" else {}
    gaps = {keys.index(k): MISSING_GAP for k in ("0", "missing") if k in keys}
    if "0" in keys and "missing" in keys:
        gaps[keys.index("missing")] = 0.15
    geometry = point_geometry(columns, rows, items, MATRIX_W, gaps, row_gaps, bracket=False)
    p = page(ctx, "P5 · Beziehungsfunktionen und persönliche Nähe", "Welche Funktionen haben nahe und weniger nahe Kontakte?",
             main_w=MATRIX_W, main_h=geometry.height, legend="bottom", sections=[("Beziehungstyp", relation_entries(ctx.case))],
             notes=["Mehrfachnennungen möglich; Kontakte können in mehreren Funktionsspalten erscheinen."])
    point_matrix(p.main, MATRIX_W, geometry, columns, rows, items, gaps=gaps, row_gaps=row_gaps, column_counts=Counter(i.column for i in items),
                 y_title="Persönliche Nähe")
    return p.figure
