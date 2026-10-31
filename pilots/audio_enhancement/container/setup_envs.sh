#!/bin/bash
# Creates the isolated model environments of the pilot inside the volume /opt/aep and downloads
# model code and weights from their official sources. This is the only step with network access;
# it never sees research audio (smoke tests use a synthetic tone).
#
# Storage: an environment that is ready is not set up again (marker in $ROOT/.ready; AEP_FORCE=1
# overrides). The package cache only saves downloads within one environment -- environments are
# copies (UV_LINK_MODE=copy), not links into it -- so it is dropped after every environment and
# when the script ends for any reason. It never outlives a setup.
#
# Usage: setup_envs.sh [whisper] [qa] [mossformer2] [resemble] [stupase] [crispvoice]
set -euo pipefail

ROOT=/opt/aep
TORCH_CPU="--extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match"

# Commits whose inference and setup scripts were read before first use.
PASE_URL=https://github.com/cisco-open/pase.git
PASE_COMMIT=45614efae73dc49bf36018d1ca6a9319b3050038
CRISP_URL=https://github.com/Francium-Tech/CrispVoice.git
CRISP_COMMIT=ac42fbc506b5d7b84b6bffa6bfe5953d8bb84f46

mkdir -p "$ROOT/envs" "$ROOT/models" "$ROOT/vendor" "$ROOT/.ready"

drop_cache() { rm -rf "${UV_CACHE_DIR:?}"; }
trap drop_cache EXIT

mkenv() { [ -x "$ROOT/envs/$1/bin/python" ] || uv venv --python 3.11 "$ROOT/envs/$1"; }
pipi() { local env=$1; shift; uv pip install --python "$ROOT/envs/$env/bin/python" "$@"; }
py() { local env=$1; shift; "$ROOT/envs/$env/bin/python" "$@"; }

fetch_repo() { # url commit dir
    if [ ! -d "$3/.git" ]; then
        mkdir -p "$3"
        git -C "$3" init -q
        git -C "$3" remote add origin "$1"
    fi
    git -C "$3" fetch -q --depth 1 origin "$2"
    git -C "$3" checkout -q FETCH_HEAD
    echo "AEP: vendor $(basename "$3") at $(git -C "$3" rev-parse HEAD)"
}

smoke_wav() { # synthetic 4 s tone with noise, 48 kHz mono
    ffmpeg -hide_banner -loglevel error -y \
        -f lavfi -i "sine=frequency=220:duration=4:sample_rate=48000" \
        -f lavfi -i "anoisesrc=d=4:c=pink:r=48000:a=0.05" \
        -filter_complex "amix=inputs=2" -ac 1 -c:a pcm_s16le "$1"
}

setup_whisper() {
    mkenv whisper
    # requests: imported by faster-whisper 1.1.1 but no longer installed by huggingface_hub
    pipi whisper "faster-whisper==1.1.1" "soundfile==0.12.1" soxr requests
    py whisper /pilot/transcribe.py --prefetch
}

setup_qa() {
    mkenv qa
    pipi qa numpy scipy soundfile soxr pyloudnorm
}

setup_mossformer2() {
    mkenv mossformer2
    pipi mossformer2 $TORCH_CPU clearvoice
    py mossformer2 /pilot/run_mossformer2.py --prefetch
}

setup_resemble() {
    mkenv resemble
    pipi resemble $TORCH_CPU "resemble-enhance==0.0.1"
    py resemble /pilot/run_resemble.py --prefetch
}

setup_stupase() {
    fetch_repo "$PASE_URL" "$PASE_COMMIT" "$ROOT/vendor/pase"
    mkenv stupase
    # requirements.txt of the repository lists torch and torchaudio twice (2.4.1 and 2.1.1) and both
    # PySoundFile and soundfile, which provide the same module; the newer pins are used.
    pipi stupase $TORCH_CPU "torch==2.4.1+cpu" "torchaudio==2.4.1+cpu" \
        "librosa==0.10.2.post1" "nnAudio==0.3.3" "numpy==1.23.5" "omegaconf==2.3.0" \
        "pandas==2.3.3" "ptflops==0.7.4" "scipy==1.10.1" "soundfile==0.13.1" "toml==0.10.2" \
        "tqdm==4.67.1" "torchdiffeq==0.2.5" "x-transformers==2.14.2" "huggingface_hub==0.30.2"
    py stupase /pilot/run_stupase.py --prefetch
}

setup_crispvoice() {
    fetch_repo "$CRISP_URL" "$CRISP_COMMIT" "$ROOT/crispvoice"
    # Reached only when the environment is not ready: leftovers of an interrupted setup go first.
    rm -rf "$ROOT/crispvoice/.venv" "$ROOT/crispvoice/.venv-dfn" "$ROOT/crispvoice/.venv-cv"
    # setup.sh pins CPU wheels only for its main environment; the other two would pull CUDA builds
    # of torch with about 6 GB of GPU libraries that a CPU-only run never loads.
    (cd "$ROOT/crispvoice" && UV_TORCH_BACKEND=cpu sh ./setup.sh)
    # First run downloads the MossFormer2 and DeepFilterNet weights; do it here on a synthetic tone
    # so that the real run works offline, and make sure no stage fell back silently.
    smoke_wav /tmp/smoke.wav
    (cd "$ROOT/crispvoice" && ./enhance /tmp/smoke.wav /tmp/smoke_out.wav --device cpu --nfe 4) \
        | tee /tmp/crisp_smoke.log
    bash /pilot/run_crispvoice.sh --check-log /tmp/crisp_smoke.log
    echo "AEP: crispvoice smoke test passed"
}

if [ $# -eq 0 ]; then
    set -- whisper qa mossformer2 resemble stupase crispvoice
fi
for name in "$@"; do
    if [ -e "$ROOT/.ready/$name" ] && [ "${AEP_FORCE:-0}" != "1" ]; then
        echo "AEP: setup $name: already ready, skipped"
        continue
    fi
    echo "AEP: setup $name ..."
    rm -f "$ROOT/.ready/$name"
    "setup_$name"
    date -u +%Y-%m-%dT%H:%M:%SZ > "$ROOT/.ready/$name"
    drop_cache
    echo "AEP: setup $name done"
done
