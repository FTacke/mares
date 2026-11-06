# ADR-0022 – `network_v1`: G4 und G5 (Gruppenstruktur nach Geburtsland) als zehnte und elfte Standardgrafik

**Datum:** 2026-11-06 · **Status:** in Kraft. Kanonisiert die in
[`ADR-0019`](ADR-0019_2026-11-06_netzwerk-v1-experiment-g3-geburtsland.md) bis
[`ADR-0021`](ADR-0021_2026-11-06_netzwerk-v1-g3-herkunft-zwei-ansichten.md) entwickelte Darstellung.

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §6 und §6.2. Texte:
[`network-v1-visualization-text-inventory.md`](../architecture/network-v1-visualization-text-inventory.md).

## Kontext

Die Projektleitung hat die beiden Geburtslandansichten (gesamt, lokal) visuell abgenommen und die Kanonisierung beschlossen. Dazu eine
letzte redaktionelle Korrektur: In der Lokalansicht steht nur noch ein Hinweis zum lokalen Ausschnitt. Überholte Experimentausgaben
und -pfade sollen entfernt werden.

## Entscheidungen

1. **Codes G4 und G5**, in der Reihe der Netzwerkgrafiken G1–G3:
   - `G4_gruppen_geburtsland` – „Gruppenstruktur nach Geburtsland“;
   - `G5_lokale_gruppen_geburtsland` – „Lokale Gruppenstruktur nach Geburtsland“.

   Die bisherigen Codes bleiben unverändert. Die Registerfolge ist G1, G2, P1–P5, G3, X1, G4, G5.
2. **Reguläre Standardgrafiken.** Die beiden Grafiken stehen im Register, entstehen bei jedem `render`/`render-all` in `graphics/`
   (PNG/SVG) und haben Skip-Gründe:
   - G4: „keine Gruppen erhoben“, „kein Geburtsland erhoben“;
   - G5: zusätzlich „kein Kontakt mit Wohnort in Marburg oder Mittelhessen“ und „keine Gruppe mit Mitgliedern in Marburg oder
     Mittelhessen“.

   Der vollständige Satz umfasst elf Grafiken, also 22 Dateien bei PNG und SVG.
3. **Ein Hinweis in G5:** „Lokaler Ausschnitt: n von N Kontakten (Marburg und Mittelhessen).“ Welche Kontakte und Gruppen fehlen und
   warum, steht im G5-Eintrag des Figure-Registers und des Run-Records (`details`), mit pseudonymen IDs und ohne Länder.
4. **Eine Implementierung.** G4 und G5 nutzen die G3-Gruppenlogik (Geometrie, Zeichnen, Labels, Skala, Ringe). G3 bleibt unverändert;
   G4 färbt nach Geburtsland, G5 filtert zusätzlich nach Wohnortbereich.
5. **Bereinigung.** Entfernt werden der Experimentbefehl (`v1 experiment`), `experiments.py`, der Titel-Parameter von `page()` und
   alle `<Fall>/experimental/`-Bestände der drei Fälle:
   - überholte X1-Ausgaben und X1 Fassung 1;
   - die Experimentkopien von G3 nach Geburtsland.

   Die Fallordner enthalten danach nur `data/` und `graphics/`. Die Entwicklung bleibt über Git, ADR-0010 bis ADR-0021 und die
   Run-Berichte nachvollziehbar.

## Folgen

- Die neun bisherigen Grafiken sind bytegleich geblieben (geprüft für alle Fälle).
- Das Pilotskript `pilots/network_v1_map/` (kartografische G2-Variante) ist ein eigenes, nicht abschließend bewertetes Experiment und
  bleibt bestehen.
