"""Logical storage references.

A persisted location is never an address. It is the *name* of a storage root plus a relative path
in POSIX spelling; a physical path exists only after :class:`mares.core.roots.Roots` resolved it
on one machine. Moving a root (the university share to its successor, the backup to another disk)
therefore changes one configured value and no stored reference.

A reference is not an identity either: ids and content hashes never contain one
(``docs/architecture/data-contract.md``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

ROOT_NAME = re.compile(r"[A-Z][A-Z0-9_]*")

# Characters that would make a stored path mean something else on another platform: a backslash is
# a separator on Windows and a name character on POSIX, a colon introduces a drive or a stream.
_FORBIDDEN = ("\\", ":", "\0")


@dataclass(frozen=True)
class StorageRef:
    """``root`` is a declared root name, ``rel`` a relative POSIX path below it."""

    root: str
    rel: str

    def __post_init__(self) -> None:
        if not isinstance(self.root, str) or not ROOT_NAME.fullmatch(self.root):
            raise ValueError(f"not a storage root name: {self.root!r}")
        if not isinstance(self.rel, str) or not self.rel:
            raise ValueError("a storage reference needs a non-empty relative path")
        if any(char in self.rel for char in _FORBIDDEN):
            raise ValueError(f"not a relative POSIX path (backslash, colon or NUL): {self.rel!r}")
        if self.rel.startswith("/"):
            raise ValueError(f"a storage reference is relative, not absolute: {self.rel!r}")
        for segment in self.rel.split("/"):
            if segment in ("", ".", ".."):
                raise ValueError(f"empty, '.' or '..' segment in storage reference: {self.rel!r}")

    @property
    def parts(self) -> tuple[str, ...]:
        return tuple(self.rel.split("/"))

    def child(self, *segments: str) -> "StorageRef":
        return StorageRef(self.root, "/".join((self.rel, *segments)))

    def to_dict(self) -> dict[str, str]:
        """The persisted form: ``{"root": "PRIMARY", "rel": "preservation/raw/..."}``."""
        return {"root": self.root, "rel": self.rel}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StorageRef":
        if set(data) != {"root", "rel"}:
            raise ValueError(f"a storage reference has exactly the keys root and rel: {sorted(data)}")
        return cls(data["root"], data["rel"])
