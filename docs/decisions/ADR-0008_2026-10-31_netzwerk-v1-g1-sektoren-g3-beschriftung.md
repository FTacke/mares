# ADR-0008 – `network_v1`: Winkelsektoren nach Beziehungstyp in G1, kompakte Gruppenbeschriftung in G3

**Datum:** 2026-10-31 · **Status:** in Kraft

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §5.3 und §6. Löst in
[`ADR-0007`](ADR-0007_2026-10-31_netzwerk-v1-g1-g3.md) die gleichmäßige Verteilung der Kontakte auf dem Ring (Entscheidung 1) und die
Form der Gruppenbeschriftung (Teil von Entscheidung 3) ab; alles Übrige aus ADR-0007 bleibt in Kraft. G2 und P1–P5 sind nicht betroffen.

## Kontext

Die Sichtprüfung der Fassung nach ADR-0007 ergab:

- **G1:** Die gleichmäßige Verteilung in ID-Reihenfolge verstreute Kontakte desselben Beziehungstyps über alle Richtungen. Familie,
  Freund:innen oder Bekannte waren nicht als zusammengehörige Kategorien wahrnehmbar, obwohl die Farbe den Typ zeigt.
- **G3:** Jede Gruppe trug „Zugehörigkeit“, eine verbale Stufe („Stark“, „Mittel“ …), „Kontakte“ und in Testfall 001 den Zusatz
  „(fiktive Bezeichnung)“. Das ergab viel wiederholten Text. Einzelne Beschriftungen standen weit von ihrer Gruppe, bei den sich
  überlappenden Gruppen C04/C05/C06 in Testfall 001 war die Zuordnung nicht unmittelbar klar.

## Entscheidungen

1. **G1 ordnet den Winkel nach Beziehungstyp.** Feste Sektorfolge für alle Fälle (Familie, Partner:in, Freund:in, Bekannte:r,
   Professionell/institutionell, Sonstige, keine Angabe), gegen den Uhrzeigersinn ab der Ringbeschriftung. Sektorbreite proportional
   zur Zahl der Kontakte des Typs; ein fehlender Typ hat keine Breite, behält aber seinen Platz in der Folge, sodass die Anordnung nicht
   von Fall zu Fall wechselt. Innerhalb eines Sektors werden Kontakte nur so weit auseinandergeschoben, dass sich keine Knoten
   berühren. Der Radius bleibt der erhobene Nähewert. Keine Sektorlinien und keine Hintergrundflächen: die Gruppierung soll aus Farbe
   und Nachbarschaft entstehen, ohne eine zusätzliche Kategorie zu behaupten.
2. **G3-Beschriftung als kompakter Block:** `C04 · <Bezeichnung> (3)` und darunter die fünf Punkte mit der Zahl. Die Skala wird einmal
   in der Legende erklärt. Fehlende Werte: kein Punkt gefüllt, Kürzel (`KA`, `NS`, `NA`, `n. e.`), aufgelöst in der Legende.
3. **Darstellungsname:** Testdaten-Zusätze wie „(fiktive Bezeichnung)“ entfallen in der Grafik (die Fallkennzeichnung oben rechts
   genügt), überlange Namen werden gekürzt. Die Daten in Tabelle C bleiben unverändert; es werden keine Namen erfunden.
4. **Platzierung an der Gruppe:** Der Block liegt unmittelbar außerhalb der eigenen Umrandung und nicht auf Knoten, Verbindungen,
   anderen Beschriftungen, Umrandungslinien oder fremden Gruppenflächen. Für eine eingebettete Gruppe gelten die Flächen der
   umschließenden Gruppen nicht als fremd. Wo kein naher Platz frei ist, bindet eine kurze Linie den Block an; ihre Kreuzungen mit
   fremden Umrandungen fließen in die Wahl ein. Links und rechts der Karte bleibt Rand für Beschriftungen.

## Folgen

- G1 und G3 beider Testfälle wurden neu erzeugt; G2 und P1–P5 sind byteidentisch geblieben.
- Eine kurze Zuordnungslinie bleibt dort nötig, wo eine Gruppe ganz in anderen liegt (Testfall 001: C04) oder rundum belegt ist
  (Testfall 002: C02). Die Linie zu C04 muss die Umrandungen von C05 und C06 kreuzen, weil C04 in beiden liegt.
- Ob die Sektoranordnung als Gruppierung nach Beziehungstyp und nicht als zusätzliche Aussage gelesen wird, ist Teil der fachlichen
  Abnahme.
