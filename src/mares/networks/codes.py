"""Coded values: the codebook and the parsing of multi-code cells.

A cell holds one code (``3``) or several codes separated by ``|`` (``1|2|3``). A well-defined
numeric range (``1-6``, also with an en dash, or ``G1-G3``) is expanded to its single codes. An
empty cell means *not collected*; it is never turned into a code, a zero or a default.

Whether a code is *valid* is not decided here but against the codebook of the package
(:class:`Codebook`), so a new instrument version needs a new codebook, not new code.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

SEPARATOR = "|"

_RANGE = re.compile(r"([A-Za-z]*)(\d+)\s*[-–—]\s*(?:\1)?(\d+)")
_ATOM = re.compile(r"[A-Za-z0-9_]+")
# A range that is not expanded blindly: a range spanning more than this is most likely a typo.
_MAX_RANGE = 99


class CodeSyntaxError(ValueError):
    """A cell is not a well-formed list of codes."""


@dataclass(frozen=True)
class ParsedCodes:
    """The codes of one cell, in order of first appearance, without duplicates."""

    codes: tuple[str, ...]
    expanded_ranges: tuple[str, ...] = ()  # the range tokens as written, if any
    duplicates: tuple[str, ...] = ()  # codes that were written more than once

    def __bool__(self) -> bool:
        return bool(self.codes)


def parse_codes(cell: str | None) -> ParsedCodes:
    """Parse one cell. Raises :class:`CodeSyntaxError`; an empty cell is the empty result."""
    text = "" if cell is None else cell.strip()
    if not text:
        return ParsedCodes(())
    codes: list[str] = []
    ranges: list[str] = []
    duplicates: list[str] = []
    for token in (part.strip() for part in text.split(SEPARATOR)):
        if not token:
            raise CodeSyntaxError(f"empty element in {text!r}")
        match = _RANGE.fullmatch(token)
        if match:
            prefix, low, high = match.group(1), int(match.group(2)), int(match.group(3))
            if high <= low:
                raise CodeSyntaxError(f"a range runs upwards: {token!r}")
            if high - low > _MAX_RANGE:
                raise CodeSyntaxError(f"range too wide to be plausible: {token!r}")
            ranges.append(token)
            expanded = [f"{prefix}{number}" for number in range(low, high + 1)]
        elif _ATOM.fullmatch(token):
            expanded = [token]
        else:
            raise CodeSyntaxError(f"not a code or a range: {token!r}")
        for code in expanded:
            if code in codes:
                duplicates.append(code)
            else:
                codes.append(code)
    return ParsedCodes(tuple(codes), tuple(ranges), tuple(duplicates))


class CodebookError(ValueError):
    """The codebook file is missing, malformed or ambiguous."""


@dataclass(frozen=True)
class Codebook:
    """``field -> code -> meaning``, as delivered with a package (``field;code;meaning_de``)."""

    entries: dict[str, dict[str, str]]

    @classmethod
    def read(cls, path: Path) -> "Codebook":
        entries: dict[str, dict[str, str]] = {}
        with open(path, encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=";")
            if reader.fieldnames is None or list(reader.fieldnames) != ["field", "code", "meaning_de"]:
                raise CodebookError(f"{Path(path).name}: expected the columns field;code;meaning_de")
            for number, row in enumerate(reader, 2):
                field, code, meaning = (row[key].strip() for key in ("field", "code", "meaning_de"))
                if not field or not code or not meaning:
                    raise CodebookError(f"{Path(path).name}:{number}: field, code and meaning are required")
                if code in entries.setdefault(field, {}):
                    raise CodebookError(f"{Path(path).name}:{number}: code {code!r} is defined twice for {field!r}")
                entries[field][code] = meaning
        if not entries:
            raise CodebookError(f"{Path(path).name}: the codebook is empty")
        return cls(entries)

    def has_field(self, field: str) -> bool:
        return field in self.entries

    def codes(self, field: str) -> tuple[str, ...]:
        """The valid codes of a field in codebook order (which carries no ranking)."""
        return tuple(self.entries[field])

    def is_valid(self, field: str, code: str) -> bool:
        return code in self.entries.get(field, {})

    def meaning(self, field: str, code: str) -> str:
        return self.entries[field][code]
