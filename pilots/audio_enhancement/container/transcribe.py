"""Whisper large-v3-turbo transcription of the whole recording (faster-whisper, CPU).

Decoding follows the CORAPAN self-hosted configuration: language fixed to Spanish, transcription
(no translation), beam size 3, word timestamps, no VAD filter, everything else at the
faster-whisper defaults. ``float16`` is not available on a CPU, so ``float32`` is used.

The result is an automatic transcript: not corrected, not validated, without speaker labels.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = "mobiuslabsgmbh/faster-whisper-large-v3-turbo"
REVISION = "0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf"
DECODING = {
    "language": "es",
    "task": "transcribe",
    "beam_size": 3,
    "word_timestamps": True,
    "vad_filter": False,
}
COMPUTE_TYPE = "float32"
NOTICE = (
    "AUTOMATISCHES TRANSKRIPT (Whisper large-v3-turbo). Nicht korrigiert, nicht wissenschaftlich "
    "validiert, keine Verbatim-Transkription, keine Sprecherzuordnung."
)


def model_path(download: bool = False) -> str:
    from huggingface_hub import snapshot_download

    return snapshot_download(REPO, revision=REVISION, local_files_only=not download)


def load_model(threads: int):
    from faster_whisper import WhisperModel

    return WhisperModel(model_path(), device="cpu", compute_type=COMPUTE_TYPE, cpu_threads=threads)


def decode(model, audio, on_progress=None) -> list[dict]:
    """Transcribe a float32 16 kHz mono array into a list of segment records."""
    segments, _ = model.transcribe(audio, **DECODING)
    records = []
    for segment in segments:
        records.append({
            "id": segment.id,
            "start": round(segment.start, 3),
            "end": round(segment.end, 3),
            "text": segment.text.strip(),
            "avg_logprob": round(segment.avg_logprob, 4),
            "no_speech_prob": round(segment.no_speech_prob, 4),
            "compression_ratio": round(segment.compression_ratio, 3),
            "words": [
                {"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3),
                 "probability": round(w.probability, 4)}
                for w in (segment.words or [])
            ],
        })
        if on_progress is not None:
            on_progress(segment.end)
    return records


def clock(seconds: float) -> str:
    minutes, rest = divmod(seconds, 60)
    hours, minutes = divmod(int(minutes), 60)
    return f"{hours:02d}:{minutes:02d}:{rest:04.1f}"


def completeness(records: list[dict], duration: float) -> dict:
    """Figures that show whether the decode covers the recording. No text."""
    gaps = []
    previous = 0.0
    for record in records:
        gaps.append((record["start"] - previous, previous))
        previous = record["end"]
    gaps.append((duration - previous, previous))
    largest = sorted(gaps, reverse=True)[:5]
    texts = [r["text"] for r in records]
    return {
        "segments": len(records),
        "words": sum(len(r["words"]) for r in records),
        "first_start": records[0]["start"] if records else None,
        "last_end": records[-1]["end"] if records else None,
        "audio_seconds": round(duration, 3),
        "covered_seconds": round(sum(r["end"] - r["start"] for r in records), 1),
        "largest_gaps": [{"seconds": round(g, 2), "at": round(t, 2)} for g, t in largest],
        "segments_compression_ratio_above_2_4": sum(r["compression_ratio"] > 2.4 for r in records),
        "segments_avg_logprob_below_minus_1": sum(r["avg_logprob"] < -1.0 for r in records),
        "segments_no_speech_prob_above_0_6": sum(r["no_speech_prob"] > 0.6 for r in records),
        "consecutive_identical_segments": sum(a == b for a, b in zip(texts, texts[1:])),
        "empty_segments": sum(not t for t in texts),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefetch", action="store_true", help="download the model and exit")
    ns = parser.parse_args()
    if ns.prefetch:
        print("AEP: whisper model at revision", REVISION, "->", Path(model_path(download=True)).name)
        return

    import ctranslate2
    import faster_whisper
    import soundfile as sf

    from common import FULL_16K, RUN, THREADS, Step, say

    step = Step("transcribe")
    audio, rate = sf.read(FULL_16K, dtype="float32")
    if rate != 16000 or audio.ndim != 1:
        raise SystemExit("expected 16 kHz mono input")
    duration = len(audio) / rate

    model = load_model(THREADS)
    state = {"next": 300.0}

    def progress(position: float) -> None:
        if position >= state["next"]:
            say(f"transcribe: {clock(position)} of {clock(duration)}")
            state["next"] += 300.0

    records = decode(model, audio, progress)
    stats = completeness(records, duration)

    out = RUN / "01_transcript"
    meta = {
        "notice": NOTICE,
        "model": {"repo": REPO, "revision": REVISION, "compute_type": COMPUTE_TYPE, "device": "cpu"},
        "decoding": DECODING,
        "versions": {"faster_whisper": faster_whisper.__version__, "ctranslate2": ctranslate2.__version__},
        "input": {"file": str(FULL_16K.relative_to(RUN)), "samplerate": rate, "seconds": round(duration, 3)},
        "completeness": stats,
    }
    (out / "transcript.json").write_text(
        json.dumps({**meta, "text": " ".join(r["text"] for r in records), "segments": records},
                   indent=1, ensure_ascii=False),
        encoding="utf-8",
    )
    lines = [NOTICE, f"Dekodierung: {json.dumps(DECODING)}; Modellrevision {REVISION[:12]}", ""]
    lines += [f"[{clock(r['start'])} - {clock(r['end'])}] {r['text']}" for r in records]
    (out / "transcript.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    step.finish(model=meta["model"], decoding=DECODING, versions=meta["versions"],
                completeness=stats, realtime_factor=None)
    say(f"transcribe: completeness {json.dumps(stats)}")


if __name__ == "__main__":
    main()
