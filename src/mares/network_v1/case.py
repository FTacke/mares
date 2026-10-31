"""Reading one network_v1 case folder (format ``mares-network-case/v1``).

``<case>/data/`` holds (``;``-separated UTF-8 CSV, header row; ``data/places.csv`` optional):

==========================  ======================================================================================
``metadata.json``           dataset version, case code and type, provenance, empirical eligibility, survey, limitations
``context.csv``             context sheet, long format ``field;value;comment`` (a multiple answer = several rows)
``contacts.csv``            table A: ``contact_id;label;closeness;relation_type;contact_frequency;functions;
                            birth_country;birth_country_iso3;residence_place;residence_country;residence_country_iso3;comment``
``communication.csv``       table B: ``contact_id;communication_forms;languages;other_languages;language_use;comment``
``groups.csv``              table C, groups: ``group_id;label;connection_status;belonging;comment``
``group_memberships.csv``   table C, members: ``group_id;contact_id``
``alter_connections.csv``   table C, single pairs: ``contact_a;contact_b;status;source;comment`` (status 1, 0, ?)
``places.csv``              explicit placements of German places: ``residence_place;area;basis``
==========================  ======================================================================================

Reading never corrects anything: raw text is kept next to the parsed value (:class:`~.codes.Cell`), and every
problem becomes a :class:`Finding`. Whether the case is usable is decided by :mod:`.validate`.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from pathlib import Path

from . import codes
from .codes import Cell
from .places import AREA_LABELS, Area, PlaceResolution, resolution_key

ERROR, WARNING, NOTE = "error", "warning", "note"

CASE_TYPES = ("test", "pilot", "regular")
PROVENANCES = ("fully_synthetic", "v0_derived_fictionalized", "survey")
FIELD_ORIGINS = ("recorded", "v0_taken", "v0_interpreted", "fictional")

TABLES: dict[str, tuple[str, ...]] = {
    "context.csv": ("field", "value", "comment"),
    "contacts.csv": (
        "contact_id", "label", "closeness", "relation_type", "contact_frequency", "functions", "birth_country",
        "birth_country_iso3", "residence_place", "residence_country", "residence_country_iso3", "comment",
    ),
    "communication.csv": ("contact_id", "communication_forms", "languages", "other_languages", "language_use", "comment"),
    "groups.csv": ("group_id", "label", "connection_status", "belonging", "comment"),
    "group_memberships.csv": ("group_id", "contact_id"),
    "alter_connections.csv": ("contact_a", "contact_b", "status", "source", "comment"),
}
OPTIONAL_TABLES: dict[str, tuple[str, ...]] = {"places.csv": ("residence_place", "area", "basis")}
# Columns and files of the v0 package format: their presence means a v0 package was given to v1.
V0_COLUMNS = frozenset({"table_ring_near_value", "relation_codes", "contact_frequency_code", "media_codes", "language_codes",
                        "language_mode_code", "function_codes", "source_block", "source_local_id", "source_case_label"})
V0_FILES = ("manifest.json", "codebook.csv", "observed_edges.csv")


@dataclass(frozen=True)
class Finding:
    level: str  # error | warning | note
    code: str
    message: str
    ref: str = ""  # file:row or object id

    def to_dict(self) -> dict[str, str]:
        return {"level": self.level, "code": self.code, "message": self.message, "ref": self.ref}


@dataclass(frozen=True)
class Contact:
    id: str
    label: str
    closeness: Cell
    relation_type: Cell
    contact_frequency: Cell
    functions: Cell
    birth_country: str
    birth_country_iso3: str
    residence_place: str
    residence_country: str
    residence_country_iso3: str
    comment: str
    ref: str


@dataclass(frozen=True)
class Communication:
    contact_id: str
    forms: Cell
    languages: Cell
    other_languages: Cell
    language_use: Cell
    comment: str
    ref: str


@dataclass(frozen=True)
class Group:
    id: str
    label: str
    status: Cell
    belonging: Cell
    comment: str
    ref: str


@dataclass(frozen=True)
class Statement:
    """One statement about one pair of contacts (a row of alter_connections.csv)."""

    a: str
    b: str
    status: Cell
    source: str
    comment: str
    ref: str


@dataclass
class Case:
    folder: Path
    metadata: dict
    contacts: list[Contact] = field(default_factory=list)
    communication: dict[str, Communication] = field(default_factory=dict)
    groups: list[Group] = field(default_factory=list)
    memberships: list[tuple[str, str, str]] = field(default_factory=list)  # (group_id, contact_id, ref)
    statements: list[Statement] = field(default_factory=list)
    context: list[tuple[str, str, str, str]] = field(default_factory=list)  # (field, value, comment, ref)
    places: dict[str, PlaceResolution] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)

    @property
    def code(self) -> str:
        return str(self.metadata.get("case_code", ""))

    @property
    def contact_ids(self) -> list[str]:
        return [c.id for c in self.contacts]

    def contact(self, contact_id: str) -> Contact:
        return next(c for c in self.contacts if c.id == contact_id)

    def members(self, group_id: str) -> list[str]:
        ids = {c for g, c, _ in self.memberships if g == group_id}
        return [c for c in self.contact_ids if c in ids]

    def groups_of(self, contact_id: str) -> list[str]:
        return [g.id for g in self.groups if contact_id in {c for gid, c, _ in self.memberships if gid == g.id}]


def is_empirical(metadata: dict) -> bool:
    """Whether a case may enter empirical overviews, case counts and statistics.

    Decided by the machine-readable metadata, never by the folder name: a real survey (``provenance: survey``), a pilot
    or regular case, and ``empirical_analysis_eligible: true``. Test cases are never empirical.
    """
    return (
        metadata.get("dataset_version") == "network_v1"
        and metadata.get("case_type") in ("pilot", "regular")
        and metadata.get("provenance") == "survey"
        and metadata.get("empirical_analysis_eligible") is True
    )


def _read_table(path: Path, columns: tuple[str, ...], findings: list[Finding]) -> list[tuple[str, dict[str, str]]]:
    name = path.name
    text = path.read_text(encoding="utf-8-sig")
    reader = csv.reader(io.StringIO(text), delimiter=";")
    rows = list(reader)
    if not rows:
        findings.append(Finding(ERROR, "table_empty", f"{name} hat keine Kopfzeile", name))
        return []
    header = [h.strip() for h in rows[0]]
    v0 = sorted(set(header) & V0_COLUMNS)
    if v0:
        findings.append(Finding(ERROR, "v0_columns", f"{name} enthält Spalten des v0-Paketformats ({', '.join(v0)}); "
                                "v0-Daten werden nicht als v1 gelesen", name))
    missing = [c for c in columns if c not in header]
    if missing:
        findings.append(Finding(ERROR, "columns_missing", f"{name}: Pflichtspalten fehlen: {', '.join(missing)}", name))
        return []
    extra = [c for c in header if c not in columns]
    if extra:
        findings.append(Finding(WARNING, "columns_unknown", f"{name}: unbekannte Spalten werden ignoriert: {', '.join(extra)}", name))
    result = []
    for number, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue
        if len(row) > len(header):
            findings.append(Finding(ERROR, "row_too_long", f"mehr Zellen als Spalten (ein ';' in einer Zelle muss in "
                                    "Anführungszeichen stehen)", f"{name}:{number}"))
            continue
        values = {h: (row[i].strip() if i < len(row) else "") for i, h in enumerate(header)}
        result.append((f"{name}:{number}", values))
    return result


def read_case(folder: Path) -> Case:
    """Read ``<case>`` (the folder that contains ``data/``)."""
    data = folder / "data"
    findings: list[Finding] = []
    metadata: dict = {}
    meta_path = data / "metadata.json"
    if not data.is_dir():
        findings.append(Finding(ERROR, "no_data_folder", "der Fall hat keinen Ordner data/", str(folder.name)))
        return Case(folder, metadata, findings=findings)
    for v0_file in V0_FILES:
        if (data / v0_file).exists():
            findings.append(Finding(ERROR, "v0_file", f"data/{v0_file} gehört zum v0-Paketformat; v0 und v1 werden nicht vermischt", v0_file))
    if meta_path.is_file():
        try:
            metadata = json.loads(meta_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as error:
            findings.append(Finding(ERROR, "metadata_json", f"metadata.json ist kein gültiges JSON: {error}", "metadata.json"))
        if not isinstance(metadata, dict):
            findings.append(Finding(ERROR, "metadata_json", "metadata.json muss ein Objekt sein", "metadata.json"))
            metadata = {}
    else:
        findings.append(Finding(ERROR, "file_missing", "metadata.json fehlt", "metadata.json"))
    case = Case(folder, metadata, findings=findings)

    tables: dict[str, list[tuple[str, dict[str, str]]]] = {}
    for name, columns in {**TABLES, **OPTIONAL_TABLES}.items():
        path = data / name
        if path.is_file():
            tables[name] = _read_table(path, columns, findings)
        elif name in TABLES:
            findings.append(Finding(ERROR, "file_missing", f"{name} fehlt (eine leere Tabelle besteht aus der Kopfzeile)", name))
            tables[name] = []
        else:
            tables[name] = []

    for ref, row in tables["contacts.csv"]:
        case.contacts.append(Contact(
            id=row["contact_id"],
            label=row["label"],
            closeness=codes.read_closeness(row["closeness"]),
            relation_type=codes.read_single(row["relation_type"], codes.RELATION_TYPE),
            contact_frequency=codes.read_single(row["contact_frequency"], codes.CONTACT_FREQUENCY),
            functions=codes.read_multi(row["functions"], codes.FUNCTIONS, exclusive=codes.FUNCTION_NONE),
            birth_country=row["birth_country"],
            birth_country_iso3=row["birth_country_iso3"].upper(),
            residence_place=row["residence_place"],
            residence_country=row["residence_country"],
            residence_country_iso3=row["residence_country_iso3"].upper(),
            comment=row["comment"],
            ref=ref,
        ))
    for ref, row in tables["communication.csv"]:
        cid = row["contact_id"]
        if cid in case.communication:
            findings.append(Finding(ERROR, "duplicate_communication", f"Tabelle B nennt {cid} mehrfach", ref))
            continue
        case.communication[cid] = Communication(
            contact_id=cid,
            forms=codes.read_multi(row["communication_forms"], codes.COMMUNICATION_FORMS),
            languages=codes.read_multi(row["languages"], codes.LANGUAGES),
            other_languages=codes.read_multi(row["other_languages"], None),
            language_use=codes.read_language_use(row["language_use"]),
            comment=row["comment"],
            ref=ref,
        )
    for ref, row in tables["groups.csv"]:
        case.groups.append(Group(
            id=row["group_id"],
            label=row["label"],
            status=codes.read_group_status(row["connection_status"]),
            belonging=codes.read_single(row["belonging"], codes.BELONGING),
            comment=row["comment"],
            ref=ref,
        ))
    for ref, row in tables["group_memberships.csv"]:
        case.memberships.append((row["group_id"], row["contact_id"], ref))
    for ref, row in tables["alter_connections.csv"]:
        case.statements.append(Statement(
            a=row["contact_a"], b=row["contact_b"], status=codes.read_single(row["status"], codes.CONNECTION),
            source=row["source"], comment=row["comment"], ref=ref,
        ))
    for ref, row in tables["context.csv"]:
        case.context.append((row["field"], row["value"], row["comment"], ref))
    areas = {a.value: a for a in (Area.MARBURG, Area.MITTELHESSEN, Area.GERMANY_OTHER)}
    for ref, row in tables["places.csv"]:
        area = areas.get(row["area"].strip())
        if area is None:
            findings.append(Finding(ERROR, "place_area", f"places.csv: Bereich {row['area']!r} ungültig (zulässig: "
                                    f"{', '.join(areas)} – nur deutsche Orte werden hier eingeordnet)", ref))
            continue
        if not row["basis"].strip():
            findings.append(Finding(ERROR, "place_basis", "places.csv: jede Einordnung braucht eine Begründung (basis)", ref))
            continue
        key = resolution_key(row["residence_place"])
        if key in case.places:
            findings.append(Finding(ERROR, "place_duplicate", f"places.csv nennt {row['residence_place']!r} mehrfach", ref))
            continue
        case.places[key] = PlaceResolution(row["residence_place"].strip(), area, row["basis"].strip())
    return case


def area_label(area: Area) -> str:
    return AREA_LABELS[area]
