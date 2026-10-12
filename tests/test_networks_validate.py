"""The validator: hard errors, warnings and open research questions are three different things."""

from __future__ import annotations

import hashlib

import pytest

import network_fixtures as fx
from mares.networks.model import Severity
from mares.networks.package import read_package
from mares.networks.validate import validate


def _codes(report, severity):
    return {f.code for f in report.of(severity)}


def _validate(tmp_path, **kwargs):
    groups, memberships = fx.standard_groups()
    contacts = kwargs.pop("contacts", fx.contact_rows(12, 8))
    params = {"contacts": contacts, "groups": groups, "memberships": memberships, "review_items": []}
    params.update(kwargs)
    return validate(read_package(fx.build_package(tmp_path / "p", **params)))


def test_a_clean_synthetic_package_passes_without_errors_or_warnings(tmp_path):
    report = _validate(tmp_path)
    assert report.errors == () and report.warnings == ()
    assert report.technical_status == "PASSED"


def test_validation_is_deterministic(tmp_path):
    first = _validate(tmp_path)
    second = validate(read_package(tmp_path / "p"))
    assert first == second


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (lambda rows: rows[1].update(contact_id="A01"), {"contact_id_duplicate"}),
        (lambda rows: rows[0].update(relation_codes="9"), {"unknown_code"}),
        (lambda rows: rows[0].update(contact_frequency_code="2|3"), {"multiple_codes_in_single_field"}),
        (lambda rows: rows[0].update(media_codes="1|7"), {"unknown_code"}),
        (lambda rows: rows[0].update(media_codes="1||2"), {"code_syntax"}),
        (lambda rows: rows[0].update(language_codes="1-9"), {"unknown_code"}),  # a range may not reach beyond the codebook
        (lambda rows: rows[0].update(residence_country_iso3="XYZ"), {"country_code_invalid"}),
        (lambda rows: rows[0].update(birth_country_iso3="Germany"), {"country_code_invalid"}),
        (lambda rows: rows[0].update(table_ring_near_value="6"), {"unknown_code"}),
        (lambda rows: rows[0].update(source_local_id="x"), {"source_position_invalid"}),
        (lambda rows: rows[2].update(source_block=rows[1]["source_block"], source_local_id=rows[1]["source_local_id"]), {"source_position_duplicate"}),
        (lambda rows: rows[0].update(source_case_label="0000-2"), {"case_label_mismatch"}),
    ],
)
def test_hard_errors_in_contacts(tmp_path, change, expected):
    rows = fx.contact_rows(12, 8)
    change(rows)
    report = _validate(tmp_path, contacts=rows)
    assert expected <= _codes(report, Severity.ERROR)
    assert report.technical_status == "FAILED"


def test_the_closeness_scale_is_the_codebook_scale_one_to_five(tmp_path):
    rows = fx.contact_rows(6)
    assert _codes(_validate(tmp_path, contacts=rows, groups=[], memberships=[]), Severity.ERROR) == set()
    rows[0]["table_ring_near_value"] = "0"
    assert "unknown_code" in _codes(_validate(tmp_path / "x", contacts=rows, groups=[], memberships=[]), Severity.ERROR)


def test_missing_values_are_warnings_or_silent_but_never_filled_in(tmp_path):
    rows = fx.contact_rows(12, 8)
    rows[0].update(table_ring_near_value="", residence_city="", residence_country_iso3="", function_codes="", birth_country_iso3="")
    report = _validate(tmp_path, contacts=rows)
    assert report.errors == ()
    missing = [f.message for f in report.warnings if f.code == "missing_expected" and f.subject == "A01"]
    assert any("table_ring_near_value" in m for m in missing) and any("residence_country_iso3" in m for m in missing)
    assert not any("function_codes" in m or "birth_country_iso3" in m for m in missing)  # optional: only counted
    completeness = {name: (filled, absent) for name, filled, absent in report.completeness}
    assert completeness["closeness"] == (11, 1) and completeness["function"][1] >= 1


def test_origin_text_without_iso_code_is_flagged_not_resolved(tmp_path):
    rows = fx.contact_rows(6)
    rows[2].update(birth_country_iso3="", birth_country_source="A/B")
    report = _validate(tmp_path, contacts=rows)
    assert any(f.code == "birth_country_unresolved" and f.subject == "A03" for f in report.warnings)


def test_place_and_country_that_contradict_are_a_warning(tmp_path):
    rows = fx.contact_rows(6)
    rows[0].update(residence_city="Marburg", residence_country_iso3="PER")
    assert any(f.code == "place_country_contradiction" for f in _validate(tmp_path, contacts=rows).warnings)


def test_group_and_membership_errors(tmp_path):
    groups, memberships = fx.standard_groups()
    bad = memberships + [
        {"group_id": "G09", "contact_id": "A01", "status": "confirmed", "derivable_edge": "yes", "source": "x"},
        {"group_id": "G01", "contact_id": "A99", "status": "confirmed", "derivable_edge": "yes", "source": "x"},
        {"group_id": "G01", "contact_id": "A01", "status": "confirmed", "derivable_edge": "yes", "source": "x"},
        {"group_id": "G01", "contact_id": "A05", "status": "confirmed", "derivable_edge": "no", "source": "x"},
        {"group_id": "G03", "contact_id": "A09", "status": "confirmed", "derivable_edge": "yes", "source": "x"},
        {"group_id": "G01", "contact_id": "A06", "status": "maybe", "derivable_edge": "no", "source": "x"},
    ]
    report = _validate(tmp_path, memberships=bad, edges=None)
    assert {
        "membership_group_unknown", "membership_contact_unknown", "membership_duplicate",
        "derivable_edge_inconsistent", "confirmed_member_in_unconfirmed_group", "membership_status_unknown",
    } <= _codes(report, Severity.ERROR)


def test_edge_table_is_a_receipt_that_must_match_the_derivation(tmp_path):
    groups, memberships = fx.standard_groups()
    edges = fx.derived_edges(groups, memberships)
    assert _codes(_validate(tmp_path, edges=edges), Severity.ERROR) == set()

    cases = {
        "edge_receipt_missing": edges[:-1],
        "edge_not_derivable": edges + [dict(edges[0], source_id="A08", target_id="A09", group_ids="G03")],
        "self_loop": edges + [dict(edges[0], source_id="A02", target_id="A02")],
        "duplicate_edge": edges + [dict(edges[0], source_id=edges[0]["target_id"], target_id=edges[0]["source_id"])],
        "edge_contact_unknown": edges + [dict(edges[0], source_id="A01", target_id="A77")],
        "edge_origin_mismatch": [dict(edges[0], group_ids="G02")] + edges[1:],
    }
    for code, table in cases.items():
        report = _validate(tmp_path / code, edges=table)
        assert code in _codes(report, Severity.ERROR), code
    report = _validate(tmp_path / "count", edges=edges, manifest={"edge_count_from_unambiguous_groups": 99})
    assert "edge_count_mismatch" in _codes(report, Severity.ERROR)


def test_an_edge_from_a_candidate_group_in_the_receipt_is_rejected(tmp_path):
    groups, memberships = fx.standard_groups()
    edges = fx.derived_edges(groups, memberships) + [
        {"source_id": "A06", "target_id": "A07", "relation": "know_each_other", "evidence": "x", "group_ids": "G03", "status": "x"}
    ]
    assert "edge_not_derivable" in _codes(_validate(tmp_path, edges=edges), Severity.ERROR)


def test_package_integrity_is_checked_against_the_checksum_list(tmp_path):
    directory = fx.build_package(tmp_path / "p")
    assert validate(read_package(directory)).errors == ()
    (directory / "groups.csv").write_bytes((directory / "groups.csv").read_bytes() + b"\n")
    assert "checksum_mismatch" in _codes(validate(read_package(directory)), Severity.ERROR)
    absent = fx.build_package(tmp_path / "q", checksums=False)
    assert "no_checksums" in _codes(validate(read_package(absent)), Severity.WARNING)


def test_manifest_contact_count_must_match(tmp_path):
    report = _validate(tmp_path, manifest={"contact_count": 13})
    assert "contact_count_mismatch" in _codes(report, Severity.ERROR)


def test_review_items_do_not_block_and_stay_separate_from_findings(tmp_path):
    report = _validate(tmp_path, review_items=[
        {"review_id": "R1", "priority": "high", "reference": "A03", "field": "f", "description": "open", "recommended_action": "manual_resolution"},
        {"review_id": "R2", "priority": "medium", "reference": "all", "field": "f", "description": "decided", "recommended_action": "rule_confirmed"},
        {"review_id": "R3", "priority": "medium", "reference": "A77", "field": "f", "description": "dangling", "recommended_action": "source_check"},
    ])
    assert report.errors == ()  # open questions never fail the validation
    questions = {q.question_id: q for q in report.open_questions}
    assert questions["R1"].state == "open" and questions["R1"].affected_contacts == ("A03",)
    assert questions["R2"].state == "decided_in_package"
    assert any(f.code == "review_reference_unknown" and f.subject == "R3" for f in report.warnings)
    assert report.open_count >= 2
    # the software's own open questions: case id, provenance, source validation
    assert {"SW-01", "SW-02", "SW-03"} <= set(questions)
    assert not any(q.question_id.startswith("R") for q in report.open_questions if q.origin == "software")


def test_a_flag_without_a_review_item_is_a_warning(tmp_path):
    rows = fx.contact_rows(6)
    rows[1]["review_flags"] = "SOME_FLAG;OTHER_FLAG"
    report = _validate(tmp_path, contacts=rows, review_items=[])
    assert any(f.code == "flag_without_review_item" and f.subject == "A02" for f in report.warnings)
    assert read_package(tmp_path / "p").contacts[1].review_flags == ("SOME_FLAG", "OTHER_FLAG")


def test_a_clarification_must_match_the_confirmed_members(tmp_path):
    groups, memberships = fx.standard_groups()
    directory = fx.build_package(tmp_path / "p", groups=groups, memberships=memberships, contacts=fx.contact_rows(12, 8))
    header = "clarification_id;source_date;group_id;member_contact_ids;relationship_rule;resolution;source_type\n"
    (directory / "source_clarifications.csv").write_text(header + "C01;0000-01-02;G02;A03|A04|A05;all_pairs_know_each_other;confirmed_by_user;user\n", encoding="utf-8")
    report = validate(read_package(directory))
    assert "clarification_mismatch" not in _codes(report, Severity.ERROR)
    assert any(f.code == "group_basis_user_statement" for f in report.of(Severity.INFO))
    (directory / "source_clarifications.csv").write_text(header + "C01;0000-01-02;G02;A03|A04;all_pairs_know_each_other;confirmed_by_user;user\n", encoding="utf-8")
    assert "clarification_mismatch" in _codes(validate(read_package(directory)), Severity.ERROR)


def test_validation_never_sets_a_quality_state():
    from mares.networks import validate as module

    assert not hasattr(module, "QualityState")  # a person decides data quality, not the validator


def test_checksums_use_real_sha256(tmp_path):
    directory = fx.build_package(tmp_path / "p")
    line = next(l for l in (directory / "SHA256SUMS.txt").read_text().splitlines() if l.endswith("manifest.json"))
    assert line.split()[0] == hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest()
