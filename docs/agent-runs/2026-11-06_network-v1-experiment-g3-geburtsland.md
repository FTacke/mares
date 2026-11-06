# Run-Bericht 2026-11-06 – `network_v1`: Experiment G3 nach Geburtsland

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §2 und §6.2,
[`ADR-0019`](../decisions/ADR-0019_2026-11-06_netzwerk-v1-experiment-g3-geburtsland.md). Vorlauf:
[`2026-11-05_network-v1-redaktioneller-standard.md`](2026-11-05_network-v1-redaktioneller-standard.md). Für den authentischen Fall MT
nennt der Bericht keine Länder, Zusammensetzungen oder sonstigen Inhalte.

## 1. Ziel und Scope

Auftrag der Projektleitung: eine experimentelle Variante von G3 mit Knotenfarbe nach Geburtsland, als Gesamt- und als Lokalansicht
(Marburg und übriges Mittelhessen), jeweils in zwei Beschriftungsvarianten. G3 bleibt kanonisch und unverändert. Eine Kanonisierung der
Variante ist nicht beschlossen.

Vorab: Working Tree sauber, `main` = `origin/main` (`2dbec5d`).

## 2. Änderungen

**Code:**
- `figures/networks.py`: G3 ist in `g3_geometry` (Positionen, Umrisse, Labelboxen, Ringsegmente) und `draw_g3` getrennt.
  `place_labels` erhält Knotenradius und Labelzeilen als Parameter. `g3()` setzt sich daraus unverändert zusammen.
- `figures/base.py`: `page()` hat einen optionalen Titel für Grafiken außerhalb von `TITLES`.
- neu `figures/birth_country.py`: Länderschlüssel, Farbzuordnung, Legenden, Lokalansicht und die vier Varianten.
- neu `experiments.py` und der CLI-Befehl `v1 experiment g3-geburtsland` (Fall oder ganzer Root). Er schreibt nach
  `<Fall>/experimental/g3_geburtsland/` und legt einen Run-Record nur mit Zahlen an.

**Dokumentation:** `network-v1.md` §2, neuer §6.2 und §8; `storage-contract.md` (Ordner `experimental/`); ADR-0019.

## 3. Entscheidungen im Lauf

- **Palette per Validator gewählt.** Ich habe den OKLab-/CVD-Validator des Datenvisualisierungs-Leitfadens auf Okabe-Ito, Paul Tol
  und weitere gängige Paletten angewandt. Bei verstreuten Knoten zählt jedes Farbpaar. Die bekannten Acht- bis Dreizehnerpaletten
  bestehen diesen Test nicht. Eine Suche fand neun Farben, die ihn bestehen; mehr Länder teilen ein Grau.
- **Lokalansicht:** Das G3-Layout wird auf das Teilnetz neu berechnet, statt die Gesamtpositionen mit Lücken zu übernehmen.
  Umrissfarben bleiben die des Falls. Die Fußzeile zählt weiter alle Kontakte; ein Hinweis nennt „n von N“. Er nennt auch die
  ausgeblendeten Gruppen und die Kontakte mit nicht zuordenbarem Wohnort.
- **Variante 1:** Knoten 24 statt 20 pt, Kürzel 5,6 pt unter der ID. Die Positionen sind dieselben wie in Variante 2 und G3; nur die
  Labelplatzierung berücksichtigt den größeren Radius.
- **Variante 2:** Die Länderlegende steht rechts neben der Karte, am rechten Rand des Inhalts und oben bündig. Die Seite wird dafür
  bei Bedarf breiter. Die grauen „weiteren“ Länder nennt die Legende mit den Kontakt-IDs, weil der Knoten kein Kürzel trägt.
- **Uncodierte Namen:** Ein genanntes, aber nicht codiertes Geburtsland wird nicht als `keine Angabe` gezählt, sondern bleibt ein
  eigener Eintrag mit seinem Namen.

## 4. Tests und Prüfungen

- Neue Tests `tests/test_network_v1_birth_country.py` (17). Sie prüfen:
  - Länderschlüssel und fehlende Angaben;
  - die Palette sowie stabile und eindeutige Farben;
  - Umrisse, Umrissfarben und Verbindungen der Gesamtansicht gleich G3, Positionen unabhängig vom Knotenradius;
  - die Knotenfarbe jedes gezeichneten Knotens gleich der Farbe seines Landes, in beiden Ansichten und beiden Varianten;
  - Kürzel nur in Variante 1 und eine Legende nur mit vorkommenden Ländern;
  - Filterung, Gruppen-IDs und Mitgliederzahlen der Lokalansicht;
  - Ausgabeort und Dateinamen, die unberührten Standardgrafiken, den Run-Record ohne Länder, einen Fall mit Prüffehlern und die CLI.
- Gesamtsuite: siehe §5.
- **Standardgrafiken unverändert:** Alle 54 Dateien (3 Fälle × 9 Grafiken × PNG/SVG) sind nach `render-all` bytegleich zum Stand vor
  dem Lauf.
- **Erzeugt:** je Fall 8 Dateien in `experimental/g3_geburtsland/` für `001_test_v0_fictionalized`, `002_test_synthetic` und
  `student_pilot/001_mt` (nur im geschützten Speicher).
- **Visuell:** alle 12 Grafiken geprüft. Keine Überlagerungen von Knoten, Labels und Legende. Die Kürzel sind lesbar, die Lokalfilter
  und Zahlen stimmen, und die Farben sind in beiden Ansichten gleich.

## 5. Status und offene Punkte

- Implementiert, getestet und gerendert; nicht wissenschaftlich validiert und nicht kanonisiert.
- Gesamtsuite: 627 Tests bestanden.
- **Vergleich der Varianten** (an 001 mit 6 und 002 mit 12 Geburtsländern):
  - **Variante 1 (Kürzel im Knoten):** Das Land jedes Knotens ist ohne Farbabgleich lesbar. Das gilt auch für die grauen „weiteren“
    Länder und bei Farbfehlsichtigkeit oder Schwarzweißdruck. Nachteile: etwas größere, dichtere Knoten und ein kleiner Kürzeltext.
  - **Variante 2 (Legende neben der Karte):** Sie ist ruhiger, und Gruppen und Verbindungen treten stärker hervor. Das Land hängt aber
    allein an der Farbe. Ähnliche Blautöne (drei der neun Farben) verlangen den Blick in die Legende. Bei mehr als neun Ländern braucht
    die Legende die ID-Liste.
  - **Empfehlung:** Variante 1 als Arbeitsfassung, weil die Länderzuordnung nicht von der Unterscheidung von bis zu neun Farbtönen
    abhängt. Variante 2 bleibt für Fälle mit wenigen Ländern und für Präsentationen erhalten.
- Offen bei einer Kanonisierung: Variantenwahl, Grafikcode, Aufnahme ins Register und ins Textinventar. Offen ist auch, ob die Lokalansicht
  die Gesamtpositionen übernehmen soll, damit beide Ansichten direkt vergleichbar sind.
- Einschränkungen:
  - Die Farbstabilität über Fälle hinweg ist nur bedingt: Zwei Länder mit demselben bevorzugten Platz weichen je nach Fall
    unterschiedlich aus.
  - Knotenfarben können Umrissfarben ähneln (etwa Weinrot und Indigo neben den gedämpften Gruppenfarben). Die Umrisse sind Linien, die
    Knoten Flächen; verwechselt wurde in der Sichtprüfung nichts.
