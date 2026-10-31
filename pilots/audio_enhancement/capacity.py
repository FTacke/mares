"""Disk-capacity policy of the audio-enhancement pilot (AEP).

The pilot writes to two places: the run directory under ``WORKSPACE`` and the data disk of the
local Docker engine, which holds the image and the volume with environments and weights. On the
project workstation both sit on the system drive, which other projects share. That disk image
grows with everything written into it and does not shrink when files are deleted inside it, so
space is checked before a command starts and watched while it runs.

Pure logic without Docker, so that it can be tested with temporary directories and fake probes.
"""

from __future__ import annotations

import os
import shutil
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

GIB = 1024**3

# Free space that must remain after a command. Other projects on the workstation stop their own
# development work at 50 GiB free; the pilot stays above that line on its own and never counts on
# anybody else freeing space.
FLOOR_GIB = 60
# A running command is stopped when free space falls below this, whatever was estimated.
STOP_GIB = 55

# Upper bounds of the additional space a command takes, in GiB. Setup figures are the installed
# environment plus weights plus the package cache of that one environment, which is dropped when
# the environment is ready (measured sizes: docs/agent-runs/2026-10-12_c-speicher-docker-audit.md).
BUILD_GIB = 3
STEP_GIB = 2
SETUP_GIB = {
    "whisper": 3,
    "qa": 1,
    "mossformer2": 3,
    "resemble": 4,
    "stupase": 5,
    "crispvoice": 14,
}


@dataclass(frozen=True)
class Decision:
    """Whether a command that needs ``need_gib`` may start with ``free_gib`` free."""

    allowed: bool
    free_gib: float
    need_gib: float
    floor_gib: float

    @property
    def message(self) -> str:
        verdict = "ok" if self.allowed else "refused"
        return (
            f"capacity {verdict}: {self.free_gib:.1f} GiB free, command may take up to "
            f"{self.need_gib:.1f} GiB, {self.floor_gib:.1f} GiB must remain"
        )


def decide(free_bytes: int, need_gib: float, floor_gib: float = FLOOR_GIB) -> Decision:
    free_gib = free_bytes / GIB
    return Decision(free_gib - need_gib >= floor_gib, free_gib, need_gib, floor_gib)


def setup_need_gib(envs: Iterable[str]) -> float:
    """Space for setting up the named environments; no names means all of them."""
    names = list(envs) or list(SETUP_GIB)
    return float(sum(SETUP_GIB[name] for name in names))


def docker_data_dir(environ: dict[str, str] | None = None) -> Path | None:
    """Where Docker Desktop keeps its disk image on Windows, if that directory exists."""
    base = (os.environ if environ is None else environ).get("LOCALAPPDATA", "")
    path = Path(base) / "Docker" if base else None
    return path if path is not None and path.is_dir() else None


def free_bytes(paths: Iterable[Path]) -> int:
    """The smallest free space among the volumes holding ``paths``."""
    return min(shutil.disk_usage(path).free for path in paths)


class Watchdog:
    """Calls ``on_low`` once when ``probe`` reports less than ``stop_gib`` free.

    ``probe`` returns free bytes. A probe that fails is treated as low: space that cannot be
    measured is not assumed to be there.
    """

    def __init__(
        self,
        probe: Callable[[], int],
        on_low: Callable[[], None],
        *,
        stop_gib: float = STOP_GIB,
        interval: float = 10.0,
    ) -> None:
        self._probe = probe
        self._on_low = on_low
        self._stop_bytes = stop_gib * GIB
        self._interval = interval
        self._done = threading.Event()
        self._thread = threading.Thread(target=self._watch, daemon=True)
        self.triggered = False

    def check(self) -> bool:
        """One measurement; True when the limit is undercut (and ``on_low`` was called)."""
        if self.triggered:
            return True
        try:
            low = self._probe() < self._stop_bytes
        except OSError:
            low = True
        if low:
            self.triggered = True
            self._on_low()
        return low

    def _watch(self) -> None:
        while not self._done.wait(self._interval):
            if self.check():
                return

    def __enter__(self) -> "Watchdog":
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._done.set()
        self._thread.join()
