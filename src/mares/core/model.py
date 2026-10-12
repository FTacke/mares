"""Provenance and the independent status dimensions of a case
(``docs/architecture/data-contract.md`` §3 and §4).

These are vocabularies and one record type, not a pipeline. The point they fix in code is that
*origin* is a fact about how a case came into being and never changes, while preservation,
backup, quality, release and permitted use are separate questions that are answered separately.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from . import ids


class Origin(enum.Enum):
    """How a case came into being. Immutable: later professional processing adds processing
    runs, quality assessments and dataset versions, it never turns TEACHING into RESEARCH."""

    TEACHING = "TEACHING"
    RESEARCH = "RESEARCH"


class IntakeState(enum.Enum):
    """The outcome of one submission event."""

    RECEIVED = "RECEIVED"
    INTAKE_VALIDATED = "INTAKE_VALIDATED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"


class PreservationState(enum.Enum):
    """Whether an original file is on the authoritative PRIMARY root, verified by read-back."""

    NOT_PRESERVED = "NOT_PRESERVED"
    PENDING = "PENDING"
    RAW_PRESERVED = "RAW_PRESERVED"


class BackupState(enum.Enum):
    """Whether an independent second copy exists. Never implied by ``RAW_PRESERVED``."""

    NO_COPY = "NO_COPY"
    COPY_UNVERIFIED = "COPY_UNVERIFIED"
    BACKUP_VERIFIED = "BACKUP_VERIFIED"


class QualityState(enum.Enum):
    """Data quality as assessed by review, independent of who collected the data."""

    UNREVIEWED = "UNREVIEWED"
    IN_REVIEW = "IN_REVIEW"
    VALIDATED = "VALIDATED"
    VALIDATED_WITH_RESERVATIONS = "VALIDATED_WITH_RESERVATIONS"
    NOT_USABLE = "NOT_USABLE"


class ReleaseState(enum.Enum):
    """The scientific decision to admit a case to a research dataset."""

    NOT_DECIDED = "NOT_DECIDED"
    RESEARCH_APPROVED = "RESEARCH_APPROVED"
    NOT_APPROVED = "NOT_APPROVED"
    WITHDRAWN = "WITHDRAWN"


@dataclass(frozen=True)
class Provenance:
    """The context in which a case was collected.

    ``collector`` is a pseudonym of the collecting person or working group; the key that maps it
    to a person lives only under ``restricted/identities`` on the PRIMARY root. ``context`` names
    the course for a TEACHING case and the project or collection campaign for a RESEARCH case.
    """

    origin: Origin
    context: str
    collector: str
    instrument: str
    cohort: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.origin, Origin):
            raise ValueError("origin must be an Origin")
        if not self.context or not self.collector:
            raise ValueError("provenance needs a context and a collector pseudonym")
        if not ids.is_instrument_version_id(self.instrument):
            raise ValueError(f"not an instrument version id: {self.instrument!r}")
        if self.origin is Origin.TEACHING:
            if self.cohort is None or not ids.is_cohort_id(self.cohort):
                raise ValueError("a TEACHING case needs a cohort such as WS2026-27 or SS2027")
        elif self.cohort is not None:
            raise ValueError("a RESEARCH case has no seminar cohort")
