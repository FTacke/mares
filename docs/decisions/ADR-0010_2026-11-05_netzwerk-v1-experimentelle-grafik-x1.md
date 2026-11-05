# ADR-0010 – `network_v1`: experimentelle Zusatzgrafik X1 (geografische Verteilung)

**Datum:** 2026-11-05 · **Status:** in Kraft (Experiment zur Evaluation; keine Aufnahme in den Standardsatz entschieden)

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §2 und §6.1.

## Kontext

G2 zeigt Wohnortbereiche als Bänder mit den bestätigten Verbindungen. Offen ist, ob eine echte Karte, die nur die räumliche
Verteilung zeigt, zusätzlich zum Standardsatz gehören soll. Die Kartenvariante von G2
([`pilots/network_v1_map/`](../../pilots/network_v1_map/README.md)) lief nur mit dem synthetischen Fall 002. Sie hatte Verbindungslinien und
einen Mittelhessen-Ausschnitt und war bei dichter lokaler Lage schwer lesbar. Für die Entscheidung wird Vergleichsmaterial aus allen
vorhandenen Fällen gebraucht, auch aus einem authentischen.

## Entscheidungen

1. **X1 ist experimentell.** Die Grafik ist kein Teil der acht Standardgrafiken und läuft nicht in `render`/`render-all`. Sie hat
   einen eigenen Befehl und liegt im eigenen Fallordner `experimental/` neben `graphics/`. So bleibt die Regel „`graphics/` enthält nur
   die Standardgrafiken“ unverändert.
2. **Nur Verteilung, keine Linien.** Die Beziehungsstruktur zeigt G2. Die Karte bleibt ruhig; Farbe bleibt Beziehungstyp.
3. **Panels Amerika · Europa · Deutschland** (von links nach rechts, in jedem Fall gleich), weitere Regionen nur bei Bedarf.
   Deutschland ersetzt den Mittelhessen-Ausschnitt.
4. **Dichte ehrlich zusammenfassen.** Auf der Deutschlandkarte liegen Orte um Marburg nur Millimeter auseinander. Sie werden zu einer
   benannten Ortsgruppe zusammengefasst; keine lange Zuordnungslinie durch die Knoten, keine scheinbare Genauigkeit.
5. **Keine erfundene Lage.** Nur das Wohnland bekannt: Länderpunkt, gestrichelt, als unscharf beschriftet. Nicht zuordenbar oder
   ohne Koordinate: nur in der Fußnote.
6. **Koordinaten aus einem lokalen, von Hand gepflegten Ortsverzeichnis** im Root der Fälle, nicht im Repository: Es verriete die
   Wohnorte echter Fälle. Kein Geocoding-Dienst, damit keine Wohnortangabe den Rechner verlässt.

## Folgen

- X1 liegt für 001*, 002* und `student_pilot` MT vor. Neue Orte brauchen einen Eintrag im Ortsverzeichnis, sonst nennt die Fußnote den
  Kontakt.
- Die Aufnahme in den Standardsatz ist offen. Sie wäre eine eigene Entscheidung, mit der Grafik dann in `graphics/` und im Register.
