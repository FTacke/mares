"""Disk-capacity policy and cleanup scope of the audio-enhancement pilot.

No Docker, no network and no configured root: the policy is pure logic, and the launcher is only
inspected, never run against an engine.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import sys
import threading

import pytest

from mares.core.paths import repo_path

PILOT = repo_path("pilots", "audio_enhancement")


def _load(name: str):
    sys.path.insert(0, str(PILOT))
    try:
        spec = importlib.util.spec_from_file_location(f"aep_{name}", PILOT / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module  # dataclasses look their module up there
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(PILOT))


capacity = _load("capacity")
aep = _load("aep")
GIB = capacity.GIB


def test_command_is_refused_when_it_could_undercut_the_floor():
    assert capacity.decide(80 * GIB, need_gib=14, floor_gib=60).allowed
    refused = capacity.decide(73 * GIB, need_gib=14, floor_gib=60)
    assert not refused.allowed
    assert "refused" in refused.message and "73.0" in refused.message


def test_floor_keeps_the_pilot_above_the_shared_limit_without_help_from_others():
    # other projects stop development work at 50 GiB free; the pilot must stop earlier by itself
    assert capacity.FLOOR_GIB > capacity.STOP_GIB > 50


def test_setup_need_covers_every_environment_and_defaults_to_all():
    assert capacity.setup_need_gib([]) == sum(capacity.SETUP_GIB.values())
    assert capacity.setup_need_gib(["qa", "whisper"]) == capacity.SETUP_GIB["qa"] + capacity.SETUP_GIB["whisper"]
    with pytest.raises(KeyError):
        capacity.setup_need_gib(["unknown"])


def test_free_bytes_takes_the_tightest_volume(tmp_path):
    assert capacity.free_bytes([tmp_path, tmp_path]) == pytest.approx(shutil.disk_usage(tmp_path).free, rel=0.01)


def test_docker_data_dir_is_none_unless_it_exists(tmp_path):
    assert capacity.docker_data_dir({}) is None
    assert capacity.docker_data_dir({"LOCALAPPDATA": str(tmp_path)}) is None
    (tmp_path / "Docker").mkdir()
    assert capacity.docker_data_dir({"LOCALAPPDATA": str(tmp_path)}) == tmp_path / "Docker"


def test_watchdog_stops_once_when_space_runs_low():
    readings = iter([70 * GIB, 56 * GIB, 54 * GIB, 40 * GIB])
    stopped = []
    watchdog = capacity.Watchdog(lambda: next(readings), lambda: stopped.append(1), stop_gib=55)
    assert not watchdog.check()
    assert not watchdog.check()
    assert watchdog.check()
    assert watchdog.check()  # stays triggered, does not stop twice and does not probe again
    assert stopped == [1]


def test_watchdog_treats_an_unmeasurable_volume_as_low():
    def probe() -> int:
        raise OSError("volume gone")

    stopped = []
    assert capacity.Watchdog(probe, lambda: stopped.append(1)).check()
    assert stopped == [1]


def test_watchdog_thread_fires_during_a_job_and_ends_with_it():
    low = threading.Event()
    with capacity.Watchdog(lambda: 10 * GIB, low.set, interval=0.01) as watchdog:
        assert low.wait(2)
    assert watchdog.triggered
    with capacity.Watchdog(lambda: 100 * GIB, low.set, interval=0.01) as quiet:
        pass
    assert not quiet.triggered


def test_clean_targets_never_reach_weights_runs_or_anything_outside_the_volume():
    for target, paths in aep.CLEAN_TARGETS.items():
        for path in paths:
            assert re.fullmatch(r"[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*", path), (target, path)
            assert ".." not in path.split("/")
            assert not path.startswith(("models", "vendor")), (target, path)
    assert aep.CLEAN_TARGETS["cache"] == ["uv-cache"]
    assert {f"env:{name}" for name in capacity.SETUP_GIB} == set(aep.CLEAN_TARGETS) - {"cache"}


def test_setup_script_drops_the_package_cache_and_skips_ready_environments():
    script = (PILOT / "container" / "setup_envs.sh").read_text(encoding="utf-8")
    assert "trap drop_cache EXIT" in script
    assert script.count("drop_cache") >= 3  # definition, trap, after every environment
    assert '[ -e "$ROOT/.ready/$name" ]' in script
    assert "UV_TORCH_BACKEND=cpu" in script
    assert "\r" not in script
