# Run-Bericht 2026-11-13 – Ortsverzeichnis von X1 ergänzt sich automatisch (GeoNames, lokal)

Journal eines Laufs, keine Spezifikation. Maßgeblich:
[`ADR-0028`](../decisions/ADR-0028_2026-11-13_netzwerk-ortsverzeichnis-automatisch-aus-geonames.md),
[`network-v1.md`](../architecture/network-v1.md) §6.1. Keine Orte oder Einzelwerte von Fällen.

## 1. Anlass und Ziel

In einem Fall fehlten drei Kontakte in X1, weil ihr erhobener Wohnort nicht im von Hand gepflegten Ortsverzeichnis stand. Die
Projektleitung wollte, dass sich das Verzeichnis künftig automatisch um alle genannten Orte erweitert.

## 2. Umsetzung

- Neu: `network_v1/gazetteer.py`.
  - Fehlende Orte werden in der GeoNames-Länderdatei ihres Landes gesucht.
  - Die Länderdatei wird einmal je Land in `WORKSPACE:cache/geonames/` geladen; die Anfrage nennt nur den Ländercode.
  - Übernommen werden nur eindeutige Treffer, angehängt an das Verzeichnis mit Quelle und Datenstand.
- `network_v1/run.py`: `load_geo` ergänzt das Verzeichnis vor dem Lesen. v1 übergibt die Wohnorte des Falls, ebenso
  `network_v0/run.py`.
- Das Ergebnis steht im Run-Record unter `map_sources.gazetteer.completion`.
- `tests/conftest.py` sperrt das Herunterladen in allen Tests. Neu sind sieben synthetische Tests in
  `tests/test_network_v1_gazetteer.py`.
- Vorher wurden für den Anlassfall zwei Orte von Hand ergänzt. Einer davon lag 8 km daneben und ist nun auf den GeoNames-Wert
  korrigiert.

## 3. Prüfungen

- Probelauf mit allen Wohnorten aller Fälle gegen ein leeres Verzeichnis im Scratchpad:
  - Alle Orte wurden gefunden, außer einer mehrdeutigen Angabe, einer unbekannten Schreibweise, einer Regionalangabe und
    „auf Reisen“.
  - Die Koordinaten stimmen mit den Handwerten meist auf 0,01° überein.
  - Wenige ältere Handeinträge weichen um bis zu 0,1° ab. Sie bleiben unverändert, weil automatisch nie überschrieben wird.
- Erste Anpassung nach dem Probelauf: Großstädte galten wegen kleiner Namensvettern als mehrdeutig, und Gemeinden ohne
  gleichnamigen Ortsteil fehlten. Daraufhin kamen die Dominanzregel und Gemeinden als Rückfall hinzu.
- Alle v1- und v0-Fälle neu gerendert:
  - Nur X1 eines Falls hat sich geändert, wegen der korrigierten Koordinate.
  - Alle übrigen Grafiken sind bytegleich.
  - Das Verzeichnis blieb unverändert, weil alle Orte schon enthalten waren.
- Gesamtsuite: 513 bestanden.

## 4. Status und offene Punkte

- Implementiert und getestet; keine wissenschaftliche Validierung.
- Nicht entschieden: ob X1 GeoNames als Koordinatenquelle neben Natural Earth nennt.
- Der GeoNames-Cache belegt rund 450 MB, davon allein die US-Datei etwa 300 MB. Er ist regenerierbar und liegt im WORKSPACE.
