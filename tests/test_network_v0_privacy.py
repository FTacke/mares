"""Research data never enters the repository -- not as a fixture, not as an example, not unignored.

``.gitignore`` is the second line of defence (AGENTS.md rule 1); these tests are the third: they look at
what is actually in the checkout.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from mares.core.paths import repo_root
from mares.core.roots import Roots, load_root_specs
from mares.network_v0 import cli
from mares.network_v0.package import read_package
from mares.network_v0.validate import validate

REPO = repo_root()
EXAMPLE = REPO / "examples" / "synthetic" / "network-package-0000"
PACKAGE_FILES = {"contacts.csv", "observed_edges.csv", "group_memberships.csv", "source_clarifications.csv", "review_items.csv"}
SKIP_DIRS = {".venv", ".git", "__pycache__", ".pytest_cache", "mares.egg-info"}
RESEARCH_SUFFIXES = {".zip", ".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg", ".mp4", ".mov", ".xlsx", ".xls", ".docx", ".doc", ".pdf", ".sqlite", ".db"}
SYNTHETIC_HOMES = ("examples/synthetic/", "templates/", "tests/fixtures/")


def checkout_files() -> list[Path]:
    found = []
    for path in REPO.rglob("*"):
        if path.is_file() and not (set(path.relative_to(REPO).parts) & SKIP_DIRS):
            found.append(path)
    return found


def test_package_tables_exist_only_in_the_synthetic_examples():
    stray = [
        p.relative_to(REPO).as_posix()
        for p in checkout_files()
        if p.name in PACKAGE_FILES and not p.relative_to(REPO).as_posix().startswith("examples/synthetic/")
    ]
    assert not stray, f"package tables outside examples/synthetic: {stray}"


def test_every_package_in_the_repository_is_marked_synthetic_with_the_reserved_year():
    manifests = [p for p in checkout_files() if p.name == "contacts.csv"]
    assert manifests, "the synthetic example package is missing"
    for contacts in manifests:
        folder = contacts.parent
        if (folder / "manifest.json").is_file():  # a network package
            manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
            assert manifest.get("synthetic") is True, contacts
            assert str(manifest.get("source_case_label", "")).startswith("0000"), contacts
            rows = contacts.read_text(encoding="utf-8-sig").splitlines()[1:]
            assert rows and all(row.startswith("0000") for row in rows if row.strip()), contacts
        elif (folder / "metadata.json").is_file():  # a network_v1 case: only fully synthetic test cases, reserved year
            meta = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
            assert (meta["dataset_version"], meta["case_type"], meta["provenance"]) == ("network_v1", "test", "fully_synthetic"), contacts
            assert meta["empirical_analysis_eligible"] is False and meta["survey"]["survey_date"].startswith("0000"), contacts
        else:  # the illustrative case folder: its case file must say synthetic and carry the reserved year
            case = json.loads((folder / "case.json").read_text(encoding="utf-8"))
            assert case["synthetic"] is True and case["case_id"].startswith("MARES-0000-"), contacts


def test_research_file_types_in_the_checkout_are_ignored_by_git_or_synthetic():
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    unprotected = []
    for path in checkout_files():
        rel = path.relative_to(REPO).as_posix()
        if path.suffix.lower() not in RESEARCH_SUFFIXES or rel.startswith(SYNTHETIC_HOMES):
            continue
        result = subprocess.run(["git", "check-ignore", "-q", rel], cwd=REPO, capture_output=True)
        if result.returncode == 1:
            unprotected.append(rel)
        elif result.returncode not in (0, 1):
            pytest.skip("not a git working tree")
    assert not unprotected, f"research-type files that git would track: {unprotected}"


def test_the_synthetic_example_package_is_valid_and_complete():
    dataset = read_package(EXAMPLE)
    report = validate(dataset)
    assert report.errors == () and report.warnings == ()
    assert dataset.case.source_label == "0000-1" and dataset.case.canonical_case_id is None
    assert len(dataset.contacts) == 12 and dataset.contacts[-1].contact_id == "A12"
    assert (dataset.contacts[8].source_block, dataset.contacts[8].source_local_id) == ("2", "A01")  # second sheet restarts


def test_the_cli_runs_on_a_copy_of_the_example_in_synthetic_roots(tmp_path):
    folders = {name: tmp_path / name for name in ("checkout", "workspace", "intake")}
    for folder in folders.values():
        folder.mkdir()
    (folders["intake"] / "inbox").mkdir()
    shutil.copytree(EXAMPLE, folders["intake"] / "inbox" / "example")
    env = {"MARES_WORKSPACE_ROOT": str(folders["workspace"]), "MARES_INTAKE_ROOT": str(folders["intake"])}
    roots = Roots(load_root_specs(), env, checkout=folders["checkout"])
    assert cli.main(["figures", "--package", "INTAKE:inbox/example", "--formats", "svg"], roots=roots) == 0
    (run,) = (folders["workspace"] / "runs").iterdir()
    assert len(list((run / "figures").glob("*/*.svg"))) == 19  # core 4, supplementary 10, diagnostic 5; the analysis versions are one level deeper


def test_no_source_text_carries_a_label_of_a_real_case():
    """Code, tests and examples refer to synthetic cases only (reserved year 0000)."""
    offenders = []
    for path in checkout_files():
        rel = path.relative_to(REPO).as_posix()
        if rel == "tests/test_network_v0_privacy.py" or not rel.startswith(("src/", "tests/", "examples/")) or path.suffix not in {".py", ".csv", ".json", ".md", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "MARES_001-2" in text or "Datenpaket_2026" in text:
            offenders.append(rel)
    assert not offenders, offenders


def test_the_synthetic_curation_example_fits_the_example_package():
    from mares.network_v0.curation import read_curation

    curation = read_curation(REPO / "examples" / "synthetic" / "network-curation-0000" / "curation.json")
    assert curation.source_label.startswith("0000") and curation.survey.stated
    report = validate(read_package(EXAMPLE), curation=curation)
    assert report.errors == () and report.warnings == ()
    categories = {q.question_id: q.category.value for q in report.open_questions}
    assert categories["RT01"] == "documented_ambiguity" and categories["RT02"] == "resolved"
