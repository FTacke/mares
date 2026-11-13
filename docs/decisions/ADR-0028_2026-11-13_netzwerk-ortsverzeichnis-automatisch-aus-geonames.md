# ADR-0028 – Ortsverzeichnis von X1 ergänzt sich automatisch aus lokalen GeoNames-Daten

**Datum:** 2026-11-13 · **Status:** in Kraft

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §6.1. Code:
[`network_v1/gazetteer.py`](../../src/mares/network_v1/gazetteer.py).

## Kontext

X1 setzt Kontakte nur an Orte, die im Ortsverzeichnis `ROOT:network_v1/reference/gazetteer.csv` stehen. Das Verzeichnis wurde bisher
von Hand gepflegt. Fehlte ein Ort, galt der Kontakt als „Wohnort nicht darstellbar“, obwohl der Ort erhoben war; so fehlten in einem
Fall drei Familienkontakte auf der Karte. Die Projektleitung hat entschieden, dass sich das Verzeichnis künftig automatisch um alle
genannten Orte erweitert.

Online-Geocoding schied aus, weil es Wohnorte von Kontakten an einen externen Dienst schicken würde (AGENTS.md Regel 3).

## Entscheidungen

1. **Lokales Nachschlagen statt Online-Geocoding.**
   - Je Land wird die freie GeoNames-Länderdatei einmal in den regenerierbaren Cache `WORKSPACE:cache/geonames/` geladen
     (CC BY 4.0).
   - Die Anfrage nennt nur den Ländercode. Kein Ortsname verlässt den Rechner.
2. **Automatisch vor jedem Lauf.**
   - `load_geo` ergänzt fehlende Orte aus den erhobenen Wohnorten des Falls, bevor X1 gezeichnet wird.
   - Das gilt für v1 (`render`, `render-all`) und v0 (`render-case`, `figures`).
3. **Nichts wird geraten.**
   - Übernommen wird nur ein eindeutiger Treffer: ein bewohnter Ort nach Name, sonst nach Alternativname, sonst eine Gemeinde.
   - Mehrere Treffer gelten als ein Ort, wenn alle innerhalb von 40 km liegen.
   - Ebenso, wenn der größte mindestens 1 000 Einwohner und das Zehnfache jedes Namensvetters hat.
   - Mehrdeutige und unbekannte Orte, regionale Angaben und Einträge ohne Wohnland bleiben draußen. Sie stehen im Run-Record.
4. **Bestehende Zeilen bleiben unverändert.**
   - Von Hand gepflegte Einträge und `group_with` haben Vorrang.
   - Neue Zeilen tragen in `basis` die GeoNames-ID, den Datenstand und die Lizenz.
5. **Ohne Netz** wird die fehlende Länderdatei als Fehler im Run-Record vermerkt. X1 nennt den Ort dann wie bisher als nicht
   darstellbar. Tests laden nie etwas (`tests/conftest.py`).

## Folgen

- Probelauf mit allen Wohnorten aller Fälle gegen ein leeres Verzeichnis:
  - Alle Orte wurden gefunden, außer einer mehrdeutigen Angabe, einer unbekannten Schreibweise, einer Regionalangabe und
    „auf Reisen“.
  - Die von Hand gepflegten Koordinaten stimmen bis auf wenige Ausnahmen auf 0,01° überein.
  - Ein eigener Handeintrag vom 2026-11-09 lag 8 km daneben; er ist auf den GeoNames-Wert korrigiert.
- Ob X1 GeoNames neben Natural Earth als Quelle nennen soll, ist nicht entschieden. Die Quelle steht im Ortsverzeichnis und im
  Run-Record.
