# Pilot: lokale KI-Audioverbesserung und Whisper-Transkription

**Status: Pilot.** Kein Teil der MARES-Produktionspipeline und nicht in Forschungsworkflows
eingebunden. Das Modul `mares.transcription` bleibt geplant
([`docs/architecture/modules.md`](../../docs/architecture/modules.md)); dieser Ordner enthält nur
die Skripte eines begrenzten Vergleichsversuchs. Ergebnisse und Befunde:
[`docs/agent-runs/2026-10-12_audio-enhancement-pilot.md`](../../docs/agent-runs/2026-10-12_audio-enhancement-pilot.md).

## Was hier liegt

| Datei | Zweck |
|---|---|
| `aep.py` | Startskript auf dem Arbeitsplatz: löst `WORKSPACE` über `mares.core.roots` auf und ruft Docker auf |
| `capacity.py` | Grenzwerte und Prüfung des freien Speicherplatzes vor und während eines Befehls |
| `Dockerfile` | Basis-Image (Python 3.11, ffmpeg, uv); enthält keine Modelle und keine Daten |
| `container/setup_envs.sh` | legt je Modell eine eigene Umgebung an und lädt Code und Gewichte (einziger Schritt mit Netz) |
| `container/prepare.py` | leitet Whisper-Eingabe und Fünf-Minuten-Testeingabe verlustfrei aus dem Original ab |
| `container/transcribe.py` | Whisper large-v3-turbo, vollständige Aufnahme |
| `container/run_*.py`, `run_crispvoice.sh` | die vier Verfahren |
| `container/qa.py` | technische Prüfung, Intervallwahl, Versatzkorrektur, Lautheitsangleich, Schnitt |
| `container/asr_diag.py` | Whisper-Diagnose der Ausschnitte (Hinweis, kein Nachweis) |
| `container/build_page.py` | Hörvergleichsseite und Lauf-Manifest |

## Wo die Daten liegen

Nichts davon liegt im Repository. Jeder Lauf schreibt nach `WORKSPACE/runs/<RUN-ID>/`:

```text
01_transcript/   full_16k_mono.flac, transcript.json, transcript.txt
02_input/        Fünf-Minuten-Testeingabe (48 kHz und 16 kHz, mono)
03_enhanced/     <verfahren>/enhanced_5min.wav   vollständig, Pegel unverändert
04_clips/        clips.json, matched/, unmatched/
qa/              qa_report.json, asr_diag.json
logs/            Protokoll und Parameter je Schritt
index.html       Hörvergleichsseite (direkt im Browser öffnen)
manifest.json    Schritte, Versionen, Parameter, Laufzeiten
```

Umgebungen, Modellgewichte und Modellcode liegen im Docker-Volume `mares-aep`.

## Ausführen

```text
.venv\Scripts\python pilots\audio_enhancement\aep.py build
.venv\Scripts\python pilots\audio_enhancement\aep.py setup
.venv\Scripts\python pilots\audio_enhancement\aep.py new-run
.venv\Scripts\python pilots\audio_enhancement\aep.py step <RUN-ID> prepare --source <Aufnahme>
.venv\Scripts\python pilots\audio_enhancement\aep.py step <RUN-ID> transcribe
.venv\Scripts\python pilots\audio_enhancement\aep.py step <RUN-ID> mossformer2   (ebenso resemble, stupase, crispvoice)
.venv\Scripts\python pilots\audio_enhancement\aep.py step <RUN-ID> qa
.venv\Scripts\python pilots\audio_enhancement\aep.py step <RUN-ID> asr-diag
.venv\Scripts\python pilots\audio_enhancement\aep.py step <RUN-ID> page
```

Andere Intervalle: `04_clips/clips.json` bearbeiten (`start`, `end` in Sekunden), dann `qa` und
`page` erneut ausführen.

## Speicherplatz

Image und Volume liegen im Datenträgerabbild von Docker Desktop, auf dem Projektarbeitsplatz also
auf dem Systemlaufwerk, das sich mehrere Projekte teilen. Das Abbild wächst mit jedem Schreibvorgang
und schrumpft nicht, wenn darin gelöscht wird. Deshalb gilt (Werte in `capacity.py`, Hintergrund:
[`docs/agent-runs/2026-10-12_c-speicher-docker-audit.md`](../../docs/agent-runs/2026-10-12_c-speicher-docker-audit.md)):

| Bestand | Ort | Aufbewahrung |
|---|---|---|
| Paketcache (`uv-cache`) | Volume | keine: wird nach jeder Umgebung und bei jedem Ende von `setup` gelöscht |
| Umgebungen | Volume | bis `clean env:<name>`; wiederherstellbar mit `setup <name>` |
| Modellgewichte, Modellcode | Volume | bleiben; über `clean` nicht löschbar |
| Laufordner | `WORKSPACE/runs` | bleiben; über `clean` nicht löschbar |

- `build`, `setup` und `step` starten nicht, wenn danach weniger als 60 GiB frei bleiben könnten
  (Exit-Code 75). Ein laufender Container dieses Startskripts wird gestoppt, sobald weniger als
  55 GiB frei sind. `--min-free-gib` (vor dem Befehl) ändert die erste Grenze ausdrücklich.
- `setup` überspringt fertige Umgebungen (`--force` baut neu). Ein abgebrochenes `setup` wird
  einfach erneut gestartet; ein gestoppter `step` ebenfalls, er schreibt seine Ausgabe neu.
- `storage` zeigt freien Platz und Belegung des Volumes, `clean` listet, was gelöscht würde, und
  löscht erst mit `--apply`. Solange ein Container das Volume benutzt, verweigert `clean`.
- Löschen im Volume gibt Platz *im* Abbild frei, den Docker wiederverwendet. Windows erhält ihn
  erst zurück, wenn das Abbild kompaktiert wird. Dazu müssen Docker Desktop und WSL beendet
  werden, was alle Container aller Projekte anhält; das ist ein eigener, abgestimmter Schritt.

## Regeln, die der Aufbau durchsetzt

- Das Original wird nur lesend eingehängt und vor und nach der Aufbereitung gehasht.
- Jeder Schritt, der Audio verarbeitet, läuft mit `--network none`. Netz hat nur `setup`, und
  `setup` sieht keine Aufnahme (Funktionsproben laufen mit einem synthetischen Ton).
- Die Konsole zeigt nur Zeilen mit Kennzahlen (`AEP: …`). Transkripttext und der Name der Aufnahme
  stehen ausschließlich in Dateien im Laufverzeichnis.
- Keine Übertragung nach MaRC3a: die Freigabe des Clusters für personenbezogene Daten ist offen
  ([`docs/architecture/modules.md`](../../docs/architecture/modules.md)).
