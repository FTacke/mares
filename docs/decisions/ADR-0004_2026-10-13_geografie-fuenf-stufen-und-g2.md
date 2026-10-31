# ADR-0004 – Fünf geografische Stufen, geografische Beziehungsnetze G2-A/G2-B und gegliedertes Abbildungsrepertoire

**Datum:** 2026-10-13 · **Status:** in Kraft; die Wahl des G2-Standardlayouts ist offen

Ergänzt [`ADR-0002`](ADR-0002_2026-10-12_netzwerkmodul.md) und [`ADR-0003`](ADR-0003_2026-10-12_erhebungsmethode-und-kuratierung.md). Aktuelle Regeln:
[`geographic-classification.md`](../architecture/geographic-classification.md), [`visualization-conventions.md`](../architecture/visualization-conventions.md) §3.3–3.7,
[`network-module.md`](../architecture/network-module.md) §7.

## Kontext

Die bisherige Einteilung (Marburg – Region Marburg – übriges Deutschland – außerhalb Deutschlands) fasste Wien und Kolumbien zusammen; für die Fragestellung (lokale, überregionale und
transkontinentale Beziehungen) ist das zu grob. Die geografischen Beziehungsnetze wirkten schematisch, die Ego–Kontakt-Linien überdeckten die Beziehungen zwischen den Kontakten, und es gab mehr
Abbildungsvarianten, als die Fragen unterscheiden, bei zu viel Text in den Bildern.

## Entscheidungen

1. **Fünf Stufen:** Marburg · Region Marburg · übriges Deutschland · **übriges Europa** · **außerhalb Europas** (+ „nicht zuordenbar“). `GeoCategory.ABROAD` entfällt; es gibt `EUROPE_OTHER` und
   `OUTSIDE_EUROPE`. Die Änderung gilt zentral (`geo.classify_residence`) und damit für alle Abbildungen, Tabellen und die kanonische Ausgabe (`residence_category`), damit „eine Variable, eine Farbe“ gilt.
   Frühere Läufe bleiben unverändert; die Abbildungen A, B1–B3, C, D2 benutzen jetzt die fünf Farben.
2. **Europa ist geografisch** (UN-Geoschema), nicht EU-Mitgliedschaft; ein Wohnland ohne gültigen ISO-Code wird `nicht zuordenbar`, nicht geraten. Grenzfälle (Russland: Europa; Türkei, Zypern,
   Kaukasus, Kasachstan: nicht Europa; Überseegebiete mit ihrem Kontinent) sind Konventionen, getestet und an einer Stelle änderbar.
3. **Lage und biografischer Bezug sind getrennte Dimensionen.** Der biografische Bezug (Herkunftsland, früheres Wohnland …) ist nicht aus dem Wohnland ableitbar und wird nicht klassifiziert; die mögliche
   Erweiterung steht in der Klassifikationsdokumentation.
4. **G2 ohne Ego–Kontakt-Linien.** In G2 geht es um die Beziehungen zwischen den Kontakten; Ego ist nicht Teil des Graphen. B3 behält die Ego–Kontakt-Linien (dort gehören sie zur Aussage).
5. **Zwei G2-Varianten, beide erhalten:** **G2-A** (Bänder, Breite folgt der Kontaktzahl, Höhe folgt der sozialen Struktur) und **G2-B** (geografisch eingeschränktes Kraftlayout: radiale Zonen um Ego,
   Beziehungen ziehen zusammen, Kontakte stoßen sich ab, der Radius bleibt im Fenster seiner Zone). Beim Pilotfall bleibt in G2-B die soziale Gruppenstruktur sichtbar besser erhalten
   (Gruppenkompaktheit 0,25 gegenüber 0,39), bei etwas mehr Kreuzungen (30 gegenüber 24) und größerer Leerfläche. **G2-B ist der Kandidat; das endgültige Standardlayout bestimmt der Projektleiter.**
6. **Das Repertoire ist gegliedert** in `core` (B3, G2-Kandidat, P1, P2), `supplementary` (A, B1, B2, G1, G2-A, P3, C, D1, D2, E) und `diagnostic` (Layout- und Variantenvergleiche, frühere G2-Fassung mit
   Ego-Linien). Die Gliederung betrifft Register und Ausgabeordner (`figures/<tier>/`), nicht die Funktionen; nichts wird gelöscht.
7. **Reduzierte `clean`-Abbildungen:** kurzer Titel, höchstens ein knapper Untertitel, kompakte Legende, ein kurzer Hinweis, Kurzkennung `MARES · 001-2 · vorläufig`; vier Schriftgrößen. Fallzahlen,
   Methodenbeschreibung, Provenienz und Datenqualität stehen in `figures/figures_index.json` und im Profil `analysis`. Das Profil `analysis` bewahrt den früheren Wortlaut der älteren Abbildungen.

## Folgen

- Kanonische Ausgabe und Tabellen führen die Werte `europe_other` und `outside_europe` statt `abroad`.
- Offen (nicht entschieden): Standard-G2; die Konvention für Türkei/Kaukasus/Kasachstan; ein Parameter `home_country` für Erhebungen außerhalb Deutschlands; ein Merkmal für den biografischen Bezug.
