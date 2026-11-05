# Run-Bericht 2026-11-05 – `network_v1`: X1 Fassung 2

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §6.1,
[`ADR-0011`](../decisions/ADR-0011_2026-11-05_netzwerk-v1-x1-fassung-2.md). Vorlauf am selben Tag:
[`2026-11-05_network-v1-experimentelle-karte-x1.md`](2026-11-05_network-v1-experimentelle-karte-x1.md). Für den authentischen Fall MT
nennt der Bericht keine Orte.

## 1. Ziel und Ausgangslage

X1 gezielt verbessern, noch nicht als Standardgrafik:
- Ortspunkt, Kontakte und Ortsbeschriftung klarer verbinden (Ortskasten mit Leader, Variante B);
- sehr nahe Orte als „… und Umgebung“ bündeln;
- dezente Flächen, größere Deutschlandkarte, engeres Europa, Amerika nach den Daten zugeschnitten.

Vorab: Working Tree sauber, `main` = `origin/main` (`3961094`).

## 2. Geänderte Dateien

- [`src/mares/network_v1/experimental.py`](../../src/mares/network_v1/experimental.py): Layout und Zeichnung neu (Fassung 2); Quellen,
  Ablage und CLI unverändert; das Laufprotokoll trägt `version: 2` und die Ortsgruppen.
- `tests/test_network_v1_experimental.py`: angepasst und erweitert, jetzt 12 Tests.
- `docs/architecture/network-v1.md` §6.1, neue ADR-0011, dieser Bericht.

## 3. Layoutregeln der Fassung 2 (umgesetzt)

1. **Panels:**
   - Amerika · Europa · Deutschland, oben bündig; Deutschland ist das größte Panel, die übrigen sind 0,8-mal so hoch.
   - Die Gesamtgrafik ist höher als in Fassung 1 (Deutschland-Panel rund 6,8 statt 5,1 Zoll hoch).
2. **Ausschnitte:**
   - Amerika: Mexiko bis Südamerika, nach Norden nur bei Kontakten in den USA oder Kanada (002: bis Toronto).
   - Europa: Portugal bis etwas östlich von Deutschland (bis 19,5° Ost).
   - Ein Ausschnitt wächst nur für Orte außerhalb oder am Rand. Im ersten Versuch wuchs auch das Deutschland-Panel, weil sich der Rand
     um jeden Ort legte. Dadurch fiel Gießen unter die 3-mm-Regel; korrigiert.
3. **Ortspunkt und Ringe:**
   - Dunkler, weiß umrandeter Punkt; die Kontakte in Ringen darum (bis 10 ein Ring, sonst 6, 12, … Plätze), nach Ort und Beziehungstyp
     sortiert.
   - Ein Ringplatz bleibt in Richtung des Ortskastens frei, durch ihn läuft die Leader-Linie bis zum Punkt.
4. **Mini-Fläche:** sehr hell, leicht umrandet, nur bei Orten mit mehreren Kontakten.
5. **„… und Umgebung“:**
   - Orte höchstens 20 km voneinander oder auf der Karte unter etwa 3 mm.
   - Im Kasten zuerst „Marburg und Umgebung · n = 14“, darunter klein die Einzelorte.
   - 30 km (erster Versuch) zog Gießen zu Marburg; die Fläche überdeckte dann Kassel und Frankfurt.
6. **Ortskästen:** acht Richtungen, vier Abstände; nicht auf Knoten, Flächen, Ortspunkten, Paneltiteln oder anderen Kästen, im Panel.
   Die Linie quert möglichst keine fremde Fläche.
7. **Ausweichen:** Überlappen sich zwei Ortsgruppen, weicht die kleinere aus. Eine gepunktete Linie führt dann zur wahren Lage
   (hohler Ring); die Legende erklärt das nur bei Bedarf.
8. Unverändert gegenüber Fassung 1:
   - keine Verbindungslinien;
   - Beziehungstypfarben;
   - „nur Land bekannt“ am Länderpunkt, gestrichelt;
   - Fußnote für nicht darstellbare Kontakte;
   - Ortsverzeichnis außerhalb des Repositorys.

## 4. Ausgabe

Je Fall `<Fall>/experimental/<Fallcode>_X1_geografische_verteilung.{png,svg}` (Fassung 2); die Fassung 1 liegt einmalig unter
`experimental/x1_fassung_1/` (verschoben, nicht neu erzeugt). Gerendert: 001*, 002*, `student_pilot` MT. Die 48 Standardgrafiken sind
vor und nach dem Lauf byteidentisch.

## 5. Visueller Befund

- **MT:** am klarsten. Je ein Ortskasten für drei Orte in Europa, einen in Amerika und einen in Deutschland. Ein Kontakt weicht
  knapp neben der größten Ortsgruppe in Europa aus. Der Amerika-Ausschnitt zeigt nur Mittel- und Südamerika.
- **002:**
  - „Marburg und Umgebung · n = 14“ und „Gießen und Umgebung · n = 4“ sind getrennt und gut lesbar; in Amerika „Bogotá und
    Umgebung · n = 4“.
  - Kassel, Frankfurt und Gießen liegen im Maßstab unter der Marburg-Fläche und weichen mit gepunkteter Linie aus.
- **001:** Marburg · n = 8, Köln, Kassel und Frankfurt je mit Kasten. Gießen (26 km) bleibt ein eigener Ort und weicht neben die
  Marburg-Fläche aus.

## 6. Tests

- X1: 12 Tests, darunter:
  - Ortsgruppe „und Umgebung“ (20 km);
  - Panelgrößen und Ausschnitte (Amerika ohne Nordkontakte bis 33° Nord, Europa mit östlichem Kontakt breiter);
  - Ortskästen nicht auf Knoten;
  - Leader durch den freien Ringplatz;
  - Flächen, Kästen und Punkte je Ort.
- Volle Suite: **585 bestanden** (vorher 583).

## 7. Status

| | X1 Fassung 2 |
|---|---|
| implementiert | ja |
| technisch getestet | ja |
| visuell geprüft (Agent, drei Fälle) | ja |
| fachlich bewertet / in den Standardsatz aufgenommen | nein (offen) |

## 8. Offene Schwächen

- Dichte Räume bleiben die Grenze: In 002 muss bei 14 Kontakten in Marburg und Umgebung die Nachbarschaft ausweichen. Die hohlen
  Ringe der wahren Lage liegen dann in der Marburg-Fläche.
- „Bogotá und Umgebung“ entsteht über die Kartenregel (Medellín liegt rund 240 km entfernt). Der Name ist im Amerika-Maßstab
  vertretbar, geografisch aber weit gefasst.
- Unter den kleineren Panels (Amerika, Europa) bleibt durch die obere Bündigkeit etwas Leerraum.
- Das Ortsverzeichnis wird von Hand gepflegt.
