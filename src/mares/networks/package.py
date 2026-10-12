"""Reader for the MARES network package (``mares-network-package/v0-draft``).

A package is a directory of CSV files (UTF-8 with or without BOM, ``;`` as column separator, ``|``
between several codes in one cell, an empty cell = not collected) plus ``manifest.json`` and a
codebook. This module only *reads*: it parses cells, records syntax problems as findings and builds
the model. Whether the content is coherent is the validator's business
(:mod:`mares.networks.validate`). Nothing is corrected, completed or guessed.

A package is read from a directory that the caller obtained from the storage resolver; this module
never builds a location itself.
"""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass
from pathlib import Path

from mares.core.hashing import sha256_file

from .codes import Codebook, CodebookError, CodeSyntaxError, ParsedCodes, parse_codes
from .model import (
    CaseIdentity,
    Clarification,
    Contact,
    Finding,
    Group,
    Membership,
    NetworkDataset,
    ProvidedEdge,
    ReviewItem,
    Severity,
    SourceFile,
    SurveySession,
)

FORMAT = "mares-network-package/v0-draft"

REQUIRED_FILES = ("contacts.csv", "groups.csv", "group_memberships.csv", "codebook.csv", "manifest.json")
OPTIONAL_FILES = ("observed_edges.csv", "review_items.csv", "source_clarifications.csv", "SHA256SUMS.txt")
DOCUMENTATION_FILES = ("README_DATEN.md",)

# Required / optional of every file's columns.
IDENTITY_COLUMNS = ("source_case_label", "contact_id", "source_block", "source_local_id")
GROUP_COLUMNS = ("group_id", "label", "map_label", "assessment", "comment")
MEMBERSHIP_COLUMNS = ("group_id", "contact_id", "status", "derivable_edge", "source")
EDGE_COLUMNS = ("source_id", "target_id", "relation", "evidence", "group_ids", "status")
REVIEW_COLUMNS = ("review_id", "priority", "reference", "field", "description", "recommended_action")
CLARIFICATION_COLUMNS = (
    "clarification_id",
    "source_date",
    "group_id",
    "member_contact_ids",
    "relationship_rule",
    "resolution",
    "source_type",
)


class PackageError(RuntimeError):
    """The package cannot be read at all (a file or a required column is missing, or unreadable)."""


@dataclass(frozen=True)
class ColumnSpec:
    """How one column of ``contacts.csv`` enters the model.

    ``kind``: ``code`` (validated against the codebook field ``field``), ``iso3`` (a country code),
    ``text`` (kept as written), ``flags`` (review flags). ``level``: ``expected`` attributes are
    reported as a warning when empty, ``optional`` ones only counted.
    """

    column: str
    attribute: str
    kind: str
    field: str | None = None
    multi: bool = False
    level: str = "optional"


CONTACT_COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec("relation_codes", "relation", "code", "relation", True, "expected"),
    ColumnSpec("birth_country_iso3", "birth_country", "iso3"),
    ColumnSpec("birth_country_source", "birth_country_source", "text"),
    ColumnSpec("residence_city", "residence_city", "text", level="expected"),
    ColumnSpec("residence_country_iso3", "residence_country", "iso3", level="expected"),
    ColumnSpec("contact_frequency_code", "contact_frequency", "code", "contact_frequency", False, "expected"),
    # The table value is the only authoritative closeness; the map position is never consulted.
    ColumnSpec("table_ring_near_value", "closeness", "code", "closeness_1_5", False, "expected"),
    ColumnSpec("media_codes", "media", "code", "media", True),
    ColumnSpec("language_codes", "language", "code", "language", True, "expected"),
    ColumnSpec("language_mode_code", "language_mode", "code", "language_mode", False),
    ColumnSpec("function_codes", "function", "code", "function", True),
    ColumnSpec("name_generator_codes", "name_generator", "code", "name_generator", True),
    ColumnSpec("review_flags", "review_flags", "flags"),
)

_FLAG_SEPARATORS = re.compile(r"[;|]")


def _decode_rows(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    """Read a delimited table strictly: wrong separator, ragged rows or bad encoding are errors."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        raise PackageError(f"{path.name}: cannot be read as UTF-8: {error}") from error
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=";", restkey="__extra__", restval=None)
    header = reader.fieldnames or []
    if len(header) < 2 and any("," in name or "\t" in name for name in header):
        raise PackageError(f"{path.name}: the column separator must be ';'")
    missing = [column for column in required if column not in header]
    if missing:
        raise PackageError(f"{path.name}: required column(s) missing: {', '.join(missing)}")
    rows: list[dict[str, str]] = []
    for number, row in enumerate(reader, 2):
        if "__extra__" in row or any(value is None for value in row.values()):
            raise PackageError(f"{path.name}:{number}: the row does not match the header")
        rows.append({key: value.strip() for key, value in row.items()})
    return rows


def _multi(cell: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in cell.split("|") if part.strip())


def _read_contacts(
    path: Path, findings: list[Finding]
) -> tuple[list[Contact], tuple[str, ...], set[str]]:
    rows = _decode_rows(path, IDENTITY_COLUMNS)
    with open(path, encoding="utf-8-sig", newline="") as handle:
        header = tuple(next(csv.reader(handle, delimiter=";")))
    case_labels = {row["source_case_label"] for row in rows}
    contacts: list[Contact] = []
    for row in rows:
        subject = row["contact_id"] or "(without id)"
        codes: dict[str, ParsedCodes] = {}
        text: dict[str, str] = {}
        flags: tuple[str, ...] = ()
        for spec in CONTACT_COLUMNS:
            if spec.column not in row:
                continue  # the column was not delivered: the attribute was not collected at all
            cell = row[spec.column]
            if spec.kind == "text":
                if cell:
                    text[spec.attribute] = cell
            elif spec.kind == "flags":
                flags = tuple(part.strip() for part in _FLAG_SEPARATORS.split(cell) if part.strip())
            elif spec.kind == "iso3":
                if cell:
                    text[spec.attribute] = cell
            else:
                try:
                    parsed = parse_codes(cell)
                except CodeSyntaxError as error:
                    findings.append(
                        Finding(Severity.ERROR, "code_syntax", subject, f"{spec.column}: {error}")
                    )
                    parsed = ParsedCodes(())
                if parsed.expanded_ranges:
                    findings.append(
                        Finding(
                            Severity.INFO,
                            "range_expanded",
                            subject,
                            f"{spec.column}: Bereich {', '.join(parsed.expanded_ranges)} zu Einzelcodes aufgelöst "
                            f"({'|'.join(parsed.codes)})",
                        )
                    )
                codes[spec.attribute] = parsed
        contacts.append(
            Contact(
                contact_id=row["contact_id"],
                source_block=row["source_block"],
                source_local_id=row["source_local_id"],
                codes=codes,
                text=text,
                review_flags=flags,
            )
        )
    return contacts, header, case_labels


def _read_optional(path: Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    return _decode_rows(path, columns) if path.is_file() else []


def read_package(directory: Path) -> NetworkDataset:
    """Read a package directory into a :class:`NetworkDataset`.

    Raises :class:`PackageError` if the package is structurally unreadable. Everything else (an
    invalid code, an unknown reference ...) is *content*: it is kept as read and left to the
    validator, so one bad cell never hides the rest of the data.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise PackageError("the package location is not a directory")
    absent = [name for name in REQUIRED_FILES if not (directory / name).is_file()]
    if absent:
        raise PackageError(f"required file(s) missing: {', '.join(absent)}")

    findings: list[Finding] = []
    known = set(REQUIRED_FILES) | set(OPTIONAL_FILES) | set(DOCUMENTATION_FILES)
    files = []
    for path in sorted(p for p in directory.iterdir() if p.is_file()):
        files.append(SourceFile(path.name, sha256_file(path), path.stat().st_size))
        if path.name not in known:
            findings.append(Finding(Severity.INFO, "unknown_file", path.name, "Datei gehört nicht zum Paketformat; ignoriert."))

    try:
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PackageError(f"manifest.json: cannot be read: {error}") from error
    if not isinstance(manifest, dict):
        raise PackageError("manifest.json: expected a JSON object")

    try:
        codebook = Codebook.read(directory / "codebook.csv")
    except (CodebookError, OSError, UnicodeDecodeError) as error:
        raise PackageError(str(error)) from error

    contacts, columns, case_labels = _read_contacts(directory / "contacts.csv", findings)

    groups = tuple(Group(*(row[c] for c in GROUP_COLUMNS)) for row in _decode_rows(directory / "groups.csv", GROUP_COLUMNS))
    memberships = tuple(
        Membership(*(row[c] for c in MEMBERSHIP_COLUMNS))
        for row in _decode_rows(directory / "group_memberships.csv", MEMBERSHIP_COLUMNS)
    )
    review_items = tuple(
        ReviewItem(*(row[c] for c in REVIEW_COLUMNS)) for row in _read_optional(directory / "review_items.csv", REVIEW_COLUMNS)
    )
    clarifications = tuple(
        Clarification(
            row["clarification_id"],
            row["source_date"],
            row["group_id"],
            _multi(row["member_contact_ids"]),
            row["relationship_rule"],
            row["resolution"],
            row["source_type"],
        )
        for row in _read_optional(directory / "source_clarifications.csv", CLARIFICATION_COLUMNS)
    )
    provided_edges = tuple(
        ProvidedEdge(row["source_id"], row["target_id"], row["relation"], row["evidence"], _multi(row["group_ids"]), row["status"])
        for row in _read_optional(directory / "observed_edges.csv", EDGE_COLUMNS)
    )

    listed: dict[str, str] = {}
    sums = directory / "SHA256SUMS.txt"
    if sums.is_file():
        for number, line in enumerate(sums.read_text(encoding="utf-8-sig").splitlines(), 1):
            if not line.strip():
                continue
            digest, _, name = line.strip().partition(" ")
            if not re.fullmatch(r"[0-9a-fA-F]{64}", digest) or not name.strip():
                raise PackageError(f"SHA256SUMS.txt:{number}: not a '<sha256>  <file>' line")
            listed[name.strip().lstrip("*")] = digest.lower()

    label = str(manifest.get("source_case_label") or "")
    if not label and len(case_labels) == 1:
        label = next(iter(case_labels))
    if not label:
        raise PackageError("no source case label: neither manifest.json nor contacts.csv names one")
    stray = sorted(case_labels - {label})
    if stray:
        findings.append(
            Finding(Severity.ERROR, "case_label_mismatch", "contacts.csv", "Die Kontakttabelle nennt eine andere Quellkennung als das Manifest.")
        )
    canonical = manifest.get("canonical_case_id")
    try:
        case = CaseIdentity(label, canonical if isinstance(canonical, str) and canonical.startswith("MARES-") else None)
    except ValueError as error:
        raise PackageError(f"manifest.json: {error}") from error
    session = SurveySession(
        source_label=label,
        session_date=manifest.get("source_date") if isinstance(manifest.get("source_date"), str) else None,
        interview_type=manifest.get("source_interview_type") if isinstance(manifest.get("source_interview_type"), str) else None,
        package_version=manifest.get("package_version") if isinstance(manifest.get("package_version"), str) else None,
        origin_note=manifest.get("source_interview_type") if isinstance(manifest.get("source_interview_type"), str) else None,
    )
    return NetworkDataset(
        case=case,
        session=session,
        contacts=tuple(contacts),
        groups=groups,
        memberships=memberships,
        review_items=review_items,
        clarifications=clarifications,
        provided_edges=provided_edges,
        codebook=codebook,
        files=tuple(files),
        listed_checksums=listed,
        manifest=manifest,
        import_findings=tuple(findings),
        contact_columns=columns,
    )
