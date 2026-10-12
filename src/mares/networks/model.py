"""The in-memory network model.

Identities are kept apart on purpose (``docs/architecture/network-module.md`` §2):

* ``CaseIdentity``   -- the MARES case. The historical source label (``001-2``) is *not* a case
  id; ``canonical_case_id`` stays ``None`` until a register assigns one.
* ``SurveySession``  -- one concrete collection (date, kind), described by the package.
* ``Contact``        -- one person named by ego, identified only inside the case.
* ``Group`` / ``Membership`` -- a drawn group outline and who lies inside it.
* ``Tie``            -- an unordered alter-alter pair with a state; pairs without evidence are not
  ties at all (see :class:`TieState`).
* ``SourceFile``     -- an input file with its SHA-256; the processing version lives in the run.

Everything is immutable. Nothing here reads a file or knows a location.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Mapping

from mares.core import ids

from .codes import Codebook, ParsedCodes

# Assessment vocabulary of the package (groups.csv, group_memberships.csv).
CONFIRMED = "confirmed"
NEEDS_REVIEW = "needs_review"
CANDIDATE = "candidate"


class Severity(enum.Enum):
    ERROR = "ERROR"  # a hard validation error: the data cannot be used as it is
    WARNING = "WARNING"  # usable, but a reader must know
    INFO = "INFO"  # a neutral remark (e.g. an expanded range)


@dataclass(frozen=True)
class Finding:
    """One result of the import or the validator, always tied to a subject."""

    severity: Severity
    code: str  # stable machine-readable key, e.g. ``unknown_code``
    subject: str  # contact id, group id, file name, ``dataset`` ...
    message: str  # German, readable without the source


class TieState(enum.Enum):
    """The state of an unordered pair (``docs/architecture/data-contract.md`` §5).

    ``NOT_RECORDED`` is the state of every pair for which the survey holds no statement. It is
    *unknown*, never ``NO``: only an explicit statement ``NO`` means the two do not know each other.
    """

    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"  # asked, ego does not know
    NOT_RECORDED = "not_recorded"  # not collected, not entered


class TieBasis(enum.Enum):
    CLIQUE_RULE = "clique_rule"  # derived from confirmed group membership
    EXPLICIT = "explicit"  # asked for this pair


@dataclass(frozen=True)
class CaseIdentity:
    source_label: str  # historical label of the source, e.g. ``001-2``
    canonical_case_id: str | None = None  # MARES-YYYY-NNN once registered; never guessed

    def __post_init__(self) -> None:
        if not self.source_label:
            raise ValueError("a case needs a source label")
        if self.canonical_case_id is not None and not ids.is_case_id(self.canonical_case_id):
            raise ValueError(f"not a case id: {self.canonical_case_id!r}")


@dataclass(frozen=True)
class SurveySession:
    source_label: str
    session_date: str | None  # ISO date as stated by the package
    interview_type: str | None
    package_version: str | None
    origin_note: str | None  # e.g. "student collection"; provenance is never dropped


@dataclass(frozen=True)
class SourceFile:
    name: str
    sha256: str
    size: int


@dataclass(frozen=True)
class Contact:
    contact_id: str
    source_block: str
    source_local_id: str
    codes: Mapping[str, ParsedCodes]  # coded attributes by model name; empty result = not collected
    text: Mapping[str, str]  # free or normalised text attributes; missing key = not collected
    review_flags: tuple[str, ...] = ()

    @property
    def number(self) -> int:
        return ids.contact_number(self.contact_id)

    def code_list(self, attribute: str) -> tuple[str, ...]:
        parsed = self.codes.get(attribute)
        return () if parsed is None else parsed.codes

    def single(self, attribute: str) -> str | None:
        """The one code (or text) of a single-valued attribute; ``None`` when not collected."""
        if attribute in self.text:
            return self.text[attribute] or None
        codes = self.code_list(attribute)
        return codes[0] if codes else None


@dataclass(frozen=True)
class Group:
    group_id: str
    label: str
    map_label: str
    assessment: str
    comment: str

    @property
    def confirmed(self) -> bool:
        return self.assessment == CONFIRMED


@dataclass(frozen=True)
class Membership:
    group_id: str
    contact_id: str
    status: str
    derivable_edge: str
    source: str


@dataclass(frozen=True)
class ReviewItem:
    review_id: str
    priority: str
    reference: str  # contact id, group id or ``all``
    field: str
    description: str
    recommended_action: str


@dataclass(frozen=True)
class Clarification:
    clarification_id: str
    source_date: str
    group_id: str
    member_contact_ids: tuple[str, ...]
    relationship_rule: str
    resolution: str
    source_type: str


@dataclass(frozen=True)
class ProvidedEdge:
    """A row of the delivered edge table: an import receipt, not a second network."""

    source_id: str
    target_id: str
    relation: str
    evidence: str
    group_ids: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class Tie:
    """An unordered alter pair with a state. ``a`` precedes ``b`` in contact order."""

    a: str
    b: str
    state: TieState
    basis: TieBasis
    group_ids: tuple[str, ...] = ()  # origin: the groups that imply the tie

    @property
    def pair(self) -> tuple[str, str]:
        return (self.a, self.b)


@dataclass(frozen=True)
class NetworkDataset:
    """Everything the importer read, still unvalidated beyond syntax."""

    case: CaseIdentity
    session: SurveySession
    contacts: tuple[Contact, ...]
    groups: tuple[Group, ...]
    memberships: tuple[Membership, ...]
    review_items: tuple[ReviewItem, ...]
    clarifications: tuple[Clarification, ...]
    provided_edges: tuple[ProvidedEdge, ...]
    codebook: Codebook
    files: tuple[SourceFile, ...]
    listed_checksums: Mapping[str, str]  # file name -> SHA-256 as claimed by the package
    manifest: Mapping[str, object]
    import_findings: tuple[Finding, ...] = field(default=())
    # Columns of the contact table as delivered; an attribute absent here was not collected at all.
    contact_columns: tuple[str, ...] = field(default=())

    def contact(self, contact_id: str) -> Contact | None:
        for contact in self.contacts:
            if contact.contact_id == contact_id:
                return contact
        return None

    @property
    def contact_ids(self) -> tuple[str, ...]:
        return tuple(contact.contact_id for contact in self.contacts)
