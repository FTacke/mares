"""The standard figures of network_v0: G1, G2, P1-P5, G3 and X1, drawn by the shared figure functions of network_v1.

network_v0 keeps its own survey design: closeness is the table value 1-5 (5 = very close), contact frequency
1 = rarely ... 5 = daily, several relation codes per contact, eleven relation functions, eight media, the language mode,
and its own geography (Marburg · Region Marburg · rest of Germany · rest of Europe · outside Europe). Nothing is recoded
to v1. What the figures need is given by :class:`V0Scheme` (scales, labels and colours, read from the codebook of the
package) and by :func:`figure_context`, which puts a v0 dataset into the case structure the figure functions read --
with the v0 codes unchanged.

* **Relation types:** one colour per v0 relation code (the v1 colour where the meaning is the same); a contact with
  several codes gets a split node. No main relation is chosen.
* **Ties:** only the confirmed ties of the v0 network (:mod:`.build`); a missing tie is unknown, never 'no'.
* **Groups:** confirmed groups and memberships only; v0 records no belonging, so G3 labels have one line and no scale.
* **Geography:** the v0 residence classification (:mod:`.geo`); 'Nähe Marburg' stays a regional statement (Region
  Marburg) and gets no coordinate in X1.
* **Version:** the footer reads ``MARES · network_v0 · <n> Kontakte``; the case badge names version and pilot status.
"""

from __future__ import annotations

import textwrap
from collections import Counter
from pathlib import Path

from mares.network_v1 import codes as v1codes
from mares.network_v1.case import Case as V1Case
from mares.network_v1.case import Communication, Contact as V1Contact, Group as V1Group
from mares.network_v1.derive import CONFIRMED, Coverage, Derived, Pair
from mares.network_v1.figures import FIGURES as V1_FIGURES
from mares.network_v1.figures import _save
from mares.network_v1.figures.base import MISSING_LABEL, Context, Geo, Scheme, file_name
from mares.network_v1.places import Area, Residence as V1Residence
from mares.network_v0.figures.style import rc

from .build import Network
from .geo import DEFAULT_LOCAL_PLACES, GeoCategory, classify_residence
from .model import CONFIRMED as GROUP_CONFIRMED
from .model import NetworkDataset, TieState

STANDARD_CODES = ("G1", "G2", "P1", "P2", "P3", "P4", "P5", "G3", "X1")  # the nine standard figures of v0 (no G4/G5)

# v0 relation code -> colour: the v1 colour where the meaning is the same (family, partner, friendship, acquaintance,
# professional, other); three v0-only codes get colours that stay apart from those six.
RELATION_COLORS = {
    "1": "#D55E00", "2": "#CC79A7", "3": "#009E73", "4": "#56B4E9", "5": "#F0E442", "6": "#661100", "7": "#332288",
    "8": "#0072B2", "9": "#6B7280",
}
EXPECTED_RELATIONS = {  # the meaning each colour was chosen for (checked against the codebook of every package)
    "1": "Familie", "2": "Partner", "3": "Freundschaft", "4": "bekannt", "5": "Arbeit", "6": "Studium", "7": "Nachbarschaft",
    "8": "professionell", "9": "andere",
}
MEDIA_SECTIONS = (("Persönliche Kommunikation", ("1",)), ("Synchron auf Distanz", ("4", "5")), ("Asynchron", ("2", "3")),
                  ("Weitere Formen", ("6", "7", "8")))
AREA_OF = {GeoCategory.LOCAL: Area.MARBURG, GeoCategory.LOCAL_REGION: Area.MITTELHESSEN, GeoCategory.GERMANY_OTHER: Area.GERMANY_OTHER,
           GeoCategory.EUROPE_OTHER: Area.EUROPE_OTHER, GeoCategory.OUTSIDE_EUROPE: Area.OUTSIDE_EUROPE,
           GeoCategory.UNKNOWN: Area.UNRESOLVED}  # display slots only: the v0 categories keep their v0 labels


class SchemeError(ValueError):
    """The codebook of a package does not have the meanings the v0 scheme was made for. Nothing is drawn."""


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


class V0Scheme(Scheme):
    """The network_v0 survey design for the shared figure functions; labels come from the package codebook."""

    version = "network_v0"
    belonging = False
    closeness_title = "Nähe (Tabellenwert)"
    frequency_title = "Kontakthäufigkeit"
    g1_missing_radius = 5.75

    def __init__(self, dataset: NetworkDataset, local_places: tuple[str, ...] = DEFAULT_LOCAL_PLACES) -> None:
        book = dataset.codebook.entries
        for field in ("relation", "closeness_1_5", "contact_frequency", "media", "language", "function"):
            if field not in book:
                raise SchemeError(f"codebook has no field {field!r}")
        for code, meaning in book["relation"].items():  # every code of the codebook needs the meaning its colour was chosen for
            word = EXPECTED_RELATIONS.get(code)
            if word is None or word.lower() not in meaning.lower():
                raise SchemeError(f"relation code {code} is {meaning!r} in the codebook; the v0 scheme has no colour for that meaning")
        self.book = book
        local = " / ".join(local_places)
        self.area_labels = {Area.MARBURG: local, Area.MITTELHESSEN: f"Region {local}", Area.GERMANY_OTHER: "übriges Deutschland",
                            Area.EUROPE_OTHER: "übriges Europa", Area.OUTSIDE_EUROPE: "außerhalb Europas",
                            Area.UNRESOLVED: "Wohnort nicht zuordenbar"}
        self.bracket = f"{local} und Region {local}"
        self.function_keys = tuple(book["function"])

    # relation codes: several per contact; colours per code, a split node for several
    def _codes(self, case: V1Case, contact_id: str) -> tuple[str, ...]:
        cell = case.contact(contact_id).relation_type
        return tuple(c for c in cell.values if c in RELATION_COLORS) if cell.recorded else ()

    def fill(self, case, contact_id):
        cs = self._codes(case, contact_id)
        if not cs:
            return None
        return RELATION_COLORS[cs[0]] if len(cs) == 1 else tuple(RELATION_COLORS[c] for c in cs)

    def relation_section(self, case):
        present = Counter()
        several, missing = [], False
        for cid in case.contact_ids:
            cs = self._codes(case, cid)
            present.update(cs)
            missing |= not cs
            if len(cs) > 1:
                several.append(cs)
        entries = [("dot", _cap(meaning), RELATION_COLORS[code]) for code, meaning in self.book["relation"].items() if present[code]]
        if several:
            entries.append(("split", "mehrere Beziehungen: geteilter Knoten", tuple(RELATION_COLORS[c] for c in several[0])))
        if missing:
            entries.append(("dot", MISSING_LABEL, None))
        return "Beziehung", entries

    def sector_key(self, case, contact_id):
        return "+".join(self._codes(case, contact_id))

    def sector_order(self, case):
        keys = {self.sector_key(case, cid) for cid in case.contact_ids} - {""}
        return tuple(sorted(keys, key=lambda k: [int(c) for c in k.split("+")])) + ("",)

    # closeness: the table value 1-5, 5 = very close (never the map position)
    def closeness(self, contact):
        return float(contact.closeness.value) if contact.closeness.recorded else None

    def g1_radius(self, value):
        return 6.0 - value  # 5 (very close) innermost ... 1 outermost

    def g1_rings(self):
        return [(6.0 - v, str(v), True) for v in range(5, 0, -1)]

    def g1_legend(self):
        words = self.book["closeness_1_5"]
        text = "\n".join(f"{v} {words[str(v)]}" for v in range(5, 0, -1))
        return [("line", text, {"color": "#9AA5B1", "linewidth": 1.0}),
                ("text", "Tabellenwert der Erhebung,\nnicht die Kartenposition", None)]

    def closeness_rows(self, include_missing):
        words = self.book["closeness_1_5"]
        rows = [(float(v), f"{v} · {words[str(v)]}") for v in range(5, 0, -1)]
        return rows + ([("missing", MISSING_LABEL)] if include_missing else [])

    def closeness_key(self, contact):
        value = self.closeness(contact)
        return value if value is not None else "missing"

    # contact frequency: 5 = daily on top
    def frequency_rows(self):
        words = self.book["contact_frequency"]
        return [(code, _cap(words[code])) for code in sorted(words, key=int, reverse=True)]

    def frequency_key(self, contact):
        return contact.contact_frequency.value if contact.contact_frequency.recorded else "missing"

    # media
    def communication_sections(self):
        words = self.book["media"]
        return [(title, [(code, _cap(words[code])) for code in keys if code in words]) for title, keys in MEDIA_SECTIONS]

    def forms(self, case, contact_id):
        b = case.communication.get(contact_id)
        return b.forms.values if b is not None and b.forms.recorded else None

    # languages: every recorded language of a contact; no main language
    def language_rows(self, case):
        words = self.book["language"]
        rows = [(code, _cap(words[code])) for code in words]
        keys = {cid: b.languages.values for cid, b in case.communication.items() if b.languages.recorded}
        return rows, keys

    # relation functions: the eleven v0 functions
    function_none = None
    p5_width = 16.0  # up to eleven function columns
    drop_empty = True  # functions, media and languages that no contact has are not shown
    x1_neighbours_with_germany = True  # X1: contacts in a neighbouring country on the Germany map, no extra Europe panel

    def function_label(self, key):
        if key == "missing":
            return MISSING_LABEL
        return "\n".join(textwrap.wrap(_cap(self.book["function"][key]), 15, break_long_words=False))

    def functions(self, contact):
        return contact.functions.values if contact.functions.recorded else None


# --------------------------------------------------------------------------------------------- the case ---
def _cell(codes: tuple[str, ...]) -> v1codes.Cell:
    if not codes:
        return v1codes.Cell("", (), v1codes.Missing.NOT_COLLECTED)
    return v1codes.Cell("|".join(codes), tuple(codes))


def _country_name(geo: Geo | None, iso3: str | None) -> str:
    """German name of a residence country from the basemap of X1 (v0 packages record the ISO code only); else ''."""
    if not iso3 or geo is None or not geo.countries or iso3 not in geo.countries:
        return ""
    return geo.countries[iso3].get("properties", {}).get("NAME_DE", "") or ""


def figure_context(dataset: NetworkDataset, network: Network, *, case_code: str, local_places: tuple[str, ...] = DEFAULT_LOCAL_PLACES,
                   geo: Geo | None = None, case_type: str = "pilot") -> Context:
    """The v0 dataset in the case structure of the shared figures -- v0 codes unchanged, confirmed groups and ties only."""
    source = dataset.case.source_label
    metadata = {"case_code": case_code, "case_type": case_type, "provenance": "survey",
                "display_code": f"v0-{'Pilot' if case_type == 'pilot' else 'Fall'} {source}", "dataset_version": "network_v0"}
    case = V1Case(Path("."), metadata)
    residence = {}
    for c in dataset.contacts:
        def codes_of(attribute):
            parsed = c.codes.get(attribute)
            return tuple(parsed.codes) if parsed else ()

        city = c.text.get("residence_city")
        country = c.text.get("residence_country")
        res = classify_residence(city, country, local_places)
        residence[c.contact_id] = V1Residence(AREA_OF[res.category], f"network_v0: {res.category.value}", city, country)
        case.contacts.append(V1Contact(
            id=c.contact_id, label="", closeness=_cell(codes_of("closeness")), relation_type=_cell(codes_of("relation")),
            contact_frequency=_cell(codes_of("contact_frequency")), functions=_cell(codes_of("function")),
            birth_country=c.text.get("birth_country_source", ""), birth_country_iso3=c.text.get("birth_country", ""),
            residence_place=city or "", residence_country=_country_name(geo, country), residence_country_iso3=country or "",
            comment="", ref="",
        ))
        case.communication[c.contact_id] = Communication(
            c.contact_id, forms=_cell(codes_of("media")), languages=_cell(codes_of("language")),
            other_languages=_cell(()), language_use=_cell(codes_of("language_mode")), comment="", ref="")
    confirmed = {m.group_id for m in dataset.memberships if m.status == GROUP_CONFIRMED}
    for g in dataset.groups:
        if g.assessment == GROUP_CONFIRMED and g.group_id in confirmed:
            case.groups.append(V1Group(g.group_id, g.label, _cell(("T",)), _cell(()), g.comment, ""))
    case.memberships = [(m.group_id, m.contact_id, "") for m in dataset.memberships
                        if m.status == GROUP_CONFIRMED and m.group_id in {g.id for g in case.groups}]
    pairs = {}
    for tie in network.ties:
        if tie.state is TieState.YES:
            key = tuple(sorted((tie.a, tie.b)))
            pairs[key] = Pair(*key, statements=[(CONFIRMED, "network_v0:" + "|".join(tie.group_ids))])
    n = len(case.contacts)
    coverage = Coverage(n, n * (n - 1) // 2, len(pairs), 0, 0, n * (n - 1) // 2 - len(pairs), 0)
    return Context(case, Derived(residence, pairs, coverage), geo, V0Scheme(dataset, local_places))


def render_standard(ctx: Context, target: Path, formats: tuple[str, ...]) -> list[dict]:
    """The nine standard figures of v0 into ``target``: the same figure functions and file names as v1 (G1 ... X1)."""
    target.mkdir(parents=True, exist_ok=True)
    entries = []
    for spec in V1_FIGURES:
        if spec.code not in STANDARD_CODES:
            continue
        entry = {"code": spec.code, "title": spec.title}
        reason = spec.missing(ctx)
        if reason:
            entries.append({**entry, "status": "skipped", "reason": reason, "files": []})
            continue
        with rc():
            written = _save(spec.draw(ctx), target / file_name(ctx.code, spec.code, spec.name, "png")[:-4], formats)
        entries.append({**entry, "status": "rendered", "reason": None, "files": [p.name for p in written]})
    return entries


def expected_files(case_code: str, formats: tuple[str, ...]) -> set[str]:
    return {file_name(case_code, s.code, s.name, f) for s in V1_FIGURES if s.code in STANDARD_CODES for f in formats}
