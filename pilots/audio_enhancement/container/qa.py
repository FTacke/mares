"""Technical checks, clip selection, time alignment and loudness matching.

Reads the five-minute input and every enhanced version that exists, then

1. measures length, sample rate, peak, clipping, level, loudness and bandwidth;
2. measures the delay of every version against the input (envelope cross-correlation: globally,
   per 30 s block and per clip) and compares the versions with each other to find places where
   one of them is silent while the others carry speech, or carries energy where the others do not;
3. chooses three clip intervals (or takes them from ``04_clips/clips.json`` when that file exists,
   so intervals can be set by hand and re-cut);
4. cuts the same interval from every version, corrected for the measured delay, once unchanged
   (``04_clips/unmatched``) and once with one static gain per file that brings all versions of an
   interval to the same integrated loudness (``04_clips/matched``).

Where speech is comes from the word timestamps of the Whisper transcript (timings only; the text
is not used). The level of the recording cannot be used for this: its noise is too loud for an
energy threshold to tell speech from noise.

Everything measured is written to ``qa/qa_report.json``. Nothing here judges how a version sounds.
"""

from __future__ import annotations

import json

import numpy as np
import pyloudnorm
import soundfile as sf
import soxr
from scipy import signal

from common import ENHANCED, INPUT_48K, INPUT_STEREO, RUN, Step, say

VARIANTS = ["original", "mossformer2", "resemble", "stupase", "crispvoice"]
EXPECTED_SECONDS = 300.0
ENV_RATE = 1000  # envelope samples per second
FRAME = 0.02  # analysis frame, seconds
TARGET_LUFS = -20.0
PEAK_CEILING_DB = -1.0
CLIP_SECONDS = 25.0
FADE_SECONDS = 0.01
LAG_CORRECTION_THRESHOLD_MS = 5.0
UNIT_SECONDS = 1.0  # stretches of speech are split into units of about this length
CLIPS_DIR = RUN / "04_clips"
TRANSCRIPT = RUN / "01_transcript" / "transcript.json"


def path_of(variant: str):
    return INPUT_48K if variant == "original" else ENHANCED / variant / "enhanced_5min.wav"


def db(x: float) -> float:
    return float(20 * np.log10(max(x, 1e-12)))


def envelope(x16: np.ndarray) -> np.ndarray:
    """Smoothed log energy envelope at 1 kHz from a 16 kHz signal."""
    hop = 16000 // ENV_RATE
    n = len(x16) // hop
    energy = np.sqrt(np.mean(x16[: n * hop].reshape(n, hop) ** 2, axis=1))
    log = 20 * np.log10(energy + 1e-4)
    return np.convolve(log, np.hanning(15) / np.hanning(15).sum(), mode="same")


def lag_ms(reference: np.ndarray, other: np.ndarray, max_lag: int = 500) -> tuple[float, float]:
    """Delay of ``other`` against ``reference`` in ms (positive: other is late) and the peak
    correlation coefficient. Both are 1 kHz envelopes."""
    n = min(len(reference), len(other))
    a = reference[:n] - reference[:n].mean()
    b = other[:n] - other[:n].mean()
    corr = signal.correlate(b, a, mode="full", method="fft")
    center = n - 1
    window = corr[center - max_lag : center + max_lag + 1]
    k = int(np.argmax(window))
    peak = window[k] / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12)
    shift = 0.0
    if 0 < k < len(window) - 1:
        y0, y1, y2 = window[k - 1], window[k], window[k + 1]
        denominator = y0 - 2 * y1 + y2
        if denominator != 0:
            shift = 0.5 * (y0 - y2) / denominator
    return round((k - max_lag + shift) * 1000 / ENV_RATE, 1), round(float(peak), 3)


def frame_db(x16: np.ndarray) -> np.ndarray:
    hop = int(16000 * FRAME)
    n = len(x16) // hop
    return 20 * np.log10(np.sqrt(np.mean(x16[: n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-6)


def runs_of(mask: np.ndarray) -> list[tuple[int, int]]:
    edges = np.flatnonzero(np.diff(np.concatenate([[0], mask.astype(np.int8), [0]])))
    return list(zip(edges[::2], edges[1::2]))


def spans(mask: np.ndarray, minimum: float) -> list[dict]:
    return [{"start": round(s * FRAME, 2), "seconds": round((e - s) * FRAME, 2)}
            for s, e in runs_of(mask) if (e - s) * FRAME >= minimum]


def energy_activity(level: np.ndarray) -> np.ndarray:
    """Activity from the level alone. Only meaningful on a denoised signal."""
    low, high = np.percentile(level, [10, 95])
    active = level > low + max(8.0, 0.35 * (high - low))
    for start, end in runs_of(~active):
        if (end - start) * FRAME < 0.25 and start > 0 and end < len(active):
            active[start:end] = True
    for start, end in runs_of(active):
        if (end - start) * FRAME < 0.2:
            active[start:end] = False
    return active


def word_activity(frames: int) -> np.ndarray | None:
    """Frames covered by a word of the Whisper transcript; pauses under 0.3 s are bridged."""
    if not TRANSCRIPT.is_file():
        return None
    active = np.zeros(frames, dtype=bool)
    for segment in json.loads(TRANSCRIPT.read_text(encoding="utf-8"))["segments"]:
        for word in segment["words"]:
            a, b = int(word["start"] / FRAME), int(np.ceil(word["end"] / FRAME))
            if a < frames:
                active[a : min(b, frames)] = True
    for start, end in runs_of(~active):
        if (end - start) * FRAME < 0.3 and start > 0 and end < frames:
            active[start:end] = True
    return active


def bandwidth_hz(x: np.ndarray, rate: int) -> float:
    """Highest frequency whose long-term spectrum is within 50 dB of the spectral peak."""
    freqs, psd = signal.welch(x, rate, nperseg=4096)
    level = 10 * np.log10(psd + 1e-20)
    above = np.flatnonzero(level > level.max() - 50)
    return float(freqs[above[-1]])


# --- clip selection --------------------------------------------------------------------------------


def channel_groups(active: np.ndarray) -> tuple[list[dict], dict]:
    """Split speech into units of about one second and group them by the level difference between
    the two channels of the recording.

    Two people at different positions relative to a stereo microphone differ in that level
    difference, so a change of group hints at a change of speaker. It is a hint, not diarisation.
    """
    units = []
    for start, end in runs_of(active):
        count = max(1, int(round((end - start) * FRAME / UNIT_SECONDS)))
        edges = np.linspace(start, end, count + 1).astype(int)
        units += [{"a": int(a), "b": int(b)} for a, b in zip(edges, edges[1:]) if b > a]
    info: dict = {"usable": False, "units": len(units)}
    if not INPUT_STEREO.is_file() or len(units) < 6:
        return units, info
    stereo, rate = sf.read(INPUT_STEREO, dtype="float64", always_2d=True)
    if stereo.shape[1] != 2:
        return units, info
    hop = int(rate * FRAME)
    for unit in units:
        piece = stereo[unit["a"] * hop : unit["b"] * hop]
        unit["ild"] = float(10 * np.log10((np.sum(piece[:, 0] ** 2) + 1e-12) / (np.sum(piece[:, 1] ** 2) + 1e-12)))
    values = np.array([u["ild"] for u in units])
    weights = np.array([u["b"] - u["a"] for u in units], dtype=float)
    low, high = np.percentile(values, [20, 80])
    group = values > (low + high) / 2
    for _ in range(30):
        if group.all() or not group.any():
            break
        low = np.average(values[~group], weights=weights[~group])
        high = np.average(values[group], weights=weights[group])
        group = np.abs(values - high) < np.abs(values - low)
    if group.all() or not group.any():
        return units, info
    spread = float(np.sqrt((np.var(values[group]) * group.sum() + np.var(values[~group]) * (~group).sum()) / len(values)))
    share = float(weights[group].sum() / weights.sum())
    info.update(
        centers_db=[round(float(low), 1), round(float(high), 1)],
        separation_db=round(float(high - low), 1),
        spread_within_groups_db=round(spread, 1),
        share_of_second_group=round(share, 2),
    )
    if high - low >= 3.0 and high - low >= 2.0 * spread and 0.08 <= share <= 0.92:
        info["usable"] = True
        for index, unit in enumerate(units):
            # a single deviating unit between two equal neighbours is treated as noise
            around = group[max(index - 1, 0) : index + 2]
            unit["group"] = int(around.sum() * 2 > len(around))
    return units, info


def discontinuities(report: dict) -> list[dict]:
    """Stretches in which a version runs at a different delay than in the rest of the file.

    Chunked generative models join their chunks by cross-correlation and can place a whole chunk
    off its position. At least two neighbouring 5 s windows must agree for a stretch to count.
    """
    found = []
    for variant, values in report["variants"].items():
        outliers = values.get("timing_against_input", {}).get("lag_profile_outliers_over_20ms", [])
        group: list[dict] = []
        for point in [*outliers, None]:
            if point is not None and (not group or point["at"] - group[-1]["at"] <= 5.0):
                group.append(point)
                continue
            if len(group) >= 2:
                found.append({
                    "variant": variant,
                    "from_about": group[0]["at"], "to_about": group[-1]["at"] + 5.0,
                    "lag_ms": float(np.median([p["lag_ms"] for p in group])),
                    "windows": len(group),
                })
            group = [point] if point is not None else []
    return found


def choose_clips(original16: np.ndarray, jumps: list[dict]) -> tuple[list[dict], dict]:
    level = frame_db(original16)
    frames = len(level)
    active = word_activity(frames)
    basis = "Wortzeitmarken des Whisper-Transkripts"
    if active is None:
        active = energy_activity(level.copy())
        basis = "Pegelschwelle der Eingabe (kein Transkript vorhanden; bei verrauschter Aufnahme unzuverlässig)"
    units, channels = channel_groups(active)
    total = frames * FRAME
    per_second = int(round(1 / FRAME))

    # A comparison clip must not straddle the edge of a displaced stretch: one delay correction
    # could not align both sides. The edges are only known to a few seconds, hence the margins.
    edges = [edge for jump in jumps for edge in (jump["from_about"] - 1.0, jump["to_about"] - 1.0)]
    zones = [(edge - 6.5, edge + 6.5) for edge in edges]

    windows = []
    for start in np.arange(0.0, total - CLIP_SECONDS + 1e-9, 1.0):
        if any(start < z1 and start + CLIP_SECONDS > z0 for z0, z1 in zones):
            continue
        a, b = int(start * per_second), int((start + CLIP_SECONDS) * per_second)
        inside = [u for u in units if u["a"] >= a and u["b"] <= b]
        groups = [u["group"] for u in inside if "group" in u]
        speech = active[a:b]
        windows.append({
            "start": float(start),
            "speech_ratio": float(speech.mean()),
            "pauses": int(len(runs_of(~speech))),
            "group_changes": int(sum(x != y for x, y in zip(groups, groups[1:]))),
            "minority_share": float(min(np.mean(groups), 1 - np.mean(groups))) if groups else 0.0,
            "speech_level_db": float(np.median(level[a:b][speech])) if speech.any() else -120.0,
        })

    chosen: list[dict] = []

    def free(window: dict) -> bool:
        return all(abs(window["start"] - c["start"]) >= CLIP_SECONDS + 5 for c in chosen)

    def pick(label: str, condition: str, candidates: list[dict], key) -> None:
        candidates = [w for w in candidates if free(w)] or [w for w in windows if free(w)]
        chosen.append({"label": label, "condition": condition, **max(candidates, key=key)})

    talk = [w for w in windows if w["speech_ratio"] >= 0.3]
    if channels["usable"]:
        pick("C", "häufige Wechsel der Kanalgruppe (Hinweis auf Sprecherwechsel)", talk,
             lambda w: (w["group_changes"], w["minority_share"]))
    else:
        pick("C", "viele kurze Sprechabschnitte und Pausen (Hinweis auf Interaktion; Kanalgruppen nicht trennbar)",
             talk, lambda w: w["pauses"])
    pick("B", "leiseste Sprache (Sprachanteil mindestens 50 %)",
         [w for w in windows if w["speech_ratio"] >= 0.5], lambda w: -w["speech_level_db"])
    pick("A", "zusammenhängende Rede: höchster Sprachanteil, keine Wechsel der Kanalgruppe",
         windows, lambda w: w["speech_ratio"] - 0.1 * w["group_changes"] - 0.01 * w["pauses"])

    # move the cut points into nearby pauses so that no word is cut
    pauses = [((s + e) / 2 * FRAME) for s, e in runs_of(~active) if (e - s) * FRAME >= 0.3]

    def snap(t: float) -> float:
        near = [p for p in pauses if abs(p - t) <= 2.5]
        return min(near, key=lambda p: abs(p - t)) if near else t

    clips = []
    for clip in sorted(chosen, key=lambda c: c["label"]):
        start = max(0.0, snap(clip["start"]))
        end = min(total, snap(clip["start"] + CLIP_SECONDS))
        if not 20.0 <= end - start <= 30.0:
            start, end = clip["start"], clip["start"] + CLIP_SECONDS
        clips.append({
            "label": clip["label"], "start": round(start, 2), "end": round(end, 2),
            "condition": clip["condition"],
            "basis": {k: round(clip[k], 2) for k in
                      ("speech_ratio", "pauses", "group_changes", "minority_share", "speech_level_db")},
        })
    # one extra clip across the first such edge, cut without any delay correction, so that the
    # displacement itself can be heard
    if jumps:
        jump = jumps[0]
        edge = jump["to_about"] - 1.0
        clips.append({
            "label": "X", "start": round(max(edge - 7.0, 0.0), 2), "end": round(min(edge + 5.0, total), 2),
            "condition": (f"Zusatz: Nahtstelle, an der die Fassung „{jump['variant']}“ die Zeitachse der Eingabe verlässt "
                          f"(Abschnitt um {jump['lag_ms']:.0f} ms verschoben); ohne Versatzkorrektur geschnitten"),
            "no_shift": True,
        })
    context = {
        "avoided_zones_seconds": [[round(z0, 1), round(z1, 1)] for z0, z1 in zones],
        "speech_from": basis,
        "speech_ratio_5min": round(float(active.mean()), 3),
        "speech_level_db_5min": round(float(np.median(level[active])), 1),
        "channel_grouping": channels,
        "method": "automatisch gewählt, nicht durch Hören geprüft",
    }
    return clips, context


# --- analysis --------------------------------------------------------------------------------------


def analyse(variant: str, x: np.ndarray, rate: int) -> dict:
    meter = pyloudnorm.Meter(rate)
    peak = float(np.abs(x).max())
    return {
        "file": str(path_of(variant).relative_to(RUN)),
        "samplerate": rate,
        "frames": int(len(x)),
        "seconds": round(len(x) / rate, 4),
        "length_difference_ms": round((len(x) / rate - EXPECTED_SECONDS) * 1000, 2),
        "subtype": sf.info(path_of(variant)).subtype,
        "peak_dbfs": round(db(peak), 2),
        "samples_at_or_above_full_scale": int(np.sum(np.abs(x) >= 0.999)),
        "rms_dbfs": round(db(float(np.sqrt(np.mean(x**2)))), 2),
        "integrated_lufs": round(float(meter.integrated_loudness(x)), 2),
        "dc_offset": round(float(x.mean()), 6),
        "bandwidth_hz": round(bandwidth_hz(x, rate)),
    }


def timing(reference: np.ndarray, env: np.ndarray) -> dict:
    lag, peak = lag_ms(reference, env)
    block = 30 * ENV_RATE
    blocks = [lag_ms(reference[i : i + block], env[i : i + block])
              for i in range(0, min(len(reference), len(env)) - block + 1, block)]
    reliable = [b[0] for b in blocks if b[1] >= 0.5]
    # fine profile: 5 s windows every 2.5 s; a jump shows where a version leaves the input's timing
    width, hop = 5 * ENV_RATE, int(2.5 * ENV_RATE)
    profile = []
    for i in range(0, min(len(reference), len(env)) - width + 1, hop):
        window_lag, window_peak = lag_ms(reference[i : i + width], env[i : i + width], max_lag=700)
        profile.append({"at": round(i / ENV_RATE, 1), "lag_ms": window_lag, "correlation": window_peak})
    trusted = [p for p in profile if p["correlation"] >= 0.6]
    return {
        "lag_profile_5s": profile,
        "lag_profile_trusted_windows": len(trusted),
        "lag_profile_outliers_over_20ms": [p for p in trusted if abs(p["lag_ms"] - lag) > 20.0],
        "lag_ms": lag, "lag_correlation": peak,
        "lag_ms_per_30s_block": [b[0] for b in blocks],
        "lag_correlation_per_30s_block": [b[1] for b in blocks],
        "lag_ms_range_reliable_blocks": [float(min(reliable)), float(max(reliable))] if reliable else None,
        "reliable_blocks": len(reliable), "blocks": len(blocks),
    }


def cross_check(at16: dict, lags: dict, original_level: np.ndarray, speech: np.ndarray | None) -> dict:
    """Compare the enhanced versions with each other.

    Each version gets its own activity mask from its (denoised) level. A version *misses* speech
    where all other versions are active and it is not; it *adds* energy where it is active and
    no other version is. Needs at least three enhanced versions.
    """
    names = [v for v in at16 if v != "original"]
    levels, masks = {}, {}
    for name in names:
        shifted = np.roll(at16[name], -int(round(lags[name] * 16)))
        levels[name] = frame_db(shifted)
    frames = min(len(level) for level in levels.values())
    for name in names:
        levels[name] = levels[name][:frames]
        masks[name] = energy_activity(levels[name].copy())
    result = {}
    for name in names:
        others = np.sum([masks[o] for o in names if o != name], axis=0)
        entry: dict = {"own_activity_ratio": round(float(masks[name].mean()), 3)}
        if len(names) >= 3:
            missing = (others == len(names) - 1) & ~masks[name]
            extra = masks[name] & (others == 0)
            entry["silent_where_all_others_active"] = {
                "seconds": round(float(sum(s["seconds"] for s in spans(missing, 0.2))), 2),
                "spans": spans(missing, 0.2)}
            entry["active_where_no_other_is"] = {
                "seconds": round(float(sum(s["seconds"] for s in spans(extra, 0.2))), 2),
                "spans": spans(extra, 0.2)}
        if speech is not None:
            # gain against the input on transcript speech frames, per 5 s
            n = min(frames, len(original_level), len(speech))
            per, gains = int(5 / FRAME), []
            for i in range(0, n - per + 1, per):
                mask = speech[i : i + per] & masks[name][i : i + per]
                if mask.mean() >= 0.3:
                    gains.append(float(np.median(levels[name][i : i + per][mask] - original_level[i : i + per][mask])))
            gains = np.array(gains)
            if len(gains) > 1:
                entry["gain_against_input_db"] = {
                    "median": round(float(np.median(gains)), 2), "std": round(float(gains.std()), 2),
                    "largest_step_between_5s_blocks": round(float(np.abs(np.diff(gains)).max()), 2),
                    "blocks": int(len(gains))}
            entry["activity_outside_transcript_speech_ratio"] = round(float((masks[name][:n] & ~speech[:n]).mean()), 3)
            entry["transcript_speech_without_activity_ratio"] = round(float((speech[:n] & ~masks[name][:n]).mean()), 3)
        result[name] = entry
    return result


# --- cutting ---------------------------------------------------------------------------------------


def cut(x: np.ndarray, rate: int, start: float, end: float, lag: float) -> np.ndarray:
    first = int(round((start + lag / 1000) * rate))
    count = int(round((end - start) * rate))
    out = np.zeros(count)
    a, b = max(first, 0), min(first + count, len(x))
    if b > a:
        out[a - first : b - first] = x[a:b]
    return out


def write_clips(clips: list[dict], audio: dict, envs: dict) -> list[dict]:
    rows = []
    for clip in clips:
        row = {**clip, "seconds": round(clip["end"] - clip["start"], 2), "variants": {}}
        a = int(max(clip["start"] - 0.5, 0) * ENV_RATE)
        b = int((clip["end"] + 0.5) * ENV_RATE)
        pieces = {}
        for variant, (x, rate) in audio.items():
            lag, peak = (0.0, 1.0) if variant == "original" else lag_ms(envs["original"][a:b], envs[variant][a:b])
            applied = lag if abs(lag) >= LAG_CORRECTION_THRESHOLD_MS and peak >= 0.3 else 0.0
            if clip.get("no_shift"):
                applied = 0.0
            piece = cut(x, rate, clip["start"], clip["end"], applied)
            pieces[variant] = (piece, rate)
            residual = (0.0, 1.0)
            if variant != "original":
                reference = cut(*audio["original"], clip["start"], clip["end"], 0.0)
                residual = lag_ms(envelope(soxr.resample(reference, audio["original"][1], 16000)),
                                  envelope(soxr.resample(piece, rate, 16000)), max_lag=300)
            row["variants"][variant] = {
                "samplerate": rate,
                "measured_lag_ms": lag, "lag_correlation": peak, "applied_shift_ms": applied,
                "residual_lag_ms": residual[0], "envelope_correlation_with_original": residual[1],
                "lufs": round(float(pyloudnorm.Meter(rate).integrated_loudness(piece)), 2),
                "peak_dbfs": round(db(float(np.abs(piece).max())), 2),
            }
        # one target per interval, lowered if any version would exceed the peak ceiling
        target = TARGET_LUFS
        for values in row["variants"].values():
            target = min(target, values["lufs"] + (PEAK_CEILING_DB - values["peak_dbfs"]))
        row["target_lufs"] = round(target, 2)
        for variant, (piece, rate) in pieces.items():
            values = row["variants"][variant]
            gain = target - values["lufs"]
            values["gain_db"] = round(gain, 2)
            name = f"{clip['label']}_{variant}.wav"
            values["matched"] = f"04_clips/matched/{name}"
            values["unmatched"] = f"04_clips/unmatched/{name}"
            sf.write(CLIPS_DIR / "unmatched" / name, piece.astype(np.float32), rate, subtype="FLOAT")
            fade = int(FADE_SECONDS * rate)
            matched = piece * 10 ** (gain / 20)
            matched[:fade] *= np.linspace(0, 1, fade)
            matched[-fade:] *= np.linspace(1, 0, fade)
            values["matched_peak_dbfs"] = round(db(float(np.abs(matched).max())), 2)
            sf.write(CLIPS_DIR / "matched" / name, matched, rate, subtype="PCM_24")
        rows.append(row)
    return rows


def main() -> None:
    step = Step("qa")
    audio, envs, at16, report = {}, {}, {}, {"variants": {}, "missing": []}
    for variant in VARIANTS:
        path = path_of(variant)
        if not path.is_file():
            report["missing"].append(variant)
            continue
        x, rate = sf.read(path, dtype="float64")
        if x.ndim != 1:
            raise SystemExit(f"{variant}: expected mono")
        audio[variant] = (x, rate)
        at16[variant] = soxr.resample(x, rate, 16000) if rate != 16000 else x
        envs[variant] = envelope(at16[variant])
        report["variants"][variant] = analyse(variant, x, rate)

    original_level = frame_db(at16["original"])
    speech = word_activity(len(original_level))
    lags = {}
    for variant in audio:
        if variant != "original":
            report["variants"][variant]["timing_against_input"] = timing(envs["original"], envs[variant])
            lags[variant] = report["variants"][variant]["timing_against_input"]["lag_ms"]
    for variant, entry in cross_check(at16, lags, original_level, speech).items():
        report["variants"][variant]["cross_check"] = entry

    report["timing_discontinuities"] = discontinuities(report)
    say(f"qa timing discontinuities: {json.dumps(report['timing_discontinuities'])}")

    for folder in ("matched", "unmatched"):
        (CLIPS_DIR / folder).mkdir(parents=True, exist_ok=True)
    clips_file = CLIPS_DIR / "clips.json"
    if clips_file.is_file():
        stored = json.loads(clips_file.read_text(encoding="utf-8"))
        clips, context = stored["clips"], stored.get("selection", {})
        context["source"] = "04_clips/clips.json (vorhanden, übernommen)"
    else:
        clips, context = choose_clips(at16["original"], report["timing_discontinuities"])
        clips_file.write_text(json.dumps({"clips": clips, "selection": context}, indent=2, ensure_ascii=False),
                              encoding="utf-8")
    report["clip_selection"] = context
    report["clips"] = write_clips(clips, audio, envs)
    report["loudness_matching"] = {
        "method": "ITU-R BS.1770 integrierte Lautheit je Ausschnitt; ein statischer Gain je Datei; keine Dynamikbearbeitung",
        "target_lufs": TARGET_LUFS, "peak_ceiling_dbfs": PEAK_CEILING_DB,
        "fades_seconds": FADE_SECONDS,
        "lag_correction_threshold_ms": LAG_CORRECTION_THRESHOLD_MS,
    }

    (RUN / "qa").mkdir(exist_ok=True)
    (RUN / "qa" / "qa_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    step.finish(variants=list(audio), missing=report["missing"])

    for variant, values in report["variants"].items():
        say(f"qa {variant}: {values['samplerate']} Hz, {values['seconds']} s, peak {values['peak_dbfs']} dBFS, "
            f"clipped {values['samples_at_or_above_full_scale']}, {values['integrated_lufs']} LUFS, "
            f"bandwidth {values['bandwidth_hz']} Hz")
        if "timing_against_input" in values:
            t, c = values["timing_against_input"], values["cross_check"]
            say(f"qa {variant}: lag {t['lag_ms']} ms (r={t['lag_correlation']}), reliable blocks "
                f"{t['reliable_blocks']}/{t['blocks']} range {t['lag_ms_range_reliable_blocks']}; "
                f"5 s profile: {t['lag_profile_trusted_windows']} trusted windows, outliers "
                f"{json.dumps(t['lag_profile_outliers_over_20ms'])}")
            say(f"qa {variant}: cross-check " + json.dumps(
                {k: (v if not isinstance(v, dict) or "spans" not in v else v["seconds"]) for k, v in c.items()}))
    say(f"qa selection: {json.dumps(context, ensure_ascii=False)}")
    for row in report["clips"]:
        say(f"qa clip {row['label']}: {row['start']}-{row['end']} s, target {row['target_lufs']} LUFS, basis {row.get('basis', '-')}")
        for variant, v in row["variants"].items():
            say(f"qa clip {row['label']} {variant}: shift {v['applied_shift_ms']} ms (measured {v['measured_lag_ms']}, "
                f"residual {v['residual_lag_ms']}, env r={v['envelope_correlation_with_original']}), "
                f"{v['lufs']} LUFS, gain {v['gain_db']} dB, matched peak {v['matched_peak_dbfs']} dBFS")


if __name__ == "__main__":
    main()
