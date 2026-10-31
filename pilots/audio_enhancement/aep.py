"""Host-side launcher of the audio-enhancement pilot (AEP).

Everything that touches audio runs inside a local Linux container without network access. This
launcher only resolves the run directory through the configured ``WORKSPACE`` root and assembles
the ``docker run`` call::

    python pilots/audio_enhancement/aep.py build
    python pilots/audio_enhancement/aep.py setup                # needs network: environments, weights
    python pilots/audio_enhancement/aep.py new-run
    python pilots/audio_enhancement/aep.py step RUN-... prepare --source <recording>
    python pilots/audio_enhancement/aep.py step RUN-... transcribe
    python pilots/audio_enhancement/aep.py storage              # what the pilot occupies
    python pilots/audio_enhancement/aep.py clean                # dry run; --apply deletes

``build``, ``setup`` and ``step`` are refused when they could leave less free disk space than the
floor in ``capacity.py``, and a running container of this launcher is stopped when free space
falls below the stop line. Only containers started here are ever stopped or inspected.

Container output goes to ``<run>/logs/<step>.log``; only lines starting with ``AEP:`` are echoed.
Those lines carry figures, never transcript text or file names of recordings.
"""

from __future__ import annotations

import argparse
import datetime
import secrets
import subprocess
import sys
from pathlib import Path

from mares.core.roots import Roots

sys.path.insert(0, str(Path(__file__).resolve().parent))
import capacity  # noqa: E402

IMAGE = "mares-aep:1"
VOLUME = "mares-aep"
LABEL = "mares.project=aep"
HERE = Path(__file__).resolve().parent
ENVS = "/opt/aep/envs"
EXIT_REFUSED = 75  # not started, or stopped, for lack of disk space

# step -> (interpreter, script); every step receives the run directory as /run
STEPS = {
    "prepare": (f"{ENVS}/qa/bin/python", "prepare.py"),
    "transcribe": (f"{ENVS}/whisper/bin/python", "transcribe.py"),
    "transcript-check": (f"{ENVS}/qa/bin/python", "transcript_check.py"),
    "mossformer2": (f"{ENVS}/mossformer2/bin/python", "run_mossformer2.py"),
    "resemble": (f"{ENVS}/resemble/bin/python", "run_resemble.py"),
    "stupase": (f"{ENVS}/stupase/bin/python", "run_stupase.py"),
    "crispvoice": ("bash", "run_crispvoice.sh"),
    "qa": (f"{ENVS}/qa/bin/python", "qa.py"),
    "asr-diag": (f"{ENVS}/whisper/bin/python", "asr_diag.py"),
    "page": (f"{ENVS}/qa/bin/python", "build_page.py"),
}

# What ``clean`` may delete, as paths inside the volume; nothing else is ever removed. The cache
# is redundant by construction, an environment is rebuilt by ``setup <name>``. Model weights
# (/opt/aep/models) and run directories cannot be cleaned from here.
CLEAN_TARGETS = {
    "cache": ["uv-cache"],
    "env:whisper": ["envs/whisper", ".ready/whisper"],
    "env:qa": ["envs/qa", ".ready/qa"],
    "env:mossformer2": ["envs/mossformer2", ".ready/mossformer2"],
    "env:resemble": ["envs/resemble", ".ready/resemble"],
    "env:stupase": ["envs/stupase", ".ready/stupase"],
    "env:crispvoice": [
        "crispvoice/.venv",
        "crispvoice/.venv-dfn",
        "crispvoice/.venv-cv",
        ".ready/crispvoice",
    ],
}


def runs_root() -> Path:
    return Roots.load().require("WORKSPACE", writable=True) / "runs"


def run_dir(run_id: str) -> Path:
    path = runs_root() / run_id
    if not path.is_dir():
        raise SystemExit(f"unknown run: {run_id}")
    return path


def watched_paths() -> list[Path]:
    """The host volumes the pilot fills: the workspace and the disk image of Docker."""
    paths = [Roots.load().require("WORKSPACE")]
    docker_data = capacity.docker_data_dir()
    if docker_data is not None:
        paths.append(docker_data)
    return paths


def free_now() -> int:
    return capacity.free_bytes(watched_paths())


def require_capacity(need_gib: float, floor_gib: float) -> None:
    decision = capacity.decide(free_now(), need_gib, floor_gib)
    print(f"AEP: {decision.message}", flush=True)
    if not decision.allowed:
        raise SystemExit(EXIT_REFUSED)


def container_name(kind: str) -> str:
    return f"mares-aep-{kind}-{secrets.token_hex(3)}"


def docker(args: list[str], log: Path | None = None, name: str | None = None) -> int:
    """Run docker; echo only ``AEP:`` lines when a log file takes the full output.

    With ``name`` (the container that ``args`` starts) free disk space is watched while the
    command runs, and that one container is stopped when it falls below the stop line.
    """
    process = subprocess.Popen(
        ["docker", *args],
        stdout=None if log is None else subprocess.PIPE,
        stderr=None if log is None else subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    def stop() -> None:
        print(f"AEP: free disk space below {capacity.STOP_GIB} GiB, stopping {name}", flush=True)
        subprocess.run(["docker", "stop", str(name)], capture_output=True)

    watchdog = capacity.Watchdog(free_now, stop) if name else None
    if watchdog is not None:
        watchdog.__enter__()
    try:
        if log is not None:
            assert process.stdout is not None
            with open(log, "a", encoding="utf-8", errors="replace") as handle:
                for line in process.stdout:
                    handle.write(line)
                    handle.flush()
                    if line.startswith("AEP:"):
                        print(line.rstrip(), flush=True)
        code = process.wait()
    finally:
        if watchdog is not None:
            watchdog.__exit__()
    return EXIT_REFUSED if watchdog is not None and watchdog.triggered else code


def base_args(network: bool) -> list[str]:
    args = ["run", "--rm", "--label", LABEL, "-v", f"{VOLUME}:/opt/aep", "-v", f"{HERE / 'container'}:/pilot:ro"]
    if not network:
        args += ["--network", "none", "-e", "HF_HUB_OFFLINE=1", "-e", "TRANSFORMERS_OFFLINE=1"]
    return args


def volume_shell(script: str, *, writable: bool) -> subprocess.CompletedProcess[str]:
    """Run a fixed shell script against the volume, without network and without audio."""
    mount = f"{VOLUME}:/opt/aep" + ("" if writable else ":ro")
    args = ["run", "--rm", "--label", LABEL, "--network", "none", "-v", mount, IMAGE, "sh", "-c", script]
    return subprocess.run(["docker", *args], capture_output=True, text=True)


def volume_in_use() -> list[str]:
    """Names of the running containers that have the pilot volume mounted."""
    listing = subprocess.run(
        ["docker", "ps", "--filter", f"volume={VOLUME}", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
        check=True,
    )
    return listing.stdout.split()


def sizes_mib(paths: list[str]) -> dict[str, int]:
    """Size in MiB of each of ``paths`` that exists inside the volume."""
    script = "cd /opt/aep && for p in " + " ".join(paths) + '; do [ -e "$p" ] && du -sm "$p"; done; true'
    result = volume_shell(script, writable=False)
    if result.returncode != 0:
        raise SystemExit(f"cannot read volume {VOLUME}: {result.stderr.strip()}")
    return {path: int(size) for size, path in (line.split(None, 1) for line in result.stdout.splitlines())}


def cmd_build(ns: argparse.Namespace) -> int:
    require_capacity(capacity.BUILD_GIB, ns.min_free_gib)
    return docker(["build", "--label", LABEL, "-t", IMAGE, str(HERE)])


def cmd_setup(ns: argparse.Namespace) -> int:
    require_capacity(capacity.setup_need_gib(ns.envs), ns.min_free_gib)
    name = container_name("setup")
    args = [*base_args(network=True), "--name", name, "-e", f"AEP_FORCE={int(ns.force)}"]
    return docker([*args, IMAGE, "bash", "/pilot/setup_envs.sh", *ns.envs], name=name)


def cmd_storage(ns: argparse.Namespace) -> int:
    print(f"AEP: {capacity.decide(free_now(), 0, ns.min_free_gib).message}")
    for path, size in sizes_mib(["uv-cache", "envs", "crispvoice", "models", "vendor"]).items():
        print(f"AEP: volume {VOLUME}: {path} {size} MiB")
    return 0


def cmd_clean(ns: argparse.Namespace) -> int:
    targets = ns.targets or ["cache"]
    paths = [path for target in targets for path in CLEAN_TARGETS[target]]
    busy = volume_in_use()
    if busy:
        print(f"AEP: clean refused: volume in use by {', '.join(busy)}")
        return EXIT_REFUSED
    found = sizes_mib(paths)
    for path in paths:
        print(f"AEP: {'delete' if ns.apply else 'would delete'} {path}: {found.get(path, 0)} MiB")
    print(f"AEP: total {sum(found.values())} MiB inside the Docker disk image")
    if not ns.apply or not found:
        return 0
    result = volume_shell("cd /opt/aep && rm -rf -- " + " ".join(found), writable=True)
    if result.returncode != 0:
        print(f"AEP: clean failed: {result.stderr.strip()}")
        return result.returncode
    print("AEP: deleted; the disk image file only shrinks when it is compacted (README)")
    return 0


def cmd_new_run(_: argparse.Namespace) -> int:
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"RUN-{stamp}-{secrets.token_hex(3)}"
    path = runs_root() / run_id
    (path / "logs").mkdir(parents=True)
    print(run_id)
    return 0


def cmd_step(ns: argparse.Namespace) -> int:
    run = run_dir(ns.run)
    interpreter, script = STEPS[ns.step]
    require_capacity(capacity.STEP_GIB, ns.min_free_gib)
    name = container_name(ns.step)
    args = base_args(network=False) + ["--name", name, "-v", f"{run}:/run", "--cpus", str(ns.cpus)]
    extra = list(ns.extra)
    if ns.source is not None:
        source = Path(ns.source).resolve()
        if not source.is_file():
            raise SystemExit("source recording not found")
        mounted = f"/source/original{source.suffix.lower()}"
        args += ["-v", f"{source}:{mounted}:ro"]
        extra = ["--source", mounted, "--source-name", source.name, *extra]
    args += ["-e", f"AEP_THREADS={ns.threads}", "-e", f"AEP_RUN_ID={ns.run}", IMAGE, interpreter, f"/pilot/{script}", *extra]
    code = docker(args, log=run / "logs" / f"{ns.step}.log", name=name)
    print(f"step {ns.step}: exit {code}")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--min-free-gib",
        type=float,
        default=capacity.FLOOR_GIB,
        help="free disk space that must remain after the command (default: %(default)s)",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build").set_defaults(func=cmd_build)
    setup = sub.add_parser("setup")
    setup.add_argument("envs", nargs="*", help="environments to set up (default: all)")
    setup.add_argument("--force", action="store_true", help="set up again even if ready")
    setup.set_defaults(func=cmd_setup)
    sub.add_parser("storage").set_defaults(func=cmd_storage)
    clean = sub.add_parser("clean")
    clean.add_argument("targets", nargs="*", help=f"what to delete (default: cache); one of {', '.join(CLEAN_TARGETS)}")
    clean.add_argument("--apply", action="store_true", help="delete; without it only sizes are listed")
    clean.set_defaults(func=cmd_clean)
    sub.add_parser("new-run").set_defaults(func=cmd_new_run)
    step = sub.add_parser("step")
    step.add_argument("run")
    step.add_argument("step", choices=sorted(STEPS))
    step.add_argument("--source", help="recording to mount read-only (prepare step only)")
    step.add_argument("--threads", type=int, default=16)
    step.add_argument("--cpus", type=int, default=20)
    step.set_defaults(func=cmd_step)
    # arguments the launcher does not know are passed on to the step's script
    ns, ns.extra = parser.parse_known_args()
    unknown = [name for name in getattr(ns, "envs", []) if name not in capacity.SETUP_GIB]
    unknown += [name for name in getattr(ns, "targets", []) if name not in CLEAN_TARGETS]
    if unknown:
        parser.error(f"unknown name: {', '.join(unknown)}")
    return ns.func(ns)


if __name__ == "__main__":
    sys.exit(main())
