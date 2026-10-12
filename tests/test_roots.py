"""The root resolver against synthetic roots. No test reads the machine's real environment or
``.env``: every ``Roots`` object here is built from an explicit mapping and temporary folders."""

from __future__ import annotations

from pathlib import Path

import pytest

from mares.core.refs import StorageRef
from mares.core.roots import RootConfigError, RootError, Roots, RootState, load_root_specs, read_env_file

SPECS = load_root_specs()


@pytest.fixture
def machine(tmp_path: Path) -> dict[str, Path]:
    """A synthetic machine: a checkout and one existing folder per root, all siblings."""
    folders = {name: tmp_path / name.lower() for name in ("checkout", "workspace", "intake", "primary", "backup")}
    for folder in folders.values():
        folder.mkdir()
    return folders


def roots_for(machine: dict[str, Path], **values: str) -> Roots:
    env = {
        "MARES_WORKSPACE_ROOT": str(machine["workspace"]),
        "MARES_INTAKE_ROOT": str(machine["intake"]),
        "MARES_PRIMARY_ROOT": str(machine["primary"]),
    }
    env.update(values)
    return Roots(SPECS, env, checkout=machine["checkout"])


def test_declared_roots_are_the_documented_ones():
    assert set(SPECS) == {"WORKSPACE", "INTAKE", "PRIMARY", "BACKUP", "EXCHANGE", "LEGACY_IMPORT"}
    assert [name for name, spec in SPECS.items() if spec.authoritative] == ["PRIMARY"]
    assert {name for name, spec in SPECS.items() if spec.required} == {"WORKSPACE", "INTAKE", "PRIMARY"}


def test_configured_root_resolves_to_its_directory(machine):
    roots = roots_for(machine)
    assert roots.require("PRIMARY") == machine["primary"]
    assert roots.require("WORKSPACE", writable=True) == machine["workspace"]
    assert list(machine["workspace"].iterdir()) == []  # the write probe leaves nothing behind


def test_missing_required_root_is_an_error_naming_the_variable(machine):
    roots = roots_for(machine, MARES_PRIMARY_ROOT="")
    with pytest.raises(RootError, match="MARES_PRIMARY_ROOT is not set") as raised:
        roots.require("PRIMARY")
    assert raised.value.state is RootState.NOT_CONFIGURED
    with pytest.raises(RootError):
        roots.optional("PRIMARY")  # a required root is never "optionally absent"


def test_optional_root_that_is_not_configured_stays_unconfigured(machine):
    roots = roots_for(machine)
    assert roots.optional("BACKUP") is None
    assert roots.state("BACKUP") is RootState.NOT_CONFIGURED
    with pytest.raises(RootError):
        roots.require("BACKUP")  # whoever needs it gets a refusal, not another root


def test_set_but_unusable_optional_root_is_a_refusal_not_a_fallback(machine):
    roots = roots_for(machine, MARES_BACKUP_ROOT=str(machine["backup"] / "not_mounted"))
    assert roots.state("BACKUP") is RootState.UNREACHABLE
    with pytest.raises(RootError, match="unknown, not empty"):
        roots.optional("BACKUP")
    assert not (machine["backup"] / "not_mounted").exists()  # resolution creates no root


def test_undeclared_root_is_refused(machine):
    with pytest.raises(RootError) as raised:
        roots_for(machine).require("ARCHIVE")
    assert raised.value.state is RootState.NOT_DECLARED


def test_relative_value_is_unusable(machine):
    roots = roots_for(machine, MARES_PRIMARY_ROOT="relative/primary")
    with pytest.raises(RootError, match="absolute") as raised:
        roots.require("PRIMARY")
    assert raised.value.state is RootState.UNUSABLE


def test_filesystem_root_is_unusable(machine):
    roots = roots_for(machine, MARES_PRIMARY_ROOT=machine["primary"].anchor)
    assert roots.state("PRIMARY") is RootState.UNUSABLE


def test_root_inside_the_checkout_is_unusable(machine):
    inside = machine["checkout"] / "data"
    inside.mkdir()
    roots = roots_for(machine, MARES_PRIMARY_ROOT=str(inside))
    with pytest.raises(RootError, match="inside the repository checkout"):
        roots.require("PRIMARY")


def test_overlapping_roots_are_unusable(machine):
    nested = machine["primary"] / "backup"
    nested.mkdir()
    roots = roots_for(machine, MARES_BACKUP_ROOT=str(nested))
    assert roots.state("BACKUP") is RootState.UNUSABLE
    assert roots.state("PRIMARY") is RootState.UNUSABLE
    same = roots_for(machine, MARES_BACKUP_ROOT=str(machine["primary"]).upper())
    assert same.state("BACKUP") is RootState.UNUSABLE  # case differences do not separate roots


def test_read_only_root_refuses_writing(machine):
    legacy = machine["backup"].with_name("legacy")
    legacy.mkdir()
    roots = roots_for(machine, MARES_LEGACY_IMPORT_ROOT=str(legacy))
    assert roots.require("LEGACY_IMPORT") == legacy
    with pytest.raises(RootError) as raised:
        roots.require("LEGACY_IMPORT", writable=True)
    assert raised.value.state is RootState.READ_ONLY
    assert list(legacy.iterdir()) == []


def test_reference_resolves_below_its_root_and_survives_relocation(machine, tmp_path):
    ref = StorageRef("PRIMARY", "preservation/manifests/example.json")
    before = roots_for(machine).resolve(ref)
    assert before == machine["primary"] / "preservation" / "manifests" / "example.json"

    successor = tmp_path / "new_fs"
    successor.mkdir()
    after = roots_for(machine, MARES_PRIMARY_ROOT=str(successor)).resolve(ref)
    assert after == successor / "preservation" / "manifests" / "example.json"
    assert ref.to_dict() == {"root": "PRIMARY", "rel": "preservation/manifests/example.json"}


def test_status_reports_every_declared_root(machine):
    status = roots_for(machine).status()
    assert status["PRIMARY"] is RootState.AVAILABLE
    assert status["EXCHANGE"] is RootState.NOT_CONFIGURED
    assert set(status) == set(SPECS)


def test_process_environment_wins_over_env_file_and_only_mares_names_are_read(machine, tmp_path):
    env_file = tmp_path / "workstation.env"
    env_file.write_text(
        "# comment\n"
        f"MARES_WORKSPACE_ROOT={machine['workspace']}\n"
        f"MARES_PRIMARY_ROOT='{machine['backup']}'\n"
        "OTHER_TOOL_ROOT=ignored\n",
        encoding="utf-8",
    )
    roots = Roots.load(process_env={"MARES_PRIMARY_ROOT": str(machine["primary"])}, env_file=env_file)
    assert roots.require("PRIMARY") == machine["primary"]
    assert roots.require("WORKSPACE") == machine["workspace"]
    assert read_env_file(env_file)["MARES_PRIMARY_ROOT"] == str(machine["backup"])


def test_missing_env_file_configures_nothing(tmp_path):
    roots = Roots.load(process_env={}, env_file=tmp_path / "absent.env")
    assert set(roots.status().values()) == {RootState.NOT_CONFIGURED}


def test_malformed_configuration_is_an_error(tmp_path):
    env_file = tmp_path / "broken.env"
    env_file.write_text("this is not an assignment\n", encoding="utf-8")
    with pytest.raises(RootConfigError):
        read_env_file(env_file)

    config = tmp_path / "storage_roots.toml"
    config.write_text('schema = "mares-storage-roots/v1"\n[roots.PRIMARY]\nenv = "SOME_PATH"\n', encoding="utf-8")
    with pytest.raises(RootConfigError):
        load_root_specs(config)
