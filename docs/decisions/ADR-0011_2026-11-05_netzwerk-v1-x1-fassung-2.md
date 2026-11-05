# ADR-0011 – `network_v1`: X1 Fassung 2 (Ortskästen, „und Umgebung“, größere Deutschlandkarte)

**Datum:** 2026-11-05 · **Status:** in Kraft (Experiment; ergänzt [`ADR-0010`](ADR-0010_2026-11-05_netzwerk-v1-experimentelle-grafik-x1.md))

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §6.1.

## Kontext

Die Sichtprüfung von X1 (Fassung 1) ergab:
- Ortsbeschriftungen waren nicht immer eindeutig einem Ort zuzuordnen.
- Die Deutschlandkarte war für den Raum Marburg/Mittelhessen zu klein.
- Die Europakarte zeigte viel leeres Osteuropa, die Amerikakarte stets ganz Nord- und Südamerika.
- „Marburg u. a.“ war als Bezeichnung einer Ortsgruppe unklar.

## Entscheidungen

1. **Ortspunkt, Ring, Ortskasten (Variante B):** Die Kontakte stehen in Ringen um einen deutlichen Ortspunkt. Ein kleiner Kasten nennt
   Ort und Zahl und ist mit einer feinen Leader-Linie verbunden. Die Linie läuft durch einen frei gehaltenen Ringplatz bis zum Punkt.
   Eine sehr helle Fläche bündelt die Kontakte eines Ortes. Sie ist bewusst schwach gehalten, damit kein Blasendiagramm entsteht.
2. **„… und Umgebung“** für Orte höchstens 20 km voneinander oder auf der Karte unter etwa 3 mm. Die Einzelorte stehen klein im
   Kasten. Mit 30 km wäre Gießen (26 km) zu Marburg gekommen. Die Fläche wäre dann so groß geworden, dass sie die Punkte von Kassel
   und Frankfurt überdeckt hätte.
3. **Größere Deutschlandkarte:** Das Deutschland-Panel ist das höchste; die übrigen sind 0,8-mal so hoch, oben bündig. Die
   Gesamtgrafik ist höher.
4. **Ausschnitte nach den Daten:** Amerika zeigt standardmäßig Mexiko bis Südamerika, Europa Portugal bis etwas östlich von
   Deutschland. Ein Ausschnitt wächst nur für Orte außerhalb oder am Rand.
5. **Versionierung:** Eine Datei je Fall unter dem bisherigen Namen. Die Fassung 1 liegt einmalig zum Vergleich in
   `experimental/x1_fassung_1/`; das Laufprotokoll trägt `version`.

## Folgen

- Bei vielen Kontakten in einem engen Raum (Testfall 002: 14 in Marburg und Umgebung) wird die Fläche groß. Benachbarte Orte müssen
  ausweichen und sind über eine gepunktete Linie mit ihrer wahren Lage verbunden.
- Ob X1 in den Standardsatz kommt, bleibt offen.
