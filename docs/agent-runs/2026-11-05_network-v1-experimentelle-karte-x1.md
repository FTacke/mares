# Run-Bericht 2026-11-05 – `network_v1`: experimentelle Zusatzgrafik X1 (geografische Verteilung)

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §6.1,
[`ADR-0010`](../decisions/ADR-0010_2026-11-05_netzwerk-v1-experimentelle-grafik-x1.md). Ortsangaben beschreiben den Projektarbeitsplatz.
Für den authentischen Fall MT nennt der Bericht keine Orte, nur Strukturangaben.

## 1. Ziel und Ausgangslage

Eine ruhige Kartenansicht „Wo leben die Kontakte?“ als experimentelle Zusatzgrafik, ohne Verbindungslinien, für alle Testfälle
(001*, 002*) und den ersten `student_pilot`-Fall (MT). Sie dient als Vergleichsmaterial für die Entscheidung über eine spätere Aufnahme in
den Standardsatz; die acht Standardgrafiken bleiben unverändert. Vorab: Working Tree sauber, `main` = `origin/main` (`5bed569`).

## 2. Änderungen

- **Code:** [`experimental.py`](../../src/mares/network_v1/experimental.py) mit Layout (`x1_layout`, Labelplatzierung `place_labels`),
  Zeichnung (`x1`) und Lauf (`render_x1`). CLI-Befehl `v1 experimental-x1 --case … | --root …`. Gemeinsame Bausteine des
  Designsystems (Seite, Fallkennzeichnung, Beziehungstypfarben und -legende, Knoten) unverändert wiederverwendet.
- **Ablage:** `<Fall>/experimental/<Fallcode>_X1_geografische_verteilung.{png,svg}`, Laufprotokoll unter `WORKSPACE/runs/`.
- **Ortsverzeichnis:** `INTAKE:network_v1/reference/gazetteer.csv` mit 25 Orten (öffentlich bekannte Koordinaten, von Hand eingetragen,
  auf 0,01° gerundet, kein Geocoding-Dienst). Es liegt nicht im Repository, weil es die Wohnorte echter Fälle verriete.
- **Basiskarte:** die vorhandene Natural-Earth-Datei 1:50m im `WORKSPACE`-Cache (vom Kartenexperiment vom 2026-10-31).
- **Doku:** `network-v1.md` §2, §6.1, §8; `storage-contract.md` §4; README des Kartenpiloten; ADR-0010.

## 3. Gestaltungsentscheidungen (im Lauf entwickelt)

1. **Panels** Amerika · Europa (ohne Deutschland) · Deutschland, auf Wunsch von links nach rechts in dieser Reihenfolge, gleiche Höhe,
   feste Ausschnitte (vergleichbar zwischen Fällen). Weitere Regionen nur bei Bedarf zwischen Amerika und Europa (im Test mit Japan geprüft).
2. **Ringe um den Ortspunkt**, nach Beziehungstyp sortiert: bis 10 Kontakte ein Ring, mehr in konzentrischen, versetzten Ringen. Die
   erste Fassung (gestapelte Ringe auf gleichen Winkeln) ergab bei 8–9 Kontakten ein Kreuzmuster und wurde ersetzt.
3. **Cluster ohne Überlappung**: größte zuerst, jeder weitere an der nächstgelegenen freien Stelle seines Punkts, mit feiner Linie zum
   Punkt. Ein iteratives Auseinanderschieben in der ersten Fassung hinterließ in Mittelhessen überlagerte Cluster und wurde verworfen.
4. **Ortsgruppen**: Orte, die auf der Karte weniger als ca. 3 mm auseinanderliegen, werden zusammengefasst („Marburg u. a. · 14“ mit
   umbrochener Ortsliste). Ohne sie liefen in 002 fünf Zuordnungslinien durch den Marburg-Cluster.
5. **Beschriftungen** in acht Richtungen und vier Abständen, nicht auf Knoten, Ortspunkten, fremden Clustern, Paneltiteln oder anderen
   Beschriftungen, im Panel; ab mittlerem Abstand mit feiner Linie.
6. **Unschärfe**: nur Wohnland → Länderpunkt im gestrichelten Kreis, „· nur Land“, Legendeneintrag nur bei Bedarf. Nicht zuordenbar
   bzw. ohne Ortsverzeichniseintrag → nur Fußnote.

## 4. Ergebnisse (visuell geprüft, PNG)

| Fall | dargestellt | nicht dargestellt | Befund |
|---|---|---|---|
| 001* | 21 (Amerika 3, Europa 1, Deutschland 17) | A17 (regionale Angabe) | ruhig; der Ortspunkt von Gießen liegt im Fußabdruck des Marburg-Rings, der Gießen-Knoten ist daneben gesetzt (mit Linie) |
| 002* | 31 (Amerika 7, Europa 3, Deutschland 21) | A22 (mehrdeutiger Ort) | Ortsgruppen „Marburg u. a. · 14“ und „Gießen u. a. · 4“, in Amerika „Bogotá u. a.“ (mit Medellín); Deutschlandpanel dicht, aber ohne Überlappung |
| MT | 22 (Amerika 3, Europa 11, Deutschland 8) | – | am klarsten: drei Orte in Europa, einer in Amerika und einer in Deutschland, je ein Ring |

„Nur Wohnland bekannt“ kommt in keinem Fall vor; die Darstellung ist mit einer synthetischen Variante getestet.

## 5. Tests und Regression

- Neu: `tests/test_network_v1_experimental.py`, 10 Tests mit Fall 002, einer künstlichen Basiskarte und einem Ortsverzeichnis der
  erfundenen Orte:
  - Panelfolge, Vollständigkeit und keine Überlappung;
  - Ortsgruppe, nur Wohnland, fehlender Verzeichniseintrag, Zusatzregion;
  - keine Verbindungslinien, Beschriftungen nicht auf Knoten;
  - Ausgabe nur in `experimental/`, fehlende Basiskarte bzw. fehlerhaftes Verzeichnis, CLI.
- Volle Suite: **583 bestanden** (vorher 573), `network_v0` eingeschlossen.
- **Standardgrafiken:** vor dem Lauf gehasht, danach alle 48 Dateien (je Fall 16) byteidentisch; `graphics/` enthält weiterhin nur
  die Standarddateien.

## 6. Status

| | X1 |
|---|---|
| implementiert | ja |
| technisch getestet | ja |
| visuell geprüft (Agent, drei Fälle) | ja |
| fachlich bewertet / in den Standardsatz aufgenommen | nein (offen) |

## 7. Offene Punkte

- Der dichte Raum Mittelhessen bleibt die Schwachstelle der Deutschlandkarte (Ortsgruppen, ausweichende Cluster).
- Das Ortsverzeichnis wird von Hand gepflegt; jeder neue Ort eines Falls braucht einen Eintrag, sonst steht der Kontakt in der Fußnote.
- Ortsgruppen hängen vom Maßstab ab: in Amerika werden Städte im Abstand von rund 250 km zusammengefasst (Bogotá/Medellín).
