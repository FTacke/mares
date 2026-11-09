# Run-Bericht 2026-11-09 – `network_v1`: student_pilot LS, GH und JZ

Journal eines Laufs, keine Spezifikation. Maßgeblich:
[`ADR-0026`](../decisions/ADR-0026_2026-11-09_netzwerk-v1-mehrere-beziehungstypen-und-student-pilot-ls-gh-jz.md),
[`network-v1.md`](../architecture/network-v1.md) §2.1 und §7. Der Bericht enthält keine Namen, Orte oder Einzelwerte, nur Zählungen,
A-IDs und Kürzel.

## 1. Ziel und Scope

Drei studentische Peer-Pilotfälle sollten aus den ausgefüllten Original-PDFs in das Korpus `student_pilot` übernommen werden, mit je
neun Standardgrafiken. Grundlage waren die Transkription und die verbindlichen Klärungen der Projektleitung. Die PDFs wurden mit
ausdrücklicher Freigabe lokal gelesen und abgeglichen.

## 2. Daten (nur im geschützten Speicher)

- Quellen in `INTAKE:inbox/MARES_student_pilot_<K>_2026-11-09/`:
  - byteidentische Kopie des PDFs;
  - `SHA256SUMS.txt`;
  - `LIEFERUNG.md` mit dem ursprünglichen Dateinamen, der Herkunft und dem Seiteninhalt.
- Die Kopien im Repository-Root wurden nach dem Prüfsummenvergleich entfernt.
- Fälle `INTAKE:network_v1/student_pilot/002_ls`, `003_gh`, `004_jz`:
  - 23, 21 und 15 Kontakte, je 5, 5 und 4 Gruppen, alle mit Status T;
  - Datenqualität `UNREVIEWED`, `empirical_analysis_eligible: false`.
- Übertragung mit einem einmaligen Skript außerhalb des Repositorys, wie beim Fall MT.
  - Rollen nur dort, wo sie keine Namen sind; Personennamen Dritter sind nicht übertragen.
  - Die Netzwerkkarten liefern keine Daten.
- Ortsverzeichnis `INTAKE:network_v1/reference/gazetteer.csv`: 17 Orte mit öffentlich bekannten Stadtkoordinaten von Hand ergänzt,
  ohne Geocoding-Dienst. Je Fall stehen zwei Orte außerhalb Mittelhessens in `places.csv`.

## 3. Abgleich mit den PDFs (Abweichungen zur Transkription)

| Fall | Abweichung | Behandlung |
|---|---|---|
| LS | Wohnort zweier Kontakte lautet im Original anders als in der Transkription | Original übernommen, nicht zugeordnet, Prüfhinweis |
| LS | gestrichene Werte bei Nähe (vier Kontakte), Häufigkeit (ein Kontakt) und Bedeutung (zwei Kontakte) | gültiger Wert übernommen, Streichung im Kommentar |
| LS | eine bei der Erhebung unterschriebene Einwilligungserklärung liegt im PDF | Vorhandensein vermerkt, nicht geprüft; Status laut Projektleitung bestätigt |
| GH | Schreibweise eines Wohnorts | Original übernommen; ohne Ortsverzeichniseintrag |
| GH | Kreuz bei Erwerbstätigkeit | geprüft: gesetzt |
| JZ | Schreibweise eines Wohnorts | normalisiert, Original im Kommentar |

Alle übrigen Werte stimmen mit der Transkription überein. Die Klärungen der Projektleitung sind umgesetzt und im Kommentar und in
`limitations` vermerkt:

- Sammelkontakte bleiben je ein Knoten.
- Zwei Beziehungstypen bei einem Kontakt.
- Mitgliedschaften gelten laut Tabelle C.
- Widersprüchliche Sprachangabe: Deutsch.
- `MR` = Marburg.
- Gestrichene Sprachgebrauchswerte sind ungültig.
- „1/S2“ wird als überwiegende Sprache gespeichert, die Situation steht im Kommentar.
- „M;S“ ist gültig.
- „auf Reisen“ ohne Wohnland.
- Keine Einzelkanten aus der Notiz „weitere Verbindungen“.

## 4. Code

- `network_v1/case.py`: `relation_type` liest mehrere Codes.
- `network_v1/validate.py`: Warnung `relation_type_several`.
- `network_v1/figures/base.py`:
  - geteilter Knoten und Legendenzeile „mehrere Beziehungstypen“;
  - G1-Sektor für Kombinationen.
- Tests: Ein Fehlerfall wurde von „1, 3“ auf einen doppelten Code umgestellt; ein neuer synthetischer Test prüft zwei Beziehungstypen.

## 5. Prüfungen

- Validierung, jeweils 0 Fehler:
  - LS: Rollen fehlen bei Kontakten, die nur mit Namen genannt sind; drei Wohnorte nicht zuordenbar.
  - GH: zwei Beziehungstypen; Abschlussblock fehlt.
  - JZ: Abschlussblock fehlt.
- Paare:
  - LS: 71 bestätigt;
  - GH: 32 bestätigt;
  - JZ: 18 bestätigt;
  - alle übrigen ohne Aussage, 0 Widersprüche.
- Rendering `COMPLETED`: je elf Grafiken, darunter G4 und G5. Die 27 verlangten Grafiken (G1, G2, P1–P5, G3, X1) sind einzeln
  visuell geprüft.
- Regression:
  - v1-Testfälle und `001_mt` mit HEAD- und neuem Code in ein Scratch-Verzeichnis gerendert: 66 von 66 Dateien bytegleich.
  - Bestehende `graphics/`-Ordner sind nicht neu geschrieben.
  - v0 ist nicht betroffen.
- Gesamtsuite: 506 bestanden, 0 fehlgeschlagen.

## 6. Status und offene Punkte

- Integriert, technisch geprüft, gerendert; **nicht wissenschaftlich validiert**, Freigabe offen.
- Offen:
  - LS: Lesart eines Wohnorts zweier Kontakte.
  - GH, JZ: formaler Einwilligungsnachweis (nicht im PDF).
  - GH, JZ: Abschlussblock nicht ausgefüllt.
  - GH: ein Wohnort ohne Ortsverzeichniseintrag.
  - JZ: Heimatort ohne Ortsverzeichniseintrag.
