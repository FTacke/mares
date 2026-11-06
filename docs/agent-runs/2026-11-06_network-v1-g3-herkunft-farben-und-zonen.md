# Run-Bericht 2026-11-06 – `network_v1`: G3-Herkunft mit festen Länderfarben, Kürzeln im Knoten und lokalen Zonen

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §6.2,
[`ADR-0020`](../decisions/ADR-0020_2026-11-06_netzwerk-v1-g3-herkunft-farben-und-zonen.md). Vorlauf:
[`2026-11-06_network-v1-experiment-g3-geburtsland.md`](2026-11-06_network-v1-experiment-g3-geburtsland.md). Für den authentischen
Fall MT nennt der Bericht keine Länder, Zusammensetzungen oder sonstigen Inhalte.

## 1. Ziel und Scope

Drei Festlegungen der Projektleitung umsetzen:

1. Kürzel im Knoten als bevorzugte Variante;
2. fallübergreifend stabile Länderfarben;
3. Lokalansicht mit schematischen Zonen und kleiner Übersichtskarte.

Die Variante bleibt experimentell, die neun Standardgrafiken bleiben unverändert. Vorab: Working Tree sauber, `main` = `origin/main`
(`1aa1d20`).

## 2. Änderungen

- `figures/networks.py`, nur optionale Parameter, die G3 selbst nicht nutzt:
  - `g3_layout(zones=…)`: Zonenbegrenzung, Anker nach Mitgliederanteil, abschließende Abstandskorrektur;
  - `g3_positions`/`g3_geometry`: Fläche, Zonen und freier Rand oben; Zonengrenze; geteilte Zeile der losen Kontakte.
- `figures/birth_country.py`:
  - feste Farbtabelle und Ergänzungsfarben;
  - Schriftfarbe nach WCAG-Kontrast;
  - `k. A.`/`–` statt erfundener Codes;
  - feste Legendenreihenfolge;
  - Zonen, kompakte Größe und Übersichtskarte;
  - nur noch die Ansichten `gesamt` und `lokal`.
- `experiments.py`: liest die Basiskarte von X1 für die Übersichtskarte; der Run-Record nennt die Zahl der Zonen.
- Tests `tests/test_network_v1_birth_country.py` neu gefasst (19).
- Dokumentation: `network-v1.md` §6.2, ADR-0020, Statusvermerk in ADR-0019.

## 3. Entscheidungen im Lauf

- **Farben per Validator.** Die zehn vorgegebenen Länder unterscheiden sich bei normalem Sehen paarweise deutlich (ΔE ≥ 16). Unter
  CVD-Simulation liegt ein Paar im Grenzbereich (ΔE 6,1); das deckt das Kürzel. Chile und das Olivgrün von GBR wurden leicht
  abgedunkelt bzw. aufgehellt, damit die Knotenschrift 4,5:1 erreicht; den Fall GBR hat ein Test gefunden.
- **Ergänzungsfarben getrennt von festen Farben.** Ein erster Stand verwendete dieselben Farben für feste und nicht feste Länder. In
  einem Fall bekamen dadurch zwei vorkommende Länder dieselbe Farbe. Die Ergänzungsfarben sind jetzt disjunkt (ΔE ≥ 10 zu jeder
  festen); ein Test sichert das.
- **Anker.** Spalten nach Mitgliederanteil allein ließen Gruppen auf gleicher Höhe kollidieren. Die Anker folgen deshalb vertikal der
  Gruppenfolge von G3; bei wenigen Gruppen ist die Spanne kleiner.
- **Abstand nach der Skalierung.** Die Zonengrenze kann zwei geschobene Knoten aneinanderhalten. Der Abstandsschritt rechnet die
  Schwelle auf die spätere Skalierung um. Ein erster Versuch ohne Umrechnung wirkte nicht; das zeigte die Messung.
- **Übersichtskarte:** Punkte als Marker, damit sie bei ungleichem Längen-/Breitenmaßstab rund bleiben; Beschriftungen von Wetzlar
  und Gießen auf gegenüberliegenden Seiten.

## 4. Tests und Prüfungen

- **Gesamtsuite:** 629 Tests bestanden.
- **Standardgrafiken:** alle 54 Dateien nach `render-all` bytegleich zum Stand vor dem Lauf. Zusätzlich wurden die Standardgrafiken der
  beiden Testfälle nach jedem Eingriff in `networks.py` neu gerendert und verglichen.
- **Erzeugt:** je Fall `…_G3_geburtsland_gesamt` und `…_lokal` (PNG, SVG) für `001_test_v0_fictionalized`, `002_test_synthetic` und
  `student_pilot/001_mt` (nur im geschützten Speicher).
- **Visuell:** alle sechs Grafiken geprüft. Kürzel und IDs sind lesbar, die Legenden passen zu den Knoten, und die Farben sind zwischen
  den Ansichten und Fällen gleich. In der Lokalansicht liegen die Zonen richtig, gemischte Gruppen sind je ein Umriss, und es gibt keine
  Überlagerungen von Knoten. Bei MT gibt es nur eine Zone.

## 5. Status und Beurteilung

- Implementiert, getestet und gerendert; nicht wissenschaftlich validiert und nicht kanonisiert.
- **Verbessern Zonen und Übersichtskarte die Lesbarkeit?** Überwiegend ja.
  - **Zonen:** Sie beantworten auf einen Blick, wer wo wohnt, und zeigen, dass Gruppen über beide Bereiche reichen; vorher stand das
    nur im Hinweis.
  - **Fläche:** Sie ist besser genutzt, und die Ansicht wirkt bei wenigen Kontakten nicht mehr verloren.
  - **Übersichtskarte:** Sie verortet den Raum ohne Konkurrenz zum Netz.
  - **Preis:** Die Zonengrenze zieht gemischte Gruppen in die Länge. Bei 002 werden zwei Umrisse lang und überschneiden sich, und
    Gruppenlabels stehen zum Teil etwas abseits in freier Fläche. Das Gruppengefüge ist dadurch schwerer zu lesen als in der
    ungezonten Fassung.
  - Für Fälle mit vielen gemischten Gruppen kann die Zonierung die Gruppenstruktur stärker überlagern, als sie hilft.
- **Offen:**
  - Ob die Übersichtskarte eine Bezirksgrenze erhalten soll; das bräuchte eine belastbare Quelle für Admin-2-Grenzen.
  - Ob die Lokalansicht die Positionen der Gesamtansicht übernehmen soll.
  - Variantenwahl, Grafikcode, Register und Textinventar bei einer Kanonisierung.
- **Einschränkungen:**
  - Zwei Länder ohne feste Farbe können sich eine Farbe teilen; das Kürzel unterscheidet sie.
  - Die Farbtabelle ist für die erwarteten Herkunftsländer ausgelegt und muss bei neuen häufigen Ländern ergänzt werden.
  - Die alten Vergleichsdateien der ersten Fassung (`…_kuerzel`, `…_legende`) liegen weiter im Experimentordner; gelöscht wird nichts.
