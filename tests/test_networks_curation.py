"""Curation: documented statements about a package -- survey method, pair coverage, review categories.

Original delivery files are never changed; what a person clarifies later is a separate, hashed file.
"""

from __future__ import annotations

import json

import pytest

import network_fixtures as fx
from mares.networks.analysis import descriptive_tables, survey_status
from mares.networks.analysis import AnalysisParams
from mares.networks.build import build_network
from mares.networks.curation import NO_CURATION, CurationError, ReviewCategory, read_curation
from mares.networks.model import Severity, TieBasis, TieState
from mares.networks.package import read_package
from mares.networks.validate import validate


def curation_file(tmp_path, **overrides):
    document = {
        "format": "mares-network-curation/v0-draft",
        "source_label": fx.LABEL,
        "applies_to_package_version": "0.0-synthetic",
        "made_on": "0000-01-02",
        "made_by": "synthetic test",
        "survey": {
            "elicitation": "asked_per_pair",
            "documentation": "group_outlines",
            "group_rule": "all_members_know_each_other",
            "pair_coverage": "not_established",
            "basis": "synthetic statement of the project lead",
        },
        "dispositions": [
            {"ref": "RT01", "category": "documented_ambiguity", "decided_by": "project_lead", "basis": "b", "note": "raw value kept"},
            {"ref": "RT02", "category": "resolved", "decided_by": "project_lead", "basis": "b"},
            {"ref": "flag:A04:SOME_FLAG", "category": "accepted_imprecision", "decided_by": "agent_proposal", "basis": "b"},
        ],
    }
    document.update(overrides)
    path = tmp_path / "curation.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def package(tmp_path, *, flag=False):
    groups, memberships = fx.standard_groups()
    rows = fx.contact_rows(12, 8)
    rows[2]["review_flags"] = "TEST_FLAG"
    if flag:
        rows[3]["review_flags"] = "SOME_FLAG"
    reviews = [
        {"review_id": "RT01", "priority": "high", "reference": "A03", "field": "f", "description": "open", "recommended_action": "source_check"},
        {"review_id": "RT02", "priority": "medium", "reference": "all", "field": "f", "description": "rule", "recommended_action": "manual_resolution"},
        {"review_id": "RT03", "priority": "high", "reference": "A05", "field": "f", "description": "undecided", "recommended_action": "manual_resolution"},
    ]
    return read_package(fx.build_package(tmp_path / "p", contacts=rows, groups=groups, memberships=memberships, review_items=reviews))


def test_a_curation_file_is_read_and_hashed(tmp_path):
    curation = read_curation(curation_file(tmp_path))
    assert curation.survey.elicitation == "asked_per_pair" and curation.survey.documentation == "group_outlines"
    assert curation.survey.group_rule == "all_members_know_each_other" and not curation.survey.coverage_complete
    assert curation.disposition("RT01").category is ReviewCategory.DOCUMENTED_AMBIGUITY
    assert curation.disposition("flag:A04:SOME_FLAG").flag == ("A04", "SOME_FLAG")
    assert len(curation.sha256) == 64
    assert NO_CURATION.survey.elicitation == "not_stated" and NO_CURATION.sha256 is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"format": "other/v1"},
        {"survey": {"elicitation": "guessed", "documentation": "group_outlines"}},
        {"survey": {"elicitation": "asked_per_pair", "documentation": "group_outlines"}},  # a method statement needs its basis
        {"survey": {"pair_coverage": "complete"}},  # so does a coverage statement
        {"survey": {"elicitation": "asked_per_pair", "documentation": "group_outlines", "basis": "b", "pair_coverage": "mostly"}},
        {"dispositions": [{"ref": "R1", "category": "fixed", "decided_by": "project_lead", "basis": "b"}]},
        {"dispositions": [{"ref": "R1", "category": "resolved", "decided_by": "somebody", "basis": "b"}]},
        {"dispositions": [{"ref": "R1", "category": "resolved", "decided_by": "project_lead"}]},
        {"dispositions": [{"ref": "R1", "category": "resolved", "decided_by": "project_lead", "basis": "b"}] * 2},
        {"dispositions": [{"ref": "not a ref!", "category": "resolved", "decided_by": "project_lead", "basis": "b"}]},
        {"made_on": ""},
    ],
)
def test_a_malformed_curation_is_refused(tmp_path, overrides):
    with pytest.raises(CurationError):
        read_curation(curation_file(tmp_path, **overrides))


def test_unreadable_curation_is_an_error(tmp_path):
    path = tmp_path / "curation.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(CurationError):
        read_curation(path)


def test_review_hints_are_in_four_categories_and_only_one_is_open(tmp_path):
    dataset = package(tmp_path, flag=True)
    report = validate(dataset, curation=read_curation(curation_file(tmp_path)))
    categories = {q.question_id: q.category for q in report.open_questions}
    assert categories["RT01"] is ReviewCategory.DOCUMENTED_AMBIGUITY
    assert categories["RT02"] is ReviewCategory.RESOLVED
    assert categories["FLAG-A04"] is ReviewCategory.ACCEPTED_IMPRECISION
    assert categories["RT03"] is ReviewCategory.OPEN_DECISION  # no statement: stays open, never closed by default
    assert {c for c in ReviewCategory} == {ReviewCategory.OPEN_DECISION, ReviewCategory.DOCUMENTED_AMBIGUITY, ReviewCategory.ACCEPTED_IMPRECISION, ReviewCategory.RESOLVED}
    open_ids = {q.question_id for q in report.open_questions if q.is_open}
    assert open_ids == {"RT03", "SW-01", "SW-02", "SW-03"} and report.open_count == 4
    by_category = report.by_category()
    assert [q.question_id for q in by_category[ReviewCategory.DOCUMENTED_AMBIGUITY]] == ["RT01"]
    decided = {q.question_id: q.decided_by for q in report.open_questions}
    assert decided["RT01"] == "project_lead" and decided["FLAG-A04"] == "agent_proposal" and decided["RT03"] == "package"


def test_without_curation_the_packages_own_action_is_the_fallback_and_nothing_is_closed(tmp_path):
    report = validate(package(tmp_path))
    categories = {q.question_id: q.category for q in report.open_questions}
    assert categories["RT01"] is ReviewCategory.OPEN_DECISION and categories["RT02"] is ReviewCategory.OPEN_DECISION
    groups, memberships = fx.standard_groups()
    reviews = [
        {"review_id": "R1", "priority": "x", "reference": "all", "field": "f", "description": "d", "recommended_action": "rule_confirmed"},
        {"review_id": "R2", "priority": "x", "reference": "all", "field": "f", "description": "d", "recommended_action": "accepted_as_approximate"},
    ]
    dataset = read_package(fx.build_package(tmp_path / "q", contacts=fx.contact_rows(12, 8), groups=groups, memberships=memberships, review_items=reviews))
    fallback = {q.question_id: q.category for q in validate(dataset).open_questions}
    assert fallback["R1"] is ReviewCategory.RESOLVED and fallback["R2"] is ReviewCategory.ACCEPTED_IMPRECISION


def test_a_flag_covered_by_the_curation_is_no_longer_a_warning(tmp_path):
    dataset = package(tmp_path, flag=True)
    assert any(f.code == "flag_without_review_item" and f.subject == "A04" for f in validate(dataset).warnings)
    report = validate(dataset, curation=read_curation(curation_file(tmp_path)))
    assert not any(f.code == "flag_without_review_item" for f in report.warnings)


def test_curation_that_does_not_fit_the_package_is_reported(tmp_path):
    dataset = package(tmp_path)
    wrong_case = validate(dataset, curation=read_curation(curation_file(tmp_path, source_label="0000-9")))
    assert "curation_label_mismatch" in {f.code for f in wrong_case.errors}
    other_version = validate(dataset, curation=read_curation(curation_file(tmp_path, applies_to_package_version="9.9")))
    assert "curation_version_mismatch" in {f.code for f in other_version.warnings}
    dangling = [{"ref": "R77", "category": "resolved", "decided_by": "project_lead", "basis": "b"}]
    stale = validate(dataset, curation=read_curation(curation_file(tmp_path, dispositions=dangling)))
    assert any(f.code == "curation_ref_unknown" and f.subject == "R77" for f in stale.warnings)


def test_the_survey_method_is_reported_and_coverage_is_not_assumed(tmp_path):
    dataset = package(tmp_path)
    curation = read_curation(curation_file(tmp_path))
    report = validate(dataset, curation=curation)
    codes = {f.code for f in report.of(Severity.INFO)}
    assert {"survey_method", "pair_coverage_not_established"} <= codes
    status = survey_status(dataset, build_network(dataset), curation)
    assert status.elicitation == "asked_per_pair" and status.documentation == "group_outlines"
    assert status.pair_coverage == "not_established" and status.completeness == "partial_unknown_not_absent"
    note = status.structure_note()
    assert "im Interview erfragt" in note and "Gruppenumrandungen dokumentiert" in note and "nicht belegt" in note
    assert "unbekannt" in note


def test_elicitation_and_documentation_form_are_different_statements(tmp_path):
    dataset = package(tmp_path)
    asked = read_curation(curation_file(tmp_path))
    status = survey_status(dataset, build_network(dataset), asked)
    document = status.to_dict()
    assert document["alter_alter_elicitation"] == "asked_per_pair" and document["alter_alter_documentation"] == "group_outlines"


# ------------------------------------------------------------ pair coverage ------------------------


def test_missing_pairs_are_denied_only_when_the_survey_covers_every_pair(tmp_path):
    dataset = package(tmp_path)
    partial = build_network(dataset)
    assert partial.state("A01", "A09") is TieState.NOT_RECORDED and not partial.is_complete()

    covered = build_network(dataset, coverage_complete=True)
    assert covered.state("A01", "A09") is TieState.NO  # now an explicit denial
    assert covered.state("A01", "A02") is TieState.YES  # nothing confirmed is removed
    assert covered.is_complete() and covered.coverage_complete
    counts = covered.pair_counts()
    assert counts[TieState.YES] == 9 and counts[TieState.NO] == 66 - 9 and counts[TieState.NOT_RECORDED] == 0
    assert {t.basis for t in covered.ties if t.state is TieState.NO} == {TieBasis.COVERAGE}
    assert {t.pair for t in partial.positive_ties} == {t.pair for t in covered.positive_ties}  # the same confirmed ties


def test_structure_measures_exist_only_with_complete_coverage(tmp_path):
    dataset = package(tmp_path)
    keys = lambda network, curation=NO_CURATION: {t.key for t in descriptive_tables(dataset, network, AnalysisParams(), curation)}
    assert "structure" not in keys(build_network(dataset))

    complete = read_curation(curation_file(tmp_path, survey={
        "elicitation": "asked_per_pair", "documentation": "group_outlines", "pair_coverage": "complete", "basis": "synthetic: every pair asked"}))
    network = build_network(dataset, coverage_complete=complete.survey.coverage_complete)
    tables = {t.key: t for t in descriptive_tables(dataset, network, AnalysisParams(), complete)}
    assert "structure" in tables
    values = dict(tables["structure"].rows)
    assert values["Beziehungen (ja)"] == 9 and values["Mögliche Paare"] == 66
    assert values["Dichte (Beziehungen / mögliche Paare)"] == f"{9 / 66:.3f}"
    assert values["Komponenten"] == 7 and values["Größen der Komponenten"].startswith("5")  # {A01..A05}, {A10,A11}, five singles
    assert "Einzelfall" in tables["structure"].note and "keine Verallgemeinerung" in tables["structure"].note
    status = survey_status(dataset, network, complete)
    assert status.completeness == "complete" and status.denied_pairs == 57 and status.to_dict()["refused_metrics"] == []


def test_without_coverage_the_refused_metrics_are_listed(tmp_path):
    dataset = package(tmp_path)
    status = survey_status(dataset, build_network(dataset), read_curation(curation_file(tmp_path)))
    document = status.to_dict()
    assert document["structural_metrics_computed"] is False and "Netzwerkdichte" in document["refused_metrics"]
