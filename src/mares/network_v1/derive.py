"""Derived features of a network_v1 case: residence area per contact and the state of every contact pair.

Pair rules (table C):

* group status ``T`` -- every pair of members: contact confirmed (``1``), source ``<group>:T``
* group status ``N`` -- every pair of members: no contact (``0``), source ``<group>:N``
* group status ``P`` or ``NS`` -- nothing is derived; only single statements (``alter_connections.csv``) count
* a single statement ``1``, ``0`` or ``?`` -- as stated, source = the row
* membership in the same group alone is **never** a connection

All statements about one pair are reconciled: ``1`` and ``0`` together are a **conflict** (reported, never resolved);
``?`` next to ``1`` or ``0`` does not contradict it. A pair without any statement is unknown, never ``0``. Every
derived pair keeps the list of its sources.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

from .case import Case
from .places import Area, Residence, classify

CONFIRMED, DENIED, UNKNOWN, CONFLICT = "1", "0", "?", "conflict"


@dataclass
class Pair:
    a: str
    b: str
    statements: list[tuple[str, str]] = field(default_factory=list)  # (status 1/0/?, source)

    @property
    def state(self) -> str:
        values = {s for s, _ in self.statements}
        if CONFIRMED in values and DENIED in values:
            return CONFLICT
        if CONFIRMED in values:
            return CONFIRMED
        if DENIED in values:
            return DENIED
        return UNKNOWN

    @property
    def sources(self) -> list[str]:
        return [f"{source}={status}" for status, source in self.statements]


def pair_key(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a <= b else (b, a)


@dataclass(frozen=True)
class Coverage:
    contacts: int
    pairs: int
    confirmed: int
    denied: int
    stated_unknown: int  # explicitly '?'
    without_statement: int
    conflicts: int

    @property
    def unknown(self) -> int:
        return self.stated_unknown + self.without_statement

    def to_dict(self) -> dict[str, int]:
        return {
            "contacts": self.contacts, "pairs": self.pairs, "confirmed": self.confirmed, "denied": self.denied,
            "unknown_stated": self.stated_unknown, "without_statement": self.without_statement, "conflicts": self.conflicts,
        }


@dataclass
class Derived:
    residence: dict[str, Residence]
    pairs: dict[tuple[str, str], Pair]
    coverage: Coverage

    @property
    def confirmed_edges(self) -> list[tuple[str, str]]:
        return sorted(k for k, p in self.pairs.items() if p.state == CONFIRMED)

    def area(self, contact_id: str) -> Area:
        return self.residence[contact_id].area


def pair_statements(case: Case) -> dict[tuple[str, str], Pair]:
    """Every statement about a pair of *known, distinct* contacts (invalid references are left to the validator)."""
    known = set(case.contact_ids)
    pairs: dict[tuple[str, str], Pair] = {}

    def add(a: str, b: str, status: str, source: str) -> None:
        if a == b or a not in known or b not in known:
            return
        key = pair_key(a, b)
        pairs.setdefault(key, Pair(*key)).statements.append((status, source))

    for group in case.groups:
        status = group.status.value
        if status not in ("T", "N"):
            continue
        for a, b in combinations(case.members(group.id), 2):
            add(a, b, CONFIRMED if status == "T" else DENIED, f"{group.id}:{status}")
    for statement in case.statements:
        if statement.status.recorded:
            add(statement.a, statement.b, statement.status.value, statement.ref)
    return pairs


def derive(case: Case) -> Derived:
    residence = {
        c.id: classify(c.residence_place, c.residence_country_iso3, case.places) for c in case.contacts
    }
    pairs = pair_statements(case)
    n = len(case.contacts)
    states = [p.state for p in pairs.values()]
    stated_unknown = sum(1 for s in states if s == UNKNOWN)
    total = n * (n - 1) // 2
    coverage = Coverage(
        contacts=n,
        pairs=total,
        confirmed=states.count(CONFIRMED),
        denied=states.count(DENIED),
        stated_unknown=stated_unknown,
        without_statement=total - len(pairs),
        conflicts=states.count(CONFLICT),
    )
    return Derived(residence, pairs, coverage)
