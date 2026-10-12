"""Content integrity: SHA-256 over file bytes.

The hash identifies *content*. It is computed over the bytes of a file and nothing else -- no
file name, no path, no root -- so the same content has the same hash wherever it lies.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

_CHUNK = 1024 * 1024


def sha256_file(path: Path) -> str:
    """The lower-case hex SHA-256 of a file's bytes, read in chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()
