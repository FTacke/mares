# Geografische Klassifikation des Wohnorts (`network_v0`)

> Gilt für `network_v0`. `network_v1` teilt Marburg und Mittelhessen (fünf Landkreise) statt Marburg und Region Marburg:
> [`network-v1.md`](network-v1.md) §3.

**Status: verbindlich für das Netzwerkmodul.** Code: [`geo.py`](../../src/mares/network_v0/geo.py) (`classify_residence`, `EUROPE_ISO3`),
Bezeichnungen und Parameter: [`analysis.py`](../../src/mares/network_v0/analysis.py) (`geo_labels`, `AnalysisParams.local_places`), Farben:
[`figures/style.py`](../../src/mares/network_v0/figures/style.py). Begründung: [`ADR-0004`](../decisions/ADR-0004_2026-10-13_geografie-fuenf-stufen-und-g2.md).
Darstellung: [`visualization-conventions.md`](visualization-conventions.md).

Die Klassifikation beschreibt, **wo ein Kontakt wohnt** – nicht, wer er ist, und nicht, was der Ort in der Biografie der Person bedeutet.

## 1. Fünf Stufen (plus „nicht zuordenbar“)

| Stufe | Kategorie (`GeoCategory`) | Regel | Pilotfall `001-2` |
|---|---|---|---:|
| 1 | `Marburg` (`LOCAL`) | deutscher Wohnort, dessen Ortsangabe **exakt** einem konfigurierten lokalen Ort entspricht (Groß-/Kleinschreibung ignoriert) | 8 |
| 2 | `Region Marburg` (`LOCAL_REGION`) | regionale Angabe zu einem lokalen Ort („Nähe/Raum/Region/Umgebung Marburg“); bleibt regional, kein Wohnort wird erfunden | 1 |
| 3 | `übriges Deutschland` (`GERMANY_OTHER`) | jeder andere deutsche Wohnort (auch „Marburg an der Lahn“, solange es nicht als lokaler Ort konfiguriert ist) | 9 |
| 4 | `übriges Europa` (`EUROPE_OTHER`) | Wohnland in Europa, nicht Deutschland | 1 |
| 5 | `außerhalb Europas` (`OUTSIDE_EUROPE`) | jedes andere gültige Wohnland | 3 |
| – | `Wohnort nicht zuordenbar` (`UNKNOWN`) | kein Wohnland angegeben **oder** kein gültiger ISO-Code | 0 |

Die tatsächlichen Wohnorte und Wohnländer bleiben eigenständige Attribute der Kontakte (`residence_city`, `residence_country`); die Kategorie wird daraus
abgeleitet und nie zurückgeschrieben. Die kanonische Ausgabe enthält Rohwert und Kategorie nebeneinander.

## 2. „Europa“

Europa ist **geografisch** definiert, nicht als Mitgliedschaft (EU, Europarat, Schengen). Grundlage: die Region Europa des UN-Geoschemas (M49), ausgeschrieben in
`geo.EUROPE_ISO3`. Festlegungen für Grenzfälle, die in einem Test (`tests/test_network_v0_geo_classification.py`) stehen und an **einer** Stelle zu ändern sind:

- **Russland** zählt zu Europa (UN-Geoschema), ebenso Ukraine, Belarus, Moldau, Kosovo (`XKX`), Island, das Vereinigte Königreich, Zwergstaaten.
- **Türkei, Zypern, Georgien, Armenien, Aserbaidschan, Kasachstan** zählen **nicht** zu Europa (UN-Geoschema: Westasien bzw. Zentralasien). Das ist eine Konvention, keine Aussage; sie ist
  im Projekt nicht abgestimmt (offen, siehe ADR-0004).
- **Überseegebiete** zählen mit ihrem Kontinent, nicht mit ihrem Staat (Französisch-Guayana, Guadeloupe, Martinique, Réunion, Grönland: außerhalb Europas).

## 3. Konfiguration und Verallgemeinerung

- **Lokaler Bezugspunkt:** `AnalysisParams.local_places` (Kommandozeile `--local-place`, mehrfach möglich). „Marburg“ steht nur als Standardwert im Code; die Stufen 1 und 2 und alle
  Bezeichnungen folgen dem konfigurierten Ort.
- **Heimatland der Erhebung:** Deutschland (`geo.HOME_COUNTRY`) – die Stufen 3 bis 5 gelten für eine in Deutschland durchgeführte Erhebung. Eine Erhebung mit einem anderen Heimatland braucht
  einen Parameter `home_country` (heute nicht vorhanden; offen).
- **Kein Herkunftsland, kein Kolumbien** im Code: die Stufen nennen weder ein Herkunftsland noch eine Herkunftsregion.
- **Nicht raten:** ein fehlendes oder kein ISO-Code führt zu `Wohnort nicht zuordenbar`; der Ort allein entscheidet nie, und mehrdeutige Angaben werden nicht aufgelöst.

## 4. Biografischer Bezug (nicht umgesetzt)

Ob ein Kontakt im **Herkunftsland**, einem **früheren Wohnland** oder einem anderen biografisch bedeutsamen Raum lebt, ist eine **eigene Dimension**. Sie ist **nicht aus dem Wohnland ableitbar** (ein
Kontakt in Spanien kann für eine Person mit Herkunft aus Kolumbien biografisch ein „Heimat-“, „Durchgangs-“ oder bloß ein „anderes“ Land sein) und wird deshalb jetzt **nicht** klassifiziert. Mögliche
spätere Erweiterung: ein zusätzliches Merkmal je Kontakt (z. B. `biographical_relation` mit Werten wie `origin_country`, `former_residence`, `other`), das die Person selbst oder das Projekt festlegt;
Geografie (Lage) und biografischer Bezug blieben getrennte Achsen und würden in getrennten Kodierungen dargestellt (z. B. Form oder Rand statt Farbe). Das braucht eine Entscheidung über Erhebung und Codebuch
und ändert das Paketformat; es gehört nicht in dieses Modul, bevor es entschieden ist.

## 5. Frühere Läufe

Frühere Läufe (vier Kategorien, Wien und Kolumbien zusammen unter „außerhalb Deutschlands“) bleiben unverändert in `WORKSPACE/runs/`; ihre Berichte beschreiben den damaligen Stand. Ein neuer Lauf
ist ein neuer Lauf (siehe [`network-module.md`](network-module.md) §7); nichts wird stillschweigend umgeschrieben.
