"""Helpers for the network_v1 tests: the synthetic case 002 and modified copies of it, temporary roots."""

from __future__ import annotations

import csv
import io
import json
import shutil
from pathlib import Path

from mares.core.roots import Roots, load_root_specs
from mares.network_v1.case import read_case
from mares.network_v1.testcases import SYNTHETIC_CODE, synthetic_source
from mares.network_v1.validate import validate

SPECS = load_root_specs()


def copy_002(base: Path, *, kind: str = "pilots", name: str = SYNTHETIC_CODE) -> Path:
    """A writable copy of case 002 at ``base/network_v1/<kind>/<name>``."""
    target = base / "network_v1" / kind / name
    shutil.copytree(synthetic_source(), target)
    if name != SYNTHETIC_CODE:
        set_metadata(target, case_code=name)
    return target


def read_rows(case: Path, table: str) -> list[dict[str, str]]:
    text = (case / "data" / table).read_text(encoding="utf-8-sig")
    return list(csv.DictReader(io.StringIO(text), delimiter=";"))


def write_rows(case: Path, table: str, rows: list[dict[str, str]], header: list[str] | None = None) -> None:
    header = header or list(rows[0])
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, header, delimiter=";", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    (case / "data" / table).write_text(buffer.getvalue(), encoding="utf-8")


def edit(case: Path, table: str, contact_or_key: str, column: str, value: str, key: str = "contact_id") -> None:
    rows = read_rows(case, table)
    for row in rows:
        if row[key] == contact_or_key:
            row[column] = value
    write_rows(case, table, rows)


def append(case: Path, table: str, row: dict[str, str]) -> None:
    rows = read_rows(case, table)
    write_rows(case, table, rows + [row], list(rows[0]) if rows else list(row))


def set_metadata(case: Path, **changes) -> None:
    path = case / "data" / "metadata.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta.update(changes)
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def check(case: Path):
    return validate(read_case(case))


def codes_of(validation, level: str | None = None) -> set[str]:
    return {f.code for f in validation.findings if level is None or f.level == level}


def machine(tmp_path: Path) -> dict[str, Path]:
    folders = {name: tmp_path / name for name in ("checkout", "workspace", "intake", "primary")}
    for folder in folders.values():
        folder.mkdir()
    (folders["workspace"] / "runs").mkdir()
    (folders["intake"] / "inbox").mkdir()
    return folders


def roots_for(folders: dict[str, Path]) -> Roots:
    env = {"MARES_WORKSPACE_ROOT": str(folders["workspace"]), "MARES_INTAKE_ROOT": str(folders["intake"])}
    return Roots(SPECS, env, checkout=folders["checkout"])
