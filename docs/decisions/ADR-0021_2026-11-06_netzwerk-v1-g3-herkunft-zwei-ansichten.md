# ADR-0021 – `network_v1`: G3-Herkunft mit zwei Ansichten, ohne geografische Zonen

**Datum:** 2026-11-06 · **Status:** in Kraft als Experiment (keine Kanonisierung). Ersetzt in
[`ADR-0020`](ADR-0020_2026-11-06_netzwerk-v1-g3-herkunft-farben-und-zonen.md) die Entscheidungen 3 bis 5 (Zonen, Übersichtskarte,
kompakte Fläche mit Zonen); Entscheidungen 1 und 2 (Kürzel im Knoten, feste Länderfarben) gelten weiter.

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §6.2.

## Kontext

Die Projektleitung hat die Fassungen an den Testfällen 001 und 002 verglichen und entschieden:

- Weitergeführt werden nur die Gesamt- und die Lokalansicht mit Kürzeln im Knoten.
- Die Zonen „Marburg“ / „Übriges Mittelhessen“ und die Übersichtskarten entfallen. Sie zogen gemischte Gruppen auseinander, machten
  die Darstellung komplexer und brachten für die Gruppenanalyse wenig.
- Die Lokalansicht soll bei kleinen Teilnetzen kompakter werden.

## Entscheidungen

1. **Zwei Ansichten, eine Beschriftung.** `gesamt` und `lokal`, beide mit A-ID und Alpha-3-Kürzel und denselben festen Farben; nur
   diese beiden Dateien je Fall und Format.
2. **Wohnort nur als Filter.** Die Lokalansicht verwendet das rein soziale G3-Layout des Teilnetzes, ohne räumliches
   Positionierungsprinzip.
3. **Verdichten nur zwischen unverbundenen Teilen.** Teile ohne gemeinsame Verbindung oder Gruppe werden nebeneinander oder
   untereinander gesetzt. Ihr Abstand hat in G3 ohnehin keine Bedeutung. Innerhalb eines Teils ändert sich nichts, so bleibt die
   Topologie erhalten. Die Fläche richtet sich nach dem Teilnetz. Es gibt keine fallbezogenen Koordinaten oder Ausnahmen.
4. **Alte Ausgaben entfernt.** Die verworfenen Dateien (`…_kuerzel`, `…_legende`, die Zonen-Karten-Fassung) wurden aus den
   Experimentordnern gelöscht; nachvollziehbar bleiben sie über Git-Historie, ADRs und Run-Berichte.

## Folgen

- G3 hat optionale Parameter für Fläche und Verdichtung, die G3 selbst nicht nutzt. Die neun Standardgrafiken bleiben bytegleich.
- Die Zonen- und Kartenfunktionen sind aus dem Code entfernt.
