# ADR-0015 – `network_v1`: X1 Fassung 2.5 (Ortspunkt immer frei, Kontakte daneben)

**Datum:** 2026-11-05 · **Status:** in Kraft (Experiment; ersetzt in
[`ADR-0011`](ADR-0011_2026-11-05_netzwerk-v1-x1-fassung-2.md) Entscheidung 1)

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §6.1.

## Kontext

Bis Fassung 2.4 standen die Kontakte in Ringen um den Ortspunkt. In dichten Panels mussten Ortsgruppen ausweichen. Ortspunkte und
Linien lagen dann unter fremden Flächen, und manche Ortsnamen waren verdeckt. X1 soll in erster Linie die geografische Verteilung
zeigen, nicht exakte Kontaktpositionen.

## Entscheidungen

1. **Der Ortspunkt bleibt an seiner wahren Lage und ist immer sichtbar.** Die Kontakte eines Ortes oder einer Ortsgruppe stehen
   grundsätzlich daneben auf einer hellen Fläche, auch ein einzelner Kontakt. Eine feine Linie bindet sie an den Ortspunkt.
2. **Vorrang bei der Platzierung:**
   1. Ortspunkte und Ortsnamen sind frei.
   2. Die Ortsgruppen sind getrennt: keine überlappenden Flächen, keine verdeckten oder kreuzenden Linien.
   3. Erst dann zählt die Nähe zum Punkt.
3. **Reihenfolge:** je Panel Ort für Ort, größte zuerst, erst der Kasten, dann die Kontakte; danach eine Nachbesserungsrunde für alle
   Kästen. Die Lücke im Ring und das Ausweichen mit gepunkteter Linie entfallen, weil jede Kontaktfläche ohnehin bewusst daneben steht.

## Folgen

- Kontaktflächen können in dichten Panels deutlich vom Ortspunkt abrücken (Testfall 001: Köln und Kassel). Die Linie zeigt die
  Zugehörigkeit, die Fläche selbst steht dann über einer anderen Gegend der Karte.
- Ein Kasten mit langer Linie kann näher an einem fremden Ortspunkt liegen als am eigenen. Die freie Linie macht die Zuordnung
  eindeutig.
