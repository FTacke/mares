# ADR-0017 – `network_v1`: Beziehungstyp-Legende nur mit den Typen des Falls

**Datum:** 2026-11-05 · **Status:** in Kraft

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §5.4. Texte:
[`network-v1-visualization-text-inventory.md`](../architecture/network-v1-visualization-text-inventory.md) A.4.

## Kontext

Die Beziehungstyp-Legende zeigte in jeder Grafik alle sechs Kategorien des Codierschlüssels, auch wenn ein Fall einige davon gar nicht
enthält. Die Legende wurde dadurch länger als nötig und deutete Kategorien an, die im Fall nicht vorkommen.

## Entscheidungen

1. **Die Legende zeigt nur die Beziehungstypen, die im Fall vorkommen.** Ein Typ erscheint, wenn mindestens ein Kontakt des Falls ihn
   mit gültigem Code hat. Ermittelt wird das je Fall über alle Kontakte, nicht je Grafik, damit alle Grafiken eines Falls dieselbe
   Legende tragen.
2. **Reihenfolge und Farben bleiben fest** (Tabelle A, `RELATION_COLORS`): Ein Typ hat in jedem Fall dieselbe Farbe, unabhängig davon,
   welche anderen Typen vorkommen.
3. **Fehlende oder ungültige Angaben werden keinem Typ zugeschlagen.** Sie bleiben weiß mit gepunktetem Rand und haben den Eintrag
   „keine Angabe“. Ein Fall ganz ohne gültige Typen hat nur diesen Eintrag.
4. **Eine Stelle:** Die Filterung steckt in der gemeinsamen Komponente `base.relation_entries`, die G1, G2, G3, P1, P2, P5 und X1
   verwenden. P3 und P4 haben keine Beziehungstyp-Legende und bleiben unverändert.

## Folgen

- Die Legenden von G1–G3, P1, P2, P5 und X1 ändern sich je nach Fall. Knoten, Farben und alle übrigen Elemente bleiben gleich; ein
  Test vergleicht dafür den Hauptbereich jeder Grafik mit dem Stand der vollen Legende.
- Bei den drei vorhandenen Fällen entfallen ein oder zwei Einträge. Die Legenden waren schon einzeilig und werden nur kürzer; die
  Gesamthöhe der Grafiken ändert sich dort nicht.
