"""Experimental figures of network_v1 -- outside the nine standard figures, never part of a regular run.

``g3-geburtsland`` (:mod:`~mares.network_v1.figures.birth_country`): G3 by birth country, total and local view,
written to ``<case>/experimental/g3_geburtsland/`` (only these files, replaced on a re-run, nothing deleted); a run
record goes to ``WORKSPACE/runs/<RUN-ID>/``. It holds counts only, never the countries of a case. ``graphics/`` is not
touched. The orientation map of the local view uses the basemap of X1 (``WORKSPACE:cache/basemaps/...``); without it
the map shows the excerpt on a plain background (recorded).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from mares.core import ids
from mares.core.refs import StorageRef
from mares.core.roots import Roots
from mares.network_v0.figures.style import rc, save_figure

from .case import read_case
from .figures.base import Context, file_name
from .figures.birth_country import CODE, VIEWS, birth_figure, countries, figure_name, local_context, zones_of
from .figures.maps import BASEMAP, read_basemap
from .run import check_case_ref
from .validate import FAILED, validate

G3_BIRTH_DIR = ("experimental", "g3_geburtsland")


@dataclass(frozen=True)
class ExperimentResult:
    case_ref: StorageRef
    status: str  # COMPLETED | FAILED_VALIDATION
    outputs: list[str]
    run_id: str
    summary: dict


def g3_birth_summary(ctx: Context) -> dict:
    """Counts for the run record (no country names or codes)."""
    cs = countries(ctx)
    local = local_context(ctx)
    zones = zones_of(local)
    return {
        "contacts": {"total": len(ctx.case.contacts), "local": len(local.case.contacts)},
        "groups": {"total": len([g for g in ctx.case.groups if ctx.case.members(g.id)]), "local": len(local.case.groups)},
        "confirmed_ties": {"total": len(ctx.derived.confirmed_edges), "local": len(local.derived.confirmed_edges)},
        "local_zones": 2 if zones else (1 if local.case.contacts else 0),
        "birth_countries": len({k for k in cs.of.values() if k is not None}),
        "birth_country_missing": sum(1 for k in cs.of.values() if k is None),
    }


def render_g3_birth(roots: Roots, case_ref: StorageRef, *, formats: tuple[str, ...] = ("png", "svg")) -> ExperimentResult:
    check_case_ref(case_ref)
    case = read_case(roots.resolve(case_ref))
    validation = validate(case)
    basemap_path = roots.resolve(StorageRef("WORKSPACE", BASEMAP))
    countries_map = read_basemap(basemap_path) if basemap_path.is_file() else None  # sources first: no empty run folder
    run_id = ids.new_run_id(datetime.now(timezone.utc))
    run_dir = roots.resolve(StorageRef("WORKSPACE", f"runs/{run_id}"), writable=True)
    run_dir.mkdir(parents=True, exist_ok=False)
    record = {"format": "mares-run-record/v0-draft", "pipeline": "network_v1 experiment g3-geburtsland", "run_id": run_id,
              "case": {"ref": case_ref.to_dict(), "case_code": case.code}, "standard_figure": False, "derived_from": CODE,
              "basemap": f"WORKSPACE:{BASEMAP}" if countries_map else "missing (orientation map without land)",
              "note": "Experiment, keine Standardgrafik; technische Prüfung, keine wissenschaftliche Validierung."}
    outputs: list[str] = []
    summary: dict = {}
    if validation.status == FAILED:
        status = "FAILED_VALIDATION"
    else:
        ctx = Context(case, validation.derived)
        target = roots.resolve(case_ref.child(*G3_BIRTH_DIR), writable=True)
        target.mkdir(parents=True, exist_ok=True)
        for view in VIEWS:
            stem = target / file_name(case.code, CODE, figure_name(view), "png")[:-4]
            with rc():
                outputs += [p.name for p in save_figure(birth_figure(ctx, view, countries_map), stem, formats)]
        summary = g3_birth_summary(ctx)
        status = "COMPLETED"
    record.update(status=status, outputs=[case_ref.child(*G3_BIRTH_DIR, n).to_dict() for n in outputs], summary=summary)
    (run_dir / "run_record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return ExperimentResult(case_ref, status, outputs, run_id, summary)
