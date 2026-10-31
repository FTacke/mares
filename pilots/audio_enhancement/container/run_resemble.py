"""Candidate B: Resemble Enhance, full enhancement (denoiser + CFM enhancer), output 44.1 kHz.

Calls the package's own ``enhance`` function, i.e. what ``resemble-enhance in_dir out_dir`` runs,
including its 30 s chunking with 1 s overlap. NFE, solver and tau are the CLI defaults; ``lambd``
is the value of the official demo with "denoise before enhancement" switched on.
"""

from __future__ import annotations

import argparse
from pathlib import Path

RUN_DIR = Path("/opt/aep/models/resemble/enhancer_stage2")
WEIGHTS_URL = "https://huggingface.co/ResembleAI/resemble-enhance/resolve/main/enhancer_stage2"
PARAMETERS = {"nfe": 64, "solver": "midpoint", "lambd": 0.9, "tau": 0.5}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefetch", action="store_true", help="download the weights and exit")
    ns = parser.parse_args()

    if ns.prefetch:
        # Release 0.0.1 fetches the weights with git-lfs; the same files are taken over HTTPS from
        # the official model repository instead, as the current upstream code does.
        import torch

        for name in ("hparams.yaml", "ds/G/default/mp_rank_00_model_states.pt"):
            target = RUN_DIR / name
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                torch.hub.download_url_to_file(f"{WEIGHTS_URL}/{name}", str(target), progress=False)
        print("AEP: resemble weights present")
        return

    from importlib.metadata import version

    import soundfile as sf
    import torch
    from resemble_enhance.enhancer.inference import enhance

    from common import ENHANCED, INPUT_48K, RUN, THREADS, Step, say

    torch.set_num_threads(THREADS)
    step = Step("resemble")
    audio, rate = sf.read(INPUT_48K, dtype="float32")
    enhanced, out_rate = enhance(
        dwav=torch.from_numpy(audio), sr=rate, device="cpu", run_dir=RUN_DIR, **PARAMETERS
    )
    enhanced = enhanced.cpu().numpy()

    out = ENHANCED / "resemble" / "enhanced_5min.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, enhanced, out_rate, subtype="FLOAT")
    step.finish(
        model="ResembleAI/resemble-enhance enhancer_stage2",
        package={"resemble-enhance": version("resemble-enhance"), "torch": torch.__version__},
        input=str(INPUT_48K.relative_to(RUN)), output=str(out.relative_to(RUN)),
        output_samplerate=int(out_rate), output_frames=int(len(enhanced)),
        parameters={**PARAMETERS, "chunk_seconds": 30.0, "overlap_seconds": 1.0},
        peak=float(abs(enhanced).max()),
    )
    say(f"resemble: {len(enhanced)} frames at {out_rate} Hz, peak {abs(enhanced).max():.3f}")


if __name__ == "__main__":
    main()
