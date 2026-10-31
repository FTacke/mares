"""The processing run: validate -> import -> analyse -> figures -> report.

One call is one run (``RUN-...``) with its own folder ``WORKSPACE/runs/<RUN-ID>``. The ladder of
stages is cumulative: ``validate`` stops after validation, ``import`` also writes the canonical
network, ``analyze`` the descriptive tables, ``figures`` the graphics, ``run`` additionally the
processing report. Everything is recomputed from the input each time; nothing is cached, so a repeated
run on a revised data version is just another run.

Locations: the input is a logical reference (``INTAKE`` or ``PRIMARY`` plus a relative path) -- the package
folder and, optionally, a curation file (statements about the package; see :mod:`mares.network_v0.curation`) --
the output is always below ``WORKSPACE``. ``BACKUP`` and ``EXCHANGE`` are never a data source, and nothing is
written anywhere else. A package with validation errors is not processed further.
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from mares import __version__
from mares.core import ids
from mares.core.hashing import sha256_file
from mares.core.paths import repo_root
from mares.core.refs import StorageRef
from mares.core.roots import Roots

from . import canonical, report as reports
from .curation import NO_CURATION, Curation, CurationError, read_curation
from .analysis import AnalysisParams, descriptive_tables, survey_status
from .build import build_network
from .figures import ego_layouts, ego_network, layouts, registry
from .figures import network as network_figures
from .figures.registry import FigureContext, FigureOptions
from .figures.style import rc, save_figure
from .package import FORMAT, PackageError, read_package
from .validate import validate

STAGES = ("validate", "import", "analyze", "figures", "run")
ALLOWED_INPUT_ROOTS = ("INTAKE", "PRIMARY")  # BACKUP and EXCHANGE are never a data source
DEFAULT_FORMATS = ("svg", "png", "pdf")

class PipelineError(RuntimeError):
    """The run cannot start or continue (an unusable input location, an unknown stage ...)."""


@dataclass(frozen=True)
class RunResult:
    run_id: str
    run_ref: StorageRef
    run_dir: Path
    status: str  # COMPLETED | FAILED_VALIDATION
    record: dict[str, object]


def parse_ref(text: str) -> StorageRef:
    """``INTAKE:inbox/delivery/contents`` -> a logical reference."""
    root, separator, rel = text.partition(":")
    if not separator:
        raise PipelineError("a package location is written ROOT:relative/path, for example INTAKE:inbox/<delivery>/contents")
    try:
        return StorageRef(root, rel)
    except ValueError as error:
        raise PipelineError(str(error)) from error


def _utc(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_state() -> tuple[str | None, bool]:
    """The commit of the checkout (``None`` if there is none yet) and whether the tree has changes."""
    if shutil.which("git") is None:
        return None, False
    root = repo_root()

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)

    head = git("rev-parse", "--verify", "HEAD")
    commit = head.stdout.strip() if head.returncode == 0 else None
    dirty = bool(git("status", "--porcelain").stdout.strip())
    return commit, dirty


def _software() -> dict[str, object]:
    import matplotlib
    import networkx
    import numpy

    commit, dirty = _git_state()
    return {
        "mares_version": __version__,
        "git_commit": commit,
        "git_dirty": dirty,
        "python": platform.python_version(),
        "dependencies": {"networkx": networkx.__version__, "matplotlib": matplotlib.__version__, "numpy": numpy.__version__},
    }


class _RunFolder:
    """Writes into one run folder, and only there."""

    def __init__(self, base: Path) -> None:
        self.base = base

    def path(self, rel: str) -> Path:
        StorageRef("WORKSPACE", rel)  # validates: relative POSIX path, no '..', no drive
        return self.base.joinpath(*rel.split("/"))

    def write_text(self, rel: str, text: str) -> Path:
        target = self.path(rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "x", encoding="utf-8", newline="\n") as handle:  # 'x': never overwrite
            handle.write(text)
        return target

    def outputs(self, run_ref: StorageRef, exclude: tuple[str, ...] = ()) -> list[dict[str, object]]:
        entries = []
        for path in sorted(p for p in self.base.rglob("*") if p.is_file()):
            rel = path.relative_to(self.base).as_posix()
            if rel in exclude:
                continue
            entries.append(
                {"ref": run_ref.child(*rel.split("/")).to_dict(), "rel": rel, "sha256": sha256_file(path), "size": path.stat().st_size}
            )
        return entries


def run_pipeline(
    roots: Roots,
    package: StorageRef,
    stage: str = "run",
    *,
    curation_ref: StorageRef | None = None,
    params: AnalysisParams | None = None,
    options: FigureOptions | None = None,
    formats: tuple[str, ...] = DEFAULT_FORMATS,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> RunResult:
    if stage not in STAGES:
        raise PipelineError(f"unknown stage {stage!r}; one of {', '.join(STAGES)}")
    if package.root not in ALLOWED_INPUT_ROOTS:
        raise PipelineError(f"{package.root} is not a permitted data source; use one of {', '.join(ALLOWED_INPUT_ROOTS)}")
    params = params or AnalysisParams()
    options = options or FigureOptions()
    level = STAGES.index(stage)

    if curation_ref is not None and curation_ref.root not in ALLOWED_INPUT_ROOTS:
        raise PipelineError(f"{curation_ref.root} is not a permitted data source; use one of {', '.join(ALLOWED_INPUT_ROOTS)}")
    source_dir = roots.resolve(package)  # raises RootError for an unconfigured or unreachable root
    curation_file = roots.resolve(curation_ref) if curation_ref is not None else None
    started = clock()
    run_id = ids.new_run_id(started)
    run_ref = StorageRef("WORKSPACE", f"runs/{run_id}")
    run_dir = roots.resolve(run_ref, writable=True)
    run_dir.mkdir(parents=True, exist_ok=False)
    folder = _RunFolder(run_dir)

    try:
        dataset = read_package(source_dir)
        curation = read_curation(curation_file) if curation_file is not None else NO_CURATION
    except (PackageError, CurationError) as error:
        record = _record(run_id, stage, "FAILED_IMPORT", started, clock(), package, None, None, params, formats, [], str(error),
                         curation_ref=curation_ref)
        folder.write_text("run_record.json", json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        return RunResult(run_id, run_ref, run_dir, "FAILED_IMPORT", record)

    validation = validate(dataset, local_places=params.local_places, curation=curation)
    folder.write_text("validation_report.md", reports.validation_markdown(dataset, validation))
    folder.write_text("validation_report.json", json.dumps(reports.validation_dict(validation), indent=2, ensure_ascii=False) + "\n")
    folder.write_text("review/review_register.csv", reports.review_register_csv(validation))

    status = None
    tables = ()
    if validation.errors:
        outcome = "FAILED_VALIDATION"
    else:
        outcome = "COMPLETED"
        network = build_network(dataset, coverage_complete=curation.survey.coverage_complete)
        status = survey_status(dataset, network, curation)
        if level >= 1:
            folder.write_text("canonical/dataset.json", canonical.dataset_json(dataset, network, params, curation))
            folder.write_text("canonical/contacts.csv", canonical.contacts_csv(dataset, params))
            folder.write_text("canonical/ties.csv", canonical.ties_csv(network))
            folder.write_text("canonical/group_memberships.csv", canonical.memberships_csv(dataset))
        if level >= 2:
            tables = descriptive_tables(dataset, network, params, curation)
            for table in tables:
                folder.write_text(f"analysis/{table.key}.csv", table.to_csv())
            folder.write_text("analysis/tables.md", "\n\n".join(t.to_markdown() for t in tables) + "\n")
            folder.write_text("analysis/survey_status.json", json.dumps(status.to_dict(), indent=2, ensure_ascii=False) + "\n")
        if level >= 3:
            figures_dir = folder.path("figures")
            figures_dir.mkdir(parents=True, exist_ok=True)
            context = FigureContext(
                dataset, status, params, network,
                structure=network_figures.build_structure(network, params_layout(params)),  # one layout for B1 and B2
                ego_structure=ego_network.build_ego_structure(network),  # B3 and P2: the same contact positions, ego added
                options=options,
            )
            for spec in registry.SPECS:
                for profile in registry.profiles_of(spec, options):
                    target = registry.target_dir(figures_dir, spec, profile)
                    target.mkdir(parents=True, exist_ok=True)
                    figure = spec.build(context, profile or "clean")
                    with rc():
                        save_figure(figure, target / spec.stem, formats)
            folder.write_text("figures/figures_index.json", json.dumps(registry.figure_index(options, formats, status), indent=2, ensure_ascii=False) + "\n")

    finished = clock()
    if level >= 4:
        record = _record(run_id, stage, outcome, started, finished, package, dataset, validation, params, formats, [], None, status,
                         curation=curation, curation_ref=curation_ref, options=options)
        outputs = folder.outputs(run_ref, exclude=("run_record.json", "processing_report.md"))
        folder.write_text(
            "processing_report.md",
            reports.processing_markdown(record=record, dataset=dataset, report=validation, status=status, curation=curation,
                                        tables=tables, outputs=outputs),
        )
    outputs = folder.outputs(run_ref, exclude=("run_record.json",))
    record = _record(run_id, stage, outcome, started, finished, package, dataset, validation, params, formats, outputs, None, status,
                     curation=curation, curation_ref=curation_ref, options=options)
    folder.write_text("run_record.json", json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return RunResult(run_id, run_ref, run_dir, outcome, record)


def params_layout(params: AnalysisParams) -> str:
    """The layout variant of the network figures: a documented choice, see the layout comparison."""
    return layouts.DEFAULT_VARIANT


def _record(run_id, stage, outcome, started, finished, package, dataset, validation, params, formats, outputs, error, status=None,
            *, curation: Curation = NO_CURATION, curation_ref: StorageRef | None = None, options: FigureOptions | None = None):
    groups = validation.by_category() if validation is not None else {}
    return {
        "schema": "mares-run-record/v0-draft",
        "run_id": run_id,
        "command": stage,
        "status": outcome,
        "error": error,
        "started_utc": _utc(started),
        "finished_utc": _utc(finished),
        "package_format": FORMAT,
        "input": {
            "ref": package.to_dict(),
            "files": [] if dataset is None else [{"name": f.name, "sha256": f.sha256, "size": f.size} for f in dataset.files],
            "curation": None
            if curation_ref is None or curation.sha256 is None
            else {"ref": curation_ref.to_dict(), "sha256": curation.sha256, "made_on": curation.made_on, "made_by": curation.made_by},
        },
        "source": None
        if dataset is None
        else {
            "source_label": dataset.case.source_label,
            "canonical_case_id": dataset.case.canonical_case_id,
            "session_date": dataset.session.session_date,
            "interview_type": dataset.session.interview_type,
            "package_version": dataset.session.package_version,
            "provenance_note": "student collection per package; cohort, collector and instrument version not registered",
        },
        "survey_method": {
            "alter_alter_elicitation": curation.survey.elicitation,
            "alter_alter_documentation": curation.survey.documentation,
            "group_rule": curation.survey.group_rule,
            "pair_coverage": curation.survey.pair_coverage,
            "basis": curation.survey.basis,
        },
        "dataset_version": None,
        "software": _software(),
        "parameters": {**params.to_dict(), "figure_formats": list(formats), "layout_seed": layouts.SEED,
                       "network_layout": layouts.DEFAULT_VARIANT, "ego_layout": ego_layouts.DEFAULT_EGO_VARIANT, "stage": stage,
                       "figure_options": (options or FigureOptions()).to_dict(), "font": "DejaVu Sans"},
        "data_quality": None
        if validation is None
        else {
            "technical_validation": validation.technical_status,
            "errors": len(validation.errors),
            "warnings": len(validation.warnings),
            "open_data_questions": validation.open_count,
            "review_hints_by_category": {c.value: len(q) for c, q in groups.items()},
            "scientific_validation": "not performed",
            "quality_state": "UNREVIEWED",
            "release_state": "NOT_DECIDED",
            "preservation_state": "NOT_PRESERVED",
            "backup_state": "NO_COPY",
        },
        "survey_status": None if status is None else status.to_dict(),
        "outputs": [{"ref": o["ref"], "sha256": o["sha256"], "size": o["size"]} for o in outputs],
        "methodological_limits": list(reports.limits(status)),
    }

