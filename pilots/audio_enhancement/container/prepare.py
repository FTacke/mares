"""Derive the pilot's working audio from the read-only original.

Writes (lossless, nothing is written next to the original):

* ``01_transcript/full_16k_mono.flac``   whole recording, 16 kHz mono s16 (Whisper input)
* ``02_input/input_5min_48k_mono.wav``   00:00-05:00, 48 kHz mono, 24 bit (common test input)
* ``02_input/input_5min_16k_mono.wav``   same interval at 16 kHz (StuPASE operates at 16 kHz)
* ``02_input/input_5min_48k_stereo.wav`` same interval with both channels (reference only)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from common import FULL_16K, INPUT_16K, INPUT_48K, INPUT_STEREO, RUN, Step, say

CLIP_SECONDS = 300


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def ffmpeg(*args: str) -> list[str]:
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args]
    subprocess.run(command, check=True)
    return command[:1] + [a if not a.startswith("/source/") else "<source>" for a in command[1:]]


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,bit_rate,format_name:stream=codec_name,sample_rate,channels,bit_rate",
         "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    data = json.loads(out)
    data["format"].pop("filename", None)
    return data


def channel_relation() -> dict:
    """How the two channels of the first five minutes relate (decides what a downmix costs)."""
    audio, _ = sf.read(INPUT_STEREO, dtype="float64", always_2d=True)
    if audio.shape[1] < 2:
        return {"channels": int(audio.shape[1])}
    left, right = audio[:, 0], audio[:, 1]
    rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x**2)) + 1e-12)
    return {
        "channels": int(audio.shape[1]),
        "correlation": round(float(np.corrcoef(left, right)[0, 1]), 4),
        "rms_left_dbfs": round(float(rms(left)), 2),
        "rms_right_dbfs": round(float(rms(right)), 2),
        "rms_difference_signal_dbfs": round(float(rms(left - right)), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-name", required=True)
    ns = parser.parse_args()

    step = Step("prepare")
    before = sha256(ns.source)
    info = probe(ns.source)
    for path in (FULL_16K, INPUT_48K):
        path.parent.mkdir(parents=True, exist_ok=True)

    commands = [
        # CORAPAN's canonical ASR input: 16 kHz mono FLAC s16, no loudness or noise processing
        ffmpeg("-i", str(ns.source), "-vn", "-ac", "1", "-ar", "16000",
               "-c:a", "flac", "-sample_fmt", "s16", str(FULL_16K)),
        ffmpeg("-i", str(ns.source), "-t", str(CLIP_SECONDS), "-vn", "-ac", "1", "-ar", "48000",
               "-c:a", "pcm_s24le", str(INPUT_48K)),
        ffmpeg("-i", str(INPUT_48K), "-ac", "1", "-ar", "16000", "-c:a", "pcm_s24le", str(INPUT_16K)),
        # the interval with its original channels: not processed by any model, kept as reference
        ffmpeg("-i", str(ns.source), "-t", str(CLIP_SECONDS), "-vn", "-ar", "48000",
               "-c:a", "pcm_s24le", str(INPUT_STEREO)),
    ]
    derived = {}
    for path in (FULL_16K, INPUT_48K, INPUT_16K, INPUT_STEREO):
        meta = sf.info(path)
        derived[str(path.relative_to(RUN))] = {
            "samplerate": meta.samplerate, "channels": meta.channels, "frames": meta.frames,
            "seconds": round(meta.frames / meta.samplerate, 3), "subtype": meta.subtype,
        }
    after = sha256(ns.source)
    if after != before:
        raise SystemExit("original changed during preparation")

    # The name of the recording stays in the run directory; it is not echoed to the console.
    step.finish(
        source={"name": ns.source_name, "sha256": before, "bytes": ns.source.stat().st_size,
                "probe": info, "first_5min_channels": channel_relation()},
        derived=derived, commands=commands,
    )
    say(f"prepare: source {float(info['format']['duration']):.1f} s, "
        f"{info['streams'][0]['codec_name']} {info['streams'][0]['sample_rate']} Hz "
        f"{info['streams'][0]['channels']} ch; test input {derived['02_input/input_5min_48k_mono.wav']['frames']} frames")
    rel = step.record["source"]["first_5min_channels"]
    say(f"prepare: channel relation {rel}")


if __name__ == "__main__":
    main()
