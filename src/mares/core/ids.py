"""Stable identifiers (``docs/architecture/data-contract.md`` §2).

An id is assigned once and never derived from where something is stored: no path, drive, root
name or file name enters an id. Content is identified by its SHA-256, not by an id.

* case: ``MARES-2026-001`` -- year of registration and a running number
* contact (per case): ``A01``, ``A02``, ... (no upper bound) -- running number; ego is ``EGO``
* asset: ``AST-9f3c2a7b41d0`` -- one preserved original file (random, assigned)
* submission: ``SUB-20261012T093000Z-1a2b3c`` -- one hand-in event
* processing run: ``RUN-20261012T093000Z-1a2b3c`` -- one execution of a processing step
* dataset version: ``DS-networks-core@v3`` -- a named dataset and its version
* instrument version: ``INS-network-sheet@v2`` -- a survey instrument and its version
* cohort: ``WS2026-27`` / ``SS2027`` -- a seminar semester

The case year ``0000`` is reserved for synthetic and test cases and never names a real one.
"""

from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone

SYNTHETIC_YEAR = "0000"
EGO = "EGO"

_CASE = re.compile(r"MARES-(\d{4})-(\d{3})")
_CONTACT = re.compile(r"A(0[1-9]|[1-9][0-9]+)")
_ASSET = re.compile(r"AST-[0-9a-f]{12}")
_EVENT = r"-\d{8}T\d{6}Z-[0-9a-f]{6}"
_SUBMISSION = re.compile("SUB" + _EVENT)
_RUN = re.compile("RUN" + _EVENT)
_VERSIONED = r"-[a-z0-9]+(?:-[a-z0-9]+)*@v[1-9]\d*"
_DATASET_VERSION = re.compile("DS" + _VERSIONED)
_INSTRUMENT_VERSION = re.compile("INS" + _VERSIONED)
_INSTRUMENT_DRAFT = re.compile(r"INS-[a-z0-9]+(?:-[a-z0-9]+)*@v0")
_COHORT = re.compile(r"WS\d{4}-\d{2}|SS\d{4}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


def is_case_id(value: str) -> bool:
    return _CASE.fullmatch(value) is not None


def is_synthetic_case_id(value: str) -> bool:
    match = _CASE.fullmatch(value)
    return match is not None and match.group(1) == SYNTHETIC_YEAR


def case_id(year: int, number: int) -> str:
    """Format a case id. Assigning the number is the registry's job, not this function's."""
    if not (0 <= year <= 9999 and 1 <= number <= 999):
        raise ValueError(f"case id out of range: year={year}, number={number}")
    return f"MARES-{year:04d}-{number:03d}"


def is_contact_id(value: str) -> bool:
    return _CONTACT.fullmatch(value) is not None


def contact_id(number: int) -> str:
    """Format a canonical contact id. There is no upper bound: ``A99`` is followed by ``A100``."""
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        raise ValueError(f"a contact number is a positive integer: {number!r}")
    return f"A{number:02d}"


def contact_number(value: str) -> int:
    """The running number of a canonical contact id (``A07`` -> 7)."""
    if not is_contact_id(value):
        raise ValueError(f"not a contact id: {value!r}")
    return int(value[1:])


def is_asset_id(value: str) -> bool:
    return _ASSET.fullmatch(value) is not None


def new_asset_id() -> str:
    """A fresh asset id. Random on purpose: it says nothing about case, content or location."""
    return f"AST-{secrets.token_hex(6)}"


def _event_id(prefix: str, moment: datetime | None) -> str:
    moment = datetime.now(timezone.utc) if moment is None else moment
    if moment.tzinfo is None:
        raise ValueError("an event id needs a timezone-aware moment")
    stamp = moment.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}-{stamp}-{secrets.token_hex(3)}"


def is_submission_id(value: str) -> bool:
    return _SUBMISSION.fullmatch(value) is not None


def new_submission_id(moment: datetime | None = None) -> str:
    return _event_id("SUB", moment)


def is_run_id(value: str) -> bool:
    return _RUN.fullmatch(value) is not None


def new_run_id(moment: datetime | None = None) -> str:
    return _event_id("RUN", moment)


def is_dataset_version_id(value: str) -> bool:
    return _DATASET_VERSION.fullmatch(value) is not None


def is_instrument_version_id(value: str) -> bool:
    """``@v0`` is accepted for an instrument only: a draft that has not been fielded."""
    return (_INSTRUMENT_VERSION.fullmatch(value) or _INSTRUMENT_DRAFT.fullmatch(value)) is not None


def is_cohort_id(value: str) -> bool:
    return _COHORT.fullmatch(value) is not None


def is_sha256(value: str) -> bool:
    return _SHA256.fullmatch(value) is not None
