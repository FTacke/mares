"""Candidate A: ClearerVoice-Studio MossFormer2_SE_48K (speech enhancement, 48 kHz).

Uses the official ``clearvoice`` package. The model output is taken as an array and written as
32-bit float WAV, because the package's own writer is 16 bit and would clip peaks above full scale.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

MODEL = "MossFormer2_SE_48K"
CHECKPOINT_HOME = Path("/opt/aep/models/clearvoice")


def load():
    # checkpoints are resolved relative to the working directory
    CHECKPOINT_HOME.mkdir(parents=True, exist_ok=True)
    os.chdir(CHECKPOINT_HOME)
    from clearvoice import ClearVoice

    return ClearVoice(task="speech_enhancement", model_names=[MODEL])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefetch", action="store_true", help="download the checkpoint and exit")
    ns = parser.parse_args()
    if ns.prefetch:
        load()
        print("AEP: mossformer2 checkpoint present")
        return

    from importlib.metadata import version

    import numpy as np
    import soundfile as sf
    import torch

    from common import ENHANCED, INPUT_48K, RUN, THREADS, Step, say

    torch.set_num_threads(THREADS)
    step = Step("mossformer2")
    model = load()
    result = model(input_path=str(INPUT_48K), online_write=False)
    if isinstance(result, dict):
        result = next(iter(result.values()))
    audio = np.asarray(result, dtype=np.float32).squeeze()
    if audio.ndim != 1 or not np.isfinite(audio).all():
        raise SystemExit("unexpected model output")

    out = ENHANCED / "mossformer2" / "enhanced_5min.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, audio, 48000, subtype="FLOAT")
    step.finish(
        model=MODEL, package={"clearvoice": version("clearvoice"), "torch": torch.__version__},
        input=str(INPUT_48K.relative_to(RUN)), output=str(out.relative_to(RUN)),
        output_samplerate=48000, output_frames=int(len(audio)),
        parameters="package defaults (windowed decoding of long input as built into the package)",
        peak=float(np.abs(audio).max()),
    )
    say(f"mossformer2: {len(audio)} frames at 48000 Hz, peak {np.abs(audio).max():.3f}")


if __name__ == "__main__":
    main()
