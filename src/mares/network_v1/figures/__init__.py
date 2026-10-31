"""The fixed set of eight standard figures of network_v1 -- no more, no automatic combinations.

A figure whose data are missing is not drawn; its entry carries the reason instead (``skipped``), so nothing
pretends to show what was not surveyed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from mares.network_v0.figures.style import rc, save_figure

from ..places import Area
from .base import Context, file_name
from .matrices import p1, p2, p3, p4, p5
from .networks import g1, g2, g3


@dataclass(frozen=True)
class FigureSpec:
    code: str
    name: str  # file name part, ASCII
    title: str
    inputs: tuple[str, ...]
    draw: Callable
    missing: Callable[[Context], str | None]  # reason why the figure cannot be drawn, or None


def _no(ctx: Context, test, reason: str) -> str | None:
    return None if any(test(c) for c in ctx.case.contacts) else reason


def _all_unresolved(ctx: Context) -> bool:
    return all(r.area is Area.UNRESOLVED for r in ctx.derived.residence.values())


FIGURES: tuple[FigureSpec, ...] = (
    FigureSpec("G1", "persoenliches_netz", "Persönliches Beziehungsnetz", ("A: Nähe", "A: Beziehungstyp", "C: bestätigte Verbindungen"), g1,
               lambda ctx: _no(ctx, lambda c: c.closeness.recorded, "keine erhobene persönliche Nähe")),
    FigureSpec("G2", "geografisches_netz", "Geografisches Beziehungsnetz", ("A: Wohnort, Wohnland", "C: bestätigte Verbindungen"), g2,
               lambda ctx: "kein Wohnort zuordenbar" if _all_unresolved(ctx) else None),
    FigureSpec("P1", "wohnort_naehe", "Wohnortbereich und persönliche Nähe", ("A: Wohnort, Wohnland", "A: Nähe"), p1,
               lambda ctx: "kein Wohnort zuordenbar" if _all_unresolved(ctx) else _no(ctx, lambda c: c.closeness.recorded, "keine erhobene persönliche Nähe")),
    FigureSpec("P2", "wohnort_haeufigkeit", "Wohnortbereich und Kontakthäufigkeit", ("A: Wohnort, Wohnland", "A: Kontakthäufigkeit"), p2,
               lambda ctx: "kein Wohnort zuordenbar" if _all_unresolved(ctx) else _no(ctx, lambda c: c.contact_frequency.recorded, "keine erhobene Kontakthäufigkeit")),
    FigureSpec("P3", "wohnort_kommunikation", "Kommunikationsformen nach Wohnortbereich", ("A: Wohnort, Wohnland", "B: Kommunikationsformen"), p3,
               lambda ctx: None if any(b.forms.recorded for b in ctx.case.communication.values()) else "keine erhobenen Kommunikationsformen"),
    FigureSpec("P4", "wohnort_sprachen", "Sprachen nach Wohnortbereich", ("A: Wohnort, Wohnland", "B: Sprachen, andere Sprachen"), p4,
               lambda ctx: None if any(b.languages.recorded for b in ctx.case.communication.values()) else "keine erhobenen Sprachen"),
    FigureSpec("P5", "funktionen_naehe", "Beziehungsfunktionen und persönliche Nähe", ("A: Bedeutung/Funktionen", "A: Nähe"), p5,
               lambda ctx: _no(ctx, lambda c: c.functions.recorded, "keine erhobenen Beziehungsfunktionen")),
    FigureSpec("G3", "gruppen_zugehoerigkeit", "Gruppenstruktur und Zugehörigkeit", ("C: Gruppen, Mitglieder, Status, Zugehörigkeit", "C: bestätigte Verbindungen"), g3,
               lambda ctx: None if ctx.case.groups else "keine Gruppen erhoben"),
)
FORMATS = ("png", "svg")


def render(ctx: Context, target: Path, formats: tuple[str, ...] = ("png",)) -> list[dict]:
    """Draw the eight figures into ``target`` (the case's ``graphics/``); returns one entry per figure."""
    if not formats or not set(formats) <= set(FORMATS):
        raise ValueError(f"formats must be a non-empty subset of {', '.join(FORMATS)}")
    target.mkdir(parents=True, exist_ok=True)
    entries = []
    for spec in FIGURES:
        entry = {"code": spec.code, "title": spec.title, "inputs": list(spec.inputs)}
        reason = spec.missing(ctx)
        if reason:
            entries.append({**entry, "status": "skipped", "reason": reason, "files": []})
            continue
        with rc():
            figure = spec.draw(ctx)
            stem = target / file_name(ctx.code, spec.code, spec.name, "png")
            written = save_figure(figure, stem.with_suffix(""), formats)
        entries.append({**entry, "status": "rendered", "reason": None, "files": [p.name for p in written]})
    return entries


def expected_files(case_code: str, formats: tuple[str, ...]) -> set[str]:
    return {file_name(case_code, s.code, s.name, f) for s in FIGURES for f in formats}
