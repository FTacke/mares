"""Repository-internal paths.

Resources that belong to the repository (configuration, templates, synthetic examples) are found
relative to the checkout, which this module derives from its own location. Nothing here reads an
environment variable, and nothing here knows where the checkout lies on a machine. External
locations are the business of :mod:`mares.core.roots`.
"""

from __future__ import annotations

from pathlib import Path


class RepoLayoutError(RuntimeError):
    """The package is not running from a MARES checkout (for example a plain wheel install)."""


def repo_root() -> Path:
    """The checkout this module lives in.

    The check is on a fact (the checkout's own files), never on a directory name: renaming or
    moving the checkout is harmless.
    """
    root = Path(__file__).resolve().parents[3]
    if not (root / "pyproject.toml").is_file() or not (root / "config").is_dir():
        raise RepoLayoutError(
            "mares must run from its repository checkout (install it with `pip install -e .`): "
            "pyproject.toml and config/ were not found above the package"
        )
    return root


def repo_path(*parts: str) -> Path:
    """A path inside the repository, given relative to its root."""
    return repo_root().joinpath(*parts)
