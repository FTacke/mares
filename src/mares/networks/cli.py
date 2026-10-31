"""Dispatch ``python -m mares.networks`` to the pipeline of a dataset version.

``v1 ...`` goes to :mod:`mares.network_v1.cli`; ``v0 ...`` and every command without a version prefix go to
:mod:`mares.network_v0.cli`, so the documented v0 calls keep working unchanged.
"""

from __future__ import annotations

import sys
from typing import Sequence

from mares.core.roots import Roots


def main(argv: Sequence[str] | None = None, *, roots: Roots | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "v1":
        from mares.network_v1.cli import main as v1_main

        return v1_main(args[1:], roots=roots)
    if args and args[0] == "v0":
        args = args[1:]
    from mares.network_v0.cli import main as v0_main

    return v0_main(args, roots=roots)


if __name__ == "__main__":
    raise SystemExit(main())
