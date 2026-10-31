"""Shared helpers of the pilot's container scripts.

Console lines starting with ``AEP:`` are echoed by the host launcher. They must only carry
figures: never transcript text and never the name of a recording.
"""

from __future__ import annotations

import datetime
import json
import os
import resource
import time
from pathlib import Path

RUN = Path("/run")
INPUT_48K = RUN / "02_input" / "input_5min_48k_mono.wav"
INPUT_16K = RUN / "02_input" / "input_5min_16k_mono.wav"
INPUT_STEREO = RUN / "02_input" / "input_5min_48k_stereo.wav"
FULL_16K = RUN / "01_transcript" / "full_16k_mono.flac"
ENHANCED = RUN / "03_enhanced"
THREADS = int(os.environ.get("AEP_THREADS", "8"))


def say(message: str) -> None:
    print(f"AEP: {message}", flush=True)


def utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def peak_rss_gb() -> float:
    own = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    children = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    return max(own, children) / 1024**2


class Step:
    """Times a step and writes its record to ``logs/<name>.json``."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.record: dict = {"step": name, "started": utcnow(), "threads": THREADS, "device": "cpu"}
        self._t0 = time.perf_counter()

    def finish(self, **fields) -> None:
        self.record.update(fields)
        self.record["finished"] = utcnow()
        self.record["wall_seconds"] = round(time.perf_counter() - self._t0, 1)
        self.record["peak_rss_gb"] = round(peak_rss_gb(), 2)
        path = RUN / "logs" / f"{self.name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.record, indent=2, ensure_ascii=False), encoding="utf-8")
        say(
            f"{self.name}: done in {self.record['wall_seconds']} s, "
            f"peak RSS {self.record['peak_rss_gb']} GB"
        )
