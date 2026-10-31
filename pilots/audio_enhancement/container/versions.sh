#!/bin/bash
# Prints what is installed in the volume: package versions per environment, vendored commits,
# disk use and the first 16 hex digits of each weight file's SHA-256. For the run report.
set -uo pipefail
cd /opt/aep

PACKAGES='^(torch|torchaudio|clearvoice|resemble-enhance|deepspeed|faster-whisper|ctranslate2|numpy|x-transformers|huggingface-hub|torchdiffeq|deepfilternet|imageio-ffmpeg) '

for env in envs/whisper envs/mossformer2 envs/resemble envs/stupase \
    crispvoice/.venv crispvoice/.venv-cv crispvoice/.venv-dfn; do
    echo "== $env"
    uv pip list --python "$env/bin/python" 2>/dev/null | grep -Ei "$PACKAGES"
done

echo "== vendored code"
for repo in vendor/pase crispvoice; do
    echo "$repo $(git -C "$repo" rev-parse HEAD)"
done

echo "== disk use"
du -sh envs models crispvoice uv-cache 2>/dev/null

echo "== weights (sha256, first 16 hex digits; bytes; file)"
find models crispvoice/models -type f \( -name '*.pt' -o -name '*.bin' -o -name '*.tar.gz' -o -name 'last_best_checkpoint*' \) 2>/dev/null \
    | sort | while read -r file; do
        printf '%s %12s %s\n' "$(sha256sum "$file" | cut -c1-16)" "$(stat -Lc %s "$file")" "$file"
    done
ffmpeg -version | head -1
