"""The coding rules of the network_v1 survey: code lists, missing-value markers and how one cell is read.

Every cell is read into a :class:`Cell`: the raw text is kept, and next to it either the parsed value(s) or the
reason why there is none. Five states are kept apart and never collapse into each other:

* a recorded value                                    -- ``Cell.values``
* ``NS`` unknown (the respondent does not know)      -- ``Missing.UNKNOWN``
* ``KA`` no answer                                    -- ``Missing.NO_ANSWER``
* ``NA`` not applicable                               -- ``Missing.NOT_APPLICABLE``
* an empty cell: not collected (or not entered)       -- ``Missing.NOT_COLLECTED``

A missing value is never ``0``. The one rule-conform empty cell (language use with exactly one language) is
decided where the languages are known (:mod:`.validate`), not here.

Multiple codes in one cell are separated by ``,`` or ``;`` (``1, 3`` or ``1;3``). Closeness is a single value, so a
comma there is a decimal comma (``2,5``). ``|`` is the separator of the v0 package format and is rejected.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass


class Missing(enum.Enum):
    UNKNOWN = "NS"
    NO_ANSWER = "KA"
    NOT_APPLICABLE = "NA"
    NOT_COLLECTED = ""


MARKERS = {m.value: m for m in Missing if m.value}
MISSING_LABELS = {
    Missing.UNKNOWN: "unbekannt (NS)",
    Missing.NO_ANSWER: "keine Antwort (KA)",
    Missing.NOT_APPLICABLE: "nicht anwendbar (NA)",
    Missing.NOT_COLLECTED: "nicht erhoben",
}

# ---------------------------------------------------------------- table A: contacts and relations -------------
CLOSENESS = {
    1.0: "sehr nah",
    1.5: "zwischen sehr nah und nah",
    2.0: "nah",
    2.5: "zwischen nah und weniger nah",
    3.0: "weniger nah",
    3.5: "zwischen weniger nah und außerhalb",
    4.0: "außerhalb der Kreise",
}
CLOSENESS_LEVELS = tuple(sorted(CLOSENESS))  # 1 = very close ... 4 = outside the circles

RELATION_TYPE = {
    "1": "Familie",
    "2": "Partner:in",
    "3": "Freund:in",
    "4": "Bekannte:r",
    "5": "professioneller/institutioneller Kontakt",
    "6": "sonstige Beziehung",
}
CONTACT_FREQUENCY = {
    "1": "(fast) täglich",
    "2": "wöchentlich",
    "3": "mehrmals monatlich",
    "4": "etwa monatlich",
    "5": "wenige Male im Jahr oder seltener",
}
FUNCTIONS = {
    "1": "persönlicher Rückhalt / Rat",
    "2": "gemeinsame Aktivitäten / Gespräche",
    "3": "praktische Hilfe im Alltag",
    "4": "sprachliche Hilfe / Übersetzung",
    "5": "sonstige Funktion",
    "0": "nichts davon",
}
FUNCTION_NONE = "0"  # exclusive: never combined with another function

# ---------------------------------------------------------------- table B: communication and languages --------
COMMUNICATION_FORMS = {
    "1": "persönlich",
    "2": "Videoanruf",
    "3": "Telefonat",
    "4": "Sprachnachrichten",
    "5": "Textnachrichten / Chat",
    "6": "Sonstiges",
}
LANGUAGES = {
    "1": "Spanisch",
    "2": "Deutsch",
    "3": "Englisch",
    "4": "Portugiesisch",
    "5": "andere Sprache",
}
LANGUAGE_OTHER = "5"  # needs the name of the language (column other_languages)
LANGUAGE_USE_FLAGS = {"M": "regelmäßige Sprachmischung", "S": "abhängig von Situation oder Medium"}

# ---------------------------------------------------------------- table C: groups and connections -------------
GROUP_STATUS = {
    "T": "alle Mitglieder haben untereinander Kontakt",
    "P": "teilweise verbunden",
    "N": "keine Verbindungen untereinander",
    "NS": "befragte Person weiß es nicht",
}
BELONGING = {"1": "sehr stark", "2": "stark", "3": "mittel", "4": "wenig", "5": "überhaupt nicht"}
CONNECTION = {"1": "Kontakt bestätigt", "0": "kein Kontakt bestätigt", "?": "unbekannt / nicht erhoben"}

CONTACT_ID = re.compile(r"A\d{2,}")
GROUP_ID = re.compile(r"C\d{2,}")
_SEPARATORS = re.compile(r"\s*[,;]\s*")


@dataclass(frozen=True)
class Cell:
    """One cell as recorded and as read."""

    raw: str
    values: tuple[str, ...] = ()
    missing: Missing | None = None
    error: str | None = None  # why the cell could not be read (an invalid code, a forbidden combination ...)

    @property
    def recorded(self) -> bool:
        return bool(self.values) and self.error is None

    @property
    def value(self) -> str | None:
        return self.values[0] if self.recorded else None


def _missing(text: str) -> Missing | None:
    if not text:
        return Missing.NOT_COLLECTED
    return MARKERS.get(text.upper())


def read_single(raw: str | None, codes: dict[str, str]) -> Cell:
    text = (raw or "").strip()
    missing = _missing(text)
    if missing is not None:
        return Cell(text, missing=missing)
    if "|" in text:
        return Cell(text, error=f"'|' ist der Trenner des v0-Paketformats, nicht von network_v1: {text!r}")
    if text not in codes:
        return Cell(text, error=f"ungültiger Code {text!r} (zulässig: {', '.join(codes)}, NS, KA, NA)")
    return Cell(text, (text,))


def read_multi(raw: str | None, codes: dict[str, str] | None, *, exclusive: str | None = None) -> Cell:
    """Several codes in one cell; ``codes=None`` accepts any non-empty item (free text lists)."""
    text = (raw or "").strip()
    missing = _missing(text)
    if missing is not None:
        return Cell(text, missing=missing)
    if "|" in text:
        return Cell(text, error=f"'|' ist der Trenner des v0-Paketformats, nicht von network_v1: {text!r}")
    items = [item for item in _SEPARATORS.split(text)]
    if any(not item for item in items):
        return Cell(text, error=f"leeres Element in einer Mehrfachangabe: {text!r}")
    if any(item.upper() in MARKERS for item in items):
        return Cell(text, error=f"NS/KA/NA stehen allein, nicht neben Codes: {text!r}")
    if codes is not None:
        bad = [item for item in items if item not in codes]
        if bad:
            return Cell(text, error=f"ungültige Codes {', '.join(bad)} (zulässig: {', '.join(codes)})")
    if len(set(items)) != len(items):
        return Cell(text, error=f"doppelter Code in {text!r}")
    if exclusive is not None and exclusive in items and len(items) > 1:
        return Cell(text, error=f"Code {exclusive} ist exklusiv und darf nicht mit weiteren Codes stehen: {text!r}")
    if codes is not None:
        order = list(codes)
        items.sort(key=order.index)
    return Cell(text, tuple(items))


def read_closeness(raw: str | None) -> Cell:
    """1, 1,5, 2, 2,5, 3, 3,5 or 4 (decimal comma or point). The original text is kept."""
    text = (raw or "").strip()
    missing = _missing(text)
    if missing is not None:
        return Cell(text, missing=missing)
    try:
        number = float(text.replace(",", "."))
    except ValueError:
        return Cell(text, error=f"Nähe {text!r} ist keine Zahl (zulässig: 1, 1,5, 2, 2,5, 3, 3,5, 4, NS, KA, NA)")
    if number not in CLOSENESS:
        hint = " – die Skala 1–5 gehört zu network_v0" if number == 5 else ""
        return Cell(text, error=f"Nähe {text!r} liegt nicht auf der Skala 1–4 in halben Schritten{hint}")
    return Cell(text, (format_closeness(number),))


def closeness_value(cell: Cell) -> float | None:
    return float(cell.value) if cell.recorded else None


def format_closeness(value: float) -> str:
    """Normalised spelling: ``1``, ``1.5`` ..."""
    return f"{value:g}"


def closeness_label(value: float) -> str:
    """German spelling in figures: ``2,5``."""
    return format_closeness(value).replace(".", ",")


def read_group_status(raw: str | None) -> Cell:
    """T, P, N or NS. Here ``NS`` is a recorded answer (the respondent does not know), not a missing value."""
    text = (raw or "").strip()
    if text.upper() in GROUP_STATUS:
        return Cell(text, (text.upper(),))
    return read_single(text, GROUP_STATUS)


def read_language_use(raw: str | None) -> Cell:
    """Empty, a language code 1-5, ``M``, ``S`` or ``M;S`` (order and separator free). Whether an empty cell is
    rule-conform depends on the number of languages and is decided by the validator."""
    text = (raw or "").strip()
    missing = _missing(text)
    if missing is not None:
        return Cell(text, missing=missing)
    if "|" in text:
        return Cell(text, error=f"'|' ist der Trenner des v0-Paketformats, nicht von network_v1: {text!r}")
    items = [item.upper() for item in _SEPARATORS.split(text)]
    if len(items) == 1 and items[0] in LANGUAGES:
        return Cell(text, (items[0],))
    if set(items) <= set(LANGUAGE_USE_FLAGS) and len(set(items)) == len(items):
        return Cell(text, tuple(sorted(items)))
    return Cell(text, error=f"Sprachgebrauch {text!r} ungültig (zulässig: leer, 1–5, M, S, M;S, NS, KA, NA)")


def language_use_label(values: tuple[str, ...]) -> str:
    if not values:
        return ""
    if values[0] in LANGUAGES:
        return f"überwiegend {LANGUAGES[values[0]]}"
    return " und ".join(LANGUAGE_USE_FLAGS[v] for v in values)
