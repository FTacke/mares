"""Diagnostic only: transcribe every loudness-matched clip with the same Whisper configuration
and compare each enhanced version with the transcript of the original clip.

A word difference shows that Whisper heard something else, not that the audio was altered, and
an identical transcript does not show that nothing was altered. The texts stay in
``qa/asr_diag.json``; the console only gets counts.
"""

from __future__ import annotations

import json
import re
import unicodedata

import soundfile as sf

from common import RUN, THREADS, Step, say
from transcribe import DECODING, decode, load_model


def tokens(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text.lower())
    return re.sub(r"[^\w\s]", " ", text).split()


def edit_counts(reference: list[str], hypothesis: list[str]) -> dict:
    """Word-level Levenshtein alignment: substitutions, deletions, insertions."""
    rows, cols = len(reference) + 1, len(hypothesis) + 1
    cost = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        cost[i][0] = i
    for j in range(cols):
        cost[0][j] = j
    for i in range(1, rows):
        for j in range(1, cols):
            cost[i][j] = min(cost[i - 1][j] + 1, cost[i][j - 1] + 1,
                             cost[i - 1][j - 1] + (reference[i - 1] != hypothesis[j - 1]))
    i, j, counts, operations = len(reference), len(hypothesis), {"sub": 0, "del": 0, "ins": 0}, []
    while i or j:
        if i and j and cost[i][j] == cost[i - 1][j - 1] + (reference[i - 1] != hypothesis[j - 1]):
            if reference[i - 1] != hypothesis[j - 1]:
                counts["sub"] += 1
                operations.append(["sub", reference[i - 1], hypothesis[j - 1]])
            i, j = i - 1, j - 1
        elif i and cost[i][j] == cost[i - 1][j] + 1:
            counts["del"] += 1
            operations.append(["del", reference[i - 1], None])
            i -= 1
        else:
            counts["ins"] += 1
            operations.append(["ins", None, hypothesis[j - 1]])
            j -= 1
    errors = sum(counts.values())
    return {**counts, "reference_words": len(reference), "hypothesis_words": len(hypothesis),
            "word_difference_rate": round(errors / max(len(reference), 1), 4),
            "operations": operations[::-1]}


def main() -> None:
    import soxr

    step = Step("asr-diag")
    report = json.loads((RUN / "qa" / "qa_report.json").read_text(encoding="utf-8"))
    model = load_model(THREADS)
    result = []
    for row in report["clips"]:
        texts = {}
        for variant, values in row["variants"].items():
            audio, rate = sf.read(RUN / values["matched"], dtype="float32")
            if rate != 16000:
                audio = soxr.resample(audio, rate, 16000).astype("float32")
            texts[variant] = " ".join(r["text"] for r in decode(model, audio))
        reference = tokens(texts["original"])
        entry = {"label": row["label"], "start": row["start"], "end": row["end"], "variants": {}}
        for variant, text in texts.items():
            entry["variants"][variant] = {"text": text}
            if variant != "original":
                counts = edit_counts(reference, tokens(text))
                entry["variants"][variant].update(counts)
                say(f"asr-diag clip {row['label']} {variant}: difference rate {counts['word_difference_rate']} "
                    f"(sub {counts['sub']}, del {counts['del']}, ins {counts['ins']}; "
                    f"{counts['reference_words']} reference words)")
        result.append(entry)
    (RUN / "qa" / "asr_diag.json").write_text(
        json.dumps({"note": "Diagnose, kein Nachweis. Referenz ist das Whisper-Transkript des Original-Ausschnitts.",
                    "decoding": DECODING, "clips": result}, indent=1, ensure_ascii=False),
        encoding="utf-8")
    step.finish(clips=len(result))


if __name__ == "__main__":
    main()
