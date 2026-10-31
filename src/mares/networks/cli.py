"""Command line: ``python -m mares.networks <command> --package ROOT:relative/path``.

Commands (cumulative, see :mod:`mares.networks.run`): ``validate``, ``import``, ``analyze``, ``figures``,
``run``. Every command makes a new run folder below WORKSPACE and prints where it is.
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
from .figures import design
from .run import DEFAULT_FORMATS, STAGES, FigureOptions, PipelineError, parse_ref, run_pipeline

_HELP = {
    "validate": "check the package and write the validation report",
    "import": "validate, then write the canonical network (JSON, CSV)",
    "analyze": "import, then write the descriptive tables",
    "figures": "analyze, then draw all figures",
    "run": "everything, including the processing report",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m mares.networks", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in STAGES:
        command = sub.add_parser(name, help=_HELP[name], description=_HELP[name])
        command.add_argument("--package", required=True, metavar="ROOT:REL", help="logical location of the package folder, e.g. INTAKE:inbox/<delivery>/contents (INTAKE or PRIMARY)")
        command.add_argument("--curation", metavar="ROOT:REL", help="logical location of a curation file (statements about the package, e.g. survey method and review decisions; INTAKE or PRIMARY)")
        command.add_argument("--local-place", action="append", metavar="NAME", help=f"place counted as 'local' (repeatable; default: {', '.join(DEFAULT_LOCAL_PLACES)})")
        command.add_argument("--profiles", default=",".join(design.PROFILES), help="profiles of the core and supplementary figures: clean (standard, in figures/<tier>/) and analysis (figures/analysis/<tier>/)")
        command.add_argument("--language-view", default="mode", help="language view of P2: mode, mode:<code>, lang:<code> or multilingual")
        command.add_argument("--tie-highlight", default="between", choices=("between", "within", "none"), help="which ties G2 brings forward")
        command.add_argument("--formats", default=",".join(DEFAULT_FORMATS), help="figure formats, comma separated (svg,png,pdf)")
    return parser


def main(argv: Sequence[str] | None = None, *, roots: Roots | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        formats = tuple(f.strip() for f in args.formats.split(",") if f.strip())
        if not formats or not set(formats) <= {"svg", "png", "pdf"}:
            raise PipelineError("formats must be a non-empty subset of svg, png, pdf")
        params = AnalysisParams(local_places=tuple(args.local_place) if args.local_place else DEFAULT_LOCAL_PLACES)
        curation = parse_ref(args.curation) if args.curation else None
        options = FigureOptions(
            profiles=tuple(x.strip() for x in args.profiles.split(",") if x.strip()),
            language_view=args.language_view,
            tie_highlight=None if args.tie_highlight == "none" else args.tie_highlight,
        )
        result = run_pipeline(roots or Roots.load(), parse_ref(args.package), args.command, curation_ref=curation, params=params, options=options, formats=formats)
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
