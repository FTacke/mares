# Run-Bericht 2026-11-05 – `network_v1`: X1 Fassung 2.8 (geografische Leserichtung)

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §6.1. Vorlauf:
[`2026-11-05_network-v1-x1-fassung-2-6-2-7.md`](2026-11-05_network-v1-x1-fassung-2-6-2-7.md). Für den authentischen Fall MT nennt der
Bericht keine Orte und keine Länder.

## 1. Ziel

Nachtrag der Projektleitung: Die Platzierung soll nicht nur Kollisionen vermeiden, sondern die grobe geografische Orientierung
erhalten. Nahe Orte im selben Panel dürfen die Nord-Süd- bzw. West-Ost-Relation nicht sichtbar umkehren, soweit das layoutseitig
vermeidbar ist; dafür dürfen auch die Kontaktflächen umgesetzt werden. Konkret in 002: Gießen oberhalb von Frankfurt am Main. Vorab:
Working Tree sauber, `main` = `origin/main` (`46c47ba`).

## 2. Änderungen ([`experimental.py`](../../src/mares/network_v1/experimental.py))

- **`_order_flips`** zählt für zwei Orte, deren Punkte im Panel höchstens 1,5 Zoll auseinanderliegen, die umgekehrten Relationen
  zweier Positionen (Flächenmitten oder Labelmitten):
  - eine **klare** Relation (Versatz ≥ 0,1 Zoll und ≥ 1,5-mal der Versatz quer dazu) darf ihr Vorzeichen nicht wechseln;
  - ein **diagonales** Paar darf sich nur nicht als Ganzes umdrehen (Skalarprodukt negativ);
  - Umkehrungen unter 0,05 Zoll gelten als nicht sichtbar.
- **Kosten:** je Umkehrung 2,0 (in Zoll Flächenversatz gerechnet) – für Flächen in `_disc_candidates`, für Labels in `_label_cost`.
  Verdecken und Mehrdeutigkeit (100/150) bleiben vorrangig; eine Umkehrung ist damit einige Zentimeter längere Linie wert, nie ein
  verdecktes Element.
- **Vorausschau:** Die Fläche eines früh gesetzten Ortes beachtet zusätzlich die Ortspunkte der noch folgenden Orte (`pending`), damit
  sie die Seite der Nachbarn freilässt. Ohne diese Vorausschau belegte in 002 Gießen (größer, also früher gesetzt) den Platz südwestlich,
  und Frankfurt blieb nur der Norden.
- Erster Ansatz mit Achsenregel auch für diagonale Paare: Kassel (nordöstlich von Marburg) wurde mit einer fast 2 Zoll langen Linie
  weggesetzt. Deshalb die Trennung klar/diagonal.
- `version: "2.8"`; [`network-v1.md`](../architecture/network-v1.md) §6.1 nennt die Leserichtung als dritte Priorität vor der
  Kompaktheit.

## 3. Tests

- Neu: `test_callouts_keep_the_geographic_reading_order` in zwei Varianten (002 und eine Variante, in der Frankfurt größer ist und
  daher vor Gießen gesetzt wird): keine Umkehrung zwischen Flächen und zwischen Labels; Gießen mit Fläche und Label über Frankfurt.
- Geändert: `test_place_points_and_names_always_stay_visible` prüfte Labels gegen das Quadrat um jeden Kontaktknoten. Ein diagonal
  angedocktes Label (Kassel) schnitt dieses Quadrat, nicht aber den Kreis (Abstand 0,176 Zoll, Knotenradius 0,139). Der Test prüft
  jetzt die tatsächliche Kreisgeometrie (`_box_hits_disc`).
- X1-Tests 26 bestanden, Gesamtsuite 599 bestanden. Die 48 kanonischen Grafiken (G1–G3, P1–P5) sind per SHA-256 unverändert.

## 4. Ergebnis (visuell geprüft, PNG)

- **002:** Marburg und Umgebung oben, Gießen und Umgebung in der Mitte (rechts), Frankfurt unten; Kassel kurz angebunden nordöstlich
  der Marburger Fläche; Berlin unverändert.
- **001:** Reihenfolge Marburg – Gießen – Frankfurt von Nord nach Süd, Köln westlich. Gießen hat dafür eine längere waagrechte Linie
  (etwa 0,85 Zoll).
- **MT:** unauffällig, keine Umkehrung sichtbar.

## 5. Status und offene Punkte

- Implementiert und getestet; neu gerendert für 001, 002 und MT. Die Regel ist eine Darstellungsheuristik, **nicht wissenschaftlich
  validiert**; die Schwellen (1,5 Zoll Nähe, Faktor 1,5, Gewicht 2,0) sind an drei Fällen eingestellt.
- Die Reihenfolge wird greedy hergestellt (größte zuerst, mit Vorausschau auf Ortspunkte); in sehr dichten Panels kann eine Umkehrung
  bleiben, wenn jede Alternative etwas verdecken würde.
- Gewichte und Linienlängen (001: Gießen) bleiben bei weiteren Fällen zu beobachten.
