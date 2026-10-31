"""Locate suspicious stretches of the automatic transcript without showing any text.

Whisper sometimes falls into a loop and repeats a phrase. Two signs are checked: runs of
consecutive identical segments and segments with a high compression ratio. A run of identical
one-word segments can be a genuine listener signal; a long run, a run of identical long segments
or a long segment with very few distinct words is more likely a loop. The output gives positions, lengths
and word counts so that the places can be checked by ear. Written to ``qa/transcript_check.json``.
"""

from __future__ import annotations

import json

from common import RUN, say


def main() -> None:
    data = json.loads((RUN / "01_transcript" / "transcript.json").read_text(encoding="utf-8"))
    segments = data["segments"]

    runs, index = [], 0
    while index < len(segments):
        end = index
        while end + 1 < len(segments) and segments[end + 1]["text"] == segments[index]["text"]:
            end += 1
        if end > index:
            runs.append({
                "start": segments[index]["start"], "end": segments[end]["end"],
                "repetitions": end - index + 1,
                "words_per_segment": len(segments[index]["text"].split()),
            })
        index = end + 1

    dense = []
    for segment in segments:
        if segment["compression_ratio"] > 2.4:
            words = segment["text"].lower().split()
            dense.append({
                "start": segment["start"], "end": segment["end"],
                "seconds": round(segment["end"] - segment["start"], 1),
                "words": len(words), "distinct_words": len(set(words)),
                "compression_ratio": segment["compression_ratio"],
            })

    probable_loops = [r for r in runs if r["repetitions"] >= 5
                      or (r["words_per_segment"] >= 3 and r["repetitions"] >= 3)]
    probable_loops += [d for d in dense if d["words"] >= 12 and d["distinct_words"] / d["words"] < 0.35]
    report = {"identical_runs": runs, "high_compression_segments": dense, "probable_loops": probable_loops}
    (RUN / "qa").mkdir(exist_ok=True)
    (RUN / "qa" / "transcript_check.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    words = [w for s in segments for w in s["words"]]
    low = sum(w["probability"] < 0.5 for w in words)
    say(f"transcript-check: identical runs {json.dumps(runs)}")
    say(f"transcript-check: high compression {json.dumps(dense)}")
    say(f"transcript-check: probable loops {len(probable_loops)}; words with probability < 0.5: "
        f"{low} of {len(words)} ({low / max(len(words), 1):.1%})")


if __name__ == "__main__":
    main()
