"""network_v1 validation: errors, warnings and permitted gaps."""

from __future__ import annotations

import json

import pytest

from mares.network_v1.derive import CONFLICT, pair_key
from network_v1_fixtures import append, check, codes_of, copy_002, edit, read_rows, set_metadata, write_rows


@pytest.fixture
def case(tmp_path):
    return copy_002(tmp_path)


def test_the_unchanged_copy_has_no_errors(case):
    assert not check(case).errors


@pytest.mark.parametrize("table, key, column, value, code", [
    ("contacts.csv", "A03", "closeness", "5", "invalid_closeness"),
    ("contacts.csv", "A03", "closeness", "4,5", "invalid_closeness"),
    ("contacts.csv", "A03", "relation_type", "7", "invalid_relation_type"),
    ("contacts.csv", "A03", "relation_type", "1, 3", "invalid_relation_type"),
    ("contacts.csv", "A03", "functions", "0, 1", "invalid_functions"),
    ("contacts.csv", "A03", "contact_frequency", "6", "invalid_contact_frequency"),
    ("contacts.csv", "A03", "residence_country_iso3", "XYZ", "country_code"),
    ("contacts.csv", "A03", "label", "Kontakt 0171 2345678", "label_contact_data"),
    ("communication.csv", "A05", "language_use", "4", "language_use_not_spoken"),
    ("communication.csv", "A05", "communication_forms", "1|2", "invalid_communication_forms"),
    ("communication.csv", "A05", "languages", "1, KA", "invalid_languages"),
])
def test_invalid_values_are_errors(case, table, key, column, value, code):
    edit(case, table, key, column, value)
    result = check(case)
    assert code in codes_of(result, "error"), result.findings


def test_duplicate_and_malformed_contact_ids(case):
    rows = read_rows(case, "contacts.csv")
    write_rows(case, "contacts.csv", rows + [dict(rows[0])])
    assert "duplicate_contact" in codes_of(check(case), "error")
    edit(case, "contacts.csv", "A02", "contact_id", "B2")
    assert "contact_id" in codes_of(check(case), "error")


def test_unknown_contacts_in_groups_and_pairs(case):
    append(case, "group_memberships.csv", {"group_id": "C01", "contact_id": "A99"})
    append(case, "alter_connections.csv", {"contact_a": "A01", "contact_b": "A77", "status": "1", "source": "", "comment": ""})
    append(case, "group_memberships.csv", {"group_id": "C09", "contact_id": "A01"})
    found = [f for f in check(case).errors]
    assert {f.code for f in found} >= {"unknown_contact", "unknown_group"}
    assert sum(f.code == "unknown_contact" for f in found) == 2


def test_a_contradiction_is_reported_never_resolved(case):
    # C01 is T (all connected); an explicit 0 contradicts it
    append(case, "alter_connections.csv", {"contact_a": "A01", "contact_b": "A02", "status": "0", "source": "", "comment": ""})
    result = check(case)
    assert "pair_conflict" in codes_of(result, "error")
    assert result.derived.pairs[pair_key("A01", "A02")].state == CONFLICT


def test_an_unknown_statement_does_not_contradict(case):
    append(case, "alter_connections.csv", {"contact_a": "A01", "contact_b": "A02", "status": "?", "source": "", "comment": ""})
    assert not check(case).errors


def test_self_pairs_and_invalid_status(case):
    append(case, "alter_connections.csv", {"contact_a": "A01", "contact_b": "A01", "status": "1", "source": "", "comment": ""})
    append(case, "alter_connections.csv", {"contact_a": "A01", "contact_b": "A05", "status": "ja", "source": "", "comment": ""})
    assert {"self_pair", "invalid_status"} <= codes_of(check(case), "error")


def test_missing_answers_are_warnings_and_do_not_stop(case):
    edit(case, "contacts.csv", "A03", "closeness", "")
    edit(case, "groups.csv", "C02", "connection_status", "", key="group_id")
    edit(case, "groups.csv", "C02", "belonging", "", key="group_id")
    edit(case, "communication.csv", "A05", "language_use", "")
    result = check(case)
    assert not result.errors
    assert {"missing_closeness", "group_status_missing", "group_belonging_missing", "language_use_missing"} <= codes_of(result, "warning")


def test_answered_non_answers_are_no_warning(case):
    edit(case, "contacts.csv", "A03", "closeness", "KA")
    assert "missing_closeness" not in codes_of(check(case))


def test_single_language_with_language_use_is_a_warning(case):
    edit(case, "communication.csv", "A01", "language_use", "M")
    assert "language_use_single" in codes_of(check(case), "warning")


def test_a_partial_group_without_single_statements_is_noted(case):
    rows = [r for r in read_rows(case, "alter_connections.csv") if r["source"] != "C02"]
    write_rows(case, "alter_connections.csv", rows)
    assert "group_partial_unstated" in codes_of(check(case), "note")


def test_small_group_and_missing_communication(case):
    rows = [r for r in read_rows(case, "group_memberships.csv") if not (r["group_id"] == "C05" and r["contact_id"] != "A27")]
    write_rows(case, "group_memberships.csv", rows)
    write_rows(case, "communication.csv", [r for r in read_rows(case, "communication.csv") if r["contact_id"] != "A07"])
    assert {"group_small", "communication_missing"} <= codes_of(check(case), "warning")


# ------------------------------------------------------------------------------------- v0 / v1 and metadata ---
def test_v0_columns_and_files_are_rejected(case):
    rows = read_rows(case, "contacts.csv")
    for r in rows:
        r["table_ring_near_value"] = "3"
    write_rows(case, "contacts.csv", rows)
    (case / "data" / "manifest.json").write_text("{}", encoding="utf-8")
    assert {"v0_columns", "v0_file"} <= codes_of(check(case), "error")


def test_v0_dataset_version_is_rejected(case):
    set_metadata(case, dataset_version="network_v0")
    errors = [f for f in check(case).errors if f.code == "dataset_version"]
    assert errors and "v0" in errors[0].message


@pytest.mark.parametrize("changes, code", [
    ({"empirical_analysis_eligible": True}, "eligibility"),
    ({"empirical_analysis_eligible": "no"}, "eligibility"),
    ({"case_type": "pilot"}, "provenance"),
    ({"provenance": "invented"}, "provenance"),
    ({"case_type": "experiment"}, "case_type"),
    ({"case_code": "002_other"}, "case_code_folder"),
    ({"format": "mares-network-package/v0-draft"}, "metadata_format"),
    ({"field_origins": {"contacts.closeness": "guessed"}}, "field_origins"),
])
def test_inconsistent_metadata_are_errors(case, changes, code):
    set_metadata(case, **changes)
    assert code in codes_of(check(case), "error")


def test_a_regular_case_belongs_under_cases_and_a_case_under_cases_must_be_regular(tmp_path):
    case = copy_002(tmp_path, kind="cases")
    assert "case_folder" in codes_of(check(case), "error")


def test_empirical_cases_need_survey_documentation(tmp_path):
    case = copy_002(tmp_path, name="003_pilot")
    set_metadata(case, case_type="pilot", provenance="survey", empirical_analysis_eligible=True, survey={})
    result = check(case)
    assert not result.errors
    assert "survey_metadata" in codes_of(result, "warning")


def test_a_missing_file_is_a_structural_error(case):
    (case / "data" / "groups.csv").unlink()
    result = check(case)
    assert "file_missing" in codes_of(result, "error") and result.derived is None


def test_a_semicolon_value_must_be_quoted(case):
    text = (case / "data" / "communication.csv").read_text(encoding="utf-8")
    (case / "data" / "communication.csv").write_text(text.replace('"M;S"', "M;S", 1), encoding="utf-8")
    assert "row_too_long" in codes_of(check(case), "error")


def test_metadata_must_be_json(case):
    (case / "data" / "metadata.json").write_text("{not json", encoding="utf-8")
    assert "metadata_json" in codes_of(check(case), "error")


def test_context_rules(case):
    append(case, "context.csv", {"field": "age", "value": "32", "comment": ""})
    append(case, "context.csv", {"field": "lieblingsfarbe", "value": "blau", "comment": ""})
    append(case, "context.csv", {"field": "language_use", "value": "Deutsch", "comment": ""})
    result = check(case)
    assert [f.code for f in result.warnings if f.code.startswith("context")].count("context_field") == 2
    assert "context_repeated" in codes_of(result, "warning")
    assert json.dumps(result.to_dict())  # serialisable
