"""network_v1 pipeline, case tree, empirical filter, test case installation and the command line."""

from __future__ import annotations

import hashlib
import json

import pytest

import network_v0_fixtures as fx0
from mares.core.refs import StorageRef
from mares.network_v1.case import read_case
from mares.network_v1.figures import expected_files
from mares.network_v1.run import PipelineError, empirical_cases, list_cases, process_case
from mares.network_v1.testcases import (
    CLOSENESS, FICTIONALIZED_CODE, SYNTHETIC_CODE, V0_MEANINGS, TestCaseError, build_fictionalized, install_synthetic,
)
from mares.network_v1.validate import validate
from mares.networks import cli
from network_v1_fixtures import copy_002, machine, roots_for, set_metadata


@pytest.fixture
def folders(tmp_path):
    return machine(tmp_path)


def listing(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}


def test_a_case_run_writes_graphics_to_the_case_and_everything_else_to_the_workspace(folders):
    copy_002(folders["intake"])
    roots = roots_for(folders)
    before = listing(folders["intake"] / "network_v1" / "pilots" / SYNTHETIC_CODE / "data")
    result = process_case(roots, StorageRef("INTAKE", f"network_v1/pilots/{SYNTHETIC_CODE}"))
    assert result.status == "COMPLETED"
    graphics = folders["intake"] / "network_v1" / "pilots" / SYNTHETIC_CODE / "graphics"
    assert {p.name for p in graphics.iterdir()} == expected_files(SYNTHETIC_CODE, ("png",))
    assert listing(graphics.parent / "data") == before  # input untouched
    run = folders["workspace"] / "runs" / result.run_id
    assert {"run_record.json", "validation_report.json", "validation_report.md", "figures_index.json", "derived/contacts.csv", "derived/pairs.csv"} <= set(listing(run))
    record = json.loads((run / "run_record.json").read_text(encoding="utf-8"))
    assert record["case"]["empirical"] is False and record["pipeline"] == "network_v1"
    assert ":\\" not in json.dumps(record) and str(folders["intake"]) not in json.dumps(record)


def test_a_rerun_replaces_the_eight_files_and_keeps_foreign_files(folders):
    copy_002(folders["intake"])
    roots = roots_for(folders)
    ref = StorageRef("INTAKE", f"network_v1/pilots/{SYNTHETIC_CODE}")
    process_case(roots, ref)
    graphics = folders["intake"] / "network_v1" / "pilots" / SYNTHETIC_CODE / "graphics"
    (graphics / "notiz.txt").write_text("x", encoding="utf-8")
    first = listing(graphics)
    second = process_case(roots, ref)
    assert listing(graphics) == first  # byte-identical figures, nothing deleted
    assert second.record["foreign_files_in_graphics"] == ["notiz.txt"]


def test_a_case_with_errors_gets_no_figures(folders):
    case = copy_002(folders["intake"])
    set_metadata(case, empirical_analysis_eligible=True)
    result = process_case(roots_for(folders), StorageRef("INTAKE", f"network_v1/pilots/{SYNTHETIC_CODE}"))
    assert result.status == "FAILED_VALIDATION" and not (case / "graphics").exists()


@pytest.mark.parametrize("text", ["WORKSPACE:network_v1/pilots/x", "BACKUP:network_v1/pilots/x", "INTAKE:inbox/x", "INTAKE:network_v1/other/x"])
def test_case_locations_are_restricted(folders, text):
    root, _, rel = text.partition(":")
    with pytest.raises(PipelineError):
        process_case(roots_for(folders), StorageRef(root, rel))


def test_the_empirical_filter_reads_metadata_not_folder_names(folders):
    copy_002(folders["intake"])
    disguised = copy_002(folders["intake"], kind="cases", name="004_regular_looking")  # a test case in cases/ stays a test case
    pilot = copy_002(folders["intake"], name="003_pilot")
    set_metadata(pilot, case_type="pilot", provenance="survey", empirical_analysis_eligible=True)
    roots = roots_for(folders)
    assert len(list_cases(roots, "INTAKE")) == 3
    assert [ref.rel for ref, _ in empirical_cases(roots, "INTAKE")] == ["network_v1/pilots/003_pilot"]
    assert disguised.exists()


def test_install_synthetic_refuses_to_replace_a_non_test_case(tmp_path):
    target = tmp_path / SYNTHETIC_CODE
    install_synthetic(target)
    install_synthetic(target)  # a test case may be replaced
    set_metadata(target, case_type="pilot")
    with pytest.raises(TestCaseError):
        install_synthetic(target)


# ------------------------------------------------------------------------------------------- case 001 ---
def v0_package(tmp_path, codebook=V0_MEANINGS):
    cb = {**codebook, "name_generator": {"G1": "a", "G2": "b"}}
    groups, memberships = fx0.standard_groups()
    return fx0.build_package(tmp_path / "v0", contacts=fx0.contact_rows(12, block_size=8), groups=groups, memberships=memberships, codebook=cb)


def test_001_is_built_from_v0_structure_and_marked_fictional(tmp_path):
    package = v0_package(tmp_path)
    before = listing(package)
    target = tmp_path / "network_v1" / "pilots" / FICTIONALIZED_CODE
    summary = build_fictionalized(package, target, source_ref="INTAKE:inbox/v0")
    assert listing(package) == before  # the v0 package is never changed
    case = read_case(target)
    m = case.metadata
    assert (m["case_type"], m["provenance"], m["empirical_analysis_eligible"]) == ("test", "v0_derived_fictionalized", False)
    assert m["field_origins"]["contacts.closeness"] == "v0_interpreted" and m["field_origins"]["contacts.residence_place"] == "fictional"
    assert summary["contacts"] == 12 and len(case.contacts) == 12
    result = validate(case)
    assert not result.errors, result.errors
    assert result.derived.coverage.denied == 0  # v0 never denied a pair: nothing becomes 'no'
    groups = {g.id: g.status.value for g in case.groups}
    assert set(groups.values()) <= {"T", "NS"}
    # v0 closeness 5 = 'sehr nah' becomes v1 1; the direction is reversed, not copied
    v0_closeness = {r["contact_id"]: r["table_ring_near_value"] for r in fx0.contact_rows(12, block_size=8)}
    for c in case.contacts:
        assert c.closeness.raw == CLOSENESS[v0_closeness[c.id]]
    assert all(c.label not in ("", None) and c.comment == "fiktionalisiert" for c in case.contacts)


def test_001_refuses_a_v0_codebook_with_other_meanings(tmp_path):
    changed = {**V0_MEANINGS, "closeness_1_5": {**V0_MEANINGS["closeness_1_5"], "5": "überhaupt nicht nah"}}
    with pytest.raises(TestCaseError):
        build_fictionalized(v0_package(tmp_path, changed), tmp_path / "out", source_ref="INTAKE:inbox/v0")
    assert not (tmp_path / "out").exists()


# ---------------------------------------------------------------------------------------- command line ---
def test_one_entry_point_for_both_versions(folders, capsys):
    roots = roots_for(folders)
    assert cli.main(["v1", "install-test-cases", "--root", "INTAKE"], roots=roots) == 0
    assert cli.main(["v1", "render", "--case", f"INTAKE:network_v1/pilots/{SYNTHETIC_CODE}"], roots=roots) == 0
    assert cli.main(["v1", "list", "--root", "INTAKE", "--empirical"], roots=roots) == 0
    out = capsys.readouterr().out
    assert "figure  G3  rendered" in out
    assert (folders["intake"] / "network_v1" / "cases").is_dir()
    # v0 keeps its calls, with and without the version prefix
    fx0.standard_package(folders["intake"] / "inbox" / "delivery" / "contents")
    assert cli.main(["validate", "--package", "INTAKE:inbox/delivery/contents"], roots=roots) == 0
    assert cli.main(["v0", "validate", "--package", "INTAKE:inbox/delivery/contents"], roots=roots) == 0
    # a v0 package is no v1 case
    assert cli.main(["v1", "render", "--case", "INTAKE:inbox/delivery/contents"], roots=roots) == 1
