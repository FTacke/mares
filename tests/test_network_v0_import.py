"""Package import: encodings, identities, contact numbering and variable contact counts."""

from __future__ import annotations

import pytest

import network_v0_fixtures as fx
from mares.core import ids
from mares.network_v0 import identity
from mares.network_v0.package import PackageError, read_package
from mares.network_v0.validate import validate


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
@pytest.mark.parametrize("bom", [True, False])
def test_import_reads_bom_and_line_ending_variants(tmp_path, newline, bom):
    groups, memberships = fx.standard_groups()
    directory = fx.build_package(
        tmp_path / "p", contacts=fx.contact_rows(12, 8), groups=groups, memberships=memberships, newline=newline, bom=bom
    )
    dataset = read_package(directory)
    assert len(dataset.contacts) == 12 and dataset.case.source_label == fx.LABEL
    assert validate(dataset).errors == ()


def test_codes_attributes_and_missing_values_are_kept_as_delivered(tmp_path):
    rows = fx.contact_rows(4)
    rows[0].update(media_codes="1-3", language_codes="1|2", birth_country_iso3="", residence_city="")
    dataset = read_package(fx.build_package(tmp_path / "p", contacts=rows))
    first = dataset.contacts[0]
    assert first.code_list("media") == ("1", "2", "3")  # the range is expanded ...
    assert any(f.code == "range_expanded" for f in dataset.import_findings)  # ... and says so
    assert first.code_list("language") == ("1", "2")
    assert "birth_country" not in first.text and "residence_city" not in first.text  # empty stays absent
    assert first.single("closeness") == "1"
    assert dataset.contacts[1].single("language_mode") == "4"


def test_source_position_is_kept_and_canonical_ids_run_on_across_sheets(tmp_path):
    rows = fx.contact_rows(22)  # sheets of 15 and 7: the second sheet restarts at A01
    dataset = read_package(fx.build_package(tmp_path / "p", contacts=rows))
    by_id = {c.contact_id: c for c in dataset.contacts}
    assert (by_id["A15"].source_block, by_id["A15"].source_local_id) == ("1", "A15")
    assert (by_id["A16"].source_block, by_id["A16"].source_local_id) == ("2", "A01")
    assert (by_id["A22"].source_block, by_id["A22"].source_local_id) == ("2", "A07")
    assert validate(dataset).errors == ()


def test_canonical_ids_follow_source_order_not_local_numbers():
    positions = [("1", f"A{i:02d}") for i in range(1, 16)] + [("2", f"A{i:02d}") for i in range(1, 8)]
    assert identity.canonical_contact_ids(positions) == [f"A{i:02d}" for i in range(1, 23)]
    # rows given in a different order still get the id of their rank
    shuffled = [("2", "A02"), ("1", "A01"), ("1", "A02"), ("2", "A01")]
    assert identity.canonical_contact_ids(shuffled) == ["A04", "A01", "A02", "A03"]
    assert identity.canonical_contact_ids([("1", "A01")]) == ["A01"]
    with pytest.raises(ValueError):
        identity.canonical_contact_ids([("1", "A01"), ("1", "A01")])
    with pytest.raises(ValueError):
        identity.canonical_contact_ids([("1", "x1")])


@pytest.mark.parametrize("count", [1, 3, 15, 16, 22, 99, 100, 150])
def test_there_is_no_upper_bound_on_the_number_of_contacts(tmp_path, count):
    dataset = read_package(fx.build_package(tmp_path / "p", contacts=fx.contact_rows(count)))
    assert len(dataset.contacts) == count
    report = validate(dataset)
    assert report.errors == (), [f.message for f in report.errors]
    assert dataset.contacts[-1].contact_id == ids.contact_id(count)


def test_wrong_canonical_id_is_an_error(tmp_path):
    rows = fx.contact_rows(5)
    rows[4]["contact_id"] = "A07"  # position 5 must be A05
    report = validate(read_package(fx.build_package(tmp_path / "p", contacts=rows)))
    assert "canonical_id_mismatch" in {f.code for f in report.errors}


def test_structural_problems_raise_package_errors(tmp_path):
    directory = fx.build_package(tmp_path / "p")
    (directory / "groups.csv").unlink()
    with pytest.raises(PackageError, match="groups.csv"):
        read_package(directory)
    directory = fx.build_package(tmp_path / "q")
    (directory / "contacts.csv").write_text("contact_id,source_block\nA01,1\n", encoding="utf-8")
    with pytest.raises(PackageError, match="separator|required column"):
        read_package(directory)
    directory = fx.build_package(tmp_path / "r")
    (directory / "contacts.csv").write_bytes(b"source_case_label;contact_id\n\xff\xfe;A01\n")
    with pytest.raises(PackageError, match="UTF-8"):
        read_package(directory)
    with pytest.raises(PackageError):
        read_package(tmp_path / "does-not-exist")


def test_source_label_is_not_a_case_id(tmp_path):
    dataset = read_package(fx.build_package(tmp_path / "p"))
    assert dataset.case.source_label == "0000-1" and dataset.case.canonical_case_id is None
    registered = read_package(fx.build_package(tmp_path / "q", manifest={"canonical_case_id": "MARES-0000-001"}))
    assert registered.case.canonical_case_id == "MARES-0000-001"
    with pytest.raises(PackageError):
        read_package(fx.build_package(tmp_path / "r", manifest={"canonical_case_id": "MARES-26-1"}))
