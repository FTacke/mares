"""Construction of the alter-alter network from confirmed groups (and explicit statements).

Rules (``docs/architecture/network-module.md`` §4), all of them about what counts as *evidence*:

1. Only a group that is ``confirmed`` implies ties, and only through its ``confirmed`` memberships:
   everyone inside one confirmed outline knows everyone else (clique rule, stated by the
   researcher). A group that needs review, and every ``candidate`` membership, implies nothing.
2. Identical pairs from several groups are one tie; the groups stay as its origin.
3. A pair without evidence is *not recorded* -- unknown, never ``no``. The model has no way to
   turn absence into ``no``; only an explicit statement can be ``no``.
4. An explicit statement that contradicts a clique tie is an error, not a vote.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable

from mares.core import ids

from .model import CONFIRMED, NetworkDataset, Tie, TieBasis, TieState


class NetworkConstructionError(ValueError):
    """The evidence is contradictory; no network is built from it."""


def pair_key(a: str, b: str) -> tuple[str, str]:
    """The canonical order of an unordered pair: by contact number."""
    return (a, b) if ids.contact_number(a) <= ids.contact_number(b) else (b, a)


@dataclass(frozen=True)
class Network:
    contact_ids: tuple[str, ...]
    ties: tuple[Tie, ...]  # only pairs with evidence, sorted by pair
    confirmed_groups: tuple[tuple[str, tuple[str, ...]], ...]  # (group id, members)
    unconfirmed_groups: tuple[tuple[str, tuple[str, ...]], ...]  # candidates: no ties derived

    def state(self, a: str, b: str) -> TieState:
        key = pair_key(a, b)
        for tie in self.ties:
            if tie.pair == key:
                return tie.state
        return TieState.NOT_RECORDED

    @property
    def positive_ties(self) -> tuple[Tie, ...]:
        return tuple(tie for tie in self.ties if tie.state is TieState.YES)

    @property
    def pair_total(self) -> int:
        n = len(self.contact_ids)
        return n * (n - 1) // 2

    def pair_counts(self) -> dict[TieState, int]:
        """How many of all possible pairs are in which state. Counts, not shares: no density."""
        counts = {state: 0 for state in TieState}
        for tie in self.ties:
            counts[tie.state] += 1
        counts[TieState.NOT_RECORDED] = self.pair_total - len(self.ties)
        return counts

    def is_complete(self) -> bool:
        """True only if every pair carries an explicit statement."""
        return self.pair_total > 0 and all(t.basis is TieBasis.EXPLICIT for t in self.ties) and len(
            self.ties
        ) == self.pair_total

    def groups_of(self, contact_id: str) -> tuple[str, ...]:
        return tuple(group for group, members in self.confirmed_groups if contact_id in members)


def build_network(dataset: NetworkDataset, explicit_ties: Iterable[Tie] = ()) -> Network:
    known = set(dataset.contact_ids)
    confirmed_groups = {group.group_id for group in dataset.groups if group.confirmed}

    members_by_group: dict[str, list[str]] = {}
    unconfirmed: dict[str, list[str]] = {}
    for membership in dataset.memberships:
        if membership.contact_id not in known:
            continue  # reported by the validator; never becomes a node
        if membership.group_id in confirmed_groups and membership.status == CONFIRMED:
            members_by_group.setdefault(membership.group_id, []).append(membership.contact_id)
        else:
            unconfirmed.setdefault(membership.group_id, []).append(membership.contact_id)

    origin: dict[tuple[str, str], list[str]] = {}
    for group_id in sorted(members_by_group):
        members = sorted(set(members_by_group[group_id]), key=ids.contact_number)
        members_by_group[group_id] = members
        for a, b in combinations(members, 2):
            origin.setdefault((a, b), []).append(group_id)

    ties: dict[tuple[str, str], Tie] = {
        pair: Tie(pair[0], pair[1], TieState.YES, TieBasis.CLIQUE_RULE, tuple(groups))
        for pair, groups in origin.items()
    }
    for explicit in explicit_ties:
        if explicit.a not in known or explicit.b not in known or explicit.a == explicit.b:
            raise NetworkConstructionError(f"explicit tie {explicit.a}-{explicit.b} names no valid pair of contacts")
        key = pair_key(explicit.a, explicit.b)
        existing = ties.get(key)
        if existing is not None and existing.state is not explicit.state:
            raise NetworkConstructionError(
                f"contradiction for {key[0]}-{key[1]}: {existing.state.value} "
                f"({existing.basis.value}) versus {explicit.state.value} (explicit)"
            )
        groups = existing.group_ids if existing else ()
        ties[key] = Tie(key[0], key[1], explicit.state, TieBasis.EXPLICIT if existing is None else existing.basis, groups)

    ordered = tuple(sorted(ties.values(), key=lambda tie: (ids.contact_number(tie.a), ids.contact_number(tie.b))))
    return Network(
        contact_ids=dataset.contact_ids,
        ties=ordered,
        confirmed_groups=tuple((g, tuple(m)) for g, m in sorted(members_by_group.items())),
        unconfirmed_groups=tuple(
            (g, tuple(sorted(set(m), key=ids.contact_number))) for g, m in sorted(unconfirmed.items())
        ),
    )
