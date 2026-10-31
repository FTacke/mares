"""Curation: documented statements *about* a package that the package itself does not carry.

Original delivery files are never changed (``docs/architecture/intake-preservation.md``). What the project
lead clarifies afterwards -- how the alter-alter relations were elicited, whether every pair was
covered, how a review hint is to be read -- goes into a separate, dated, hashed file that a run
reads next to the package and records. Without it a package is processed with everything
"not stated" and every review hint open.

Format ``mares-network-curation/v0-draft`` (JSON)::

    {"format": ..., "source_label": "001-2", "applies_to_package_version": "1.1-draft",
     "made_on": "2026-10-12", "made_by": "...",
     "survey": {"elicitation": "asked_per_pair", "documentation": "group_outlines",
                "group_rule": "all_members_know_each_other", "pair_coverage": "not_established",
                "basis": "..."},
     "dispositions": [{"ref": "R01", "category": "resolved", "decided_by": "project_lead",
                       "basis": "...", "note": "..."}, ...]}

``ref`` is a review id (``R01``) or ``flag:<contact id>:<FLAG>`` for a review flag on a contact that
has no review item of its own.
"""

from __future__ import annotations

import enum
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

FORMAT = "mares-network-curation/v0-draft"

ELICITATION = {"asked_per_pair": "Beziehungen einzeln erfragt", "not_stated": "Erhebungsmethode nicht angegeben"}
DOCUMENTATION = {"group_outlines": "Gruppenumrandungen der Netzwerkkarte", "not_stated": "Dokumentationsform nicht angegeben"}
COVERAGE = ("not_established", "complete")
GROUP_RULES = ("all_members_know_each_other",)
DECIDERS = ("project_lead", "agent_proposal")

_FLAG_REF = re.compile(r"flag:(A(?:0[1-9]|[1-9][0-9]+)):([A-Za-z0-9_]+)")


class ReviewCategory(enum.Enum):
    """What a review hint is *now*. Only the first is an open data question."""

    OPEN_DECISION = "open_decision"  # a decision-relevant data question that is still open
    DOCUMENTED_AMBIGUITY = "documented_ambiguity"  # the source is ambiguous; documented, raw value kept
    ACCEPTED_IMPRECISION = "accepted_imprecision"  # an imprecision of the survey that is accepted
    RESOLVED = "resolved"  # settled or closed

    @property
    def is_open(self) -> bool:
        return self is ReviewCategory.OPEN_DECISION


CATEGORY_LABELS = {
    ReviewCategory.OPEN_DECISION: "offene, entscheidungsrelevante Datenfrage",
    ReviewCategory.DOCUMENTED_AMBIGUITY: "dokumentierte Mehrdeutigkeit der Quelle",
    ReviewCategory.ACCEPTED_IMPRECISION: "akzeptierte Unschärfe der Erhebung",
    ReviewCategory.RESOLVED: "geklärt / abgeschlossen",
}


class CurationError(ValueError):
    """The curation file is malformed. Never guessed around."""


@dataclass(frozen=True)
class SurveyMethod:
    """How the alter-alter relations were obtained and how they are documented.

    *Elicitation* (what the explorator did) and *documentation form* (how it was written down) are
    different things. ``pair_coverage`` says whether **every** pair of contacts was covered: only
    then may a missing pair count as explicitly denied.
    """

    elicitation: str = "not_stated"
    documentation: str = "not_stated"
    group_rule: str | None = None
    pair_coverage: str = "not_established"
    basis: str | None = None

    @property
    def stated(self) -> bool:
        return self.elicitation != "not_stated"

    @property
    def coverage_complete(self) -> bool:
        return self.pair_coverage == "complete"


@dataclass(frozen=True)
class Disposition:
    ref: str
    category: ReviewCategory
    decided_by: str
    basis: str
    note: str = ""

    @property
    def flag(self) -> tuple[str, str] | None:
        match = _FLAG_REF.fullmatch(self.ref)
        return (match.group(1), match.group(2)) if match else None


@dataclass(frozen=True)
class Curation:
    source_label: str | None = None
    applies_to_package_version: str | None = None
    made_on: str | None = None
    made_by: str | None = None
    survey: SurveyMethod = field(default_factory=SurveyMethod)
    dispositions: tuple[Disposition, ...] = ()
    sha256: str | None = None  # of the file, set by the reader

    def disposition(self, ref: str) -> Disposition | None:
        for item in self.dispositions:
            if item.ref == ref:
                return item
        return None


NO_CURATION = Curation()


def _text(document: dict, key: str, where: str, *, required: bool = True) -> str | None:
    value = document.get(key)
    if value is None and not required:
        return None
    if not isinstance(value, str) or not value.strip():
        raise CurationError(f"{where}: {key!r} must be a non-empty string")
    return value.strip()


def read_curation(path: Path) -> Curation:
    """Read and strictly check a curation file."""
    from mares.core.hashing import sha256_file

    path = Path(path)
    try:
        document = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CurationError(f"{path.name}: cannot be read: {error}") from error
    if not isinstance(document, dict) or document.get("format") != FORMAT:
        raise CurationError(f"{path.name}: expected format {FORMAT!r}")

    raw_survey = document.get("survey", {})
    if not isinstance(raw_survey, dict):
        raise CurationError(f"{path.name}: 'survey' must be an object")
    elicitation = raw_survey.get("elicitation", "not_stated")
    documentation = raw_survey.get("documentation", "not_stated")
    coverage = raw_survey.get("pair_coverage", "not_established")
    group_rule = raw_survey.get("group_rule")
    if elicitation not in ELICITATION or documentation not in DOCUMENTATION or coverage not in COVERAGE:
        raise CurationError(f"{path.name}: unknown elicitation, documentation or pair_coverage value")
    if group_rule is not None and group_rule not in GROUP_RULES:
        raise CurationError(f"{path.name}: unknown group_rule {group_rule!r}")
    basis = raw_survey.get("basis")
    if (elicitation != "not_stated" or coverage == "complete") and not (isinstance(basis, str) and basis.strip()):
        raise CurationError(f"{path.name}: a statement about the survey method needs its 'basis'")

    items = []
    seen: set[str] = set()
    for index, raw in enumerate(document.get("dispositions", []), 1):
        where = f"{path.name}: disposition {index}"
        if not isinstance(raw, dict):
            raise CurationError(f"{where}: must be an object")
        ref = _text(raw, "ref", where)
        try:
            category = ReviewCategory(raw.get("category"))
        except ValueError as error:
            raise CurationError(f"{where}: unknown category {raw.get('category')!r}") from error
        decided_by = raw.get("decided_by")
        if decided_by not in DECIDERS:
            raise CurationError(f"{where}: 'decided_by' must be one of {', '.join(DECIDERS)}")
        if ref in seen:
            raise CurationError(f"{where}: {ref!r} is disposed twice")
        seen.add(ref)
        item = Disposition(ref, category, decided_by, _text(raw, "basis", where) or "", str(raw.get("note", "")).strip())
        if not (_FLAG_REF.fullmatch(ref) or re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", ref)):
            raise CurationError(f"{where}: {ref!r} is neither a review id nor flag:<contact>:<FLAG>")
        items.append(item)

    return Curation(
        source_label=_text(document, "source_label", path.name),
        applies_to_package_version=_text(document, "applies_to_package_version", path.name, required=False),
        made_on=_text(document, "made_on", path.name),
        made_by=_text(document, "made_by", path.name),
        survey=SurveyMethod(elicitation, documentation, group_rule, coverage, basis.strip() if isinstance(basis, str) else None),
        dispositions=tuple(items),
        sha256=sha256_file(path),
    )
