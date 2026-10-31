# Run-Bericht 2026-10-12 – Ego-einschließende Netzwerkabbildung B3

Journal eines Laufs, keine Spezifikation. Maßgeblich sind [`visualization-conventions.md`](../architecture/visualization-conventions.md) §3.2 und
[`network-module.md`](../architecture/network-module.md). Ortsangaben beschreiben den Projektarbeitsplatz. Dieser Bericht enthält keine
Forschungsdaten; Kennzahlen sind Zählungen und Layoutmaße.

## 1. Ziel und Scope

Eine zusätzliche Perspektive: **B3 – das persönliche Netzwerk einschließlich Ego**, also Ego, alle Kontakte, je eine Ego–Kontakt-Linie und die
bestätigten Kontakt–Kontakt-Beziehungen. B1, B2 und die Ringabbildungen bleiben unverändert; keine Überarbeitung der Pipeline, keine neue Datenerhebung,
keine Rohdatenänderung, kein Commit.

## 2. Erprobte Layoutvarianten

Verglichen in `fig_B3_0_layoutvergleich` (alle deterministisch, nur NumPy, fester Seed; gleiche 22 Ego-Linien und 41 Beziehungen):

| Variante | Konstruktion | Kreuzungen (davon Ego-Linien) | von Ego-Linien gestreifte Kontakte | Ego-Abstand zur Mitte | Struktur wie B2 |
|---|---|---|---|---|---|
| **A · Kontakte wie in B2, Ego ergänzt** | Kontaktpositionen aus B1/B2 unverändert; Ego nahe dem Schwerpunkt, dort wo seine Linien am wenigsten Beziehungen kreuzen und keinen Kontakt streifen (festes Raster) | **60 (27)** | **0** | 0,15 | **1,00** |
| B · gemeinsames gewichtetes Layout | Stress-Majorisierung aller Knoten; Ego–Kontakt-Strecke 2,0 statt 1,0, mit 0,2 gewichtet | 62 (30) | 1 | 0,04 | 0,89 |
| Referenz · Ego als gewöhnlicher Knoten | alle Strecken gleich | 71 (39) | 2 | 0,01 | 0,80 |

„Struktur wie B2“ ist die Korrelation der Abstände zwischen den Kontakten mit dem Layout ohne Ego (1 = identisch). Die Maße vergleichen Layouts
und sagen nichts über die Daten.

## 3. Auswahl und Begründung

Gewählt ist **Variante A**. Die Kontakt–Kontakt-Struktur bleibt exakt die von B1/B2: Die Abbildungen sind unmittelbar vergleichbar, die Überlappung
der verschachtelten Gruppen G04/G05/G06 bleibt erkennbar, es gibt die wenigsten Kreuzungen, und keine Ego-Linie läuft durch einen Kontakt. Die
Referenzvariante bestätigt die Erwartung des Auftrags: Als gewöhnlicher Knoten zieht Ego die Gruppen zusammen (Struktur 0,80). Das gewichtete
Layout (B) erhält die Struktur besser (0,89) und rückt Ego genau in die Mitte, verändert aber die Anordnung gegenüber B1/B2 und erzeugt zusätzliche
Kreuzungen. Ego liegt in A nicht zwanghaft im Mittelpunkt, aber klar zentral zwischen den Teilnetzen. Die Wahl ist eine Abwägung zugunsten der
Vergleichbarkeit; wo ein Ego im exakten Zentrum wichtiger wäre, bietet sich B an (`variant="weighted"`).

**Gruppenflächen:** sehr weich (7 % Füllung) auch in B3. Sie stören die Linien nicht; die Überlappung bleibt erkennbar. `show_groups=False`
bleibt als Rückfallebene für dichtere Netze.

## 4. Implementierung

- `figures/ego_layouts.py` (Ego-Layoutvarianten, Platzierung, Maße), `figures/ego_network.py` (B3 und Layoutvergleich); `figures/layouts.py`:
  die Stress-Majorisierung ist als `smacof(dist, weights, …)` herausgelöst (Verhalten für B1/B2 unverändert); `figures/network.py`:
  `place_labels` kennt Hindernisse und „weiche“ Linien (Ego-Linien), `draw_groups` die Deckkraft. `run.py`/`report.py`: B3 im Standard-Workflow,
  Parameter `ego_layout` im Run-Record.
- Ausgabe je Fall automatisch: `fig_B3_ego_netzwerk` und `fig_B3_0_layoutvergleich` (SVG, PNG, PDF). Keine feste Kontaktzahl.
- Dokumentation nur soweit nötig: `visualization-conventions.md` §3.2 (Layouts, Interpretation), Modul-Dokument (Abbildungsliste, Code-Karte), README.

## 5. Wissenschaftliche Absicherung

B3 unterscheidet drei Dimensionen: **Zugehörigkeit zum persönlichen Netzwerk** (helle Ego–Kontakt-Linien), **erhobene Beziehungen** (dunklere
Kontakt–Kontakt-Linien) und die **subjektive Nähe**, die nur Abbildung A zeigt. In der Abbildung und in der Dokumentation steht: Der Abstand zu
Ego ist kein Nähemaß; der Abstand zwischen getrennten Gruppen ist keine soziale oder geografische Distanz; der Graph ist durch Ego
zwangsläufig zusammenhängend (kein Befund); Strukturmaße beruhen auf dem Netz ohne Ego. Das Netzwerkmodell wird für B3 nicht verändert: Ego ist
kein Knoten des Modells, es entstehen keine Beziehungen, und die Auswertung bleibt auf dem Alter-Alter-Netz.

## 6. Tests

**234 → 265 bestanden**, 0 fehlgeschlagen. Neu (`tests/test_networks_ego_network.py`, synthetische Daten): genau ein Ego-Knoten; eine Ego-Linie je
Kontakt ohne Dopplung; genau die bestätigten Alter-Alter-Linien, keine zusätzliche, keine berührt Ego; zwei visuell getrennte Linienarten (Farbe,
Breite, Ebene) und getrennte Legendeneinträge; Kontaktpositionen und Wohnortfarben wie in B1; Ego ohne geografische Kategorie; die Fußnote trennt
die drei Dimensionen; Gruppenflächen weich und abschaltbar; **B1 und B2 sind nach dem Bau von B3 byteidentisch**; B3 für 1, 2, 3, 40 und 100
Kontakte und ohne jede Beziehung; Ego-Layouts deterministisch, auch über Prozessgrenzen mit verschiedenen Hash-Seeds; die feste Variante erhält die Struktur
exakt, die gewichtete verändert sie weniger als die Referenz; keine sich überlappenden ID-Beschriftungen; B3 byte-reproduzierbar. Die Zählungen der
bestehenden Tests (Zahl der Abbildungen) wurden angepasst, sonst nichts.

**Kontrollierter Lauf auf dem Pilotfall** (`RUN-20261012T181225Z-22a503`): 58 Ausgabedateien, technische Prüfung PASSED (0 Fehler, 0 Warnungen). **Alle
bisherigen Abbildungen (A, B0, B1, B2, C, D1, D2, E) sind gegenüber dem vorherigen Lauf byteidentisch** (SHA-256 aller Dateien verglichen); neu
sind nur die B3-Dateien (und der Verarbeitungsbericht wegen des neuen Parameters).

**Sichtprüfung:** Layoutvergleich und B3 wurden angesehen. Behoben: abgeschnittene Legendeneinträge (jetzt Sektionen „Ego“ und „Kontakte nach
Wohnort“). Bewusst belassen: die Kreuzungen der hellen Ego-Linien mit den Gruppen (Ego verbindet alle; sie liegen unter den Beziehungslinien) und die
Kreuzungen innerhalb der Cliquen.

Implementierte Änderungen und bestandene Tests sind kein Nachweis der Datenrichtigkeit; wissenschaftlich validiert ist nichts (Datenqualität `UNREVIEWED`).

## 7. Ablage

`C:\dev\mares\mares_workspace\runs\RUN-20261012T181225Z-22a503\figures\`: `fig_B3_ego_netzwerk.{svg,png,pdf}`, `fig_B3_0_layoutvergleich.{svg,png,pdf}`.
Eigene Zwischenläufe und Vorschauen dieses und des vorigen Laufs wurden per exaktem Namen entfernt; der Pilotlauf des Audio-Pilots wurde nicht angefasst.

## 8. Einschränkungen und offene Punkte

1. Nähe zu Ego, Distanz zwischen Gruppen und Zusammenhang des Graphen sind in B3 **nicht interpretierbar** (§5); dafür gelten A, B1, B2.
2. Die Paarabdeckung des Pilotfalls ist weiterhin nicht belegt; B3 zeigt nur bestätigte Beziehungen, die übrigen 190 Paare sind unbekannt.
3. Die vorhandenen offenen Datenfragen und die als Vorschlag gekennzeichneten Kuratierungseinträge bleiben unverändert.
4. Variante B ist implementiert, aber nicht der Standard; ein Wechsel ist ein Parameter, kein Umbau.

## 9. Git

Kein Commit, kein Push, kein Remote. Neue Dateien: `src/mares/networks/figures/ego_layouts.py`, `ego_network.py`, `tests/test_networks_ego_network.py`
und dieser Bericht; geändert: `layouts.py`, `network.py`, `run.py`, `report.py`, einige Tests und Dokumente.
