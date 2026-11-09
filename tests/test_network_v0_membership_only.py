"""Group rule 'membership_only' and intermediate scale codes (3.5) in network_v0 (synthetic packages only).

A survey that documents clusters without alter-alter ties keeps its groups, but no tie follows from them; a value
between two scale steps that the package codebook defines (3.5) is kept as it is, never rounded.
"""

from __future__ import annotations

import json

import pytest

import network_v0_fixtures as fx
from mares.network_v0 import standard
from mares.network_v0.build import build_network
from mares.network_v0.codes import parse_codes
from mares.network_v0.curation import read_curation
from mares.network_v0.figures.style import rc
from mares.network_v0.model import Severity
from mares.network_v0.package import read_package
from mares.network_v0.validate import validate
from mares.network_v1.figures.networks import g1_layout

BOOK = {**fx.CODEBOOK,
        "closeness_1_5": {**fx.CODEBOOK["closeness_1_5"], "3.5": "zwischen mittel und nah"},
        "contact_frequency": {**fx.CODEBOOK["contact_frequency"], "3.5": "mehrmals im Monat – wöchentlich"}}


def _members_only(group_id, ids):
    return [{**m, "derivable_edge": "no"} for m in fx.members(group_id, ids)]


def _package(tmp_path, *, derivable="no"):
    rows = fx.contact_rows(6)
    rows[0]["table_ring_near_value"] = "3.5"
    rows[1]["contact_frequency_code"] = "3.5"
    groups = [fx.group("C01"), fx.group("C02")]
    memberships = fx.members("C01", ["A01", "A02", "A03"]) + fx.members("C02", ["A03", "A04"])
    if derivable == "no":
        memberships = [{**m, "derivable_edge": "no"} for m in memberships]
    return read_package(fx.build_package(tmp_path / "p", contacts=rows, groups=groups, memberships=memberships,
                                         edges=None, codebook=BOOK))


def _curation(tmp_path, rule):
    path = tmp_path / "curation.json"
    path.write_text(json.dumps({
        "format": "mares-network-curation/v0-draft", "source_label": fx.LABEL, "made_on": "0000-01-02", "made_by": "synthetic",
        "survey": {"elicitation": "not_stated", "documentation": "group_outlines", "group_rule": rule,
                   "pair_coverage": "not_established", "basis": "synthetic statement"},
        "dispositions": []}), encoding="utf-8")
    return read_curation(path)


def test_a_decimal_code_parses_and_stays_unrounded():
    assert parse_codes("3.5").codes == ("3.5",)
    assert parse_codes("2-6").codes == ("2", "3", "4", "5", "6")  # ranges unchanged


def test_membership_only_keeps_groups_but_derives_no_tie(tmp_path):
    data = _package(tmp_path)
    network = build_network(data, clique_rule=False)
    assert not network.positive_ties
    assert tuple(dict(network.confirmed_groups)["C01"]) == ("A01", "A02", "A03")
    assert network.groups_of("A03") == ("C01", "C02")  # several memberships stay several
    assert build_network(data).positive_ties  # the clique rule stays the default


def test_overlapping_groups_do_not_merge(tmp_path):
    data = _package(tmp_path)  # C01 = A01, A02, A03; C02 = A03, A04; A03 is in both
    pairs = {tuple(sorted(tie.pair)) for tie in build_network(data).positive_ties}
    assert ("A03", "A04") in pairs and ("A01", "A03") in pairs  # the shared member knows both groups
    assert ("A01", "A04") not in pairs and ("A02", "A04") not in pairs  # across groups: unknown, not merged


def test_the_validator_follows_the_curations_group_rule(tmp_path):
    data = _package(tmp_path)
    report = validate(data, curation=_curation(tmp_path, "membership_only"))
    assert not [f for f in report.findings if f.severity is Severity.ERROR]
    clique = validate(data, curation=_curation(tmp_path, "all_members_know_each_other"))
    assert any(f.code == "derivable_edge_inconsistent" for f in clique.findings)  # 'no' contradicts the clique rule


def test_a_membership_package_claiming_derivable_ties_is_an_error(tmp_path):
    data = _package(tmp_path, derivable="yes")
    report = validate(data, curation=_curation(tmp_path, "membership_only"))
    assert any(f.code == "derivable_edge_inconsistent" for f in report.findings)


def test_intermediate_steps_come_from_the_codebook(tmp_path):
    data = _package(tmp_path)
    ctx = standard.figure_context(data, build_network(data, clique_rule=False), case_code="0000")
    scheme = ctx.scheme
    assert [r[0] for r in scheme.closeness_rows(False)] == [5.0, 4.0, 3.5, 3.0, 2.0, 1.0]
    assert scheme.closeness_rows(False)[2][1] == "3,5 · zwischen mittel und nah"
    assert [r[0] for r in scheme.frequency_rows()] == ["5", "4", "3.5", "3", "2", "1"]
    rings = scheme.g1_rings()
    assert (2.5, None, False) in rings  # dashed, unlabelled ring between 3 and 4
    assert g1_layout(ctx)["A01"] is not None and scheme.closeness(ctx.case.contact("A01")) == 3.5
    assert not ctx.derived.confirmed_edges


def test_without_ties_no_figure_explains_a_tie_line(tmp_path):
    data = _package(tmp_path)
    ctx = standard.figure_context(data, build_network(data, clique_rule=False), case_code="0000")
    with rc():
        for code in ("G2", "G3"):
            figure = next(s for s in standard.V1_FIGURES if s.code == code).draw(ctx)
            shown = [t.get_text() for t in figure.findobj(lambda a: hasattr(a, "get_text") and a.get_text())]
            assert "bestätigte Verbindung" not in shown and "innerhalb eines Bereichs" not in shown
