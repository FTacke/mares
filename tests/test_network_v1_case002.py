"""Test case 002 (fully synthetic): expected properties as machine-checkable assertions.

The constellation is invented; the patterns asserted here are test assumptions, not research hypotheses.
"""

from __future__ import annotations

from collections import Counter

import pytest

from mares.network_v1.case import is_empirical, read_case
from mares.network_v1.codes import Missing
from mares.network_v1.derive import CONFIRMED, DENIED, UNKNOWN, pair_key
from mares.network_v1.places import Area
from mares.network_v1.testcases import synthetic_source
from mares.network_v1.validate import PASSED_WITH_WARNINGS, validate


@pytest.fixture(scope="module")
def case():
    return read_case(synthetic_source())


@pytest.fixture(scope="module")
def checked(case):
    return validate(case)


def state(checked, a, b):
    pair = checked.derived.pairs.get(pair_key(a, b))
    return pair.state if pair else UNKNOWN


def test_metadata_mark_a_synthetic_test_case_that_never_counts_empirically(case):
    m = case.metadata
    assert (m["dataset_version"], m["case_type"], m["provenance"], m["empirical_analysis_eligible"]) == ("network_v1", "test", "fully_synthetic", False)
    assert not is_empirical(m)
    assert m["survey"]["survey_date"].startswith("0000")


def test_valid_with_exactly_the_intended_findings(checked):
    assert checked.status == PASSED_WITH_WARNINGS
    assert [f.code for f in checked.warnings] == ["residence_unresolved"]  # A22 'Neustadt': ambiguous, not guessed
    assert [f.code for f in checked.notes] == ["pair_repeated"]  # A12-A14 stated twice, identically


def test_size_and_groups(case):
    assert len(case.contacts) == 32 and len(case.groups) == 5
    assert {g.status.value for g in case.groups} == {"T", "P", "N", "NS"}
    assert sorted(len(case.members(g.id)) for g in case.groups) == [3, 4, 5, 6, 7]
    assert {g.belonging.value for g in case.groups} == {"1", "2", "3", "5"}
    assert {c for c in case.contact_ids if len(case.groups_of(c)) > 1} == {"A09", "A12"}  # overlapping memberships


def test_every_display_area_is_used(checked):
    counts = Counter(r.area for r in checked.derived.residence.values())
    assert counts == {Area.MARBURG: 11, Area.MITTELHESSEN: 7, Area.GERMANY_OTHER: 3, Area.EUROPE_OTHER: 3, Area.OUTSIDE_EUROPE: 7, Area.UNRESOLVED: 1}
    assert checked.derived.residence["A25"].area is Area.MARBURG  # 'Wehrda' via places.csv
    assert checked.derived.residence["A22"].area is Area.UNRESOLVED


def test_pair_coverage(checked):
    cov = checked.derived.coverage
    assert (cov.pairs, cov.confirmed, cov.denied, cov.stated_unknown, cov.conflicts) == (496, 35, 7, 2, 0)
    assert cov.unknown == 496 - 35 - 7


def test_group_rules(checked):
    assert state(checked, "A01", "A04") == CONFIRMED  # C01 T
    assert any(s.startswith("C01:T") for s in checked.derived.pairs[pair_key("A01", "A04")].sources)
    assert state(checked, "A13", "A16") == CONFIRMED  # C03 T
    assert state(checked, "A27", "A28") == DENIED  # C05 N
    assert state(checked, "A09", "A11") == DENIED  # C02 P, explicitly denied
    assert state(checked, "A08", "A10") == CONFIRMED  # C02 P, explicitly confirmed
    assert state(checked, "A10", "A26") == UNKNOWN  # C02 P, explicitly '?'
    assert state(checked, "A10", "A12") == UNKNOWN  # C02 P, not stated: same group is no connection
    assert state(checked, "A17", "A18") == UNKNOWN  # C04 NS, not stated
    assert state(checked, "A17", "A19") == CONFIRMED  # C04 NS, explicitly confirmed
    assert state(checked, "A09", "A12") == UNKNOWN  # two overlapping members of C02 (P)


def test_connections_across_groups_and_to_ungrouped_contacts(checked):
    assert state(checked, "A06", "A07") == CONFIRMED  # both ungrouped
    assert state(checked, "A03", "A31") == CONFIRMED  # group member and ungrouped
    assert state(checked, "A23", "A24") == DENIED


def test_closeness_with_half_steps_and_missing_answer(case):
    values = Counter(c.closeness.value for c in case.contacts if c.closeness.recorded)
    assert {"1.5", "2.5", "3.5"} <= set(values)
    assert case.contact("A02").closeness.raw == "1,5"
    assert case.contact("A22").closeness.missing is Missing.NO_ANSWER


def test_languages_and_language_use(case):
    b = case.communication
    assert b["A06"].language_use.values == ("M", "S") and b["A11"].language_use.values == ("M",) and b["A10"].language_use.values == ("S",)
    assert b["A01"].languages.values == ("1",) and b["A01"].language_use.missing is Missing.NOT_COLLECTED  # rule-conform empty
    assert b["A28"].other_languages.values == ("Französisch",)
    assert sum(len(x.languages.values) > 1 for x in b.values()) >= 10


def test_communication_mixes_analogue_and_digital(case):
    forms = Counter(f for x in case.communication.values() for f in x.forms.values)
    assert forms["1"] >= 15 and forms["2"] >= 5 and forms["5"] >= 15 and forms["6"] >= 1


def test_functions_several_and_none(case):
    assert case.contact("A06").functions.values == ("1", "2", "3", "4")
    assert case.contact("A20").functions.values == ("0",)
    assert case.contact("A32").functions.missing is Missing.NO_ANSWER


def test_invented_pattern_close_transnational_and_less_close_local_ties(case, checked):
    """Test assumption of the constellation: the very close contacts include several abroad; contacts in
    Marburg and Mittelhessen are on average less close than those outside Europe."""
    area = {c: r.area for c, r in checked.derived.residence.items()}
    close_abroad = [c.id for c in case.contacts if c.closeness.recorded and float(c.closeness.value) <= 1.5
                    and area[c.id] in (Area.EUROPE_OTHER, Area.OUTSIDE_EUROPE)]
    assert len(close_abroad) >= 4

    def mean(areas):
        vals = [float(c.closeness.value) for c in case.contacts if c.closeness.recorded and area[c.id] in areas]
        return sum(vals) / len(vals)

    assert mean({Area.MARBURG, Area.MITTELHESSEN}) > mean({Area.OUTSIDE_EUROPE})


def test_context_sheet_keeps_multiple_answers_as_rows(case):
    fields = Counter(f for f, *_ in case.context)
    assert fields["daily_languages"] == 3 and fields["migration_context"] == 2 and fields["age"] == 1
