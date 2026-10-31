"""The matrix figures of network_v1: P1-P5.

* P1 residence area x personal closeness (point matrix)
* P2 residence area x contact frequency (point matrix)
* P3 residence area x communication forms (count matrix, multiple answers)
* P4 residence area x languages (count matrix, multiple answers; named other languages differentiated)
* P5 relation functions x personal closeness (point matrix; a contact with several functions appears several times)

Ordinal codes stay categories: rows are placed in code order, never on a metric axis. Missing answers are a row or
column of their own and are never counted as 'no'.
"""

from __future__ import annotations

from collections import Counter

from .. import codes
from ..places import Area
from .base import (
    AREA_COLORS, MUTED, SMALL_PT, Context, Item, area_bracket, area_columns, closeness_rows, count_matrix, frame, new_figure,
    point_matrix,
)

MAX_OTHER_LANGUAGES = 3  # named other languages shown as rows of their own; the rest is 'weitere'


def _area_fill(ctx: Context, cid: str) -> str | None:
    area = ctx.derived.area(cid)
    return None if area is Area.UNRESOLVED else AREA_COLORS[area]


def _area_counts(ctx: Context) -> Counter:
    return Counter(r.area for r in ctx.derived.residence.values())


def _header_colors(ctx: Context) -> dict:
    return {a: AREA_COLORS[a] for a in ctx.areas_present() if a is not Area.UNRESOLVED}


def _closeness_key(cell: codes.Cell):
    value = codes.closeness_value(cell)
    return value if value is not None else "missing"


def p1(ctx: Context):
    figure = new_figure(12.0, 9.0)
    ax = figure.add_axes((0.16, 0.1, 0.81, 0.72))
    columns = area_columns(ctx)
    items = [Item(c.id, ctx.derived.area(c.id), _closeness_key(c.closeness), _area_fill(ctx, c.id)) for c in ctx.case.contacts]
    missing = any(i.row == "missing" for i in items)
    rows = closeness_rows(missing)
    point_matrix(ax, columns, rows, items, row_gaps=[len(rows) - 1] if missing else [], column_counts=_area_counts(ctx),
                 column_header_colors=_header_colors(ctx))
    area_bracket(ax, columns, y=-0.95)
    note = ("Nähe = im Gespräch erfragter Wert aus Tabelle A (1 = sehr nah … 4 = außerhalb der Kreise; Zwischenwerte als eigene Zeilen), "
            "nie aus der Kartenposition.\nWohnortbereich = Kategorie, keine Entfernung: persönliche Nähe und geografische Lage sind getrennte Achsen.")
    frame(figure, ctx, "P1 · Wohnortbereich und persönliche Nähe", "Jeder Kontakt erscheint einmal, beschriftet mit seiner ID", note)
    figure.text(0.03, 0.83, "persönliche Nähe ↓", fontsize=SMALL_PT + 1, color=MUTED)
    return figure


def p2(ctx: Context):
    figure = new_figure(12.0, 8.0)
    ax = figure.add_axes((0.2, 0.1, 0.77, 0.7))
    columns = area_columns(ctx)
    rows: list = [(code, f"{code} · {label}") for code, label in codes.CONTACT_FREQUENCY.items()]
    items = []
    for c in ctx.case.contacts:
        key = c.contact_frequency.value if c.contact_frequency.recorded else "missing"
        items.append(Item(c.id, ctx.derived.area(c.id), key, _area_fill(ctx, c.id)))
    missing = any(i.row == "missing" for i in items)
    if missing:
        rows.append(("missing", "keine Angabe"))
    point_matrix(ax, columns, rows, items, row_gaps=[len(rows) - 1] if missing else [], column_counts=_area_counts(ctx),
                 column_header_colors=_header_colors(ctx))
    area_bracket(ax, columns, y=-0.95)
    note = "Kontakthäufigkeit ist eine geordnete Kategorie (1 = (fast) täglich … 5 = wenige Male im Jahr oder seltener), kein Messwert; Abstände zwischen den Zeilen haben keine Bedeutung."
    frame(figure, ctx, "P2 · Wohnortbereich und Kontakthäufigkeit", "Jeder Kontakt erscheint einmal, beschriftet mit seiner ID", note)
    return figure


def _matrix_counts(ctx: Context, values_of) -> tuple[dict, dict, dict]:
    """Counts per (area, row) among contacts with a recorded answer; bases and missing per area."""
    counts: Counter = Counter()
    bases: Counter = Counter()
    missing: Counter = Counter()
    for c in ctx.case.contacts:
        area = ctx.derived.area(c.id)
        values = values_of(c.id)
        if values is None:
            missing[area] += 1
            continue
        bases[area] += 1
        for v in values:
            counts[(area, v)] += 1
    return counts, bases, missing


def p3(ctx: Context):
    def forms(cid):
        b = ctx.case.communication.get(cid)
        return b.forms.values if b is not None and b.forms.recorded else None

    counts, bases, missing = _matrix_counts(ctx, forms)
    figure = new_figure(12.0, 7.6)
    ax = figure.add_axes((0.2, 0.12, 0.77, 0.66))
    columns = area_columns(ctx)
    rows = [(code, f"{code} · {label}") for code, label in codes.COMMUNICATION_FORMS.items()]
    count_matrix(ax, columns, rows, counts, bases, missing=missing, column_header_colors=_header_colors(ctx))
    area_bracket(ax, columns, y=-1.22)
    note = ("Mehrfachnennungen: ein Kontakt zählt in jeder genannten Kommunikationsform; Spalten summieren sich daher nicht zu n.\n"
            "n = Kontakte des Bereichs mit Angabe in Tabelle B; „ohne Angabe“ = nicht erhoben, keine Antwort oder unbekannt (nie als „nein“ gezählt). "
            "Plattformen sind keine eigene Kategorie.")
    frame(figure, ctx, "P3 · Kommunikationsformen nach Wohnortbereich", "Anzahl und Anteil der Kontakte je Form", note)
    return figure


def language_rows(ctx: Context) -> tuple[list[tuple[str, str]], dict[str, tuple[str, ...]]]:
    """Rows of P4 and the row keys of every contact. Named other languages get their own rows (up to
    MAX_OTHER_LANGUAGES, most frequent first); further ones share a row; code 5 without a name has its own row."""
    named: Counter = Counter()
    for b in ctx.case.communication.values():
        if b.other_languages.recorded:
            named.update(b.other_languages.values)
    shown = [name for name, _ in sorted(named.items(), key=lambda kv: (-kv[1], kv[0]))[:MAX_OTHER_LANGUAGES]]
    rows = [(code, f"{code} · {label}") for code, label in codes.LANGUAGES.items() if code != codes.LANGUAGE_OTHER]
    rows += [(f"other:{name}", f"5 · {name}") for name in shown]
    keys: dict[str, tuple[str, ...]] = {}
    extra = unnamed = False
    for cid, b in ctx.case.communication.items():
        if not b.languages.recorded:
            continue
        ks = [v for v in b.languages.values if v != codes.LANGUAGE_OTHER]
        if codes.LANGUAGE_OTHER in b.languages.values:
            names = b.other_languages.values if b.other_languages.recorded else ()
            if not names:
                ks.append("other:?")
                unnamed = True
            for name in names:
                if name in shown:
                    ks.append(f"other:{name}")
                else:
                    ks.append("other:more")
                    extra = True
        keys[cid] = tuple(dict.fromkeys(ks))
    if extra:
        rows.append(("other:more", "5 · weitere andere Sprachen"))
    if unnamed:
        rows.append(("other:?", "5 · andere (ohne Bezeichnung)"))
    return rows, keys


def p4(ctx: Context):
    rows, keys = language_rows(ctx)
    counts, bases, missing = _matrix_counts(ctx, lambda cid: keys.get(cid))
    figure = new_figure(12.0, 7.0 + 0.35 * max(0, len(rows) - 5))
    ax = figure.add_axes((0.2, 0.13, 0.77, 0.64))
    columns = area_columns(ctx)
    count_matrix(ax, columns, rows, counts, bases, missing=missing, column_header_colors=_header_colors(ctx), shade="#6B3D7A")
    area_bracket(ax, columns, y=-1.22)
    note = ("Mehrfachnennungen: mehrsprachige Kontakte zählen in jeder verwendeten Sprache. Benannte andere Sprachen stehen einzeln "
            f"(höchstens {MAX_OTHER_LANGUAGES}).\nSprachmischung (M) und situativer Sprachgebrauch (S) sind im Datenmodell erhalten, aber nicht Teil dieser Grafik. "
            "„ohne Angabe“ wird nie als „nein“ gezählt.")
    frame(figure, ctx, "P4 · Sprachen nach Wohnortbereich", "Anzahl und Anteil der Kontakte, mit denen eine Sprache verwendet wird", note)
    return figure


def p5(ctx: Context):
    figure = new_figure(12.0, 9.0)
    ax = figure.add_axes((0.16, 0.1, 0.81, 0.72))
    labels = {
        "1": "1 · Rückhalt /\nRat", "2": "2 · Aktivitäten /\nGespräche", "3": "3 · praktische\nHilfe", "4": "4 · sprachliche\nHilfe",
        "5": "5 · sonstige\nFunktion", "0": "0 · nichts\ndavon", "missing": "keine\nAngabe",
    }
    items, mentions, persons = [], 0, 0
    for c in ctx.case.contacts:
        row = _closeness_key(c.closeness)
        if c.functions.recorded:
            persons += 1
            for f in c.functions.values:
                items.append(Item(c.id, f, row, "#5B6770"))
                mentions += 1 if f != codes.FUNCTION_NONE else 0
        else:
            items.append(Item(c.id, "missing", row, None))
    column_keys = ["1", "2", "3", "4", "5", "0"] + (["missing"] if any(i.column == "missing" for i in items) else [])
    columns = [(k, labels[k]) for k in column_keys]
    rows = closeness_rows(any(i.row == "missing" for i in items))
    counts = Counter(i.column for i in items)
    point_matrix(ax, columns, rows, items, column_gaps=[5] + ([6] if "missing" in column_keys else []),
                 row_gaps=[len(rows) - 1] if rows[-1][0] == "missing" else [], column_counts=counts, per_line=3)
    note = (f"Mehrfachnennungen: Kontakte mit mehreren Funktionen erscheinen in jeder Funktionsspalte ({mentions} Nennungen von {persons} Kontakten mit Angabe).\n"
            "„0 · nichts davon“ ist eine Antwort (keine der Funktionen) und steht getrennt; „keine Angabe“ ist keine Antwort. Nähe: 1 = sehr nah … 4 = außerhalb der Kreise.")
    frame(figure, ctx, "P5 · Beziehungsfunktionen und persönliche Nähe", "Welche Funktionen haben nahe und weniger nahe Kontakte?", note)
    return figure
