"""Canonical contact ids from source positions.

A paper sheet holds a fixed number of alter slots; a longer list continues on a further sheet whose
local numbering starts again. The canonical id is therefore *not* the local number but the rank of
a contact in source order (sheet block, then local number): ``(1, A01..A15)`` followed by
``(2, A01..A07)`` becomes ``A01..A22``. The source position is kept as provenance next to it.
"""

from __future__ import annotations

import re
from typing import Sequence

from mares.core import ids

_LOCAL = re.compile(r"A(\d{2,})")


def local_number(local_id: str) -> int | None:
    match = _LOCAL.fullmatch(local_id)
    return int(match.group(1)) if match else None


def source_order_key(block: str, local_id: str) -> tuple[int, str, int]:
    """Sort key of a source position: numeric blocks first in numeric order, then the local number."""
    number = local_number(local_id)
    return (int(block) if block.isdigit() else 10**9, block, -1 if number is None else number)


def canonical_contact_ids(positions: Sequence[tuple[str, str]]) -> list[str]:
    """Canonical ids for source positions ``(block, local_id)``, returned in the order given.

    Raises ``ValueError`` if a position is repeated or malformed: a position that cannot be told
    apart from another one gets no id by guessing.
    """
    if len(set(positions)) != len(positions):
        raise ValueError("a source position occurs more than once")
    for block, local_id in positions:
        if not block or local_number(local_id) is None:
            raise ValueError(f"not a source position: block={block!r}, local id={local_id!r}")
    ranked = sorted(range(len(positions)), key=lambda index: source_order_key(*positions[index]))
    result = [""] * len(positions)
    for rank, index in enumerate(ranked, 1):
        result[index] = ids.contact_id(rank)
    return result
