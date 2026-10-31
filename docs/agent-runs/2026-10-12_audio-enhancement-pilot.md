# Run-Bericht: Pilot Audioverbesserung und Whisper-Transkription

**Datum:** 2026-10-12 · **Lauf:** `RUN-20261012T115507Z-7c373f` · **Status:** abgeschlossen, Hörbewertung offen

Dieser Bericht dokumentiert einen einzelnen Versuch. Er ist keine Spezifikation und keine Empfehlung
für ein Verfahren. Er trennt drei Dinge: was **implementiert** wurde, was **technisch geprüft** ist
und was **wissenschaftlich validiert** wäre. Validiert ist hier nichts: weder das Transkript noch
die Originaltreue einer der vier Fassungen.

## 1. Ziel und Scope

Eine spanischsprachige Interviewaufnahme (48:08 min, AAC 48 kHz Stereo; Name und SHA-256 stehen in
`logs/prepare.json` des Laufs, nicht hier) wurde vollständig mit Whisper large-v3-turbo
transkribiert. Die ersten fünf Minuten wurden mit vier Verfahren zur Sprachverbesserung verarbeitet
und als direkt vergleichbare Hörbeispiele aufbereitet. Nicht Teil des Versuchs: Diarisierung,
Produktionspipeline, Einbindung in Forschungsworkflows.

## 2. Ergebnisse und Pfade

Alles liegt außerhalb des Repositorys unter
`C:\dev\mares\mares_workspace\runs\RUN-20261012T115507Z-7c373f\`:

| Inhalt | Pfad im Lauf |
|---|---|
| **Hörvergleichsseite** (im Browser öffnen) | `index.html` |
| Transkript, lesbar / zeitcodiert mit Wortzeiten | `01_transcript/transcript.txt` / `transcript.json` |
| Whisper-Eingabe (16 kHz mono FLAC) | `01_transcript/full_16k_mono.flac` |
| Testeingabe 00:00–05:00 (mono 48 kHz, mono 16 kHz, Stereo-Referenz) | `02_input/` |
| vollständige Fünf-Minuten-Fassungen, Pegel unverändert | `03_enhanced/<verfahren>/enhanced_5min.wav` |
| Ausschnitte, lautheitsangeglichen / unverändert | `04_clips/matched/`, `04_clips/unmatched/` |
| Intervalle (editierbar) | `04_clips/clips.json` |
| Messwerte, Whisper-Diagnose, Transkriptprüfung | `qa/qa_report.json`, `qa/asr_diag.json`, `qa/transcript_check.json` |
| Parameter, Versionen, Laufzeiten je Schritt | `manifest.json`, `logs/` |

Skripte: [`pilots/audio_enhancement/`](../../pilots/audio_enhancement/README.md). Das Original
blieb unverändert (SHA-256 vor und nach jedem Aufbereitungslauf identisch, nur lesend eingehängt).

## 3. Ausführungsort und Blocker MaRC3a

**Keine Audioübertragung nach MaRC3a.** [`modules.md`](../architecture/modules.md) legt fest, dass
dort bis zur gesonderten Freigabe für personenbezogene Forschungsdaten nur synthetisches Audio
läuft; ADR-0001 führt die Freigabe als offen. Die CORAPAN-Dokumentation enthält dazu keine Aussage
(dort wird öffentlicher Rundfunk verarbeitet). Aus CORAPAN wurde nur die Whisper-Konfiguration
übernommen; das Repository wurde ausschließlich gelesen, es wurde keine SSH-Verbindung geöffnet und
kein Job berührt.

Gerechnet wurde deshalb **lokal auf dem Projektarbeitsplatz, nur CPU** (Intel Core Ultra 9 285K,
64 GB RAM, keine CUDA-GPU), in einem Linux-Container (Docker Desktop, Image `mares-aep:1`).
Jedes Modell hat eine eigene Umgebung im Docker-Volume `mares-aep`. Netzwerk hatte nur der
Setup-Schritt, der keine Aufnahme sieht; alle Schritte mit Audio liefen mit `--network none`.
Die Konsole des Agenten erhielt nur Kennzahlen, weder Transkripttext noch Audio.

## 4. Modelle, Versionen, Parameter

| | Modell und Gewichte | Code / Paket | Parameter | Ein → Aus |
|---|---|---|---|---|
| Whisper | `mobiuslabsgmbh/faster-whisper-large-v3-turbo`, Revision `0a363e91…` (MIT) | faster-whisper 1.1.1, CTranslate2 4.8.2 | `language=es`, `task=transcribe`, `beam_size=3`, `word_timestamps`, kein VAD-Filter, sonst Standard; `float32` statt `float16` (CPU) | 16 kHz mono |
| A MossFormer2 | `MossFormer2_SE_48K` (Apache-2.0), 221,6 MB | `clearvoice` 0.1.2, torch 2.14.1 | Paketstandard | 48 → 48 kHz |
| B Resemble Enhance | `ResembleAI/resemble-enhance`, `enhancer_stage2` (MIT), 713 MB | `resemble-enhance` 0.0.1, torch 2.1.1, deepspeed 0.12.4 | volle Enhancement-Funktion: `nfe=64`, `solver=midpoint`, `tau=0.5`, `lambd=0.9`; 30-s-Abschnitte mit 1 s Überlappung (eingebaut) | 48 → 44,1 kHz |
| C StuPASE | `cisco-ai/stupase`: DeWavLM-R, CFM, Vocoder_Mel-16k (Apache-2.0), 2,26 GB | `cisco-open/pase` @ `45614ef`, torch 2.4.1 | `steps=8`, `cfg_strength=0.5`, `sway_sampling_coef=-1.0` (Standard) | 16 → 16 kHz |
| D CrispVoice | MossFormer2_SE_48K + Resemble `enhancer_stage2` + DeepFilterNet3 | `Francium-Tech/CrispVoice` @ `ac42fbc` (MIT), eigenes `setup.sh` | vollständige Pipeline, Standard: Vorreinigung, `nfe=64`, `lambd=0.4`, 10-s-Abschnitte, 25 % Beimischung, Mastering „podcast“ (−19 LUFS) | 48 → 44,1 kHz, 16 Bit |

Audiokonvertierungen (ffmpeg 5.1.9, alle verlustfrei): Original → 16 kHz mono FLAC s16
(Whisper, wie CORAPAN, ohne Lautheits- oder Rauschbearbeitung); Original 0–300 s → 48 kHz mono
WAV 24 Bit (gemeinsame Testeingabe, exakt 14 400 000 Frames) → 16 kHz für StuPASE. Die Ausgaben von
A–C sind 32-Bit-Float-WAV ohne Pegelanpassung.

Abweichungen von den offiziellen Abläufen:

- **StuPASE:** Das offizielle Skript gibt eine Datei am Stück durch das Modell; bei fünf Minuten
  nicht machbar. Ergänzt wurden 15-s-Abschnitte mit 1 s Überlappung und 100 ms Überblendung an
  festen Positionen. Das ist eine Zutat des Piloten und kann Nahtstellen hörbar machen.
- **Resemble Enhance:** Release 0.0.1 lädt Gewichte per `git lfs`; dieselben Dateien wurden per
  HTTPS aus dem offiziellen Modell-Repository geholt.
- **CrispVoice** enthält StuPASE nicht; es kombiniert A und B mit DeepFilterNet und einem
  ffmpeg-Mastering (EQ, De-Esser, Kompressor 2:1, Limiter, Lautheitsnormalisierung).
- **Monomischung:** Die Aufnahme ist echtes Stereo (Kanalkorrelation 0,70, links 3,2 dB lauter).
  Alle Verfahren arbeiten mono; verglichen wird gegen die Monomischung, nicht gegen das
  Stereo-Original. Die Stereofassung der fünf Minuten liegt als Referenz bei.

## 5. Laufzeiten und Ressourcen

Nur CPU; die Läufe liefen teilweise parallel, die Zeiten sind deshalb Obergrenzen.

| Schritt | Threads | Laufzeit | Faktor zur Audiodauer | Spitzen-RAM |
|---|---|---|---|---|
| Whisper, 48:08 min | 10 | 1078 s | 0,37 | 6,7 GB |
| MossFormer2, 5 min | 6 | 51 s | 0,17 | 1,1 GB |
| Resemble Enhance, 5 min | 10 | 1900 s | 6,3 | 9,6 GB |
| StuPASE, 5 min | 4 | 463 s | 1,5 | 3,1 GB |
| CrispVoice, 5 min | 10 | 1939 s | 6,5 | nicht gemessen |

GPU-Bedarf wurde nicht gemessen. Das Volume belegt rund 37 GB (davon 15 GB Paket-Cache, der
gelöscht werden kann).

## 6. Verarbeitungsschritte

Alle vier Kandidaten ließen sich installieren und haben die fünf Minuten vollständig verarbeitet.
Bei CrispVoice wurden alle Stufen im Protokoll bestätigt; das Programm würde bei einem Fehler der
Vorreinigung stillschweigend ohne sie weiterrechnen, deshalb prüft das Startskript das Protokoll.

**Zwischenfall:** Eine parallel arbeitende Sitzung (Netzwerkpipeline) löschte beim Aufräumen mit
dem Muster `runs/RUN-*` Teile dieses Laufordners (dort vermerkt:
[`2026-10-12_netzwerkpipeline-pilot-001-2.md`](2026-10-12_netzwerkpipeline-pilot-001-2.md)).
Testeingabe, MossFormer2, StuPASE und die Transkription wurden neu erzeugt. Die Testeingabe ist
bitgleich reproduziert. StuPASE lieferte im zweiten Lauf eine andere Rohspitze (1,004 statt 0,952):
das Verfahren ist nicht deterministisch, ein Seed wird nicht gesetzt.

## 7. Technische Prüfung

Geprüft, mit Ergebnis:

| Prüfung | Ergebnis |
|---|---|
| Länge der Fassungen | alle exakt 300,000 s |
| Clipping | keine Fassung erreicht Vollaussteuerung (Spitzen −6,4 bis −6,6 dBFS; CrispVoice −1,5 dBFS) |
| Lautheit | Original −28,2 LUFS; A −28,7; B −28,0; C −29,8; D −19,1 |
| Bandbreite (−50 dB) | Original 10,4 kHz; A 10,4 kHz; B 16,4 kHz; C 8,0 kHz; D 16,3 kHz |
| Zeitversatz gesamt | A −0,2 ms; B +2,0 ms; C −5,4 ms; D +6,5 ms |
| Zeitversatz der Ausschnitte | ab 5 ms korrigiert; Rest nach Korrektur ≤ 2,2 ms in A, B, C |
| Transkript deckt die Aufnahme | 691 Segmente, 6332 Wörter, erstes Wort bei 5,1 s, letztes Segment endet bei 2888,1 von 2888,2 s; größte Lücke 16,4 s |

**Auffälligkeiten:**

1. **Resemble Enhance verschiebt einen ganzen Abschnitt.** Zwischen etwa 01:27 und 01:57 liegt die
   Ausgabe rund 437 ms zu früh (zehn aufeinanderfolgende 5-s-Fenster, Korrelation bis 0,86). Das
   entspricht einem der 30-s-Abschnitte, den die eingebaute Zusammenfügung per Kreuzkorrelation
   falsch platziert. An beiden Rändern ändern sich Pausenlängen, oder Signal fehlt beziehungsweise
   doppelt sich. CrispVoice nutzt dieselbe Zusammenfügung mit 10-s-Abschnitten; dort wurde kein
   Sprung gefunden, ausgeschlossen ist er für andere Aufnahmen nicht.
2. **StuPASE ist stellenweise still, wo die anderen Signal haben:** 25,1 s insgesamt (A 3,3 s,
   B 7,6 s, D 2,4 s), längste Stelle 5,6 s ab 00:36. Im Ausschnitt C, der diese Stelle enthält,
   findet Whisper in der StuPASE-Fassung 12 von 39 Wörtern nicht. Ob dort Sprache fehlt, muss
   gehört werden. Dazu passen die Einschränkungen des Modells: überwiegend auf Englisch trainiert,
   16 kHz, also weniger Bandbreite als die Aufnahme selbst hat.
3. **Resemble und CrispVoice erzeugen Bandbreite oberhalb von 10,4 kHz**, die in der Aufnahme
   nicht vorhanden ist. Das ist der beabsichtigte Studioeffekt und zugleich synthetisches Material.
4. **CrispVoice verändert die Dynamik** (Kompressor, Limiter, EQ, De-Esser) und ist 9 dB lauter.
5. **Transkript, 40:23–40:53:** elf identische Ein-Wort-Segmente in Folge mit extremer
   Kompressionsrate. Kandidat für eine Whisper-Wiederholungsschleife; kann auch eine echte
   Wiederholung sein. 6,0 % der Wörter haben eine Wahrscheinlichkeit unter 0,5.

**Whisper-Diagnose der Ausschnitte** (Wortabweichung gegen das Whisper-Transkript des
Original-Ausschnitts; Hinweis, kein Nachweis in die eine oder andere Richtung):

| Ausschnitt | Referenzwörter | MossFormer2 | Resemble | StuPASE | CrispVoice |
|---|---|---|---|---|---|
| A | 69 | 13 % | 26 % | 22 % | 14 % |
| B | 53 | 0 % | 6 % | 13 % | 19 % |
| C | 39 | 3 % | 23 % | 31 % | 26 % |

Einfügungen können auch bedeuten, dass Whisper im verrauschten Original Wörter überhört, die es
in der bereinigten Fassung erkennt.

## 8. Hörbeispiele

| | Intervall | Auswahlgrund (automatisch) |
|---|---|---|
| A | 02:23,04–02:50,16 | höchster Sprachanteil (98 %), eine Pause |
| B | 03:52,23–04:18,30 | leiseste Sprache bei mindestens 50 % Sprachanteil (rund 3 dB unter dem Mittel) |
| C | 00:33,15–00:56,11 | viele kurze Sprechabschnitte und Pausen |
| X | 01:49,50–02:01,50 | Zusatz: Nahtstelle des Resemble-Zeitsprungs, ohne Versatzkorrektur |

- Sprachstellen stammen aus den Wortzeitmarken des Transkripts. Der Pegel taugt dafür nicht: das
  Störgeräusch ist zu laut.
- **Sprecherwechsel konnten nicht belegt werden.** Weder Grundfrequenz noch der Pegelunterschied
  der Stereokanäle trennen zwei Gruppen belastbar. C ist deshalb über Pausen gewählt, nicht über
  nachgewiesene Wechsel. Die Intervalle wurden nicht durch Hören geprüft.
- Die Auswahl meidet die Ränder des Resemble-Zeitsprungs, damit jeder Vergleich mit einer einzigen
  Versatzkorrektur exakt deckungsgleich ist.
- **Pegelangleich:** integrierte Lautheit nach ITU-R BS.1770 je Ausschnitt, ein statischer Gain je
  Datei, Ziel −20 LUFS, je Zeile abgesenkt, bis keine Fassung −1 dBFS überschreitet (A −22,4;
  B −26,1; C −22,4 LUFS); 10 ms Ein- und Ausblendung. Keine Dynamikbearbeitung. Gains stehen auf
  der Seite und in `qa_report.json`. Abtastraten wurden nicht angeglichen.

## 9. Vorläufige Einschätzung

Zur Klangqualität sagt dieser Bericht nichts; sie wird durch Hören beurteilt. Technisch gilt:

- **MossFormer2** ist das einzige nicht generative Verfahren: zeitlich exakt, gleiche Bandbreite
  wie die Eingabe, geringste Abweichungen in allen Messungen, mit Abstand am schnellsten. Es kann
  Sprache dämpfen, aber keine erzeugen.
- **Resemble Enhance** und **CrispVoice** synthetisieren die Stimme neu. Für Hörfassungen kann das
  nützlich sein; als Grundlage für Transkription oder Analyse wäre jede Stelle am Original zu
  prüfen. Der Zeitsprung bei Resemble ist für Pausen- und Überlappungsanalysen ein Ausschlussgrund,
  solange die Zusammenfügung nicht ersetzt wird.
- **StuPASE** ist für diese Aufnahme technisch am auffälligsten (stille Stellen, 8 kHz Bandbreite,
  nicht deterministisch, Englisch-Training).
- In jedem Fall bleibt eine verbesserte Fassung ein abgeleitetes Hörhilfsmittel neben dem Original.

## 10. Tests

`pytest`: 62 bestanden (Repository-Verträge einschließlich der Prüfung auf Maschinenpfade, mit den
neuen Dateien). Die Pilotskripte selbst haben keine automatischen Tests; geprüft wurden sie durch
die Messungen in Abschnitt 7 und eine Funktionsprobe von CrispVoice mit einem synthetischen Ton.

## 11. Offene Punkte

1. Hörbewertung der vier Verfahren und Prüfung der Intervalle (insbesondere, ob C Interaktion
   enthält).
2. Freigabe von MaRC3a für personenbezogene Daten; ohne sie bleibt nur lokale CPU-Verarbeitung.
3. Die Aufnahme liegt im Repository-Root. Sie ist durch `.gitignore` geschützt, gehört nach
   Regel 1 aber über den Intake nach `PRIMARY`.
4. Der Laufordner liegt in `WORKSPACE`, das als regenerierbar gilt und heute einmal teilweise
   gelöscht wurde. Die generativen Fassungen sind nicht bitgleich wiederherstellbar. Wer die
   Hörbeispiele behalten will, muss sie an einen erhaltenden Ort kopieren.
5. Transkript bei 40:23–40:53 durch Hören prüfen.
6. Lizenz der StuPASE-Trainingsdaten ist gemischt (CC BY, CC0, CC BY-SA); für Forschung
   unkritisch, vor einer Weitergabe von Gewichten zu prüfen.
