"""Builder for synthetic network packages (``mares-network-package/v0-draft``).

Everything produced here is invented: the source label carries the reserved year ``0000``, the
manifest says ``"synthetic": true``, and the values are a few made-up places and codes. No test reads a
real package or a configured storage root.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from itertools import combinations
from pathlib import Path

LABEL = "0000-1"
BLOCK_SIZE = 15

CODEBOOK = {
    "relation": {"1": "Familie", "2": "Partner:in", "3": "Freundschaft", "4": "bekannt", "5": "Arbeit", "6": "Studium"},
    "contact_frequency": {"1": "selten", "2": "monatlich", "3": "mehrmals im Monat", "4": "wöchentlich", "5": "täglich"},
    "closeness_1_5": {"1": "überhaupt nicht nah", "2": "eher wenig nah", "3": "mittel", "4": "nah", "5": "sehr nah"},
    "media": {"1": "persönlich", "2": "Chat", "3": "Sprachnachricht", "4": "Telefon", "5": "Video"},
    "language": {"1": "Spanisch", "2": "Deutsch", "3": "Englisch", "4": "Portugiesisch", "5": "andere Sprache"},
    "language_mode": {"1": "überwiegend Spanisch", "2": "überwiegend Deutsch", "3": "überwiegend Englisch", "4": "Mischung", "5": "abhängig", "6": "anderer Modus"},
    "function": {"1": "emotional", "2": "Familie", "3": "Alltag", "4": "praktisch"},
    "name_generator": {"G1": "Alltag", "G2": "wichtig"},
}

CONTACT_COLUMNS = (
    "source_case_label", "contact_id", "source_block", "source_local_id", "relation_codes", "birth_country_iso3",
    "birth_country_source", "residence_city", "residence_country_iso3", "contact_frequency_code", "table_ring_near_value",
    "media_codes", "language_codes", "language_mode_code", "function_codes", "name_generator_codes", "review_flags",
)
GROUP_COLUMNS = ("group_id", "label", "map_label", "assessment", "comment")
MEMBERSHIP_COLUMNS = ("group_id", "contact_id", "status", "derivable_edge", "source")
EDGE_COLUMNS = ("source_id", "target_id", "relation", "evidence", "group_ids", "status")
REVIEW_COLUMNS = ("review_id", "priority", "reference", "field", "description", "recommended_action")

PLACES = (("Marburg", "DEU"), ("Berlin", "DEU"), ("Lima", "PER"), ("Bogotá", "COL"), ("Marburg", "DEU"))


def contact_ids(n: int) -> list[str]:
    return [f"A{i:02d}" for i in range(1, n + 1)]


def contact_rows(n: int, block_size: int = BLOCK_SIZE) -> list[dict[str, str]]:
    """``n`` synthetic contacts on sheets of ``block_size`` slots: the local numbering restarts on every
    sheet, the canonical ids run on."""
    rows = []
    for index in range(n):
        number = index + 1
        place, country = PLACES[index % len(PLACES)]
        rows.append(
            {
                "source_case_label": LABEL,
                "contact_id": f"A{number:02d}",
                "source_block": str(index // block_size + 1),
                "source_local_id": f"A{index % block_size + 1:02d}",
                "relation_codes": ["1", "3", "3|6", "4"][index % 4],
                "birth_country_iso3": ["COL", "DEU", "PER", ""][index % 4],
                "birth_country_source": ["Kolumbien", "Deutschland", "Peru", ""][index % 4],
                "residence_city": place,
                "residence_country_iso3": country,
                "contact_frequency_code": str(index % 5 + 1),
                "table_ring_near_value": str(index % 5 + 1),
                "media_codes": ["1|2", "2", "1|2|3", "4|5"][index % 4],
                "language_codes": ["1", "1|2", "2", "1|4"][index % 4],
                "language_mode_code": ["1", "4", "2", "1"][index % 4],
                "function_codes": ["1|2", "3", "", "4"][index % 4],
                "name_generator_codes": ["G1", "", "G2|G1", ""][index % 4],
                "review_flags": "",
            }
        )
    return rows


def _csv(columns: tuple[str, ...], rows: list[dict[str, str]], *, bom: bool = True, newline: str = "\n") -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns, delimiter=";", lineterminator=newline)
    writer.writeheader()
    writer.writerows([{c: r.get(c, "") for c in columns} for r in rows])
    return (("﻿" if bom else "") + buffer.getvalue()).encode("utf-8")


def group(group_id: str, *, assessment: str = "confirmed") -> dict[str, str]:
    return {"group_id": group_id, "label": f"Gruppe {group_id}", "map_label": "", "assessment": assessment, "comment": "synthetic"}


def members(group_id: str, contact_ids_: list[str], *, status: str = "confirmed") -> list[dict[str, str]]:
    return [
        {"group_id": group_id, "contact_id": c, "status": status, "derivable_edge": "yes" if status == "confirmed" else "no", "source": "synthetic"}
        for c in contact_ids_
    ]


def derived_edges(groups: list[dict[str, str]], memberships: list[dict[str, str]]) -> list[dict[str, str]]:
    """The edge table a correct package would carry: one row per pair, with all its groups."""
    confirmed = {g["group_id"] for g in groups if g["assessment"] == "confirmed"}
    origin: dict[tuple[str, str], list[str]] = {}
    by_group: dict[str, list[str]] = {}
    for m in memberships:
        if m["status"] == "confirmed" and m["group_id"] in confirmed:
            by_group.setdefault(m["group_id"], []).append(m["contact_id"])
    for group_id in sorted(by_group):
        for a, b in combinations(sorted(by_group[group_id], key=lambda c: int(c[1:])), 2):
            origin.setdefault((a, b), []).append(group_id)
    return [
        {"source_id": a, "target_id": b, "relation": "know_each_other", "evidence": "synthetic", "group_ids": "|".join(g), "status": "inferred_from_confirmed_circle"}
        for (a, b), g in sorted(origin.items(), key=lambda kv: (int(kv[0][0][1:]), int(kv[0][1][1:])))
    ]


def build_package(
    directory: Path,
    *,
    contacts: list[dict[str, str]] | None = None,
    groups: list[dict[str, str]] | None = None,
    memberships: list[dict[str, str]] | None = None,
    edges: list[dict[str, str]] | str | None = "derive",
    review_items: list[dict[str, str]] | None = None,
    manifest: dict[str, object] | None = None,
    checksums: bool = True,
    newline: str = "\n",
    bom: bool = True,
    codebook: dict[str, dict[str, str]] | None = None,
) -> Path:
    """Write a package into ``directory`` (created) and return it."""
    directory.mkdir(parents=True, exist_ok=True)
    contacts = contact_rows(6) if contacts is None else contacts
    groups = [] if groups is None else groups
    memberships = [] if memberships is None else memberships
    files: dict[str, bytes] = {
        "contacts.csv": _csv(CONTACT_COLUMNS, contacts, bom=bom, newline=newline),
        "groups.csv": _csv(GROUP_COLUMNS, groups, bom=bom, newline=newline),
        "group_memberships.csv": _csv(MEMBERSHIP_COLUMNS, memberships, bom=bom, newline=newline),
    }
    cb = CODEBOOK if codebook is None else codebook
    files["codebook.csv"] = _csv(
        ("field", "code", "meaning_de"),
        [{"field": f, "code": c, "meaning_de": m} for f, entries in cb.items() for c, m in entries.items()],
        bom=bom,
        newline=newline,
    )
    if edges == "derive":
        edges = derived_edges(groups, memberships)
    if edges is not None:
        files["observed_edges.csv"] = _csv(EDGE_COLUMNS, edges, bom=bom, newline=newline)
    if review_items is not None:
        files["review_items.csv"] = _csv(REVIEW_COLUMNS, review_items, bom=bom, newline=newline)
    document: dict[str, object] = {
        "package_version": "0.0-synthetic",
        "project": "MARES",
        "synthetic": True,
        "source_case_label": LABEL,
        "source_date": "0000-01-01",
        "source_interview_type": "synthetic test collection",
        "contact_count": len(contacts),
        "canonical_case_id": "not assigned",
    }
    if isinstance(edges, list):
        document["edge_count_from_unambiguous_groups"] = len(edges)
    document.update(manifest or {})
    files["manifest.json"] = (json.dumps(document, indent=2) + "\n").encode("utf-8")
    if checksums:
        files["SHA256SUMS.txt"] = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(files.items())).encode("utf-8")
    for name, data in files.items():
        (directory / name).write_bytes(data)
    return directory


def standard_groups() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Two overlapping confirmed groups (sharing one pair), one unconfirmed candidate group, one pair."""
    groups = [group("G01"), group("G02"), group("G03", assessment="needs_review"), group("G04")]
    memberships = (
        members("G01", ["A01", "A02", "A03", "A04"])
        + members("G02", ["A03", "A04", "A05"])
        + members("G03", ["A06", "A07", "A08"], status="candidate")
        + members("G04", ["A10", "A11"])
    )
    return groups, memberships


def standard_package(directory: Path, *, n: int = 12) -> Path:
    groups, memberships = standard_groups()
    contacts = contact_rows(n, block_size=8)
    contacts[2]["review_flags"] = "TEST_FLAG"
    reviews = [
        {"review_id": "RT01", "priority": "high", "reference": "A03", "field": "language_mode", "description": "synthetic open question", "recommended_action": "source_check"},
        {"review_id": "RT02", "priority": "medium", "reference": "all", "field": "rule", "description": "synthetic decided rule", "recommended_action": "rule_confirmed"},
    ]
    return build_package(directory, contacts=contacts, groups=groups, memberships=memberships, review_items=reviews)
