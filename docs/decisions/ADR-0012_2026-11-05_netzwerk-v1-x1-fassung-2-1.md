# ADR-0012 – `network_v1`: X1 Fassung 2.1 (Ortsgruppen nur nach Entfernung, Ausschnitte nach den Daten)

**Datum:** 2026-11-05 · **Status:** in Kraft (Experiment; ändert in [`ADR-0011`](ADR-0011_2026-11-05_netzwerk-v1-x1-fassung-2.md)
die Entscheidungen 2 und 4)

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §6.1.

## Kontext

Fassung 2 fasste Orte auch dann zu „… und Umgebung“ zusammen, wenn sie nur auf der Karte zusammenfielen. In Testfall 002 entstand
so „Bogotá und Umgebung“ mit dem rund 240 km entfernten Medellín. Die Kartenausschnitte waren fest und zeigten bei wenigen,
konzentrierten Orten viel leere Fläche, etwa bei MT ganz Nord- und Mittelamerika oder Osteuropa.

## Entscheidungen

1. **„… und Umgebung“ nur nach geografischer Entfernung** (Luftlinie aus dem Ortsverzeichnis, höchstens 20 km). Kollidierende
   Symbole weiter entfernter Orte weichen aus; eine gepunktete Linie führt zur wahren Lage. Diese Linien sind Positionskorrekturen,
   keine Beziehungen.
2. **Ausschnitte nach den Daten:** Umriss der Orte des Panels, dazu ein Rand, eine Mindestgröße zur Orientierung und ein begrenztes
   Seitenverhältnis. Deutschland bleibt im Deutschland-Rahmen und ist mit mindestens 9° × 7,5° erkennbar. Ohne Kontakte gilt der
   Standardausschnitt. Es gibt keine fallbezogenen Koordinaten oder Ausschnitte im Code.
3. **Eigene Maßstäbe je Panel**, in der Fußnote genannt: Entfernungen sind zwischen den Panels nicht vergleichbar.
4. **Kompaktere Ortskästen:** kleinere Schrift, die Einzelorte heller und kleiner, engere Innenabstände, dünnerer Rahmen.
   Die Flächen sind etwas enger.
5. Versionierung: Fassung 2.1 ersetzt Fassung 2 unter demselben Dateinamen; Fassung 1 bleibt in `experimental/x1_fassung_1/`.
   Fassung 2 ist aus Git reproduzierbar.

## Folgen

- In Testfall 002 stehen Bogotá und Medellín getrennt; Medellín weicht neben die Bogotá-Fläche aus.
- Je weniger und je enger die Orte, desto größer der Maßstab eines Panels. Gleich große Symbole stehen deshalb in den Panels für
  unterschiedlich große Gebiete.
