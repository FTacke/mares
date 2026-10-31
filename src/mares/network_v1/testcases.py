"""The two network_v1 test cases.

* ``002_test_synthetic`` -- fully synthetic; its source is ``examples/synthetic/network_v1/002_test_synthetic/data`` in the
  repository. Installing copies the files into a case tree.
* ``001_test_v0_fictionalized`` -- built from the v0 pilot package: the network *structure* (contacts, groups,
  memberships) and the v0 codes are taken over and re-coded by documented interpretation; everything that could
  identify a person (labels, places, countries, group names) is replaced by invented values; what v1 asks but v0 did not
  collect is invented. The v0 package is read, never changed. Nothing of it enters the repository.

Both cases say so in ``metadata.json`` (``case_type: test``, ``empirical_analysis_eligible: false``) and in every figure.
Interpretation tables below are the documented reading of the v0 codebook (``docs/architecture/network-versions.md``).
"""

from __future__ import annotations

import csv
import io
import json
import shutil
from itertools import cycle
from pathlib import Path

from mares.core.paths import repo_root
from mares.network_v0.geo import GeoCategory, classify_residence
from mares.network_v0.package import read_package

from . import DATASET_VERSION, FORMAT
from .case import TABLES, read_case
from .places import Area, classify

SYNTHETIC_CODE = "002_test_synthetic"
FICTIONALIZED_CODE = "001_test_v0_fictionalized"


class TestCaseError(RuntimeError):
    """A test case cannot be installed without risk (it would replace a non-test case, the source differs ...)."""

    __test__ = False  # not a pytest test class


def synthetic_source() -> Path:
    return repo_root() / "examples" / "synthetic" / "network_v1" / SYNTHETIC_CODE


def _guard(target: Path) -> None:
    """Only a test case may be replaced; anything else in the target folder stops the installation."""
    meta = target / "data" / "metadata.json"
    if meta.exists():
        try:
            existing = json.loads(meta.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as error:
            raise TestCaseError(f"{target.name}: existing metadata.json is unreadable; nothing replaced") from error
        if existing.get("case_type") != "test":
            raise TestCaseError(f"{target.name}: the existing case is not a test case; nothing replaced")
    elif (target / "data").exists() and any((target / "data").iterdir()):
        raise TestCaseError(f"{target.name}: data/ exists without metadata.json; nothing replaced")


def install_synthetic(target: Path) -> list[str]:
    """Copy the synthetic case into ``target`` (= ``.../pilots/002_test_synthetic``); returns the copied file names."""
    _guard(target)
    source = synthetic_source() / "data"
    (target / "data").mkdir(parents=True, exist_ok=True)
    (target / "graphics").mkdir(exist_ok=True)
    names = sorted(p.name for p in source.iterdir() if p.is_file())
    for name in names:
        shutil.copyfile(source / name, target / "data" / name)
    return names


# ------------------------------------------------------------------------------------------------ 001 -----
# The meanings the v0 codebook must have for the interpretation below to hold; checked before anything is written.
V0_MEANINGS = {
    "closeness_1_5": {"1": "überhaupt nicht nah", "2": "eher wenig nah", "3": "mittel", "4": "nah", "5": "sehr nah"},
    "contact_frequency": {"1": "wenige Male im Jahr oder seltener", "2": "ungefähr einmal im Monat", "3": "mehrmals im Monat",
                          "4": "wöchentlich", "5": "täglich oder fast täglich"},
    "relation": {"1": "Familie oder Verwandtschaft", "2": "Partner:in", "3": "Freundschaft", "4": "bekannte Person",
                 "5": "Kontakt aus der Arbeit", "6": "Kontakt aus Universität oder Studium", "7": "Nachbarschaft, Verein oder Community",
                 "8": "professioneller oder institutioneller Kontakt", "9": "andere Beziehung"},
    "media": {"1": "persönlich", "2": "Textnachrichten oder Chat", "3": "Sprachnachrichten", "4": "Telefon", "5": "Videoanruf",
              "6": "soziale Medien", "7": "E-Mail", "8": "anderes Medium"},
    "language": {"1": "Spanisch", "2": "Deutsch", "3": "Englisch", "4": "Portugiesisch", "5": "andere Sprache"},
    "language_mode": {"1": "überwiegend Spanisch", "2": "überwiegend Deutsch", "3": "überwiegend Englisch",
                      "4": "regelmäßige Mischung mehrerer Sprachen", "5": "abhängig von Situation oder Medium", "6": "anderer Modus"},
    "function": {"1": "emotionale Unterstützung", "2": "Familie oder Fürsorge", "3": "Alltag oder Freizeit", "4": "praktische Hilfe",
                 "5": "sprachliche Hilfe oder Übersetzung", "6": "Arbeit oder Studium", "7": "institutionelle Orientierung",
                 "8": "Zugehörigkeit oder Community", "9": "transnationaler Kontakt", "10": "Information", "11": "andere Funktion"},
}
# v0 closeness 1-5 (5 = very close) -> v1 1-4 (1 = very close). An interpretation: the scales differ in length and direction.
CLOSENESS = {"5": "1", "4": "2", "3": "3", "2": "3,5", "1": "4"}
FREQUENCY = {"5": "1", "4": "2", "3": "3", "2": "4", "1": "5"}  # reversed direction, same five steps
# v0 relation (several codes allowed) -> one v1 main relation, by priority. Work, study and neighbourhood/club contacts
# become 'Bekannte:r'; v1 has no own category for them.
RELATION_PRIORITY = (("2", "2"), ("1", "1"), ("3", "3"), ("8", "5"), ("4", "4"), ("5", "4"), ("6", "4"), ("7", "4"), ("9", "6"))
# v0 function -> v1 function: support/care/information -> Rückhalt/Rat; everyday/leisure -> Aktivitäten; practical help and
# institutional orientation -> praktische Hilfe; language help -> sprachliche Hilfe; everything else -> sonstige Funktion.
FUNCTIONS = {"1": "1", "2": "1", "10": "1", "3": "2", "4": "3", "7": "3", "5": "4", "6": "5", "8": "5", "9": "5", "11": "5"}
# v0 media -> v1 communication forms; social media, e-mail and other media -> Sonstiges (platforms are no category of their own).
MEDIA = {"1": "1", "2": "5", "3": "4", "4": "3", "5": "2", "6": "6", "7": "6", "8": "6"}
MODE = {"1": "1", "2": "2", "3": "3", "4": "M", "5": "S"}  # mode 6 ('anderer Modus') has no v1 counterpart: left empty

ROLE = {"1": "Familienangehörige:r", "2": "Partner:in", "3": "Freund:in", "4": "Bekannte:r", "5": "institutioneller Kontakt", "6": "sonstiger Kontakt"}
COUNTRY_NAMES = {"DEU": "Deutschland", "COL": "Kolumbien", "PER": "Peru", "ECU": "Ecuador", "MEX": "Mexiko", "ESP": "Spanien",
                 "AUT": "Österreich", "FRA": "Frankreich", "PRT": "Portugal", "CHL": "Chile"}
PLACES = {
    Area.MITTELHESSEN: ["Gießen", "Wetzlar", "Kirchhain", "Cölbe", "Lahntal"],
    Area.GERMANY_OTHER: ["Frankfurt am Main", "Kassel", "Köln", "Berlin", "Leipzig"],
    Area.EUROPE_OTHER: [("Madrid", "ESP"), ("Wien", "AUT"), ("Lyon", "FRA"), ("Lissabon", "PRT")],
    Area.OUTSIDE_EUROPE: [("Bogotá", "COL"), ("Lima", "PER"), ("Quito", "ECU"), ("Ciudad de México", "MEX"), ("Santiago", "CHL")],
}
BIRTH = ["COL", "PER", "ECU", "MEX", "CHL"]
BELONGING = ["1", "2", "3", "2", "4", "3", "5"]
FIELD_ORIGINS = {
    "contacts.contact_id": "v0_taken",
    "contacts.label": "fictional",
    "contacts.closeness": "v0_interpreted",
    "contacts.relation_type": "v0_interpreted",
    "contacts.contact_frequency": "v0_interpreted",
    "contacts.functions": "v0_interpreted",
    "contacts.birth_country": "fictional",
    "contacts.residence_place": "fictional",
    "contacts.residence_country": "fictional",
    "communication.communication_forms": "v0_interpreted",
    "communication.languages": "v0_taken",
    "communication.other_languages": "fictional",
    "communication.language_use": "v0_interpreted",
    "groups.group_id": "v0_taken",
    "groups.label": "fictional",
    "groups.connection_status": "v0_interpreted",
    "groups.belonging": "fictional",
    "group_memberships": "v0_taken",
    "alter_connections": "v0_taken",
    "context": "fictional",
}


def check_codebook(dataset) -> list[str]:
    """Fields whose v0 meanings differ from the documented ones (an empty list = the interpretation holds)."""
    bad = []
    for field_name, expected in V0_MEANINGS.items():
        if not dataset.codebook.has_field(field_name):
            bad.append(field_name)
            continue
        for code, meaning in expected.items():
            if not dataset.codebook.is_valid(field_name, code) or dataset.codebook.meaning(field_name, code) != meaning:
                bad.append(field_name)
                break
    return bad


def _write(path: Path, header: tuple[str, ...], rows: list[list[str]]) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    path.write_text(buffer.getvalue(), encoding="utf-8")


def build_fictionalized(v0_package: Path, target: Path, *, source_ref: str) -> dict[str, object]:
    """Build ``001_test_v0_fictionalized`` from a v0 package. Returns counts only (no content)."""
    dataset = read_package(v0_package)
    bad = check_codebook(dataset)
    if bad:
        raise TestCaseError(f"the v0 codebook differs from the documented meanings in: {', '.join(bad)}; nothing written")
    _guard(target)
    filled: dict[str, int] = {}

    def fill(name: str) -> None:
        filled[name] = filled.get(name, 0) + 1

    pools = {area: cycle(values) for area, values in PLACES.items()}
    births = cycle(BIRTH)
    contacts, communication = [], []
    for c in dataset.contacts:
        relations = c.code_list("relation")
        relation = next((v1 for v0, v1 in RELATION_PRIORITY if v0 in relations), None)
        if relation is None:
            relation = "4"
            fill("relation_type")
        closeness = CLOSENESS.get(c.single("closeness") or "")
        if closeness is None:
            closeness = "3"
            fill("closeness")
        frequency = FREQUENCY.get(c.single("contact_frequency") or "")
        if frequency is None:
            frequency = "3"
            fill("contact_frequency")
        functions = sorted({FUNCTIONS[f] for f in c.code_list("function") if f in FUNCTIONS}, key=int)
        if not functions:
            functions = ["1"] if relation in ("1", "2") else ["2"] if relation == "3" else ["0"]
            fill("functions")
        # residence: the v0 category (and, within Germany, the Mittelhessen list) decides the area; the place is invented
        city, country = c.single("residence_city"), c.single("residence_country")
        v0_area = classify_residence(city, country).category
        place, iso = "", ""
        if v0_area is GeoCategory.LOCAL:
            place, iso = "Marburg", "DEU"
        elif v0_area is GeoCategory.LOCAL_REGION:
            place, iso = "Nähe Marburg", "DEU"  # a regional statement stays one: unresolved in v1, as it should be
        elif v0_area is GeoCategory.GERMANY_OTHER:
            v1_area = classify(city, country).area
            area = v1_area if v1_area in (Area.MARBURG, Area.MITTELHESSEN) else Area.GERMANY_OTHER
            place, iso = ("Marburg" if area is Area.MARBURG else next(pools[area])), "DEU"
        elif v0_area in (GeoCategory.EUROPE_OTHER, GeoCategory.OUTSIDE_EUROPE):
            area = Area.EUROPE_OTHER if v0_area is GeoCategory.EUROPE_OTHER else Area.OUTSIDE_EUROPE
            place, iso = next(pools[area])
        birth_iso = c.single("birth_country")
        birth = "DEU" if birth_iso == "DEU" else next(births)
        contacts.append([
            c.contact_id, ROLE[relation], closeness, relation, frequency, ", ".join(functions),
            COUNTRY_NAMES[birth], birth, place, COUNTRY_NAMES.get(iso, ""), iso, "fiktionalisiert",
        ])
        languages = list(c.code_list("language"))
        if not languages:
            languages = ["1"]
            fill("languages")
        other = "Französisch" if "5" in languages else ""
        media = sorted({MEDIA[m] for m in c.code_list("media") if m in MEDIA}, key=int)
        if not media:
            media = ["5"]
            fill("communication_forms")
        use = ""
        if len(languages) > 1:
            mode = c.single("language_mode")
            if mode is None:
                use = "M"
                fill("language_use")
            else:
                use = MODE.get(mode, "")
                if use in ("1", "2", "3") and use not in languages:
                    use = "M"
        communication.append([c.contact_id, ", ".join(media), ", ".join(languages), other, use, ""])

    groups, memberships = [], []
    belonging = cycle(BELONGING)
    for i, g in enumerate(dataset.groups, start=1):
        gid = f"C{i:02d}"
        status = "T" if g.confirmed else "NS"
        groups.append([gid, f"Kreis {i} (fiktive Bezeichnung)", status, next(belonging), f"v0-Gruppe {g.group_id}"])
        for m in dataset.memberships:
            if m.group_id == g.group_id and m.status == "confirmed":
                memberships.append([gid, m.contact_id])

    data = target / "data"
    data.mkdir(parents=True, exist_ok=True)
    (target / "graphics").mkdir(exist_ok=True)
    _write(data / "contacts.csv", TABLES["contacts.csv"], contacts)
    _write(data / "communication.csv", TABLES["communication.csv"], communication)
    _write(data / "groups.csv", TABLES["groups.csv"], groups)
    _write(data / "group_memberships.csv", TABLES["group_memberships.csv"], memberships)
    _write(data / "alter_connections.csv", TABLES["alter_connections.csv"], [])
    _write(data / "context.csv", TABLES["context.csv"], [
        ["origin_country", "COL", "fiktiv"], ["age", "35", "fiktiv"], ["stay_duration", "6 Jahre", "fiktiv"],
        ["migration_context", "Studium", "fiktiv"], ["residence_place", "Marburg", "fiktiv"], ["marburg_relation", "Wohnort", "fiktiv"],
        ["occupation", "Angestellte", "fiktiv"], ["housing", "Wohnung mit Partner", "fiktiv"], ["daily_languages", "Spanisch", "fiktiv"],
        ["daily_languages", "Deutsch", "fiktiv"], ["language_use:familie", "Spanisch", "fiktiv"], ["language_use:arbeit", "Deutsch", "fiktiv"],
        ["language_confidence:deutsch", "sicher", "fiktiv"],
    ])
    metadata = {
        "format": FORMAT,
        "dataset_version": DATASET_VERSION,
        "case_code": FICTIONALIZED_CODE,
        "case_type": "test",
        "provenance": "v0_derived_fictionalized",
        "empirical_analysis_eligible": False,
        "description": (
            "Konstruierter v1-Testfall auf der Grundlage des v0-Pilotfalls 001 (Quellkennung 001-2). Übernommen: Kontakt-IDs, "
            "Gruppen und bestätigte Mitgliedschaften (Netzwerkstruktur). Umcodiert nach dokumentierter Lesart: Nähe (v0 1–5, 5 = sehr nah "
            "→ v1 1–4), Kontakthäufigkeit, Beziehungstyp, Funktionen, Kommunikationsformen, Sprachgebrauch. Erfunden: Bezeichnungen, Orte, "
            "Länder, Gruppennamen, Zugehörigkeitswerte, Kontextbogen und alle in v0 fehlenden Angaben. Kein Wert ist eine v1-Erhebung."
        ),
        "survey": {"design": "network_v0 (umcodiert)", "instrument_version": "not applicable (test)", "survey_date": "0000-01-01",
                   "data_origin": "derived from the v0 pilot package and fictionalized"},
        "data_quality": "TEST",
        "limitations": [
            "Die Nähe-Skalen von v0 und v1 unterscheiden sich in Länge und Richtung; die Umrechnung ist eine Testannahme.",
            "Gruppen der v0-Erhebung gelten als T (Cliquenregel von v0); Paare außerhalb der Gruppen bleiben unbekannt.",
            "Orte und Länder sind erfunden; die Wohnortbereiche folgen der v0-Einordnung, nicht einem Ort.",
            "Nicht für empirische Aussagen verwendbar.",
        ],
        "field_origins": FIELD_ORIGINS,
        "construction": {
            "source": {"dataset_version": "network_v0", "source_label": dataset.case.source_label, "package_ref": source_ref,
                       "package_version": dataset.session.package_version},
            "filled_because_missing_in_v0": filled,
            "v0_groups_needs_review_as_NS": sum(1 for g in dataset.groups if not g.confirmed),
            "v0_candidate_memberships_dropped": sum(1 for m in dataset.memberships if m.status != "confirmed"),
        },
    }
    (data / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    case = read_case(target)
    return {"contacts": len(case.contacts), "groups": len(case.groups), "memberships": len(case.memberships), "filled": filled}
