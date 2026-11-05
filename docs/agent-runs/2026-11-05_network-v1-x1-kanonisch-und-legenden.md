# Run-Bericht 2026-11-05 – `network_v1`: X1 als neunte Standardgrafik, Textinventar, dynamische Beziehungstyp-Legende

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §5.4, §6 und §6.1,
[`ADR-0016`](../decisions/ADR-0016_2026-11-05_netzwerk-v1-x1-kanonisch.md),
[`ADR-0017`](../decisions/ADR-0017_2026-11-05_netzwerk-v1-dynamische-beziehungstyp-legende.md). Vorlauf:
[`2026-11-05_network-v1-x1-fassung-2-8.md`](2026-11-05_network-v1-x1-fassung-2-8.md). Für den authentischen Fall MT nennt der Bericht
keine Orte, Länder oder sonstigen Inhalte.

## 1. Ziel und Scope

Drei Aufträge der Projektleitung:

1. **X1 kanonisieren.** Die Karte wird redaktionell reduziert und als neunte Standardgrafik in die reguläre Fallpipeline aufgenommen.
2. **Textinventar.** Alle sichtbaren Texte der neun Grafiken werden als Iststand erfasst. Die Texte von G1–G3 und P1–P5 werden dabei
   nicht verändert.
3. **Nachtrag im selben Lauf.** Die Beziehungstyp-Legenden zeigen nur noch die im Fall vorkommenden Typen, zentral in der gemeinsamen
   Komponente.

Vorab: Working Tree sauber, `main` = `origin/main` (`3ebcfd3`).

## 2. Änderungen

### 2.1 X1 kanonisch (Commit `28342d1`, Doku `c9b620b`)

- **Code und Aufruf:**
  - `experimental.py` wurde nach `figures/maps.py` verschoben (`git mv`); es bleibt eine einzige Implementierung.
  - `render_x1` und der eigene Ausgabeort `experimental/` entfallen, ebenso der Befehl `experimental-x1`.
  - X1 steht als neunter Eintrag im Register `FIGURES` (G1, G2, P1–P5, G3, X1).
- **Kartenquellen:**
  - `run.load_geo` liest Ortsverzeichnis und Basiskarte vor dem Anlegen des Run-Ordners.
  - Beide Quellen stehen mit SHA-256 unter `map_sources` im Run-Record und im `figures_index.json`.
  - Fehlt eine Datei, wird X1 übersprungen, mit dem Grund im Protokoll. Eine fehlerhafte Datei stoppt den Lauf mit `PipelineError`.
  - Die Quellen gelangen über das neue Feld `Context.geo` (`base.Geo`) zur Grafik.
- **Redaktionell (X1):**
  - Titel ohne Code, kein Untertitel. `page()` erhält dafür einen optionalen Untertitel mit niedrigerem Kopf und eine optionale
    eigene Fußzeile.
  - Ortszahlen als `n = x`, ein einzelner Kontakt ohne Zahl.
  - Legende ohne Linien- und Zahlerklärung.
  - Hinweise nur noch „Wohnort nicht darstellbar: …“ (nicht zuordenbar und ohne Ortsverzeichnis zusammengefasst) und „Kartengrundlage:
    Natural Earth.“
  - Fußzeile ohne Gruppenzahl und ohne Datenqualität.
  - Layout, Gruppierung und Platzierung sind unverändert (Fassung 2.8).
- **Fallmetadaten MT:**
  - `data_quality` steht nach Entscheidung der Projektleitung im Lauf jetzt auf `VALIDATED` statt `UNREVIEWED`.
  - Geändert ist nur dieser Wert in `metadata.json` im geschützten Storage. Er erscheint nicht in X1, wohl aber, wie bisher für
    authentische Fälle, in der Fußzeile von G1–G3 und P1–P5.
- **Dokumentation:**
  - `network-v1.md` (§1, §2, §6 mit neun Grafiken, §6.1 neu gefasst, §8 ohne Experimentbefehl);
  - `storage-contract.md`, `network-versions.md`, README, Pilot-README;
  - ADR-0016;
  - [`network-v1-visualization-text-inventory.md`](../architecture/network-v1-visualization-text-inventory.md).
- **Textinventar:**
  - Teil A (gemeinsame Texte), Teil B (je Grafik eine Tabelle mit Element, Wortlaut, Herkunft und Bedingung), Teil C
    (Doppelimplementierungen und abweichende Wortlaute).
  - Der Entwurf für G1–P5 stammt von einem Subagenten, der ausschließlich Quellcode las. Die Zeilenverweise wurden danach per
    Zeilenabgleich auf den Endstand umgerechnet und stichprobenartig geprüft.
  - X1 wurde nach der Bereinigung ergänzt.

### 2.2 Dynamische Beziehungstyp-Legende

- **Zentral in `base.relation_entries`:**
  - Es erscheinen nur die Typen, die mindestens ein Kontakt des Falls mit gültigem Code hat, in fester Reihenfolge und mit fester Farbe.
  - Ein Kontakt ohne gültigen Typ bleibt „keine Angabe“.
  - Ohne Kontakte entfällt der Abschnitt.
  - Keine Grafik hat eine eigene Logik dafür.
- **Doku:** `network-v1.md` §5.4, Inventar A.4, ADR-0017.

## 3. Tests und Prüfungen

- **Neue oder geänderte Tests:**
  - neun Grafiken im Register;
  - X1 durch `process_case` in `graphics/` (18 Dateien bei PNG und SVG);
  - Skip ohne Basiskarte;
  - fehlerhaftes Ortsverzeichnis stoppt den Lauf vor dem Schreiben;
  - der Befehl `experimental-x1` existiert nicht mehr;
  - die vereinbarten X1-Texte, darunter der Ausschluss von Fassung, Experiment, Maßstab und Datenqualität;
  - Datenqualität eines authentischen Falls erscheint nicht in X1;
  - Legende nur mit vorhandenen Typen in fester Reihenfolge und Farbe;
  - Fall ohne gültige Typen rendert alle Grafiken;
  - **Hauptbereich jeder Grafik unverändert** gegenüber der vollen Legende (Knoten, Farben, Texte, Linien, Flächen);
  - Legende mit weniger Typen braucht weniger Platz.
  - Die gemeinsamen Test-Fixtures stellen jetzt eine synthetische Basiskarte und ein synthetisches Ortsverzeichnis bereit.
- **Testläufe:**
  - Vor der Legendenänderung bestand die Gesamtsuite mit 602 Tests.
  - Endstand: 606 Tests bestanden.
- **Regression G1–G3, P1–P5 nach der Kanonisierung:**
  - Nach dem regulären Rendern waren alle 48 bisherigen Dateien der drei Fälle per SHA-256 bytegleich.
  - Nach der Statusänderung bei MT unterschieden sich dessen 16 Dateien. Ein Rendern im Speicher mit dem alten Status ergab wieder alle
    16 bytegleich: Die Abweichung kommt allein aus der Metadatenangabe der Fußzeile.
- **Regression nach der Legendenänderung:**
  - P3 und P4 (ohne Beziehungstyp-Legende) sind bytegleich.
  - G1, G2, G3, P1, P2, P5 und X1 haben sich geändert.
  - Für alle drei Fälle und alle neun Grafiken ist der Hauptbereich identisch mit dem Stand der vollen Legende.
  - Die Legenden enthalten 001: vier Typen, 002: fünf, MT: vier.
  - Die Gesamthöhe der Grafiken ändert sich nicht, weil die Legenden einzeilig bleiben.
- **Rendering:** Alle drei Fälle (`001_test_v0_fictionalized`, `002_test_synthetic`, `student_pilot/001_mt`) wurden regulär mit
  `render --formats png,svg` gerendert. Jeweils 18 Dateien liegen in `graphics/`, X1 ist `rendered`.
- **Visuell geprüft:**
  - X1 aller drei Fälle (Titel, kein Untertitel, `n = x`, Legende, Hinweise, Fußzeile; MT mit allen 22 Kontakten);
  - G1 von MT und P1 von 002 nach der Legendenänderung.

## 4. Entscheidungen

- **Fehlende Kartenquellen:** X1 wird als expliziter Zustand übersprungen, statt den ganzen Lauf abzubrechen. So bleiben Läufe ohne
  Basiskarte möglich, und der Grund steht im Protokoll (ADR-0016, Entscheidung 3).
- **Bedingte Legendeneinträge:** „○ weiterer Ort einer Ortsgruppe“ und „nur Wohnland bekannt (Lage unscharf)“ bleiben bedingt in der
  X1-Legende. Sie erklären ein Symbol, nicht die Platzierung. Ihre Prüfung gehört zur redaktionellen Runde.
- **Fallkennzeichnung:** Sie bleibt die gemeinsame Logik aller Grafiken (`FALL · {display_code}`) und wurde für X1 nicht eigens
  umgestellt.
- **Alte Ausgaben:** Entwicklungsstände unter `<Fall>/experimental/` bleiben liegen. Die Pipeline liest und schreibt dort nichts.
  Gelöscht wurde nichts.

## 5. Status und offene Punkte

- **Status:**
  - Implementiert, getestet, gerendert.
  - Gesamtsuite im Endstand: 606 Tests bestanden.
  - Fachlich nicht validiert: Die Gestaltung ist abgenommen, die Grafiken sind keine wissenschaftlich validierten Ergebnisse.
- **Offen:**
  - Redaktionelle Prüfung der Texte von G1–G3 und P1–P5 anhand des Inventars. Das Inventar nennt dafür auffällige Doppel- und
    Abweichungsstellen, etwa vier Formulierungen für fehlende Angaben und drei für nicht zuordenbare Wohnorte.
  - Die Fußzeile von G1–G3 und P1–P5 zeigt weiter die Datenqualität authentischer Fälle (bei MT jetzt `VALIDATED`).
  - Die Verzeichnisse `<Fall>/experimental/` können auf Entscheidung einer Person entfernt werden.
  - Das Inventar nennt zwei ungeprüfte Codepfade: die G3-Sortierung bei ungültigem Zugehörigkeitswert und die „keine Angabe“-Legende
    bei nicht gezeichneten Kontakten.
