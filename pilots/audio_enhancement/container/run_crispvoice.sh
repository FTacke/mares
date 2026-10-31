#!/bin/bash
# Candidate D: CrispVoice, complete pipeline with its defaults on CPU:
# MossFormer2 clarity front-end -> Resemble Enhance (nfe 64, lambd 0.4, tau 0.5, 10 s chunks)
# -> 25 % DeepFilterNet3 texture blend -> mastering preset "podcast" (-19 LUFS) -> 44.1 kHz s16 WAV.
#
# enhance.py continues without the clarity front-end or the blend when their environments fail,
# so the log is checked: a run that silently skipped a stage is not the complete pipeline.
set -euo pipefail

check_log() {
    grep -q "clarity front-end (MossFormer2)" "$1" || { echo "AEP: crispvoice: clarity stage did not start"; exit 3; }
    if grep -Eq "clarity front-end unavailable|skipping clarity|skipping blend|falling back" "$1"; then
        echo "AEP: crispvoice: a stage was skipped"; exit 3
    fi
    grep -q "blending in denoised original" "$1" || { echo "AEP: crispvoice: blend stage did not run"; exit 3; }
    grep -q "^wrote:" "$1" || { echo "AEP: crispvoice: no output written"; exit 3; }
}

if [ "${1:-}" = "--check-log" ]; then
    check_log "$2"
    exit 0
fi

OUT=/run/03_enhanced/crispvoice
mkdir -p "$OUT"
START=$(date +%s)
cd /opt/aep/crispvoice
./enhance /run/02_input/input_5min_48k_mono.wav "$OUT/enhanced_5min.wav" \
    --device cpu --threads "${AEP_THREADS:-8}" | tee /tmp/crispvoice.log
check_log /tmp/crispvoice.log
END=$(date +%s)

cat > /run/logs/crispvoice.json <<EOF
{
  "step": "crispvoice",
  "device": "cpu",
  "threads": ${AEP_THREADS:-8},
  "wall_seconds": $((END - START)),
  "commit": "$(git -C /opt/aep/crispvoice rev-parse HEAD)",
  "input": "02_input/input_5min_48k_mono.wav",
  "output": "03_enhanced/crispvoice/enhanced_5min.wav",
  "parameters": {
    "clarity_front_end": "MossFormer2_SE_48K",
    "nfe": 64, "solver": "midpoint", "lambd": 0.4, "tau": 0.5,
    "chunk_seconds": 10.0, "overlap_seconds": 1.0,
    "blend": 0.25, "blend_model": "DeepFilterNet3",
    "master_preset": "podcast", "loudness_target_lufs": -19
  },
  "stages_confirmed_in_log": ["clarity", "resemble", "blend", "master"]
}
EOF
echo "AEP: crispvoice: done in $((END - START)) s, all stages confirmed"
