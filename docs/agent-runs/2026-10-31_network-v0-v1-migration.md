# Run-Bericht 2026-10-31 – Bereinigung des Working Trees, `network_v0`/`network_v1`, Testfälle und acht Standardgrafiken

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-versions.md`](../architecture/network-versions.md),
[`network-v1.md`](../architecture/network-v1.md), [`ADR-0005`](../decisions/ADR-0005_2026-10-31_netzwerk-v0-v1.md). Ortsangaben
beschreiben den Projektarbeitsplatz.

## 0. Vorphase – Working Tree

**Bestand:** 30 geänderte bzw. gelöschte und 46 unversionierte Dateien, letzte Änderung 2026-10-13; kein Prozess schrieb mehr in den
Checkout. Volle Testsuite vorab: 372 bestanden. Geprüft auf Maschinenpfade (nur in Run-Berichten, dort zulässig), Namen, Forschungsinhalte
und Binärdateien: nichts davon in den Änderungen.

**Drei Commits** (lokal, nicht gepusht), mit expliziten Pfaden:

| Commit | Inhalt |
|---|---|
| `208b37e` pilot: local audio enhancement … | `pilots/audio_enhancement/` (Skripte, Dockerfile, README), `tests/test_aep_capacity.py`, Run-Bericht Audio-Pilot |
| `7c03aec` docs: … C: drive and Docker storage audit | Run-Bericht Speicher-/Docker-Audit |
| `894f11a` networks: curation file, design system, five-level geography | fünf aufeinanderfolgende Netzwerk-Runs vom 12./13.10. (Kuratierung, ADR-0003/-0004, Designsystem, G1/G2, Perspektiven, Tests, Verträge) |

Die Netzwerkänderungen wurden **nicht** weiter aufgeteilt: die fünf Runs ändern dieselben Dateien nacheinander, getestete Zwischenstände
existierten nie. Bereinigt wurde nichts (keine Artefakte im Checkout; `__pycache__` ist ignoriert). Uncommittet blieb nichts.

## 1. Bestandsaufnahme (vor der Migration)

- Code `src/mares/networks/` (≈ 6 500 Zeilen, 25 Module): Paketformat `mares-network-package/v0-draft`, Kuratierung, Validierung, Cliquenregel,
  Auswertung, 19 Abbildungen in drei Gruppen, CLI `python -m mares.networks <Schritt>`, Ausgaben nur `WORKSPACE/runs/`.
- Daten: der einzige Pilotfall (`001-2`) liegt als Lieferung in `INTAKE:inbox/…` mit Kuratierung; nicht erhalten, nicht gesichert. Im
  Repository nur synthetische Beispiele.
- Keine v1-Erhebungsbögen und kein Codierschlüssel im Repository (`templates/` leer) → v1 folgt den Festlegungen des Auftrags.
- `PRIMARY` ist nicht konfiguriert; verfügbar sind `INTAKE` und `WORKSPACE`.

## 2. Migration

| Was | Wohin | Warum |
|---|---|---|
| `src/mares/networks/*` | `src/mares/network_v0/` (Git-Umbenennung, Code unverändert außer Modulnamen in Docstrings) | eindeutige Versionsbezeichnung, keine Kopie |
| `tests/test_networks_*.py`, `network_fixtures.py` | `tests/test_network_v0_*.py`, `network_v0_fixtures.py` | dito |
| `mares.networks` | neuer, kleiner gemeinsamer Einstieg (Dispatch v0/v1) | ein Bedienweg; alle dokumentierten v0-Aufrufe gelten weiter |
| v0-Pilotfall | **bleibt** in `INTAKE:inbox`; neu `INTAKE:network_v0/pilots/001/data/case.json` (Verweis mit SHA-256 auf Paket und Kuratierung) | einzige, nicht erhaltene Kopie; keine redundanten Bestände |
| aktuelle Architekturdokumente | Pfade auf `network_v0`, Hinweise auf v1 | Vertrag folgt Code (Regel 15) |
| frühere Run-Berichte, frühere Läufe | unverändert | historische Journale; nichts wird umgeschrieben |

Nicht umgesetzt: ein `graphics/`-Ordner mit v0-Grafiken für `network_v0/pilots/001` (der Ordner existiert, ist leer; die v0-Grafiken liegen
weiterhin in den Läufen unter `WORKSPACE/runs/`).

## 3. Implementierung `network_v1`

| Modul | Stand |
|---|---|
| `codes.py` | Codelisten A/B/C, fünf Zustände (Wert, NS, KA, NA, nicht erhoben), Mehrfachangaben mit `,`/`;`, Dezimalkomma bei Nähe, M/S, Gruppenstatus |
| `places.py` | fünf Darstellungsbereiche, vier Primärkategorien; Verzeichnis der 101 Gemeinden der fünf Landkreise (Stand 2026-10, aus den öffentlichen Gemeindelisten der Kreise), Großstädte außerhalb, mehrdeutige Kurznamen, `places.csv` |
| `case.py` | Fallordner `mares-network-case/v1` lesen; `is_empirical` |
| `validate.py` | Fehler/Warnungen/Hinweise wie gefordert, inkl. v0/v1-Vermischung und Metadatenkonsistenz |
| `derive.py` | Wohnortbereich je Kontakt, Paarzustände mit Quellen (T/N/P/NS-Regeln, Widersprüche), Abdeckung |
| `figures/` | acht Standardgrafiken G1, G2, P1–P5, G3 (PNG, optional SVG), deterministische Layouts |
| `run.py`, `cli.py` | Fall prüfen und rendern, alle Fälle rendern, Fälle auflisten (mit Empirie-Filter), Testfälle installieren |
| `testcases.py` | 002 installieren; 001 aus einem v0-Paket bauen (Codebuch-Prüfung vorab, Ausgabe nur Zählungen) |

Entscheidungen: Fallbaum in `INTAKE` statt im Repository (Regel 1; ADR-0005); Grafiken des Falls in `graphics/`, alles Technische in
`WORKSPACE/runs/`; Mittelhessen nur per Verzeichnis oder ausdrücklicher Einordnung; v1 importiert versionsneutrale Bausteine aus v0, statt
sie zu kopieren.

## 4. Testfälle

| Fall | Ort | Datenstatus | wichtigste Prüfungen |
|---|---|---|---|
| `002_test_synthetic` | Quelle `examples/synthetic/network_v1/…`; installiert in `INTAKE:network_v1/pilots/` | vollständig erfunden; `test`, `fully_synthetic`, nicht empirisch | 32 Kontakte in allen fünf Bereichen + 1 nicht zuordenbar; 5 Gruppen (T, P, N, NS) mit Überlappung; 35 bestätigte, 7 verneinte, 2 ausdrücklich unbekannte Paare; Zwischenwerte, KA, M/S/M;S, Funktion 0; 14 Tests zu erwarteten Eigenschaften |
| `001_test_v0_fictionalized` | nur `INTAKE:network_v1/pilots/` | Struktur des v0-Pilotfalls, Codes umgedeutet, alles Identifizierende erfunden; `test`, `v0_derived_fictionalized`, nicht empirisch | 22 Kontakte, 6 Gruppen (T), 25 Mitgliedschaften; 41 bestätigte Paare und 190 unbekannte – identisch mit v0; 0 Fehler, 2 Warnungen (regionale Wohnortangabe, v0-Sprachmodus 6 ohne v1-Entsprechung) |

Beim ersten Aufbau von 001 griff die Schutzprüfung: das Codebuch des Pilotpakets hat feinere Kategorien als das synthetische v0-Beispiel. Gelesen
wurde daraufhin nur `codebook.csv` (Codebedeutungen, keine Angaben zu Personen); die Lesart steht in `network-versions.md` §4. Inhalte der
Kontakttabellen wurden vom Agenten nicht gelesen; die fiktionalisierten Grafiken wurden zur visuellen Prüfung angesehen.

## 5. Visualisierungen

Erzeugt unter `C:\dev\mares\mares_storage\network_v1\pilots\<Fall>\graphics\` (je PNG und SVG), z. B.
`002_test_synthetic_G1_persoenliches_netz.png` … `002_test_synthetic_G3_gruppen_zugehoerigkeit.png`; ebenso für `001_test_v0_fictionalized`.

| Grafik | implementiert | technisch getestet | visuell geprüft (002 / 001) | Korrekturen nach Sichtprüfung |
|---|---|---|---|---|
| G1 | ja | Radius = Nähe, deterministisch | ja / ja | Ringmarken frei gehalten; Kanten nahe Ego gebogen (sahen wie Ego-Linien aus) |
| G2 | ja | keine Ego-Elemente, Kantenzahl = bestätigte Paare | ja / – | isolierte Kontakte in eigener Zeile statt an Rändern; Legende von Notiz getrennt |
| P1 | ja | über Render- und Namenstests | ja / – | – |
| P2 | ja | dito | nein (gleicher Baustein wie P1) | – |
| P3 | ja | dito | ja / – | Klammer „Marburg und Mittelhessen“ angehoben |
| P4 | ja | dito | ja / – | dito |
| P5 | ja | dito | ja / – | Beschriftungen entzerrt |
| G3 | ja | keine Nichtmitglieder in fremden Umrandungen (002) | ja / ja | Layout ins Bild skaliert, Ungruppierte außen, rechte Spalte neu; **eingebettete Gruppe (001: eine Gruppe liegt ganz in zwei anderen) war unsichtbar** → engere, gestrichelte Umrandung |

## 6. Tests

- Vorphase: volle Suite 372 bestanden (vor den Commits).
- Neu: 137 Tests `tests/test_network_v1_*.py` (Codes und Geografie, Testfall 002, Validierung, Grafiken, Pipeline/CLI/Testfall 001) – bestanden.
- Volle Suite nach der Migration: **509 bestanden** (372 bisherige, jetzt als v0-Tests, + 137 neue). Drei v0-Tests mussten an die Umbenennung
  angepasst werden (zwei alte Modulnamen in Tests; die Datenschutzprüfung der Beispiele kennt jetzt v1-Fallordner und verlangt dort
  `test`/`fully_synthetic`/Jahr `0000`).

## 7. Status

| | |
|---|---|
| **implementiert** | v0-Abgrenzung, v1-Datenmodell, Prüfung, Ableitungen, acht Grafiken, CLI, zwei Testfälle, Dokumentation |
| **technisch getestet** | alle obigen Teile mit synthetischen Daten; beide Testfälle laufen fehlerfrei durch |
| **fachlich geprüft** | nichts. Die Sichtprüfung betraf Lesbarkeit, nicht wissenschaftliche Angemessenheit; die v0→v1-Lesart in 001 ist eine Testannahme |
| **offen** | §8 |

## 8. Offene Punkte

1. Die finalen v1-Erhebungsbögen und der Codierschlüssel fehlen im Repository; Kontextbogen-Felder und -Skalen sind vorläufig.
2. Lage des Fallbaums in `PRIMARY` (sobald eingerichtet); bis dahin `INTAKE`.
3. Kein Import aus einer v1-Excel-Vorlage; die Übertragung der Bögen in CSV ist Handarbeit.
4. `network_v0/pilots/001/graphics/` ist leer (kein v0-Export mit Standarddateinamen).
5. G1 bleibt bei vielen Kanten zwischen fernen Ringen unruhig (Winkellayout, siehe 001); für 30–40 Kontakte vorgesehen, über 32 nicht geprüft.
6. Das Mittelhessen-Verzeichnis enthält keine Ortsteile; Ortsteile brauchen `places.csv`.
7. Die Gemeindeliste stammt aus öffentlichen Kreislisten (Abruf 2026-10-31) und ist nicht gegen eine amtliche Quelle (AGS) geprüft.

## 9. Nächster Schritt

Die finalen v1-Bögen (leer) unter `templates/` ablegen und Codes sowie Kontextbogen gegen `network-v1.md` abgleichen – danach den ersten echten
v1-Pilotfall als `pilots/<NNN_name>/` mit `case_type: pilot` übertragen und rendern.
