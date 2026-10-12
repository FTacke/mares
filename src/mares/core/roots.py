"""Named storage roots and their fail-closed resolution.

This module is the only place that turns a root name into a physical path and the only reader of
the ``MARES_*_ROOT`` variables. Everything else asks it::

    roots = Roots.load()
    primary = roots.require("PRIMARY")                 # raises, naming the variable, if unusable
    backup = roots.optional("BACKUP")                  # None when deliberately not configured
    path = roots.resolve(StorageRef("PRIMARY", "preservation/manifests/x.json"))

Rules (``docs/architecture/storage-contract.md``):

* The names and their variables are declared in ``config/storage_roots.toml``; the values come
  from the process environment or the gitignored ``.env`` of the checkout (the process wins).
* There is no default location and no fallback -- not into the checkout, not to another root, not
  to another drive. A set value that cannot be used is a refusal, never a reason to substitute.
* A root is never created by resolving it: a missing directory on a network share means the share
  is not mounted. An unreachable root's content is unknown, not empty.
* No path appears in this module or in tracked configuration.
"""

from __future__ import annotations

import enum
import os
import re
import tomllib
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .paths import repo_path, repo_root
from .refs import ROOT_NAME, StorageRef

SCHEMA = "mares-storage-roots/v1"
ENV_PREFIX = "MARES_"

_VARIABLE = re.compile(r"MARES_[A-Z0-9]+(?:_[A-Z0-9]+)*_ROOT")
_ENV_LINE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)")
_SPEC_KEYS = {"env", "required", "authoritative", "read_only", "purpose"}


class RootState(enum.Enum):
    """What resolving a root name yields. Only ``AVAILABLE`` lets a caller proceed."""

    NOT_DECLARED = "NOT_DECLARED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    UNUSABLE = "UNUSABLE"
    UNREACHABLE = "UNREACHABLE"
    READ_ONLY = "READ_ONLY"
    AVAILABLE = "AVAILABLE"


class RootError(RuntimeError):
    """A storage root may not be used. Never caught to fall back to another location."""

    def __init__(self, name: str, state: RootState, message: str) -> None:
        super().__init__(message)
        self.name = name
        self.state = state


class RootConfigError(RuntimeError):
    """The tracked root declaration or the workstation ``.env`` is malformed."""


@dataclass(frozen=True)
class RootSpec:
    name: str
    variable: str
    required: bool
    authoritative: bool
    read_only: bool
    purpose: str


def load_root_specs(path: Path | None = None) -> dict[str, RootSpec]:
    """Read the declared roots. Anything but the documented shape is an error, not interpreted."""
    path = repo_path("config", "storage_roots.toml") if path is None else Path(path)
    try:
        with open(path, "rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise RootConfigError(f"{path.name}: cannot be read: {error}") from error
    if data.get("schema") != SCHEMA or set(data) != {"schema", "roots"}:
        raise RootConfigError(f"{path.name}: expected schema {SCHEMA!r} and a [roots] table only")

    specs: dict[str, RootSpec] = {}
    for name, fields in data["roots"].items():
        if not ROOT_NAME.fullmatch(name) or not isinstance(fields, dict) or set(fields) != _SPEC_KEYS:
            raise RootConfigError(f"{path.name}: root {name!r} must have exactly {sorted(_SPEC_KEYS)}")
        flags = (fields["required"], fields["authoritative"], fields["read_only"])
        if not all(isinstance(flag, bool) for flag in flags) or not isinstance(fields["purpose"], str):
            raise RootConfigError(f"{path.name}: root {name!r} has a field of the wrong type")
        if not isinstance(fields["env"], str) or not _VARIABLE.fullmatch(fields["env"]):
            raise RootConfigError(f"{path.name}: {name}.env must be a MARES_*_ROOT variable name")
        specs[name] = RootSpec(name, fields["env"], *flags, fields["purpose"])

    variables = [spec.variable for spec in specs.values()]
    if len(set(variables)) != len(variables):
        raise RootConfigError(f"{path.name}: two roots share one environment variable")
    if sum(spec.authoritative for spec in specs.values()) != 1:
        raise RootConfigError(f"{path.name}: exactly one root is authoritative")
    return specs


def read_env_file(path: Path) -> dict[str, str]:
    """Parse a workstation ``.env`` (``NAME=value`` lines, ``#`` comments). Reads, never exports."""
    values: dict[str, str] = {}
    for number, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _ENV_LINE.fullmatch(line)
        if match is None:
            raise RootConfigError(f"{Path(path).name}:{number}: not a NAME=value line")
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[match.group(1)] = value
    return values


def _segments(path: str | Path) -> tuple[str, ...]:
    """A path as case-folded segments, split at both separators.

    Lexical and case-insensitive on every platform: no link resolution and no I/O, so it works on
    an unreachable root, and it refuses a configuration that would only be safe on a
    case-sensitive file system.
    """
    return tuple(part.casefold() for part in re.split(r"[\\/]+", os.path.normpath(path)) if part)


def _within(path: str | Path, parent: str | Path) -> bool:
    child, base = _segments(path), _segments(parent)
    return child[: len(base)] == base


def _write_probe(root: Path) -> bool:
    """Create and remove an empty, uniquely named probe file directly in the root."""
    marker = root / f".mares_write_probe-{uuid.uuid4().hex[:12]}"
    try:
        with open(marker, "xb"):
            pass
    except OSError:
        return False
    try:
        marker.unlink()
    except OSError:
        pass
    return True


class Roots:
    """The declared roots together with one machine's values for them."""

    def __init__(
        self,
        specs: Mapping[str, RootSpec],
        env: Mapping[str, str],
        *,
        checkout: Path | None = None,
    ) -> None:
        self._specs = dict(specs)
        # Only MARES_* names are kept, so the mapping cannot leak or reconfigure anything else.
        self._env = {name: value for name, value in env.items() if name.startswith(ENV_PREFIX)}
        self._checkout = repo_root() if checkout is None else Path(checkout)

    @classmethod
    def load(
        cls,
        *,
        process_env: Mapping[str, str] | None = None,
        env_file: Path | None = None,
        config_file: Path | None = None,
    ) -> "Roots":
        """The roots of this machine: the process environment over the checkout's ``.env``.

        A missing ``.env`` is legal and means that nothing is configured from it.
        """
        env_file = repo_path(".env") if env_file is None else Path(env_file)
        values = read_env_file(env_file) if env_file.is_file() else {}
        values.update(os.environ if process_env is None else process_env)
        return cls(load_root_specs(config_file), values)

    @property
    def specs(self) -> dict[str, RootSpec]:
        return dict(self._specs)

    def _configured_value(self, spec: RootSpec) -> str:
        return self._env.get(spec.variable, "").strip()

    def _unusable_reason(self, spec: RootSpec, value: str) -> str | None:
        """Lexical checks only (no I/O); ``normpath`` rather than ``resolve``, which blocks on an
        offline network share."""
        if not os.path.isabs(value):
            return "a storage root is an absolute path"
        root = Path(os.path.normpath(value))
        if root == Path(root.anchor):
            return "a filesystem root is not a storage root"
        if _within(root, self._checkout):
            return "a storage root may not lie inside the repository checkout"
        for other in self._specs.values():
            other_value = self._configured_value(other)
            if other.name == spec.name or not other_value or not os.path.isabs(other_value):
                continue
            if _within(root, other_value) or _within(other_value, root):
                return f"it overlaps the root {other.name}: every root has exactly one role"
        return None

    def _inspect(self, name: str, writable: bool) -> tuple[RootState, Path | None, str]:
        spec = self._specs.get(name)
        if spec is None:
            return RootState.NOT_DECLARED, None, f"{name}: no such root is declared in config/storage_roots.toml"
        value = self._configured_value(spec)
        if not value:
            return RootState.NOT_CONFIGURED, None, f"{name}: {spec.variable} is not set"
        reason = self._unusable_reason(spec, value)
        if reason is not None:
            return RootState.UNUSABLE, None, f"{name} ({spec.variable}): {reason}"
        root = Path(os.path.normpath(value))
        try:
            reachable = root.is_dir()
        except OSError:
            reachable = False
        if not reachable:
            return (
                RootState.UNREACHABLE,
                None,
                f"{name}: {spec.variable} does not name a reachable directory (its content is unknown, not empty)",
            )
        if writable:
            if spec.read_only:
                return RootState.READ_ONLY, None, f"{name}: this root is declared read-only"
            if not _write_probe(root):
                return RootState.READ_ONLY, None, f"{name}: {spec.variable} is not writable"
        return RootState.AVAILABLE, root, ""

    def state(self, name: str, *, writable: bool = False) -> RootState:
        """The state of a root. Never raises and never substitutes."""
        return self._inspect(name, writable)[0]

    def status(self) -> dict[str, RootState]:
        """Every declared root with its state, for status output and reports."""
        return {name: self.state(name) for name in sorted(self._specs)}

    def require(self, name: str, *, writable: bool = False) -> Path:
        """The directory of a root, or a :class:`RootError` raised before anything is written."""
        state, root, message = self._inspect(name, writable)
        if root is None:
            raise RootError(name, state, message)
        return root

    def optional(self, name: str, *, writable: bool = False) -> Path | None:
        """Like :meth:`require`, but ``None`` for an optional root that is not configured.

        ``None`` is a statement, never a default. A value that is set and unusable still raises,
        and so does an unconfigured root that is declared required.
        """
        spec = self._specs.get(name)
        if spec is not None and not spec.required and not self._configured_value(spec):
            return None
        return self.require(name, writable=writable)

    def resolve(self, ref: StorageRef, *, writable: bool = False) -> Path:
        """The physical path of a logical reference on this machine."""
        return self.require(ref.root, writable=writable).joinpath(*ref.parts)
