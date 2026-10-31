"""Validation of a network_v1 case.

Three levels, kept apart:

* **error**   -- the case is not processed further (a duplicate or unknown ID, an invalid code, a forbidden combination,
  an invalid closeness value, contradicting statements about a pair, v0 and v1 mixed, inconsistent metadata ...)
* **warning** -- usable, but to be known (a missing answer, an unresolvable residence, missing group information ...)
* **note**    -- a permitted gap or a documented fact (the rule-conform empty language use, identical duplicate statements)

The validator never sets a data quality: a technically valid case is not a scientifically validated one.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass

from . import DATASET_VERSION, FORMAT
from . import codes
from .case import CASE_TYPES, ERROR, FIELD_ORIGINS, NOTE, PROVENANCES, WARNING, Case, Finding
from .derive import CONFLICT, Derived, derive
from .places import ISO3, Area

PASSED, PASSED_WITH_WARNINGS, FAILED = "PASSED", "PASSED_WITH_WARNINGS", "FAILED"
CASE_CODE = re.compile(r"[0-9]{3}[a-z0-9_]*")
CONTACT_DATA = re.compile(r"@|\+?\d[\d /-]{6,}")  # an e-mail address or a phone number in a label

# Context sheet: field names follow the areas of the sheet. ``language_use`` and ``language_confidence`` take a
# qualifier (``language_use:arbeit``, ``language_confidence:deutsch``). Values are kept as recorded.
CONTEXT_FIELDS = {
    "origin_country": "Herkunft (Land)",
    "age": "Alter",
    "stay_duration": "Aufenthaltsdauer",
    "migration_context": "Migrationskontext",
    "residence_place": "aktueller Wohnort",
    "marburg_relation": "Marburg-Bezug",
    "occupation": "Tätigkeit",
    "housing": "Wohnsituation",
    "daily_languages": "Sprachen im Alltag",
    "language_use": "Sprachverwendung nach Lebensbereichen",
    "language_confidence": "subjektive sprachliche Sicherheit",
}
CONTEXT_MULTI = {"migration_context", "daily_languages", "occupation", "marburg_relation"}
CONTEXT_QUALIFIED = {"language_use", "language_confidence"}


@dataclass
class Validation:
    findings: list[Finding]
    derived: Derived | None

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == WARNING]

    @property
    def notes(self) -> list[Finding]:
        return [f for f in self.findings if f.level == NOTE]

    @property
    def status(self) -> str:
        if self.errors:
            return FAILED
        return PASSED_WITH_WARNINGS if self.warnings else PASSED

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "counts": {"errors": len(self.errors), "warnings": len(self.warnings), "notes": len(self.notes)},
            "findings": [f.to_dict() for f in self.findings],
        }


def _metadata(case: Case, out: list[Finding]) -> None:
    m = case.metadata
    if not m:
        return
    if m.get("format") != FORMAT:
        out.append(Finding(ERROR, "metadata_format", f"format muss {FORMAT!r} sein, nicht {m.get('format')!r}", "metadata.json"))
    version = m.get("dataset_version")
    if version != DATASET_VERSION:
        hint = " – v0-Daten werden nicht als v1 verarbeitet" if version == "network_v0" else ""
        out.append(Finding(ERROR, "dataset_version", f"dataset_version muss 'network_v1' sein, nicht {version!r}{hint}", "metadata.json"))
    code = m.get("case_code")
    if not isinstance(code, str) or not CASE_CODE.fullmatch(code):
        out.append(Finding(ERROR, "case_code", f"case_code {code!r} ungültig (drei Ziffern, dann a-z, 0-9, _)", "metadata.json"))
    elif code != case.folder.name:
        out.append(Finding(ERROR, "case_code_folder", f"case_code {code!r} passt nicht zum Ordner {case.folder.name!r}", "metadata.json"))
    case_type, provenance, eligible = m.get("case_type"), m.get("provenance"), m.get("empirical_analysis_eligible")
    if case_type not in CASE_TYPES:
        out.append(Finding(ERROR, "case_type", f"case_type {case_type!r} ungültig ({', '.join(CASE_TYPES)})", "metadata.json"))
    if provenance not in PROVENANCES:
        out.append(Finding(ERROR, "provenance", f"provenance {provenance!r} ungültig ({', '.join(PROVENANCES)})", "metadata.json"))
    if not isinstance(eligible, bool):
        out.append(Finding(ERROR, "eligibility", "empirical_analysis_eligible muss true oder false sein", "metadata.json"))
    if case_type == "test" and eligible is True:
        out.append(Finding(ERROR, "eligibility", "ein Testfall ist nie empirisch auswertbar (empirical_analysis_eligible: false)", "metadata.json"))
    if provenance in ("fully_synthetic", "v0_derived_fictionalized") and case_type != "test":
        out.append(Finding(ERROR, "provenance", f"Fälle mit provenance {provenance!r} sind Testfälle (case_type: test)", "metadata.json"))
    if case_type in ("pilot", "regular") and provenance != "survey":
        out.append(Finding(ERROR, "provenance", f"ein {case_type}-Fall stammt aus einer Erhebung (provenance: survey)", "metadata.json"))
    parent = case.folder.parent.name
    if parent == "cases" and case_type != "regular":
        out.append(Finding(ERROR, "case_folder", "unter cases/ liegen nur reguläre Erhebungen (case_type: regular)", "metadata.json"))
    if parent == "pilots" and case_type not in ("pilot", "test"):
        out.append(Finding(ERROR, "case_folder", "unter pilots/ liegen Pilot- und Testfälle", "metadata.json"))
    survey = m.get("survey") if isinstance(m.get("survey"), dict) else {}
    if case_type in ("pilot", "regular"):
        for key in ("design", "instrument_version", "survey_date", "data_origin"):
            if not survey.get(key):
                out.append(Finding(WARNING, "survey_metadata", f"survey.{key} fehlt (für empirische Fälle zu dokumentieren)", "metadata.json"))
        for key in ("data_quality", "limitations"):
            if key not in m:
                out.append(Finding(WARNING, "survey_metadata", f"{key} fehlt (für empirische Fälle zu dokumentieren)", "metadata.json"))
    origins = m.get("field_origins", {})
    if not isinstance(origins, dict) or any(v not in FIELD_ORIGINS for v in origins.values()):
        out.append(Finding(ERROR, "field_origins", f"field_origins: Werte aus {', '.join(FIELD_ORIGINS)}", "metadata.json"))


def _cells(ref: str, owner: str, cells: dict[str, codes.Cell], out: list[Finding]) -> None:
    for name, cell in cells.items():
        if cell.error:
            out.append(Finding(ERROR, f"invalid_{name}", f"{owner}: {cell.error}", ref))


def _missing_summary(label: str, ids: list[str], out: list[Finding], code: str) -> None:
    if ids:
        out.append(Finding(WARNING, code, f"{label} fehlt bei {len(ids)} Kontakt(en): {', '.join(ids)}", "contacts"))


def _contacts(case: Case, out: list[Finding]) -> None:
    ids = [c.id for c in case.contacts]
    for cid, n in Counter(ids).items():
        if n > 1:
            out.append(Finding(ERROR, "duplicate_contact", f"Kontakt-ID {cid} kommt {n}-mal vor", "contacts.csv"))
    for c in case.contacts:
        if not codes.CONTACT_ID.fullmatch(c.id):
            out.append(Finding(ERROR, "contact_id", f"Kontakt-ID {c.id!r} ungültig (A01, A02, …)", c.ref))
    numbers = sorted(int(i[1:]) for i in set(ids) if codes.CONTACT_ID.fullmatch(i))
    if numbers and numbers != list(range(1, len(numbers) + 1)):
        out.append(Finding(WARNING, "contact_sequence", "Kontakt-IDs sind nicht fortlaufend ab A01", "contacts.csv"))
    if not case.contacts:
        out.append(Finding(ERROR, "no_contacts", "Tabelle A enthält keinen Kontakt", "contacts.csv"))
    missing: dict[str, list[str]] = defaultdict(list)
    for c in case.contacts:
        _cells(c.ref, c.id, {"closeness": c.closeness, "relation_type": c.relation_type,
                             "contact_frequency": c.contact_frequency, "functions": c.functions}, out)
        if not c.label:
            missing["label"].append(c.id)
        elif CONTACT_DATA.search(c.label):
            out.append(Finding(ERROR, "label_contact_data", f"{c.id}: die Bezeichnung enthält Kontaktdaten; nur Pseudonym oder Rolle", c.ref))
        for name, cell in (("closeness", c.closeness), ("relation_type", c.relation_type),
                           ("contact_frequency", c.contact_frequency), ("functions", c.functions)):
            if cell.missing is codes.Missing.NOT_COLLECTED:
                missing[name].append(c.id)
        for iso, label in ((c.birth_country_iso3, "Geburtsland"), (c.residence_country_iso3, "Wohnland")):
            if iso and iso not in ISO3 and iso not in codes.MARKERS:
                out.append(Finding(ERROR, "country_code", f"{c.id}: {label} {iso!r} ist kein ISO-3166-alpha-3-Code", c.ref))
        if c.birth_country and not c.birth_country_iso3:
            out.append(Finding(NOTE, "birth_country_uncoded", f"{c.id}: Geburtsland genannt, aber nicht codiert", c.ref))
    labels = {"label": "Person/Rolle", "closeness": "Persönliche Nähe", "relation_type": "Beziehungstyp",
              "contact_frequency": "Kontakthäufigkeit", "functions": "Beziehungsfunktion"}
    for name, label in labels.items():
        _missing_summary(label, missing.get(name, []), out, f"missing_{name}")


def _residence(case: Case, derived: Derived, out: list[Finding]) -> None:
    used = set()
    for c in case.contacts:
        residence = derived.residence[c.id]
        if residence.area is Area.UNRESOLVED:
            out.append(Finding(WARNING, "residence_unresolved", f"{c.id}: Wohnort nicht eindeutig zuordenbar ({residence.basis})", c.ref))
        if residence.basis.startswith("places.csv"):
            used.add(residence.place.casefold() if residence.place else "")
    for key, resolution in case.places.items():
        if resolution.place.casefold() not in used:
            out.append(Finding(NOTE, "place_unused", f"places.csv: {resolution.place!r} wird von keinem Kontakt benutzt", "places.csv"))


def _communication(case: Case, out: list[Finding]) -> None:
    known = set(case.contact_ids)
    for cid, b in case.communication.items():
        if cid not in known:
            out.append(Finding(ERROR, "unknown_contact", f"Tabelle B nennt unbekannten Kontakt {cid!r}", b.ref))
            continue
        _cells(b.ref, cid, {"communication_forms": b.forms, "languages": b.languages, "language_use": b.language_use}, out)
        languages = b.languages.values if b.languages.recorded else ()
        if codes.LANGUAGE_OTHER in languages and not b.other_languages.recorded:
            out.append(Finding(WARNING, "other_language_unnamed", f"{cid}: „andere Sprache“ ohne Bezeichnung", b.ref))
        if b.other_languages.recorded and codes.LANGUAGE_OTHER not in languages:
            out.append(Finding(WARNING, "other_language_without_code", f"{cid}: Sprache benannt, aber Code 5 fehlt", b.ref))
        use = b.language_use
        if len(languages) == 1:
            if use.recorded and use.values != languages:
                out.append(Finding(WARNING, "language_use_single", f"{cid}: bei genau einer Sprache bleibt Sprachgebrauch leer "
                                   f"(eingetragen: {use.raw!r})", b.ref))
        elif len(languages) > 1:
            if use.missing is codes.Missing.NOT_COLLECTED:
                out.append(Finding(WARNING, "language_use_missing", f"{cid}: mehrere Sprachen, Sprachgebrauch nicht erhoben", b.ref))
            elif use.recorded and use.values[0] in codes.LANGUAGES and use.values[0] not in languages:
                out.append(Finding(ERROR, "language_use_not_spoken", f"{cid}: überwiegende Sprache {use.values[0]} ist keine der "
                                   f"angegebenen Sprachen ({', '.join(languages)})", b.ref))
        elif use.recorded:
            out.append(Finding(WARNING, "language_use_without_languages", f"{cid}: Sprachgebrauch ohne Sprachen", b.ref))
    absent = [cid for cid in case.contact_ids if cid not in case.communication]
    if absent:
        out.append(Finding(WARNING, "communication_missing", f"Tabelle B fehlt für {len(absent)} Kontakt(e): {', '.join(absent)}", "communication.csv"))
    for name, code in (("communication_forms", "forms"), ("languages", "languages")):
        empty = [cid for cid, b in case.communication.items() if getattr(b, code).missing is codes.Missing.NOT_COLLECTED]
        if empty:
            out.append(Finding(WARNING, f"missing_{name}", f"{name} nicht erhoben bei: {', '.join(empty)}", "communication.csv"))


def _groups(case: Case, derived: Derived, out: list[Finding]) -> None:
    known = set(case.contact_ids)
    group_ids = [g.id for g in case.groups]
    for gid, n in Counter(group_ids).items():
        if n > 1:
            out.append(Finding(ERROR, "duplicate_group", f"Gruppen-ID {gid} kommt {n}-mal vor", "groups.csv"))
    for g in case.groups:
        if not codes.GROUP_ID.fullmatch(g.id):
            out.append(Finding(ERROR, "group_id", f"Gruppen-ID {g.id!r} ungültig (C01, C02, …)", g.ref))
        _cells(g.ref, g.id, {"connection_status": g.status, "belonging": g.belonging}, out)
        if not g.label:
            out.append(Finding(WARNING, "group_label", f"{g.id}: Gruppenbezeichnung fehlt", g.ref))
        if g.status.missing is not None:
            out.append(Finding(WARNING, "group_status_missing", f"{g.id}: Verbindungsstatus (T/P/N/NS) fehlt", g.ref))
        if g.belonging.missing is not None and g.belonging.missing is not codes.Missing.UNKNOWN:
            out.append(Finding(WARNING, "group_belonging_missing", f"{g.id}: Zugehörigkeit von Ego fehlt ({codes.MISSING_LABELS[g.belonging.missing]})", g.ref))
        members = case.members(g.id)
        if len(members) < 2:
            out.append(Finding(WARNING, "group_small", f"{g.id}: {len(members)} Mitglied(er) – eine Gruppe braucht mindestens zwei", g.ref))
        if g.status.value == "P":
            stated = [p for p in derived.pairs.values() if p.a in members and p.b in members]
            if not stated:
                out.append(Finding(NOTE, "group_partial_unstated", f"{g.id} (P): keine Einzelverbindung erfasst; alle Paare bleiben unbekannt", g.ref))
    seen = Counter()
    for gid, cid, ref in case.memberships:
        if gid not in group_ids:
            out.append(Finding(ERROR, "unknown_group", f"Mitgliedschaft in unbekannter Gruppe {gid!r}", ref))
        if cid not in known:
            out.append(Finding(ERROR, "unknown_contact", f"Mitgliedschaft eines unbekannten Kontakts {cid!r}", ref))
        seen[(gid, cid)] += 1
    for (gid, cid), n in seen.items():
        if n > 1:
            out.append(Finding(WARNING, "duplicate_membership", f"{cid} ist in {gid} {n}-mal eingetragen", "group_memberships.csv"))


def _connections(case: Case, derived: Derived, out: list[Finding]) -> None:
    known = set(case.contact_ids)
    groups = {g.id for g in case.groups}
    for s in case.statements:
        _cells(s.ref, f"{s.a}–{s.b}", {"status": s.status}, out)
        for cid in (s.a, s.b):
            if cid not in known:
                out.append(Finding(ERROR, "unknown_contact", f"Verbindung mit unbekanntem Kontakt {cid!r}", s.ref))
        if s.a == s.b:
            out.append(Finding(ERROR, "self_pair", f"Verbindung eines Kontakts mit sich selbst ({s.a})", s.ref))
        if s.status.missing is not None:
            out.append(Finding(WARNING, "connection_status_missing", f"{s.a}–{s.b}: Status fehlt (1, 0 oder ?)", s.ref))
        if s.source in groups and not {s.a, s.b} <= set(case.members(s.source)):
            out.append(Finding(WARNING, "connection_source_group", f"{s.a}–{s.b}: Quelle {s.source}, aber nicht beide sind Mitglieder", s.ref))
    for pair in derived.pairs.values():
        if pair.state == CONFLICT:
            out.append(Finding(ERROR, "pair_conflict", f"widersprüchliche Aussagen zu {pair.a}–{pair.b}: {', '.join(pair.sources)}", f"{pair.a}–{pair.b}"))
        elif len(pair.statements) > 1 and len({s for s, _ in pair.statements}) == 1 and any(src.startswith("alter_connections") for _, src in pair.statements):
            out.append(Finding(NOTE, "pair_repeated", f"{pair.a}–{pair.b}: mehrfach gleichlautend erfasst ({', '.join(pair.sources)})", f"{pair.a}–{pair.b}"))


def _context(case: Case, out: list[Finding]) -> None:
    counts = Counter(f for f, _, _, _ in case.context)
    for field_name, value, _comment, ref in case.context:
        base = field_name.split(":", 1)[0]
        if base not in CONTEXT_FIELDS:
            out.append(Finding(WARNING, "context_field", f"unbekanntes Feld des Kontextbogens {field_name!r}", ref))
        elif base in CONTEXT_QUALIFIED and ":" not in field_name:
            out.append(Finding(WARNING, "context_field", f"{field_name!r} braucht einen Lebensbereich bzw. eine Sprache ({base}:<…>)", ref))
        if "|" in value:
            out.append(Finding(ERROR, "context_separator", f"{field_name}: '|' ist der v0-Trenner; Mehrfachantworten als eigene Zeilen", ref))
    for field_name, n in counts.items():
        if n > 1 and field_name.split(":", 1)[0] not in CONTEXT_MULTI:
            out.append(Finding(WARNING, "context_repeated", f"{field_name!r} steht {n}-mal, ist aber eine Einzelangabe", "context.csv"))
    if not case.context:
        out.append(Finding(WARNING, "context_missing", "der Kontextbogen ist leer", "context.csv"))


def validate(case: Case) -> Validation:
    findings = list(case.findings)
    _metadata(case, findings)
    structural = any(f.level == ERROR and f.code in ("no_data_folder", "file_missing", "columns_missing", "metadata_json") for f in findings)
    if structural:
        return Validation(findings, None)
    derived = derive(case)
    _contacts(case, findings)
    _residence(case, derived, findings)
    _communication(case, findings)
    _groups(case, derived, findings)
    _connections(case, derived, findings)
    _context(case, findings)
    return Validation(findings, derived)
