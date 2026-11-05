# ADR-0013 – `network_v1`: X1 Fassung 2.2 (Zentren bleiben getrennt, Land im Ortskasten)

**Datum:** 2026-11-05 · **Status:** in Kraft (Experiment; ändert in
[`ADR-0012`](ADR-0012_2026-11-05_netzwerk-v1-x1-fassung-2-1.md) Entscheidung 1)

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §6.1.

## Kontext

Die Entfernungsregel (höchstens 20 km) von Fassung 2.1 ist notwendig, aber nicht hinreichend. Zwei eigenständige Städte wie Gießen
und Wetzlar (13 km) wären zu „Gießen und Umgebung“ geworden; gemeint sind aber Zentren mit ihren Stadtteilen und Umlandgemeinden. Eine
Liste von Ausnahmen für einzelne Orte im Code wäre weder allgemein noch nachvollziehbar. Außerdem fehlte bei Orten im Ausland der
Länderbezug (etwa „Madrid“ ohne Spanien).

## Entscheidungen

1. **Zentrumsstatus im Ortsverzeichnis**, Spalte `centre`: 1 = eigenständiges Zentrum (Mittel- oder Oberzentrum bzw. eigenständige
   Stadt), 0 = Stadtteil oder Umlandgemeinde. Er wird wie die Koordinaten von Hand gepflegt und begründet (`basis`).
2. **Gruppierung:**
   - Ein Ort mit `centre` = 0 kommt zum nächstgelegenen Zentrum innerhalb von 20 km Luftlinie.
   - Zentren werden nie zusammengefasst; Ketten gibt es nicht.
   - Ohne Angabe gilt ein Ort als Zentrum. Im Zweifel bleibt er also getrennt.

   Kollisionen getrennter Orte löst weiterhin das Ausweichen mit gepunkteter Linie zur unveränderten wahren Lage.
3. **Land im Ortskasten** außerhalb Deutschlands („Bogotá · Kolumbien · n = 3“, „Madrid · Spanien“). Im
   Deutschland-Panel steht nur der Ort, weil das Panel das Land schon nennt. Keine zusätzlichen Länderbeschriftungen auf der Karte.

## Folgen

- In den Testfällen gehören Wehrda, Cölbe und Lahntal zu Marburg. Gießen, Wetzlar, Kirchhain (Mittelzentrum), Kassel, Bogotá und
  Medellín stehen für sich.
- Mehr eigenständige Orte im dichten Raum Mittelhessen bedeuten mehr ausweichende Symbole.
- Das Ortsverzeichnis hat eine sechste Spalte; Verzeichnisse ohne sie bleiben lesbar (dann keine Ortsgruppen).
