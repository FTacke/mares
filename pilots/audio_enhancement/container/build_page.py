"""Write the listening page ``index.html`` and the run manifest ``manifest.json``.

The page is a single static file next to the clips: no server, no external script or stylesheet.
It shows intervals and levels only, no transcript text.
"""

from __future__ import annotations

import html
import json
import os

from common import RUN, say, utcnow

TITLES = {
    "original": "Original",
    "mossformer2": "MossFormer2",
    "resemble": "Resemble",
    "stupase": "StuPASE",
    "crispvoice": "CrispVoice",
}
NOTES = {
    "original": "Monomischung der Aufnahme, 48 kHz",
    "mossformer2": "MossFormer2_SE_48K, 48 kHz",
    "resemble": "Resemble Enhance, 44,1 kHz",
    "stupase": "StuPASE, 16 kHz (Bandbreite 8 kHz)",
    "crispvoice": "CrispVoice-Pipeline, 44,1 kHz",
}
ORDER = list(TITLES)

STYLE = """
:root { color-scheme: light dark; --bg:#fbfaf7; --fg:#1d1d1b; --muted:#6b6a65; --line:#d9d6cc; --card:#ffffff; --accent:#1f5f7a; }
@media (prefers-color-scheme: dark) { :root { --bg:#16181a; --fg:#e8e6e1; --muted:#9a988f; --line:#33373b; --card:#1e2124; --accent:#7cc0dc; } }
* { box-sizing: border-box; }
body { margin: 0; padding: 24px 16px 48px; background: var(--bg); color: var(--fg); font: 15px/1.5 system-ui, "Segoe UI", sans-serif; }
main { max-width: 1280px; margin: 0 auto; }
h1 { font-size: 1.5rem; margin: 0 0 4px; }
h2 { font-size: 1.1rem; margin: 32px 0 8px; }
p { margin: 6px 0; max-width: 72ch; }
.muted { color: var(--muted); }
.scroll { overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; background: var(--card); }
table { border-collapse: collapse; width: 100%; }
th, td { padding: 10px 12px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
tr:last-child td { border-bottom: 0; }
thead th { font-weight: 600; white-space: nowrap; }
thead small, td small { display: block; font-weight: 400; color: var(--muted); }
td.clip { min-width: 150px; }
td.clip b { font-size: 1.15rem; color: var(--accent); }
audio { width: 190px; height: 36px; display: block; }
td.playing { outline: 2px solid var(--accent); outline-offset: -2px; }
.num { font-variant-numeric: tabular-nums; }
details { margin-top: 16px; }
summary { cursor: pointer; font-weight: 600; }
label { display: inline-flex; gap: 6px; align-items: center; margin-top: 10px; }
"""

SCRIPT = """
const players = Array.from(document.querySelectorAll('audio'));
const keep = document.getElementById('keep');
players.forEach(function (player) {
  player.addEventListener('play', function () {
    players.forEach(function (other) {
      if (other === player) { return; }
      if (!other.paused && keep.checked && other.dataset.clip === player.dataset.clip
          && other.closest('table') === player.closest('table')) {
        try { player.currentTime = other.currentTime; } catch (e) {}
      }
      other.pause();
    });
    player.closest('td').classList.add('playing');
  });
  ['pause', 'ended'].forEach(function (name) {
    player.addEventListener(name, function () { player.closest('td').classList.remove('playing'); });
  });
});
"""


def clock(seconds: float) -> str:
    return f"{int(seconds // 60):02d}:{seconds % 60:05.2f}"


def table(report: dict, kind: str, variants: list[str]) -> str:
    head = "".join(f"<th>{TITLES[v]}<small>{html.escape(NOTES[v])}</small></th>" for v in variants)
    body = []
    for row in report["clips"]:
        cells = [
            f"<td class='clip'><b>{row['label']}</b> <span class='num'>{clock(row['start'])}–{clock(row['end'])}</span>"
            f"<small>{row['seconds']:.1f} s · {html.escape(row.get('condition', ''))}</small></td>"
        ]
        for variant in variants:
            values = row["variants"][variant]
            if kind == "matched":
                note = f"Gain {values['gain_db']:+.1f} dB"
                if values["applied_shift_ms"]:
                    note += f" · Versatz {values['applied_shift_ms']:+.0f} ms korrigiert"
            else:
                note = f"{values['lufs']:.1f} LUFS · Spitze {values['peak_dbfs']:.1f} dBFS"
            cells.append(
                f"<td><audio controls preload='metadata' data-clip='{row['label']}' src='{values[kind]}'></audio>"
                f"<small class='num'>{note}</small></td>"
            )
        body.append("<tr>" + "".join(cells) + "</tr>")
    return (f"<div class='scroll'><table><thead><tr><th>Ausschnitt</th>{head}</tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table></div>")


def full_table(report: dict, variants: list[str]) -> str:
    head = "".join(f"<th>{TITLES[v]}</th>" for v in variants)
    cells = []
    for variant in variants:
        values = report["variants"][variant]
        cells.append(
            f"<td><audio controls preload='none' data-clip='full' src='{values['file']}'></audio>"
            f"<small class='num'>{values['integrated_lufs']:.1f} LUFS · {values['samplerate'] / 1000:g} kHz</small></td>"
        )
    return (f"<div class='scroll'><table><thead><tr><th>Fassung</th>{head}</tr></thead><tbody><tr>"
            f"<td class='clip'><b>5 min</b> <span class='num'>00:00–05:00</span><small>Pegel unverändert</small></td>"
            f"{''.join(cells)}</tr></tbody></table></div>")


def findings(report: dict, variants: list[str]) -> str:
    """Positions worth listening to, taken from the measurements. Figures only."""
    items = []
    for jump in report.get("timing_discontinuities", []):
        items.append(
            f"<li><b>{TITLES[jump['variant']]}</b>: zwischen etwa {clock(jump['from_about'] - 2.5)} und "
            f"{clock(jump['to_about'] - 1.0)} um rund {jump['lag_ms']:.0f} ms gegen die Eingabe verschoben. "
            f"An beiden Rändern ändert sich dadurch die Länge der Pause oder es fehlt beziehungsweise doppelt sich Signal.</li>"
        )
    for variant in variants:
        check = report["variants"][variant].get("cross_check", {})
        for key, text in (("silent_where_all_others_active", "still, wo alle anderen Verfahren Signal haben"),
                          ("active_where_no_other_is", "Signal, wo kein anderes Verfahren Signal hat")):
            entry = check.get(key)
            if not entry or not entry["spans"]:
                continue
            longest = sorted(entry["spans"], key=lambda s: -s["seconds"])[:5]
            places = ", ".join(f"{clock(s['start'])} ({s['seconds']:.1f} s)" for s in sorted(longest, key=lambda s: s["start"]))
            items.append(f"<li><b>{TITLES[variant]}</b>: {entry['seconds']:.1f} s {text}; längste Stellen: "
                         f"<span class='num'>{places}</span></li>")
    return "<ul>" + "".join(items) + "</ul>" if items else "<p>Keine.</p>"


def main() -> None:
    report = json.loads((RUN / "qa" / "qa_report.json").read_text(encoding="utf-8"))
    variants = [v for v in ORDER if v in report["variants"]]
    missing = [TITLES[v] for v in report.get("missing", [])]
    matching = report["loudness_matching"]

    page = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hörvergleich Audioverbesserung</title>
<style>{STYLE}</style>
</head>
<body>
<main>
<h1>Hörvergleich Audioverbesserung</h1>
<p class="muted">MARES-Pilot · {html.escape(os.environ.get('AEP_RUN_ID', 'Lauf'))} · erzeugt {utcnow()} · personenbezogene Forschungsdaten, nicht weitergeben</p>
<p>Jede Zeile zeigt denselben Zeitabschnitt der ersten fünf Minuten in allen Fassungen. Die Ausschnitte
sind auf gleiche Lautheit gebracht (ein fester Gain je Datei, Ziel {matching['target_lufs']:.0f} LUFS, keine Dynamikbearbeitung).
Startet ein Player, halten die anderen an.</p>
{"<p><b>Nicht enthalten:</b> " + ", ".join(missing) + " (siehe Bericht).</p>" if missing else ""}
<label><input type="checkbox" id="keep" checked> Beim Wechsel innerhalb einer Zeile an derselben Stelle weiterspielen</label>

<h2>Vergleich bei angeglichener Lautheit</h2>
{table(report, "matched", variants)}

<details>
<summary>Dieselben Ausschnitte ohne Pegelangleich</summary>
<p class="muted">Unveränderte Pegel der Verfahren (32-Bit-Float-WAV). Die Lautstärken unterscheiden sich deutlich; vorsichtig aussteuern.</p>
{table(report, "unmatched", variants)}
</details>

<h2>Vollständige Fünf-Minuten-Fassungen</h2>
<p class="muted">Nicht angeglichen: CrispVoice ist durch sein Mastering deutlich lauter als die übrigen Fassungen.</p>
{full_table(report, variants)}

<h2>Messbefunde zum gezielten Nachhören</h2>
<p class="muted">Zeitangaben beziehen sich auf die Fünf-Minuten-Fassungen. Die Befunde stammen aus Pegelvergleichen
zwischen den Fassungen und sagen nicht, ob eine Stelle Sprache, Atem oder Geräusch ist.</p>
{findings(report, variants)}

<h2>Hinweise zum Hören</h2>
<p>Die Intervalle wurden automatisch gewählt (Sprachstellen aus den Wortzeitmarken des Whisper-Transkripts) und nicht
durch Hören geprüft. Sie lassen sich in <code>04_clips/clips.json</code> ändern und neu schneiden.</p>
<p>StuPASE liefert nur 16 kHz; der Klang ist dadurch bandbegrenzt. Die Fassungen haben unterschiedliche Abtastraten
und wurden für die Seite nicht umgerechnet.</p>
<p>Die vollständigen, nicht angeglichenen Fünf-Minuten-Fassungen liegen unter <code>03_enhanced/</code>,
die Testeingabe unter <code>02_input/</code>.</p>
</main>
<script>{SCRIPT}</script>
</body>
</html>
"""
    (RUN / "index.html").write_text(page, encoding="utf-8")

    steps = {}
    for path in sorted((RUN / "logs").glob("*.json")):
        steps[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    manifest = {
        "schema": "mares-pilot-audio-enhancement/v1",
        "written": utcnow(),
        "execution": "lokaler Linux-Container, CPU, Audioschritte ohne Netzwerk",
        "steps": steps,
        "clips": [{k: row[k] for k in ("label", "start", "end", "target_lufs")} for row in report["clips"]],
        "missing_variants": report.get("missing", []),
    }
    (RUN / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    say(f"page: index.html with {len(report['clips'])} x {len(variants)} players; manifest with {len(steps)} steps")


if __name__ == "__main__":
    main()
