"""Guards for the assumptions the architecture rests on: no machine path in tracked operative
files, the code works from a checkout at any location, and git ignores what must never be
committed. They keep the written rules true (``AGENTS.md``)."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from mares.core.paths import repo_root

REPO = repo_root()

# Operative files: code, configuration, fixtures. Documentation may say where something lay on
# one machine (provenance); these files may not.
OPERATIVE_DIRS = ("src", "config", "tests", "templates", "examples")
OPERATIVE_FILES = ("pyproject.toml", ".env.example", ".gitignore", ".gitattributes")
TEXT_SUFFIXES = {".py", ".toml", ".json", ".csv", ".md", ".txt", ".yml", ".yaml", ".cfg", ".ini", ".example", ""}
MARKER = "path-literal-ok"

MACHINE_PATH = re.compile(
    r"(?<![A-Za-z])[A-Za-z]:[\\/]"  # a drive letter  # path-literal-ok: the pattern itself
    r"|(?<![A-Za-z0-9_.-])\\\\[A-Za-z0-9]"  # a UNC share (not an escaped separator inside a name)
    r"|/(?:home|Users|mnt|media)/"  # path-literal-ok: home and mount directories
)


def operative_files() -> list[Path]:
    files = [REPO / name for name in OPERATIVE_FILES]
    for directory in OPERATIVE_DIRS:
        files += [path for path in (REPO / directory).rglob("*") if path.is_file()]
    return [
        path
        for path in files
        if path.suffix in TEXT_SUFFIXES and "__pycache__" not in path.parts and ".egg-info" not in str(path)
    ]


def test_no_machine_path_in_tracked_operative_files():
    findings = []
    for path in operative_files():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if MARKER not in line and MACHINE_PATH.search(line):
                findings.append(f"{path.relative_to(REPO).as_posix()}:{number}: {line.strip()}")
    assert not findings, "machine path in an operative file:\n" + "\n".join(findings)


def test_env_example_holds_names_only():
    lines = (REPO / ".env.example").read_text(encoding="utf-8").splitlines()
    assignments = [line for line in lines if line.strip() and not line.startswith("#")]
    assert assignments and all(re.fullmatch(r"MARES_[A-Z_]+_ROOT=", line) for line in assignments)


def test_env_example_lists_exactly_the_declared_variables():
    from mares.core.roots import load_root_specs

    declared = {spec.variable for spec in load_root_specs().values()}
    listed = {
        line.split("=")[0]
        for line in (REPO / ".env.example").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    assert listed == declared


def test_code_works_from_a_checkout_at_another_location(tmp_path):
    """Copy the code and its configuration elsewhere and run it there, without any environment."""
    elsewhere = tmp_path / "some other place" / "renamed_checkout"
    shutil.copytree(REPO / "src", elsewhere / "src", ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
    shutil.copytree(REPO / "config", elsewhere / "config")
    shutil.copy(REPO / "pyproject.toml", elsewhere / "pyproject.toml")
    script = (
        "import sys; sys.path.insert(0, sys.argv[1])\n"
        "from mares.core.paths import repo_root\n"
        "from mares.core.roots import Roots\n"
        "roots = Roots.load(process_env={})\n"
        "print(repo_root())\n"
        "print(sorted(state.value for state in set(roots.status().values())))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script, str(elsewhere / "src")],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=True,
    )
    located, states = result.stdout.splitlines()
    assert Path(located) == elsewhere.resolve()
    assert states == "['NOT_CONFIGURED']"  # nothing configured there, and nothing guessed


IGNORED = [
    ".env",
    ".env.local",
    "config/storage_roots.local.toml",
    ".venv/pyvenv.cfg",
    "interview.wav",
    "anywhere/below/recording.m4a",
    "anywhere/below/recording.mp3",
    "submission.xlsx",
    "docs/consent_form_signed.pdf",
    "transcript.docx",
    "registry.sqlite",
    "data/cases.csv",
    "preservation/raw/file.bin",
    "restricted/identities/key.csv",
    "inbox/anything.txt",
    "runs/RUN-x/output.json",
    "notes.log",
]
TRACKABLE = [
    ".env.example",
    "config/storage_roots.toml",
    "docs/architecture/data-contract.md",
    "examples/synthetic/MARES-0000-001/case.json",
    "examples/synthetic/MARES-0000-001/contacts.csv",
    "examples/synthetic/sheet.xlsx",
    "templates/network_sheet.xlsx",
    "src/mares/preservation/__init__.py",
    "src/mares/exports/__init__.py",
]


def _git_ignores(path: str) -> bool:
    result = subprocess.run(["git", "check-ignore", "-q", path], cwd=REPO, capture_output=True)
    if result.returncode not in (0, 1):
        pytest.skip("git is not available or this is not a git working tree")
    return result.returncode == 0


@pytest.mark.parametrize("path", IGNORED)
def test_git_ignores_local_configuration_and_research_data(path):
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    assert _git_ignores(path)


@pytest.mark.parametrize("path", TRACKABLE)
def test_git_keeps_contracts_templates_and_synthetic_examples_trackable(path):
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    assert not _git_ignores(path)
