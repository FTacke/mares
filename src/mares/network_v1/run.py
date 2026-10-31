"""Processing a network_v1 case: read -> validate -> derive -> eight standard figures.

Locations (logical references only):

* the case: ``ROOT:network_v1/{pilots,cases}/<case_code>`` in ``INTAKE`` (interim) or ``PRIMARY`` (target); never
  ``BACKUP``, ``EXCHANGE`` or ``WORKSPACE``
* the finished figures: the case's ``graphics/`` -- the eight standard files and nothing else; a re-run replaces exactly
  these files and never deletes anything
* everything technical (validation report, derived tables, figure register, run record): ``WORKSPACE/runs/<RUN-ID>/``

A case with validation errors gets no figures. Test cases are processed like any case; whether a case may enter
empirical overviews is :func:`~.case.is_empirical`, decided by its metadata.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from mares.core import ids
from mares.core.hashing import sha256_file
from mares.core.refs import StorageRef
from mares.core.roots import Roots
from mares.network_v0.run import _RunFolder, _software, _utc  # version-neutral run helpers

from . import DATASET_VERSION, codes
from .case import Case, is_empirical, read_case
from .figures import FIGURES, expected_files, render
from .figures.base import Context
from .places import AREA_LABELS, PRIMARY_LABELS
from .validate import FAILED, Validation, validate

ALLOWED_ROOTS = ("INTAKE", "PRIMARY")
TREE = "network_v1"
KINDS = ("pilots", "cases")


class PipelineError(RuntimeError):
    """The run cannot start (a location outside the allowed roots, a missing case folder ...)."""


@dataclass(frozen=True)
class CaseResult:
    case_ref: StorageRef
    run_id: str
    run_ref: StorageRef
    status: str  # COMPLETED | FAILED_VALIDATION
    validation: Validation
    figures: list[dict]
    record: dict


def check_case_ref(ref: StorageRef) -> None:
    if ref.root not in ALLOWED_ROOTS:
        raise PipelineError(f"{ref.root} is not a permitted location of case data; use one of {', '.join(ALLOWED_ROOTS)}")
    parts = ref.parts
    if len(parts) != 3 or parts[0] != TREE or parts[1] not in KINDS:
        raise PipelineError(f"a case is addressed as ROOT:{TREE}/pilots/<case> or ROOT:{TREE}/cases/<case>, not {ref.root}:{ref.rel}")


def list_cases(roots: Roots, root: str) -> list[tuple[StorageRef, dict]]:
    """Every case folder of the tree in ``root`` with its metadata (unreadable metadata = an empty dict)."""
    if root not in ALLOWED_ROOTS:
        raise PipelineError(f"{root} holds no case data; use one of {', '.join(ALLOWED_ROOTS)}")
    found = []
    for kind in KINDS:
        base = roots.resolve(StorageRef(root, f"{TREE}/{kind}"))
        if not base.is_dir():
            continue
        for folder in sorted(p for p in base.iterdir() if p.is_dir()):
            try:
                meta = json.loads((folder / "data" / "metadata.json").read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                meta = {}
            found.append((StorageRef(root, f"{TREE}/{kind}/{folder.name}"), meta if isinstance(meta, dict) else {}))
    return found


def empirical_cases(roots: Roots, root: str) -> list[tuple[StorageRef, dict]]:
    """The filter for empirical overviews, case counts and statistics: metadata decide, not folder names."""
    return [(ref, meta) for ref, meta in list_cases(roots, root) if is_empirical(meta)]


def _csv(header: list[str], rows: list[list[object]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()


def derived_tables(case: Case, validation: Validation) -> dict[str, str]:
    """Derived features as CSV: one row per contact, one row per pair with a statement."""
    d = validation.derived
    contacts = []
    for c in case.contacts:
        r = d.residence[c.id]
        b = case.communication.get(c.id)
        contacts.append([
            c.id, c.closeness.raw, codes.closeness_value(c.closeness) if c.closeness.recorded else "",
            c.closeness.missing.value if c.closeness.missing else "", r.area.value, AREA_LABELS[r.area], r.primary.value,
            PRIMARY_LABELS[r.primary], r.basis, ", ".join(case.groups_of(c.id)),
            codes.language_use_label(b.language_use.values) if b and b.language_use.recorded else "",
        ])
    pairs = [[p.a, p.b, p.state, " | ".join(p.sources)] for p in sorted(d.pairs.values(), key=lambda p: (p.a, p.b))]
    return {
        "derived/contacts.csv": _csv(["contact_id", "closeness_raw", "closeness", "closeness_missing", "area", "area_label", "primary",
                                      "primary_label", "area_basis", "groups", "language_use"], contacts),
        "derived/pairs.csv": _csv(["contact_a", "contact_b", "state", "sources"], pairs),
    }


def _report_md(case: Case, validation: Validation) -> str:
    lines = [f"# Prüfbericht network_v1 · {case.code or case.folder.name}", "", f"Status: **{validation.status}** · "
             f"{len(validation.errors)} Fehler · {len(validation.warnings)} Warnungen · {len(validation.notes)} Hinweise", ""]
    for title, items in (("Fehler", validation.errors), ("Warnungen", validation.warnings), ("Hinweise", validation.notes)):
        lines += [f"## {title}", ""] + ([f"- `{f.code}` {f.message} ({f.ref})" for f in items] or ["- keine"]) + [""]
    if validation.derived:
        lines += ["## Abdeckung der Kontaktpaare", "", "```", json.dumps(validation.derived.coverage.to_dict(), ensure_ascii=False), "```", ""]
    lines.append("Eine bestandene technische Prüfung ist keine wissenschaftliche Validierung.")
    return "\n".join(lines) + "\n"


def process_case(
    roots: Roots,
    case_ref: StorageRef,
    *,
    formats: tuple[str, ...] = ("png",),
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> CaseResult:
    check_case_ref(case_ref)
    folder = roots.resolve(case_ref)
    if not (folder / "data").is_dir():
        raise PipelineError(f"{case_ref.root}:{case_ref.rel} has no data/ folder")
    started = clock()
    run_id = ids.new_run_id(started)
    run_ref = StorageRef("WORKSPACE", f"runs/{run_id}")
    run_dir = roots.resolve(run_ref, writable=True)
    run_dir.mkdir(parents=True, exist_ok=False)
    out = _RunFolder(run_dir)

    case = read_case(folder)
    validation = validate(case)
    out.write_text("validation_report.json", json.dumps(validation.to_dict(), indent=2, ensure_ascii=False) + "\n")
    out.write_text("validation_report.md", _report_md(case, validation))
    figures: list[dict] = []
    foreign: list[str] = []
    if validation.status != FAILED:
        for rel, text in derived_tables(case, validation).items():
            out.write_text(rel, text)
        graphics = roots.resolve(case_ref.child("graphics"), writable=True)
        figures = render(Context(case, validation.derived), graphics, formats)
        allowed = expected_files(case.code, ("png", "svg"))
        foreign = sorted(p.name for p in graphics.iterdir() if p.name not in allowed)
        out.write_text("figures_index.json", json.dumps({
            "format": "mares-network-v1-figures/v1", "case_code": case.code, "graphics": case_ref.child("graphics").to_dict(),
            "figures": figures, "standard_set": [f"{s.code} {s.title}" for s in FIGURES],
            "foreign_files_in_graphics": foreign,
        }, indent=2, ensure_ascii=False) + "\n")
    status = "FAILED_VALIDATION" if validation.status == FAILED else "COMPLETED"
    data_files = sorted(p for p in (folder / "data").iterdir() if p.is_file())
    record = {
        "format": "mares-run-record/v0-draft",
        "pipeline": DATASET_VERSION,
        "run_id": run_id,
        "started": _utc(started),
        "finished": _utc(clock()),
        "status": status,
        "case": {"ref": case_ref.to_dict(), "case_code": case.code, "case_type": case.metadata.get("case_type"),
                 "provenance": case.metadata.get("provenance"), "empirical_analysis_eligible": case.metadata.get("empirical_analysis_eligible"),
                 "empirical": is_empirical(case.metadata)},
        "inputs": [{"ref": case_ref.child("data", p.name).to_dict(), "sha256": sha256_file(p), "size": p.stat().st_size} for p in data_files],
        "validation": validation.to_dict()["counts"] | {"status": validation.status},
        "coverage": validation.derived.coverage.to_dict() if validation.derived else None,
        "figures": [{k: f[k] for k in ("code", "status", "reason", "files")} for f in figures],
        "foreign_files_in_graphics": foreign,
        "software": _software(),
        "note": "Technische Prüfung, keine wissenschaftliche Validierung.",
    }
    record["outputs"] = out.outputs(run_ref)
    out.write_text("run_record.json", json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return CaseResult(case_ref, run_id, run_ref, status, validation, figures, record)
