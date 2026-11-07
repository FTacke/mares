"""Command line: ``python -m mares.network_v0 <command> --package ROOT:relative/path``.

Commands (cumulative, see :mod:`mares.network_v0.run`): ``validate``, ``import``, ``analyze``, ``figures``,
``run``; and ``render-case --case ROOT:network_v0/pilots/<case>``, which runs everything for a registered case and draws
the nine standard figures into its ``graphics/``. Every command makes a new run folder below WORKSPACE and prints where it is.
Exit status: 0 = completed, 2 = the package has validation errors or cannot be read, 1 = the run
could not start (unconfigured or unusable storage root, bad arguments).
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from mares.core.roots import RootError, Roots

from .analysis import AnalysisParams
from .geo import DEFAULT_LOCAL_PLACES
from .run import DEFAULT_FORMATS, STAGES, PipelineError, parse_ref, render_case, run_pipeline

_HELP = {
    "validate": "check the package and write the validation report",
    "import": "validate, then write the canonical network (JSON, CSV)",
    "analyze": "import, then write the descriptive tables",
    "figures": "analyze, then draw the nine standard figures (into the run folder)",
    "run": "everything, including the processing report",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m mares.network_v0", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in STAGES:
        command = sub.add_parser(name, help=_HELP[name], description=_HELP[name])
        command.add_argument("--package", required=True, metavar="ROOT:REL", help="logical location of the package folder, e.g. INTAKE:inbox/<delivery>/contents (INTAKE or PRIMARY)")
        command.add_argument("--curation", metavar="ROOT:REL", help="logical location of a curation file (statements about the package, e.g. survey method and review decisions; INTAKE or PRIMARY)")
        command.add_argument("--local-place", action="append", metavar="NAME", help=f"place counted as 'local' (repeatable; default: {', '.join(DEFAULT_LOCAL_PLACES)})")
        command.add_argument("--formats", default=",".join(DEFAULT_FORMATS), help="figure formats, comma separated (png,svg)")
    command = sub.add_parser("render-case", help="everything for a registered case; the nine standard figures into its graphics/")
    command.add_argument("--case", required=True, metavar="ROOT:REL", help="e.g. INTAKE:network_v0/pilots/001 (with data/case.json)")
    command.add_argument("--local-place", action="append", metavar="NAME")
    command.add_argument("--formats", default=",".join(DEFAULT_FORMATS))
    return parser


def main(argv: Sequence[str] | None = None, *, roots: Roots | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        formats = tuple(f.strip() for f in args.formats.split(",") if f.strip())
        if not formats or not set(formats) <= {"svg", "png"}:
            raise PipelineError("formats must be a non-empty subset of png, svg")
        params = AnalysisParams(local_places=tuple(args.local_place) if args.local_place else DEFAULT_LOCAL_PLACES)
        if args.command == "render-case":
            result = render_case(roots or Roots.load(), parse_ref(args.case), formats=formats, params=params)
        else:
            curation = parse_ref(args.curation) if args.curation else None
            result = run_pipeline(roots or Roots.load(), parse_ref(args.package), args.command, curation_ref=curation, params=params, formats=formats)
    except (PipelineError, RootError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    record = result.record
    quality = record["data_quality"] or {}
    print(f"run     {result.run_id}")
    print(f"folder  {result.run_ref.root}:{result.run_ref.rel}")
    print(f"status  {result.status}")
    if quality:
        print(
            f"checks  {quality['technical_validation']} ({quality['errors']} errors, {quality['warnings']} warnings, "
            f"{quality['open_data_questions']} open data questions) - quality state {quality['quality_state']}"
        )
    if record["error"]:
        print(f"error   {record['error']}", file=sys.stderr)
    print(f"files   {len(record['outputs'])}")
    return 0 if result.status == "COMPLETED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
