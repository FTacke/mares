"""Logical references, identifiers, provenance and the synthetic example case."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from itertools import combinations

import pytest

from mares.core import ids
from mares.core.hashing import sha256_file
from mares.core.model import BackupState, Origin, PreservationState, Provenance, QualityState, ReleaseState
from mares.core.paths import repo_path
from mares.core.refs import StorageRef

EXAMPLE = ("examples", "synthetic", "MARES-0000-001")


@pytest.mark.parametrize(
    "rel",
    [
        "",
        "/preservation/raw",
        "preservation//raw",
        "preservation/../restricted",
        "./preservation",
        "preservation/raw/",
        "preservation\\raw",
        "C:/preservation/raw",  # path-literal-ok: a rejected example
        "\\\\server\\share\\raw",  # path-literal-ok: a rejected example
    ],
)
def test_reference_rejects_anything_but_a_relative_posix_path(rel):
    with pytest.raises(ValueError):
        StorageRef("PRIMARY", rel)


def test_reference_rejects_a_path_as_root_name():
    with pytest.raises(ValueError):
        StorageRef("primary", "preservation/raw")


def test_reference_round_trips_through_its_persisted_form():
    ref = StorageRef("PRIMARY", "preservation/raw").child("ab", "abcdef")
    assert ref.to_dict() == {"root": "PRIMARY", "rel": "preservation/raw/ab/abcdef"}
    assert StorageRef.from_dict(ref.to_dict()) == ref
    with pytest.raises(ValueError):
        StorageRef.from_dict({"root": "PRIMARY", "rel": "x", "path": "y"})


def test_identifier_formats():
    assert ids.case_id(2026, 1) == "MARES-2026-001"
    assert ids.is_case_id("MARES-2026-001") and not ids.is_case_id("MARES-2026-1")
    assert not ids.is_case_id("mares-2026-001") and not ids.is_case_id("MARES-2026-001-v2")
    assert ids.is_synthetic_case_id("MARES-0000-001") and not ids.is_synthetic_case_id("MARES-2026-001")

    assert [ids.contact_id(number) for number in (1, 15, 22, 99, 100)] == ["A01", "A15", "A22", "A99", "A100"]
    assert all(ids.is_contact_id(value) for value in ("A01", "A16", "A22", "A99", "A100", "A1234"))
    assert not any(ids.is_contact_id(value) for value in ("A00", "A1", "A001", "A0", "a01", "EGO", "A01b"))
    assert ids.contact_number("A22") == 22 and ids.contact_number("A100") == 100
    for bad in (0, -1, True, "7"):
        with pytest.raises(ValueError):
            ids.contact_id(bad)

    moment = datetime(2026, 10, 12, 9, 30, tzinfo=timezone.utc)
    assert ids.new_run_id(moment).startswith("RUN-20261012T093000Z-") and ids.is_run_id(ids.new_run_id(moment))
    assert ids.is_submission_id(ids.new_submission_id(moment)) and not ids.is_run_id(ids.new_submission_id(moment))
    assert ids.is_asset_id(ids.new_asset_id()) and ids.new_asset_id() != ids.new_asset_id()

    assert ids.is_dataset_version_id("DS-networks-core@v3") and not ids.is_dataset_version_id("DS-networks-core@v0")
    assert ids.is_instrument_version_id("INS-network-sheet@v2") and ids.is_instrument_version_id("INS-network-sheet@v0")
    assert ids.is_cohort_id("WS2026-27") and ids.is_cohort_id("SS2027") and not ids.is_cohort_id("WS2026")


def test_content_hash_depends_on_bytes_only(tmp_path):
    first, second = tmp_path / "a" / "one.bin", tmp_path / "b" / "renamed.bin"
    for path in (first, second):
        path.parent.mkdir()
        path.write_bytes(b"synthetic content")
    assert sha256_file(first) == sha256_file(second) == hashlib.sha256(b"synthetic content").hexdigest()
    assert ids.is_sha256(sha256_file(first))


def test_provenance_rules():
    teaching = Provenance(Origin.TEACHING, "SEMINAR", "COL-01", "INS-network-sheet@v1", cohort="WS2026-27")
    assert teaching.origin is Origin.TEACHING
    with pytest.raises(ValueError):
        Provenance(Origin.TEACHING, "SEMINAR", "COL-01", "INS-network-sheet@v1")  # no cohort
    with pytest.raises(ValueError):
        Provenance(Origin.RESEARCH, "PROJECT", "COL-01", "INS-network-sheet@v1", cohort="WS2026-27")
    with pytest.raises(ValueError):
        Provenance(Origin.RESEARCH, "PROJECT", "COL-01", "network sheet, second version")
    with pytest.raises(AttributeError):
        teaching.origin = Origin.RESEARCH  # origin never changes


def test_synthetic_case_follows_the_data_contract():
    case = json.loads(repo_path(*EXAMPLE, "case.json").read_text(encoding="utf-8"))
    assert case["synthetic"] is True and ids.is_synthetic_case_id(case["case_id"])

    provenance = dict(case["provenance"])
    Provenance(Origin(provenance.pop("origin")), **provenance)

    status = case["status"]
    PreservationState(status["preservation"]), BackupState(status["backup"])
    QualityState(status["quality"]), ReleaseState(status["release"])
    assert status["permitted_uses"] == []  # unknown consent permits nothing

    for entry in case["files"]:
        StorageRef.from_dict(entry["ref"])  # logical references only, no address


def test_synthetic_network_distinguishes_unknown_from_missing_ties():
    with open(repo_path(*EXAMPLE, "contacts.csv"), encoding="utf-8", newline="") as handle:
        contacts = [row["contact_id"] for row in csv.DictReader(handle)]
    assert contacts and all(ids.is_contact_id(contact) for contact in contacts)
    assert len(set(contacts)) == len(contacts)

    with open(repo_path(*EXAMPLE, "ties.csv"), encoding="utf-8", newline="") as handle:
        ties = {(row["contact_a"], row["contact_b"]): row["tie"] for row in csv.DictReader(handle)}
    assert set(ties) == set(combinations(contacts, 2))  # every unordered pair exactly once
    assert set(ties.values()) == {"yes", "no", "unknown", ""}
    assert ties[("A02", "A04")] == "unknown" and ties[("A03", "A05")] == ""  # asked-and-unknown vs not recorded
