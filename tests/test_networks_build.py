"""Network construction: the clique rule, overlap, candidates, unknown versus explicit 'no'."""

from __future__ import annotations

import pytest

import network_fixtures as fx
from mares.networks.build import NetworkConstructionError, build_network, pair_key
from mares.networks.model import Tie, TieBasis, TieState
from mares.networks.package import read_package


def _network(tmp_path, groups, memberships, n=12, **kwargs):
    contacts = fx.contact_rows(n, 8)
    dataset = read_package(fx.build_package(tmp_path / "p", contacts=contacts, groups=groups, memberships=memberships))
    return dataset, build_network(dataset, **kwargs)


def test_a_confirmed_group_is_a_clique(tmp_path):
    groups, memberships = [fx.group("G01")], fx.members("G01", ["A01", "A02", "A03", "A04"])
    _, network = _network(tmp_path, groups, memberships)
    assert {t.pair for t in network.positive_ties} == {
        ("A01", "A02"), ("A01", "A03"), ("A01", "A04"), ("A02", "A03"), ("A02", "A04"), ("A03", "A04")
    }
    assert all(t.state is TieState.YES and t.basis is TieBasis.CLIQUE_RULE and t.group_ids == ("G01",) for t in network.ties)


def test_overlapping_confirmed_groups_share_one_tie_and_keep_both_origins(tmp_path):
    groups, memberships = fx.standard_groups()
    _, network = _network(tmp_path, groups, memberships)
    pairs = [t.pair for t in network.positive_ties]
    assert len(pairs) == len(set(pairs)) == 6 + 2 + 1  # G01: 6, G02: 3 of which A03-A04 is shared, G04: 1
    shared = next(t for t in network.positive_ties if t.pair == ("A03", "A04"))
    assert shared.group_ids == ("G01", "G02")
    assert next(t for t in network.positive_ties if t.pair == ("A04", "A05")).group_ids == ("G02",)


def test_a_group_nested_in_another_adds_no_new_ties(tmp_path):
    groups = [fx.group("G01"), fx.group("G02"), fx.group("G03")]
    memberships = fx.members("G01", ["A01", "A02", "A03", "A04"]) + fx.members("G02", ["A01", "A02", "A05"]) + fx.members("G03", ["A01", "A02"])
    _, network = _network(tmp_path, groups, memberships)
    assert len(network.positive_ties) == 6 + 2  # G01 and the two new pairs of G02; G03 only re-states A01-A02
    assert next(t for t in network.ties if t.pair == ("A01", "A02")).group_ids == ("G01", "G02", "G03")


def test_candidate_groups_create_no_ties(tmp_path):
    groups, memberships = fx.standard_groups()
    _, network = _network(tmp_path, groups, memberships)
    inside_candidate = {"A06", "A07", "A08"}
    assert not [t for t in network.ties if t.a in inside_candidate and t.b in inside_candidate]
    assert dict(network.unconfirmed_groups) == {"G03": ("A06", "A07", "A08")}
    assert "G03" not in {g for g, _ in network.confirmed_groups}


def test_a_candidate_membership_inside_a_confirmed_group_creates_no_tie(tmp_path):
    groups = [fx.group("G01")]
    memberships = fx.members("G01", ["A01", "A02", "A03"]) + fx.members("G01", ["A04"], status="candidate")
    _, network = _network(tmp_path, groups, memberships)
    assert {t.pair for t in network.ties} == {("A01", "A02"), ("A01", "A03"), ("A02", "A03")}


def test_a_confirmed_membership_in_an_unconfirmed_group_is_ignored(tmp_path):
    groups = [fx.group("G01", assessment="needs_review")]
    _, network = _network(tmp_path, groups, fx.members("G01", ["A01", "A02", "A03"]))
    assert network.ties == ()


def test_pairs_without_evidence_are_not_recorded_never_no(tmp_path):
    groups, memberships = fx.standard_groups()
    _, network = _network(tmp_path, groups, memberships)
    assert network.state("A01", "A02") is TieState.YES
    assert network.state("A02", "A01") is TieState.YES  # unordered
    assert network.state("A01", "A09") is TieState.NOT_RECORDED
    assert network.state("A06", "A07") is TieState.NOT_RECORDED  # inside an unconfirmed outline: still unknown
    assert TieState.NOT_RECORDED is not TieState.NO
    counts = network.pair_counts()
    assert counts[TieState.YES] == 9 and counts[TieState.NO] == 0
    assert counts[TieState.NOT_RECORDED] == network.pair_total - 9 == 12 * 11 // 2 - 9
    assert not network.is_complete()


def test_explicit_statements_are_kept_apart_from_missing_ones(tmp_path):
    groups, memberships = fx.standard_groups()
    explicit = [
        Tie("A01", "A09", TieState.NO, TieBasis.EXPLICIT),
        Tie("A12", "A02", TieState.UNKNOWN, TieBasis.EXPLICIT),
    ]
    _, network = _network(tmp_path, groups, memberships, explicit_ties=explicit)
    assert network.state("A01", "A09") is TieState.NO  # asked: they do not know each other
    assert network.state("A02", "A12") is TieState.UNKNOWN  # asked: ego does not know
    assert network.state("A01", "A10") is TieState.NOT_RECORDED  # never asked
    counts = network.pair_counts()
    assert (counts[TieState.NO], counts[TieState.UNKNOWN]) == (1, 1)
    assert counts[TieState.NOT_RECORDED] == network.pair_total - 9 - 2


def test_an_explicit_statement_contradicting_a_clique_tie_is_an_error(tmp_path):
    groups, memberships = fx.standard_groups()
    with pytest.raises(NetworkConstructionError, match="contradiction"):
        _network(tmp_path, groups, memberships, explicit_ties=[Tie("A02", "A01", TieState.NO, TieBasis.EXPLICIT)])
    with pytest.raises(NetworkConstructionError):
        _network(tmp_path, groups, memberships, explicit_ties=[Tie("A01", "A01", TieState.YES, TieBasis.EXPLICIT)])
    with pytest.raises(NetworkConstructionError):
        _network(tmp_path, groups, memberships, explicit_ties=[Tie("A01", "A99", TieState.YES, TieBasis.EXPLICIT)])


def test_a_network_is_complete_only_if_every_pair_is_explicit(tmp_path):
    contacts = fx.contact_rows(3)
    dataset = read_package(fx.build_package(tmp_path / "p", contacts=contacts))
    explicit = [Tie("A01", "A02", TieState.YES, TieBasis.EXPLICIT), Tie("A01", "A03", TieState.NO, TieBasis.EXPLICIT)]
    assert not build_network(dataset, explicit).is_complete()
    explicit.append(Tie("A02", "A03", TieState.UNKNOWN, TieBasis.EXPLICIT))
    assert build_network(dataset, explicit).is_complete()


def test_pair_order_is_by_contact_number():
    assert pair_key("A10", "A02") == ("A02", "A10")
    assert pair_key("A100", "A99") == ("A99", "A100")


def _pilot_shape(tmp_path):
    """22 contacts on two sheets and six confirmed groups shaped like the pilot case (synthetic ids and values)."""
    groups = [fx.group(f"G0{i}") for i in range(1, 7)]
    memberships = (
        fx.members("G01", ["A07", "A08", "A10", "A11", "A14", "A15"])
        + fx.members("G02", ["A09", "A19", "A20"])
        + fx.members("G03", ["A21", "A22"])
        + fx.members("G04", ["A04", "A05", "A06"])
        + fx.members("G05", ["A01", "A02", "A03", "A04", "A05", "A06"])
        + fx.members("G06", ["A04", "A05", "A06", "A12", "A16"])
    )
    return read_package(fx.build_package(tmp_path / "p", contacts=fx.contact_rows(22), groups=groups, memberships=memberships))


def test_a_pilot_shaped_network_keeps_22_contacts_6_groups_and_41_unique_ties(tmp_path):
    dataset = _pilot_shape(tmp_path)
    network = build_network(dataset)
    assert len(dataset.contacts) == 22 and len(network.confirmed_groups) == 6 and network.unconfirmed_groups == ()
    pairs = [t.pair for t in network.positive_ties]
    assert len(pairs) == len(set(pairs)) == 15 + 3 + 1 + 15 + 10 - 3  # overlaps counted once: G04 adds nothing, G05 and G06 share a triangle
    assert next(t for t in network.ties if t.pair == ("A04", "A05")).group_ids == ("G04", "G05", "G06")
    assert network.pair_total == 231 and network.pair_counts()[TieState.NOT_RECORDED] == 231 - 41
    from mares.networks.validate import validate

    assert validate(dataset).errors == ()  # the receipt table agrees with the derivation
    assert {tie.state for tie in network.ties} == {TieState.YES}  # nothing is removed, nothing denied


def test_contact_ids_decide_the_links_not_labels_or_names(tmp_path):
    """Whatever a source calls a contact, the ids link the tables: a group names ids, never labels."""
    dataset = _pilot_shape(tmp_path)
    assert {m.contact_id for m in dataset.memberships} <= set(dataset.contact_ids)
    assert all(c.contact_id.startswith("A") for c in dataset.contacts)
    assert not any("label" in vars(c) for c in dataset.contacts)  # the contact model has no name or label field
