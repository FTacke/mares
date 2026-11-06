# Run-Bericht 2026-11-06 – `network_v1`: G3-Herkunft auf zwei Ansichten finalisiert

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §6.2,
[`ADR-0021`](../decisions/ADR-0021_2026-11-06_netzwerk-v1-g3-herkunft-zwei-ansichten.md). Vorlauf:
[`2026-11-06_network-v1-g3-herkunft-farben-und-zonen.md`](2026-11-06_network-v1-g3-herkunft-farben-und-zonen.md). Für den
authentischen Fall MT nennt der Bericht keine Länder, Zusammensetzungen oder sonstigen Inhalte.

## 1. Ziel und Scope

Nach der Entscheidung der Projektleitung werden nur die Gesamt- und die Lokalansicht mit Kürzeln im Knoten weitergeführt. Zonen
und Übersichtskarte entfallen, die Lokalansicht wird kompakter, verworfene Ausgaben werden entfernt. Weiterhin experimentell, die
neun Standardgrafiken bleiben unverändert. Vorab: Working Tree sauber, `main` = `origin/main` (`6978541`).

## 2. Änderungen

- `figures/networks.py`: Zonenlogik entfernt (Stand vor ADR-0020 wiederhergestellt). Neu sind nur optionale Parameter, die G3 selbst
  nicht nutzt:
  - Fläche (`width`, `height`) in `g3_positions`/`g3_geometry`;
  - `compact` mit `structure_parts` (unverbundene Teile) und `_compact`: unverbundene Teile rechts oder unterhalb ansetzen, je
    nach Seitenverhältnis.
- `figures/birth_country.py`: Zonen, Karten und deren Konstanten entfernt. Die Lokalansicht ist das G3-Layout des Teilnetzes mit
  Verdichtung und einer an das Teilnetz angepassten Fläche (`local_size`). Der Hinweis ist kürzer.
- `experiments.py`: keine Basiskarte mehr; Speichern mit der Wiederholung bei kurz gesperrter Datei (`_save`), wie bei den
  Standardgrafiken.
- Tests neu gefasst (19):
  - keine Geografie in der Lokalansicht;
  - Verdichtung verschiebt nur ganze Teile;
  - kompaktes Layout ohne Überlagerungen, alles innerhalb der Fläche;
  - an einer synthetischen Kopie von 002 mit zwei unverbundenen lokalen Gruppen.
- Dokumentation: `network-v1.md` §6.2 neu gefasst, ADR-0021, Statusvermerk in ADR-0020.

## 3. Daten im geschützten Speicher

- Je Fall acht verworfene Dateien einzeln mit exaktem Namen gelöscht: `…_G3_geburtsland_{gesamt|lokal}_{kuerzel|legende}.{png,svg}`,
  insgesamt 24. Die Zonen-Karten-Fassung (`…_gesamt`/`…_lokal`) wurde durch das Neurendern ersetzt. X1-Dateien und andere
  Experimentordner blieben unberührt.
- Ein Renderlauf brach an einer kurz gesperrten Datei ab. Ursache war eine offene Vorschau; daher gibt es jetzt die Wiederholung beim
  Speichern. Sein leerer Laufordner unter `WORKSPACE/runs/` wurde mit exaktem Namen entfernt.

## 4. Tests und Prüfungen

- **Gesamtsuite:** 629 Tests bestanden.
- **Standardgrafiken:** alle 54 Dateien nach `render-all` bytegleich zum Stand vor den G3-Herkunft-Läufen.
- **Erzeugt:** je Fall genau vier Dateien (`gesamt`, `lokal` × PNG, SVG) für `001_test_v0_fictionalized`, `002_test_synthetic` und
  `student_pilot/001_mt` (nur im geschützten Speicher).
- **Visuell:** alle sechs PNGs geprüft.
  - Kürzel und IDs sind lesbar, und es gibt keine Überlagerungen.
  - Jedes Land hat einen eigenen Legendeneintrag; eine graue Sammelkategorie gibt es nicht.
  - Lokal 001 und MT: zwei Gruppen nebeneinander statt übereinander mit leerem Band.
  - Lokal 002: Gruppenüberschneidungen bleiben erkennbar; „5 von 7“ steht am richtigen Label.
  - Keine Zonen, keine Karten.

## 5. Status und offene Punkte

- Implementiert, getestet und gerendert; nicht wissenschaftlich validiert und nicht kanonisiert.
- In kleinen lokalen Netzen sind die Abstände zwischen den Knoten wegen der Mindestfläche größer als in der Gesamtansicht; die Knoten
  selbst sind nicht größer.
- Offen bei einer Kanonisierung: Grafikcode, Aufnahme ins Register und ins Textinventar.
