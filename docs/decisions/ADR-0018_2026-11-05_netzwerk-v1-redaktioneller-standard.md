# ADR-0018 – `network_v1`: ein redaktioneller Standard für alle neun Grafiken

**Datum:** 2026-11-05 · **Status:** in Kraft (ergänzt [`ADR-0006`](ADR-0006_2026-10-31_netzwerk-v1-gestaltung.md) für die Texte;
übernimmt für G1–G3 und P1–P5 die mit [`ADR-0016`](ADR-0016_2026-11-05_netzwerk-v1-x1-kanonisch.md) für X1 eingeführte reduzierte Form)

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §5.2 und §5.7. Texte:
[`network-v1-visualization-text-inventory.md`](../architecture/network-v1-visualization-text-inventory.md).

## Kontext

Nach der Kanonisierung von X1 trugen die übrigen acht Grafiken weiter Code im Titel, Untertitel, methodische Hinweise, die Abdeckung der
Kontaktpaare und eine Fußzeile mit Gruppenzahl und Datenqualität. Das Textinventar zeigte außerdem uneinheitliche Wortlaute für fehlende
Angaben und mehrfach implementierte Texte. Die Projektleitung hat die redaktionellen Festlegungen für alle neun Grafiken freigegeben.

## Entscheidungen

1. **Titel nur inhaltlich, kein Untertitel.** Die Titel stehen in einer Tabelle (`base.TITLES`), die auch das Register nutzt; die Codes
   bleiben intern (Register, Dateinamen, Metadaten, Dokumentation).
2. **Eine Fußzeile:** `MARES · network_v1 · <n> Kontakte`. Gruppenzahl, Datenqualität und Prüfstatus gehören in Metadaten, Prüfbericht
   und Run-Record.
3. **Einheitliche Wortlaute** für fehlende Angaben (`keine Angabe`) und nicht zuordenbare Wohnorte (`Wohnort nicht zuordenbar: …`; X1
   `Wohnort nicht darstellbar: …`), je an einer Stelle definiert.
4. **Methodische Erläuterungen in die Dokumentation**, nicht in die Grafik: Lesart von G1, Kategorien statt Entfernungen, fehlende
   Linien, Gruppenmitgliedschaft, geordnete Häufigkeit, Abdeckung der Paare. Sie gelten unverändert (§5.7). Die Erhebung sieht eine
   vollständige Klärung der Paare vor; eine allgemeine Warnung in jeder Grafik entfällt. Unbekannte Paare bleiben unbekannt und werden
   im Prüfbericht gezählt.
5. **Legenden erklären Zeichen.** P3 und P4 teilen eine Heatmap-Legende mit Bezugsgröße; G1 behält die Nähe-Skala samt Zwischenwerten,
   weil die gestrichelten Ringe immer gezeichnet sind; G3 erklärt die Skala in einer Zeile und nur die vorkommenden Kurzcodes.

## Folgen

- Alle neun Grafiken haben einen niedrigeren Kopf und weniger Hinweise; Daten, Ableitungen, Layouts, Farben und Kategorien bleiben
  unverändert. Tests vergleichen dafür den Hauptbereich nicht, sondern prüfen die Texte; X1 ist bytegleich geblieben.
- Wer eine Lesart nachschlagen will, findet sie in `network-v1.md` §5.7, nicht mehr in der Abbildung.
