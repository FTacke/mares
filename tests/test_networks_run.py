"""The processing run and the command line, against synthetic roots in temporary folders.

No test reads the machine's ``.env`` or a real root. The point of these tests is *where* things go:
output only below WORKSPACE, input only from INTAKE or PRIMARY, nothing written anywhere else.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import network_fixtures as fx
from mares.core.refs import StorageRef
from mares.core.roots import RootError, Roots, load_root_specs
from mares.networks import cli
from mares.networks.run import PipelineError, STAGES, _RunFolder, parse_ref, run_pipeline

SPECS = load_root_specs()
PACKAGE = "INTAKE:inbox/delivery/contents"


@pytest.fixture
def machine(tmp_path: Path) -> dict[str, Path]:
    folders = {name: tmp_path / name for name in ("checkout", "workspace", "intake", "primary", "backup", "exchange")}
    for folder in folders.values():
        folder.mkdir()
    for sub in ("inbox", "reports", "staging"):
        (folders["intake"] / sub).mkdir()
    (folders["workspace"] / "runs").mkdir()
    fx.standard_package(folders["intake"] / "inbox" / "delivery" / "contents")
    return folders


def roots_for(machine, **extra) -> Roots:
    env = {"MARES_WORKSPACE_ROOT": str(machine["workspace"]), "MARES_INTAKE_ROOT": str(machine["intake"])}
    env.update(extra)
    return Roots(SPECS, env, checkout=machine["checkout"])


def listing(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}


def test_a_full_run_writes_only_below_the_workspace_run_folder(machine):
    roots = roots_for(machine)
    before = {name: listing(machine[name]) for name in ("intake", "checkout", "primary", "backup", "exchange")}
    result = run_pipeline(roots, parse_ref(PACKAGE), "run", formats=("svg", "png"))
    assert result.status == "COMPLETED"
    assert result.run_ref == StorageRef("WORKSPACE", f"runs/{result.run_id}")
    assert result.run_dir == machine["workspace"] / "runs" / result.run_id
    after = {name: listing(machine[name]) for name in before}
    assert after == before  # input untouched, nothing written to INTAKE, the checkout or any other root

    written = {p.relative_to(machine["workspace"]).parts[:2] for p in machine["workspace"].rglob("*") if p.is_file()}
    assert written == {("runs", result.run_id)}  # nowhere else in the workspace
    names = {p.relative_to(result.run_dir).as_posix() for p in result.run_dir.rglob("*") if p.is_file()}
    assert {"run_record.json", "processing_report.md", "validation_report.md", "validation_report.json", "canonical/dataset.json",
            "canonical/ties.csv", "analysis/tables.md", "analysis/survey_status.json"} <= names
    for stem in ("fig_A_ego_naehe_wohnort", "fig_B_gruppen_beziehungen", "fig_C_geografisches_profil", "fig_D1_sprachprofil",
                 "fig_D2_ego_sprachmodus", "fig_E_deskriptive_uebersicht"):
        assert {f"figures/{stem}.svg", f"figures/{stem}.png"} <= names and f"figures/{stem}.pdf" not in names


def test_the_run_record_documents_inputs_parameters_status_and_outputs(machine):
    roots = roots_for(machine)
    result = run_pipeline(roots, parse_ref(PACKAGE), "run", formats=("svg",))
    record = json.loads((result.run_dir / "run_record.json").read_text(encoding="utf-8"))

    package_dir = machine["intake"] / "inbox" / "delivery" / "contents"
    assert record["input"]["ref"] == {"root": "INTAKE", "rel": "inbox/delivery/contents"}
    assert {f["name"]: f["sha256"] for f in record["input"]["files"]} == {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in package_dir.iterdir()
    }
    assert record["source"]["source_label"] == "0000-1" and record["source"]["canonical_case_id"] is None
    assert record["dataset_version"] is None
    assert record["run_id"] == result.run_id and record["command"] == "run" and record["status"] == "COMPLETED"
    assert {"mares_version", "git_commit", "git_dirty", "python", "dependencies"} <= set(record["software"])
    assert record["parameters"]["local_places"] == ["Marburg"] and record["parameters"]["figure_formats"] == ["svg"]
    quality = record["data_quality"]
    assert quality["quality_state"] == "UNREVIEWED" and quality["scientific_validation"] == "not performed"
    assert quality["preservation_state"] == "NOT_PRESERVED" and quality["backup_state"] == "NO_COPY"
    assert quality["technical_validation"] in ("PASSED", "PASSED_WITH_WARNINGS")
    assert record["survey_status"]["completeness"] == "partial_unknown_not_absent"
    assert record["methodological_limits"]

    listed = {o["ref"]["rel"]: o for o in record["outputs"]}
    on_disk = {p.relative_to(machine["workspace"]).as_posix() for p in result.run_dir.rglob("*") if p.is_file()}
    assert set(listed) == on_disk - {f"runs/{result.run_id}/run_record.json"}
    for rel, entry in listed.items():
        assert entry["ref"]["root"] == "WORKSPACE"
        assert entry["sha256"] == hashlib.sha256((machine["workspace"] / rel).read_bytes()).hexdigest()


def test_a_record_holds_logical_references_never_machine_paths(machine):
    result = run_pipeline(roots_for(machine), parse_ref(PACKAGE), "run", formats=("svg",))
    for name in ("run_record.json", "processing_report.md", "validation_report.md"):
        text = (result.run_dir / name).read_text(encoding="utf-8")
        for root in machine.values():
            assert str(root) not in text and root.as_posix() not in text, name


def test_the_processing_report_states_status_limits_and_open_questions(machine):
    result = run_pipeline(roots_for(machine), parse_ref(PACKAGE), "run", formats=("svg",))
    report = (result.run_dir / "processing_report.md").read_text(encoding="utf-8")
    for expected in ("UNREVIEWED", "NOT_PRESERVED", "Wissenschaftlich validiert: **nein**", "keine** Fall-ID", "Bekannte methodische Grenzen",
                     "Nicht berechnet (bewusst)", "Netzwerkdichte", "SHA-256", "studentische"):
        assert expected in report
    validation = (result.run_dir / "validation_report.md").read_text(encoding="utf-8")
    assert "Harte Fehler" in validation and "Warnungen" in validation and "Offene Forschungsfragen" in validation
    assert "RT01" in validation and "SW-01" in validation


def test_stages_are_cumulative(machine):
    roots = roots_for(machine)
    expected = {
        "validate": {"validation_report.md"},
        "import": {"canonical/dataset.json"},
        "analyze": {"analysis/tables.md"},
        "figures": {"figures/fig_A_ego_naehe_wohnort.png"},
        "run": {"processing_report.md"},
    }
    seen: set[str] = set()
    for stage in STAGES:
        result = run_pipeline(roots, parse_ref(PACKAGE), stage, formats=("png",))
        names = {p.relative_to(result.run_dir).as_posix() for p in result.run_dir.rglob("*") if p.is_file()}
        assert "run_record.json" in names and expected[stage] <= names
        later = set().union(*(expected[s] for s in STAGES[STAGES.index(stage) + 1 :]), set())
        assert not (later & names), stage
        seen |= expected[stage]


def test_input_comes_only_from_intake_or_primary(machine):
    roots = roots_for(machine, MARES_BACKUP_ROOT=str(machine["backup"]), MARES_EXCHANGE_ROOT=str(machine["exchange"]))
    for root in ("BACKUP", "EXCHANGE", "WORKSPACE", "LEGACY_IMPORT"):
        with pytest.raises(PipelineError, match="not a permitted data source"):
            run_pipeline(roots, StorageRef(root, "inbox/delivery/contents"), "validate")
    assert list((machine["workspace"] / "runs").iterdir()) == []  # refused before anything was created


def test_an_unconfigured_input_root_is_an_error_not_a_fallback(machine):
    roots = roots_for(machine)  # PRIMARY is not configured
    with pytest.raises(RootError, match="MARES_PRIMARY_ROOT is not set"):
        run_pipeline(roots, StorageRef("PRIMARY", "derived/x"), "validate")
    assert list((machine["workspace"] / "runs").iterdir()) == []


def test_without_a_workspace_nothing_runs_and_nothing_is_written_elsewhere(machine):
    roots = Roots(SPECS, {"MARES_INTAKE_ROOT": str(machine["intake"])}, checkout=machine["checkout"])
    before = listing(machine["intake"])
    with pytest.raises(RootError, match="MARES_WORKSPACE_ROOT"):
        run_pipeline(roots, parse_ref(PACKAGE), "run")
    assert listing(machine["intake"]) == before and listing(machine["checkout"]) == {}


def test_a_package_with_errors_is_not_processed_further(machine):
    package = machine["intake"] / "inbox" / "delivery" / "contents"
    (package / "contacts.csv").write_bytes((package / "contacts.csv").read_bytes().replace(b"A02;", b"A01;", 1))
    for name in ("SHA256SUMS.txt",):
        (package / name).unlink()
    result = run_pipeline(roots_for(machine), parse_ref(PACKAGE), "run", formats=("png",))
    assert result.status == "FAILED_VALIDATION"
    names = {p.relative_to(result.run_dir).as_posix() for p in result.run_dir.rglob("*") if p.is_file()}
    assert names == {"validation_report.md", "validation_report.json", "run_record.json", "processing_report.md"}
    assert not (result.run_dir / "figures").exists() and not (result.run_dir / "canonical").exists()
    assert result.record["data_quality"]["errors"] >= 1


def test_an_unreadable_package_fails_in_the_record_without_output(machine):
    (machine["intake"] / "inbox" / "delivery" / "contents" / "groups.csv").unlink()
    result = run_pipeline(roots_for(machine), parse_ref(PACKAGE), "run")
    assert result.status == "FAILED_IMPORT" and "groups.csv" in result.record["error"]
    assert {p.name for p in result.run_dir.iterdir()} == {"run_record.json"}


def test_a_repeated_run_is_a_new_run_with_identical_results(machine):
    roots = roots_for(machine)
    stamps = iter([datetime(2026, 10, 12, 9, 0, 0, tzinfo=timezone.utc), datetime(2026, 10, 12, 9, 0, 0, tzinfo=timezone.utc)] * 8)
    first = run_pipeline(roots, parse_ref(PACKAGE), "run", formats=("svg", "png"), clock=lambda: next(stamps))
    second = run_pipeline(roots, parse_ref(PACKAGE), "run", formats=("svg", "png"), clock=lambda: next(stamps))
    assert first.run_id != second.run_id and first.run_dir != second.run_dir  # a run is never overwritten
    assert all(p.exists() for p in (first.run_dir, second.run_dir))

    def outputs(result):
        return {o["ref"]["rel"].split("/", 2)[2]: o["sha256"] for o in result.record["outputs"] if not o["ref"]["rel"].endswith("processing_report.md")}

    assert outputs(first) == outputs(second)  # figures, tables and canonical data are reproducible


def test_a_new_data_version_gives_new_input_hashes(machine):
    roots = roots_for(machine)
    first = run_pipeline(roots, parse_ref(PACKAGE), "validate")
    package = machine["intake"] / "inbox" / "delivery" / "contents"
    (package / "review_items.csv").write_bytes((package / "review_items.csv").read_bytes() + b"")
    again = run_pipeline(roots, parse_ref(PACKAGE), "validate")
    assert {f["name"]: f["sha256"] for f in first.record["input"]["files"]} == {f["name"]: f["sha256"] for f in again.record["input"]["files"]}
    (package / "manifest.json").write_text((package / "manifest.json").read_text() + "\n", encoding="utf-8")
    changed = run_pipeline(roots, parse_ref(PACKAGE), "validate")
    assert {f["name"]: f["sha256"] for f in changed.record["input"]["files"]} != {f["name"]: f["sha256"] for f in first.record["input"]["files"]}


@pytest.mark.parametrize("text", ["inbox/x", "C:/x", "INTAKE", "INTAKE:../escape", "INTAKE:/abs", "intake:inbox/x", "INTAKE:a\\b"])  # path-literal-ok: rejected examples
def test_package_locations_must_be_logical_references(text):
    with pytest.raises(PipelineError):
        parse_ref(text)


def test_the_run_folder_cannot_write_outside_itself(tmp_path):
    folder = _RunFolder(tmp_path / "run")
    (tmp_path / "run").mkdir()
    for rel in ("../escape.txt", "/abs.txt", "a/../../b.txt", "c:/x.txt", "back\\slash.txt"):  # path-literal-ok: rejected examples
        with pytest.raises(ValueError):
            folder.write_text(rel, "x")
    folder.write_text("ok/file.txt", "x")
    with pytest.raises(FileExistsError):
        folder.write_text("ok/file.txt", "y")  # never overwrites
    assert not (tmp_path / "escape.txt").exists()


def test_cli_runs_and_reports_exit_codes(machine, capsys):
    roots = roots_for(machine)
    assert cli.main(["run", "--package", PACKAGE, "--formats", "png"], roots=roots) == 0
    out = capsys.readouterr().out
    assert "WORKSPACE:runs/RUN-" in out and "COMPLETED" in out and "UNREVIEWED" in out
    assert cli.main(["validate", "--package", "BACKUP:inbox/x"], roots=roots) == 1
    assert "not a permitted data source" in capsys.readouterr().err
    assert cli.main(["validate", "--package", "nonsense"], roots=roots) == 1
    assert cli.main(["validate", "--package", PACKAGE, "--formats", "gif"], roots=roots) == 1
    (machine["intake"] / "inbox" / "delivery" / "contents" / "groups.csv").unlink()
    assert cli.main(["validate", "--package", PACKAGE], roots=roots) == 2


def test_cli_local_place_parameter_is_applied_and_recorded(machine):
    roots = roots_for(machine)
    result = run_pipeline(roots, parse_ref(PACKAGE), "analyze", params=__import__("mares.networks.analysis", fromlist=["x"]).AnalysisParams(("Berlin",)))
    assert result.record["parameters"]["local_places"] == ["Berlin"]
    table = (result.run_dir / "analysis" / "geo_category.csv").read_text(encoding="utf-8")
    assert "Berlin;3" in table  # the local category is named after the configured local place
