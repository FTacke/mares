"""Candidate C: StuPASE (cisco-open/pase), 16 kHz in, 16 kHz out.

The model class, the checkpoints and the sampling parameters are the official ones. The official
inference script, however, passes a whole file through the model at once, which is not feasible
for five minutes. This script therefore adds what the repository does not provide: fixed-length
chunks with one second of overlap, joined by a 100 ms crossfade in the middle of the overlap. The
positions of the chunks are fixed, so the output keeps the timing of the input.

The official per-file peak rescaling is applied once to the joined signal.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

VENDOR = Path("/opt/aep/vendor/pase/stupase")
CHECKPOINTS = Path("/opt/aep/models/stupase")
FILES = {"dewavlm": "DeWavLM-R.pt", "cfm": "CFM.pt", "vocoder": "Vocoder_Mel-16k.pt"}
PARAMETERS = {"steps": 8, "cfg_strength": 0.5, "sway_sampling_coef": -1.0}
RATE = 16000
CHUNK_SECONDS = 15.0
OVERLAP_SECONDS = 1.0
FADE_SECONDS = 0.1


def join(chunks, starts, length, overlap, fade):
    """Overlap-join at fixed positions; the crossfade sits in the middle of each overlap."""
    import numpy as np

    out = np.zeros(length, dtype=np.float32)
    ramp = np.zeros(overlap, dtype=np.float32)
    a, b = (overlap - fade) // 2, (overlap + fade) // 2
    ramp[a:b] = np.linspace(0.0, 1.0, b - a, dtype=np.float32)
    ramp[b:] = 1.0
    for index, (chunk, start) in enumerate(zip(chunks, starts)):
        end = min(start + len(chunk), length)
        chunk = chunk[: end - start]
        if index == 0:
            out[start:end] = chunk
            continue
        n = min(overlap, len(chunk))
        out[start : start + n] = out[start : start + n] * (1 - ramp[:n]) + chunk[:n] * ramp[:n]
        out[start + n : end] = chunk[n:]
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefetch", action="store_true", help="download the checkpoints and exit")
    ns = parser.parse_args()

    sys.path.insert(0, str(VENDOR))
    if ns.prefetch:
        from inference.inference import get_checkpoint_path

        for name in FILES.values():
            get_checkpoint_path(None, name, str(CHECKPOINTS))
        print("AEP: stupase checkpoints present")
        return

    import numpy as np
    import soundfile as sf
    import torch
    from models.stupase import StuPASE

    from common import ENHANCED, INPUT_16K, RUN, THREADS, Step, say

    torch.set_num_threads(THREADS)
    step = Step("stupase")
    audio, rate = sf.read(INPUT_16K, dtype="float32")
    if rate != RATE or audio.ndim != 1:
        raise SystemExit("expected 16 kHz mono input")

    model = StuPASE(
        dewavlm_ckpt_path=str(CHECKPOINTS / FILES["dewavlm"]),
        cfm_ckpt_path=str(CHECKPOINTS / FILES["cfm"]),
        vocoder_ckpt_path=str(CHECKPOINTS / FILES["vocoder"]),
    ).eval()

    chunk, overlap = int(CHUNK_SECONDS * RATE), int(OVERLAP_SECONDS * RATE)
    starts = list(range(0, len(audio) - overlap, chunk - overlap))
    chunks = []
    for index, start in enumerate(starts, 1):
        piece = torch.from_numpy(audio[start : start + chunk]).unsqueeze(0)
        with torch.inference_mode():
            out = model(piece, **PARAMETERS)
        chunks.append(out.squeeze().cpu().numpy().astype(np.float32))
        if index % 5 == 0 or index == len(starts):
            say(f"stupase: chunk {index}/{len(starts)}")

    enhanced = join(chunks, starts, len(audio), overlap, int(FADE_SECONDS * RATE))
    if not np.isfinite(enhanced).all():
        raise SystemExit("unexpected model output")
    raw_peak = float(np.abs(enhanced).max())
    # as in the official inference_file(): match the peak of the input
    enhanced = enhanced / (raw_peak + 1e-8) * float(np.abs(audio).max())

    out_path = ENHANCED / "stupase" / "enhanced_5min.wav"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out_path, enhanced, RATE, subtype="FLOAT")
    step.finish(
        model="cisco-ai/stupase (DeWavLM-R, CFM, Vocoder_Mel-16k)",
        package={"torch": torch.__version__},
        input=str(INPUT_16K.relative_to(RUN)), output=str(out_path.relative_to(RUN)),
        output_samplerate=RATE, output_frames=int(len(enhanced)),
        parameters={**PARAMETERS, "chunk_seconds": CHUNK_SECONDS, "overlap_seconds": OVERLAP_SECONDS,
                    "crossfade_seconds": FADE_SECONDS, "chunks": len(starts),
                    "chunking": "added by the pilot, not part of the official script"},
        raw_peak_before_rescaling=raw_peak, peak=float(np.abs(enhanced).max()),
    )
    say(f"stupase: {len(enhanced)} frames at {RATE} Hz, {len(starts)} chunks, raw peak {raw_peak:.3f}")


if __name__ == "__main__":
    main()
