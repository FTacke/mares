# Run-Bericht 2026-10-13 – Geografische Netzwerkabbildungen G1 und G2

Journal eines Laufs, keine Spezifikation. Maßgeblich sind [`visualization-conventions.md`](../architecture/visualization-conventions.md) §3.3 und
[`network-module.md`](../architecture/network-module.md). Ortsangaben beschreiben den Projektarbeitsplatz. Dieser Bericht enthält keine
Forschungsdaten; Kennzahlen sind Zählungen und Layoutmaße.

## 1. Ziel und Scope

Zusätzliche, geografisch interpretierbare Abbildungen für den Pilotfall `001-2`: die räumliche Einordnung der Kontakte **relativ zu Ego in Stufen**, ausdrücklich
keine Karte und keine Entfernung in Kilometern. Die Abbildungen A, B1, B2, B3 bleiben unverändert; keine Änderung am Netzwerkmodell, keine neue Erhebung,
keine neue Infrastruktur, kein Commit.

## 2. Neue Abbildungen

| Datei (`figures/`) | Inhalt |
|---|---|
| `fig_G1_geografische_zonen` | G1: Ego im Zentrum, vier konzentrische Zonen (Marburg, Region Marburg, übriges Deutschland, außerhalb Deutschlands), jeder Kontakt mit ID in seiner Zone |
| `fig_G2_geografisches_beziehungsnetz` | G2 (regulär = Variante G2b): vier gleich breite Wohnort-Bänder, die 41 bestätigten Beziehungen in zwei Linienarten (innerhalb / zwischen Zonen), Ego links mit hellen Zugehörigkeitslinien |
| `fig_G2_0_variantenvergleich` | Arbeitsabbildung: G2a (Ringe) neben G2b (Bänder) mit Lesbarkeitsmaßen |

Jeweils SVG, PNG und PDF. Ablage: `C:\dev\mares\mares_workspace\runs\RUN-20261013T070329Z-66da3a\figures\`.

## 3. Umsetzung der geografischen Kategorien

Die Kategorien kommen aus der bestehenden Wohnortregel (`geo.classify_residence`), nicht aus einer neuen Logik:

- `Marburg`: nur bei exakt genanntem Ort (Groß-/Kleinschreibung ignoriert); „Marburg an der Lahn“ gilt deshalb als übriges Deutschland und wäre eine bewusste Parametrierung (`--local-place`).
- `Region Marburg`: eigene Kategorie für regionale Angaben („Nähe/Raum/Region/Umgebung Marburg“); Deutschland, nicht die Stadt, kein erfundener Wohnort.
- `übriges Deutschland`: deutscher Wohnort außerhalb dieser beiden.
- `außerhalb Deutschlands`: jedes andere Land.
- Ein fünftes, gestricheltes Band „unbekannt“ erscheint nur, wenn ein Wohnort keinem Land zuzuordnen ist; ein Kontakt wird nie in eine Zone geraten oder weggelassen.

Technisch: `figures/geo_zones.py`. G1 und G2a belegen die Zonen mit `ring_layout` (Radius allein aus der Kategorie; die Ringbreite wächst nur so weit, wie die Kontakte
Platz brauchen; leere Zonen bleiben sichtbar); G2b mit `band_layout`. Ein Kontakt steht in G1 gleichmäßig auf dem Ring (sortiert nach Ort, dann ID). In G2 ordnet
`structure_order` die Kontakte zirkulär nach dem Winkel im B1/B2-Layout, sodass verbundene Kontakte ähnliche Höhe im Band haben. Alles ist deterministisch (festes Raster,
sortierte Reihenfolgen, kein Zufall) und unabhängig vom Hash-Seed des Prozesses.

## 4. Wahl von G2

**Gewählt: G2b (Bänder).**

| | G2a · konzentrische Zonen | G2b · Bänder |
|---|---|---|
| Kreuzungen (Pilotfall) | 37 | **30** |
| Knotenabstand relativ zur Beziehungslänge | 0,49 | **0,98** |
| Beschriftungen | Linien und ID-Beschriftungen konkurrieren in den Ringabschnitten | frei lesbar |
| Geografische Staffelung | Zonen als Ringe, aber die Linien einer Gruppe bündeln sich in einem Ringabschnitt | klare Staffelung von Marburg bis außerhalb |
| Beziehungen innerhalb/zwischen Zonen | schwer zu verfolgen | zwischen Zonen = waagerechte, hellere und kräftigere Linien; innerhalb = senkrechte, dunkle Linien |

Auf den Pilotdaten verlaufen 30 der 41 Beziehungen innerhalb einer Zone und 11 zwischen zwei Zonen; die zwischen den Zonen verlaufenden stehen alle zwischen „übriges Deutschland“ und „außerhalb
Deutschlands“. Die Gruppe in Marburg bildet für sich einen dichten Block. Dass die Bänder räumlich getrennt gezeichnet sind, heißt nicht, dass die Kontakte sozial getrennt sind (Hinweis in der Abbildung).

**Kontaktgruppen und weitere Kodierungen:** In G2 sind die erhobenen Gruppen bewusst nicht als Flächen eingezeichnet: Flächen über Ringen oder Bändern würden Kontakte anderer Zonen
umschließen und Mitgliedschaft suggerieren; die Gruppenstruktur zeigen B2 und B3. Symbole für Beziehungstyp und Geburtsland am Knoten wurden erwogen und verworfen (Überladung; Geburtsland
steht in Abbildung C). In G1 stehen die Orte je Zone in der Legende statt am Knoten (längere Ortsnamen kollidieren am Ring).

## 5. Interpretationsgrenzen (in Abbildung und Dokumentation)

- G1/G2 zeigen **Kategorien**, keine Karte, keine Kilometer; Ringbreiten richten sich nach der Zahl der Kontakte, Bänder sind gleich breit.
- Die Lage ist **nicht** subjektive Nähe (Abbildung A) und **nicht** ein graphentheoretisches Layout wie B1–B3; in G2b folgt nur die Höhe im Band der Beziehungsstruktur, in G1 ist die Reihenfolge ohne Information.
- Ego ist in G2b mit allen Kontakten durch helle Zugehörigkeitslinien verbunden; sie sagen nichts über Nähe oder Beziehungen.
- Paare ohne Angabe bleiben unbekannt (Paarabdeckung nicht belegt); die Abbildung führt weder Verneinungen noch neue Linien.

## 6. Tests

**265 → 289 Tests** (24 neue in `tests/test_networks_geo_figures.py`, synthetische Daten; die Zahl der Abbildungen in bestehenden Tests wurde angepasst). Abgedeckt: Zuordnung der Kontakte zu den vier Kategorien
(`Region Marburg` als eigene Kategorie; „Marburg an der Lahn“ nicht als Marburg), Reihenfolge und Verschachtelung der Zonen, leere Zonen und das Band „unbekannt“, Kontakte in ihrer Zone und Farbe,
keine Linien in G1, in G2 genau die bestätigten Beziehungen (keine verloren, keine zusätzlich, keine doppelt, innerhalb/zwischen korrekt klassifiziert) und eine Ego-Linie je Kontakt, Hinweise zu Karte/Entfernung/Nähe,
Stabilität für 1 bis 100 Kontakte, Byte-Reproduzierbarkeit, deterministische Layouts über Prozessgrenzen, keine Überlappung der Kontakte, **keine Veränderung an B1, B2 und B3**, nur IDs und Codes im Text.
Vollständiger Testlauf: **289 bestanden, 0 fehlgeschlagen**.

**Kontrollierter Lauf auf dem Pilotfall:** technische Prüfung PASSED (0 Fehler, 0 Warnungen); 67 Ausgabedateien. **Alle bisherigen Abbildungen (A, B0–B3, C, D1, D2, E) sind gegenüber dem
vorherigen Lauf byteidentisch** (SHA-256 verglichen); neu sind nur die G-Dateien und der Verarbeitungsbericht (er listet sie). **Sichtprüfung:** G1, G2 und der Variantenvergleich wurden angesehen und überarbeitet
(Bandbeschriftungen, Linienfarben zwischen/innerhalb der Zonen, abgeschnittene Legende, gleichmäßige Belegung der Ringe in G1, Figurhöhe von G2b, „links → rechts“ statt „innen → außen“ in der Legende von G2b).
Implementierte Änderungen und bestandene Tests sind kein Nachweis der Datenrichtigkeit; wissenschaftlich validiert ist nichts (Datenqualität `UNREVIEWED`).

## 7. Offene Punkte

1. Paarabdeckung weiterhin nicht belegt; die Zahl „unbekannt“ (190 Paare) gilt auch für G2.
2. Die als Vorschlag gekennzeichneten Kuratierungseinträge und die offenen Datenfragen sind unverändert.
3. Eine Variante mit Gruppenkonturen in G2 wäre möglich, wurde aber nicht erstellt (siehe §4).

## 8. Git

Kein Commit, kein Push. Neue Dateien: `src/mares/networks/figures/geo_zones.py`, `tests/test_networks_geo_figures.py` und dieser Bericht; geändert: `run.py`, einige Tests und Dokumente.
