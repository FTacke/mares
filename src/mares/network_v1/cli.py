"""Command line of network_v1: ``python -m mares.networks v1 <command> ...``.

Commands:

* ``validate --case ROOT:network_v1/pilots/<case>``   check one case; report in WORKSPACE/runs
* ``render   --case ROOT:network_v1/pilots/<case>``   check, then draw the eight figures into the case's graphics/
* ``render-all --root INTAKE``                         every case of the tree (test cases included, marked as such)
* ``list --root INTAKE [--empirical]``                 cases with type, provenance and eligibility
* ``install-test-cases --root INTAKE [--v0-package ROOT:rel]``
                                                       install 002 (synthetic) and, with a v0 package, build 001

Exit status: 0 = completed, 2 = validation errors in at least one case, 1 = could not start.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from mares.core.refs import StorageRef
from mares.core.roots import RootError, Roots

from .case import is_empirical
from .run import ALLOWED_ROOTS, TREE, PipelineError, list_cases, process_case
from .testcases import FICTIONALIZED_CODE, SYNTHETIC_CODE, TestCaseError, build_fictionalized, install_synthetic


def _ref(text: str) -> StorageRef:
    root, sep, rel = text.partition(":")
    if not sep:
        raise PipelineError("a location is written ROOT:relative/path, e.g. INTAKE:network_v1/pilots/002_test_synthetic")
    try:
        return StorageRef(root, rel)
    except ValueError as error:
        raise PipelineError(str(error)) from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m mares.networks v1", description="network_v1: validate and render cases")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, text in (("validate", "check one case"), ("render", "check one case and draw the eight standard figures")):
        cmd = sub.add_parser(name, help=text)
        cmd.add_argument("--case", required=True, metavar="ROOT:REL", help=f"e.g. INTAKE:{TREE}/pilots/{SYNTHETIC_CODE}")
        cmd.add_argument("--formats", default="png", help="png and/or svg, comma separated (default png)")
    cmd = sub.add_parser("render-all", help="render every case of the tree")
    cmd.add_argument("--root", required=True, choices=ALLOWED_ROOTS)
    cmd.add_argument("--formats", default="png")
    cmd = sub.add_parser("list", help="list the cases of the tree")
    cmd.add_argument("--root", required=True, choices=ALLOWED_ROOTS)
    cmd.add_argument("--empirical", action="store_true", help="only cases that may enter empirical overviews")
    cmd = sub.add_parser("install-test-cases", help="install the test cases into the tree")
    cmd.add_argument("--root", required=True, choices=ALLOWED_ROOTS)
    cmd.add_argument("--v0-package", metavar="ROOT:REL", help="v0 pilot package to build 001 from (INTAKE or PRIMARY)")
    return parser


def _print_result(result) -> None:
    v = result.validation
    print(f"case    {result.case_ref.root}:{result.case_ref.rel}")
    print(f"run     {result.run_id} ({result.run_ref.root}:{result.run_ref.rel})")
    print(f"checks  {v.status} ({len(v.errors)} errors, {len(v.warnings)} warnings, {len(v.notes)} notes)")
    for f in result.figures:
        print(f"figure  {f['code']}  {f['status']}" + (f"  ({f['reason']})" if f["reason"] else ""))
    print(f"status  {result.status}")


def main(argv: Sequence[str] | None = None, *, roots: Roots | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        roots = roots or Roots.load()
        if args.command in ("validate", "render"):
            formats = tuple(x.strip() for x in args.formats.split(",") if x.strip()) if args.command == "render" else ()
            if args.command == "validate":
                from .case import read_case
                from .run import check_case_ref
                from .validate import validate

                ref = _ref(args.case)
                check_case_ref(ref)
                validation = validate(read_case(roots.resolve(ref)))
                for f in validation.findings:
                    print(f"{f.level:8} {f.code:28} {f.message}")
                print(f"status  {validation.status}")
                return 2 if validation.errors else 0
            result = process_case(roots, _ref(args.case), formats=formats)
            _print_result(result)
            return 0 if result.status == "COMPLETED" else 2
        if args.command == "render-all":
            formats = tuple(x.strip() for x in args.formats.split(",") if x.strip())
            worst = 0
            for ref, _meta in list_cases(roots, args.root):
                result = process_case(roots, ref, formats=formats)
                _print_result(result)
                print()
                worst = max(worst, 0 if result.status == "COMPLETED" else 2)
            return worst
        if args.command == "list":
            for ref, meta in list_cases(roots, args.root):
                if args.empirical and not is_empirical(meta):
                    continue
                print(f"{ref.rel:55} {meta.get('case_type', '?'):8} {meta.get('provenance', '?'):26} "
                      f"empirical={'yes' if is_empirical(meta) else 'no'}")
            return 0
        if args.command == "install-test-cases":
            base = StorageRef(args.root, f"{TREE}/pilots")
            roots.resolve(StorageRef(args.root, f"{TREE}/cases"), writable=True).mkdir(parents=True, exist_ok=True)
            target = roots.resolve(base.child(SYNTHETIC_CODE), writable=True)
            names = install_synthetic(target)
            print(f"installed {SYNTHETIC_CODE}: {len(names)} files")
            if args.v0_package:
                package = _ref(args.v0_package)
                if package.root not in ALLOWED_ROOTS:
                    raise PipelineError(f"{package.root} is not a permitted data source")
                summary = build_fictionalized(roots.resolve(package), roots.resolve(base.child(FICTIONALIZED_CODE), writable=True),
                                              source_ref=f"{package.root}:{package.rel}")
                print(f"built     {FICTIONALIZED_CODE}: {summary['contacts']} contacts, {summary['groups']} groups, "
                      f"{summary['memberships']} memberships; filled because missing in v0: {summary['filled'] or 'nothing'}")
            return 0
    except (PipelineError, RootError, TestCaseError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 1
