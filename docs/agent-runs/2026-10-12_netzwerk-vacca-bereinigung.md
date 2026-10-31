# Run-Bericht 2026-10-12 – Netzwerkdaten bereinigen, Visualisierungen überarbeiten (Vacca-inspiriert)

Journal eines Laufs, keine Spezifikation. Maßgeblich sind [`network-module.md`](../architecture/network-module.md),
[`visualization-conventions.md`](../architecture/visualization-conventions.md) und
[`ADR-0003`](../decisions/ADR-0003_2026-10-12_erhebungsmethode-und-kuratierung.md). Ortsangaben beschreiben den
Projektarbeitsplatz. Dieser Bericht enthält keine Forschungsdaten; Kennzahlen sind Zählungen. Er berichtigt die Beschreibung
der Alter-Alter-Erhebung im [vorherigen Netzwerk-Bericht](2026-10-12_netzwerkpipeline-pilot-001-2.md).

## 1. Ziel und Scope

Die Netzwerkpipeline am Pilotfall `001-2` methodisch und grafisch überarbeiten: (a) die falsche Lesart der
Alter-Alter-Erhebung berichtigen, (b) unnötige oder irreführende Prüfhinweise bereinigen und aus den Abbildungen
entfernen, (c) die Gruppen- und Beziehungsdarstellung durch eine kraftbasierte Netzwerkabbildung nach dem Prinzip von
Vacca et al. (2016, Abb. 2) ersetzen, (d) Tests und Dokumentation nachziehen. Nicht Teil: ASR, MaRC3a, weitere Migration,
neue Speicher, neue Instrumente, Inferenzstatistik, Commit/Push.

## 2. Korrigierte Interpretation

**Klarstellung der Projektleitung (2026-10-12):** Der Explorator hat die Beziehungen zwischen den Netzwerkpersonen im
Interview erfragt; die Gruppenumrandungen fassen diese erhobenen Beziehungen grafisch zusammen; alle Mitglieder derselben
bestätigten Gruppe kennen sich.

- Die Cliquen-Rekonstruktion ist für die sechs bestätigten Gruppen zulässig; die **41** Beziehungen sind durch die Erhebung gedeckt
  (Überlappungen einfach gezählt, nichts entfernt). Die frühere Formulierung „aus Gruppenmitgliedschaft angenommen / Alter-Alter-
  Erhebung unvollständig“ ist berichtigt (Modul-, Pilot- und Konventionsdokumente, Statusfelder, Berichte, Abbildungsfußzeilen).
- **Erhebungsmethode** (einzeln erfragt), **Dokumentationsform** (Gruppenumrandungen) und **Paarabdeckung** sind jetzt getrennte
  Aussagen im Modell, im Run-Record und im Datenvertrag.
- **Paarabdeckung (231 Paare): nicht belegt.** Weder das Paket noch die Klarstellung sagen, dass für Paare außerhalb der Gruppen
  eine Verneinung erhoben wurde. Deshalb bleiben **190** Paare unbekannt, es werden keine Strukturmaße berechnet, und niemand
  gilt als „kennt sich nicht“. Der Zustand „Paarabdeckung vollständig“ ist implementiert und getestet (fehlende Paare werden `no`,
  Strukturmaße werden als explorative Einzelfallbeschreibung berechnet), wird auf den echten Daten aber nicht ausgelöst.
  **Zu klären:** Hat der Explorator jedes der 231 Paare erfragt?

## 3. Datenstatus und Provenienz

Die Originallieferung (Paket v1.1) blieb unverändert. Die Klarstellungen stehen in einer **Kuratierungsdatei**
(`mares-network-curation/v0-draft`), die ich im lokalen Eingang abgelegt habe:
`INTAKE/inbox/MARES_001-2_Kuratierung_2026-10-12/curation.json`, SHA-256
`37b88a6b8c53fd50641cd7baa488175edd8b83108c2f443a7ada9d4f498a2cf1`; Protokoll `INTAKE/reports/curation_MARES_001-2_2026-10-12.json`.
Sie trägt die Erhebungsmethode, die Paarabdeckung und je Prüfhinweis Kategorie, Urheber und Begründung. Jeder Lauf liest sie neben
dem Paket und hält ihren Hash im Run-Record fest. Zustand: Intake `RECEIVED`, `NOT_PRESERVED`, `NO_COPY` (kein `PRIMARY`/`BACKUP`).
Datenqualität weiterhin `UNREVIEWED`, Freigabe `NOT_DECIDED`.

## 4. Prüfhinweise (Stand auf den echten Daten)

| Kategorie | Anzahl | Inhalt (ohne Einzelheiten) |
|---|---|---|
| offene, entscheidungsrelevante Datenfrage | 5 | mögliche zusätzliche Funktionscodes bei einem Kontakt; Paarabdeckung; Fall-ID, Provenienz, Quellenprüfung (drei Registeraufgaben) |
| dokumentierte Mehrdeutigkeit | 5 | Geburtsland mit zwei genannten Ländern (Rohwert erhalten); handschriftliche Ergänzungen bei drei Kontakten; ein nicht übertragener Freitext |
| akzeptierte Unschärfe | 1 | regionale Ortsangabe („Region Marburg“) |
| geklärt | 5 | Namensabweichung (maßgeblich: Kontakt-ID); Tabellenwert-Regel; Gruppenquelle; Datenschutzhinweis; Ortsabkürzung |

Technische Prüfung: **PASSED** (0 Fehler, 0 Warnungen). Die frühere Warnung zum Geburtsland ist eine dokumentierte Mehrdeutigkeit
(Status „mehrdeutig“: weder ein Land gewählt noch zwei gezählt noch als fehlend behandelt), die frühere Warnung zur
Ortsabkürzung ist durch die Kuratierung abgedeckt. Sprachmodus 6 bei den zwei Kontakten ohne Erläuterung bleibt als erhobener Wert
bestehen (im Paket gibt es dazu keinen Hinweis). **Die handschriftlichen Originalbögen lagen mir nicht vor**; was das Paket nicht
dokumentiert, habe ich nicht ergänzt, und Lesarten, die nur am Original entschieden werden können (Funktionscodes), bleiben offen.
Einträge mit Urheber `agent_proposal` (R02, R04–R07, R12, R14, Ortsabkürzung) sind Vorschläge und warten auf Bestätigung.

## 5. Implementierte Änderungen

- `curation.py` (Kuratierung, Vier-Kategorien-Modell), `geo.py` (Region Marburg, Status des Geburtslands), `build.py` (Paarabdeckung,
  `TieBasis.COVERAGE`), `analysis.py` (`SurveyStatus` mit Methode/Form/Abdeckung, Strukturtabelle nur bei bestätigter Abdeckung, Geburtsland-Status),
  `validate.py`/`report.py` (Kategorien, Review-Register `review/review_register.csv`), `canonical.py` (Rohwerte plus abgeleitete Kategorien),
  `run.py`/`cli.py` (`--curation`).
- Grafiken: Prüfmarkierungen und ihre Legenden entfernt (A, C, D1, D2); Region-Marburg-Kategorie und „mehrdeutig“ in A–E; **neu**
  `figures/layouts.py` (Spring, Stress-Majorisierung, ForceAtlas2, Lesbarkeitsmaße) und `figures/network.py` (B0, B1, B2); die alte
  Gruppenfigur (`figures/groups.py`) ist ersetzt.
- Dokumentation: ADR-0003, `network-module.md`, `visualization-conventions.md`, `pilot-case-001-2.md`, `data-contract.md` §5, README, `modules.md`,
  `examples/synthetic/README.md`; synthetisches Beispiel einer Kuratierung.

## 6. Die neuen Netzwerkabbildungen

Pfad: `C:\dev\mares\mares_workspace\runs\RUN-20261012T132300Z-806168\figures\` (je SVG, PNG, PDF; ein zweiter, byteidentischer Lauf
`RUN-20261012T132254Z-cfa85a`).

- **`fig_B1_netzwerkstruktur`** – 22 Kontakte als kleine Knoten, 41 dünne Linien, Position aus dem Layout, Farbe = Wohnort.
- **`fig_B2_netzwerkstruktur_gruppen`** – identische Positionen, dazu die sechs erhobenen Gruppen als weiche Flächen mit Kürzel.
- **`fig_B0_layoutvergleich`** – Arbeitsabbildung zur Wahl des Layouts.

**Vergleich der kraftbasierten Verfahren** (gleiche 41 Linien; die Zahlen vergleichen Layouts, nicht Daten):

| Verfahren | Kreuzungen | Knotenabstand (rel.) | Beziehungslänge (Anteil am Bild) | Eindruck |
|---|---|---|---|---|
| Spring (Fruchterman–Reingold) | 32 | 0,46 | ≈ 0 % | Teilnetze werden zusammengedrückt, die unverbundenen Kontakte fliegen an den Rand; unlesbar |
| **Stress-Majorisierung** (gewählt) | 33 | 0,52 | 21 % | Teilnetze groß und klar getrennt, Kontakte ohne Beziehung am Rand; keine sich berührenden Knoten |
| ForceAtlas2 | 28 | 0,43 | 12 % | etwas weniger Kreuzungen, aber kompakter; ein Knoten liegt im Zentrum einer Clique; parameterempfindlich |

**B1 gegen B2:** B1 zeigt die Struktur ohne zusätzliche Information: vier zusammenhängende Teilnetze (6er-Clique, die
überlappenden Gruppen G05/G06 mit gemeinsamem Kern, Dreiergruppe, Paar) und drei Kontakte ohne bestätigte Beziehung. Die Teilnetze
entstehen aus den Verbindungsmustern, nicht aus Rahmen. B2 legt dieselben Positionen unter die erhobenen Gruppen: Überlappung und
Verschachtelung (die kleine Gruppe liegt im Durchschnitt der beiden größeren, hier als schmales Band) werden als überlagerte Flächen
erkennbar, und die Gruppen entsprechen den Teilnetzen. B1 ist die Hauptabbildung, B2 die Ergänzung für die Gruppenfrage; die
Kontakte in der gemeinsamen Mitte der beiden großen Gruppen liegen im Layout auf einer Linie (die Verbindungsstruktur dieser drei
ist identisch), was die Überlappungsfläche schmal macht.

**Sichtprüfung:** alle acht Abbildungen wurden angesehen. Behoben: Spring-Layout zerdrückte Teilnetze (nur im Vergleich belassen),
Beschriftungskollisionen der Gruppenkürzel mit ID-Beschriftungen (jetzt freie Position gegenüber ID-Boxen), zu lange Fußnoten
(jetzt umgebrochen), verwaiste Zeilenumbrüche, zu lange Spaltenbeschriftung (Region Marburg), Legendenreste der Prüfmarkierungen.
Bewusst belassen: die Kreuzungen innerhalb der Cliquen (in jeder Geradlinien-Zeichnung unvermeidlich) und die weiße Fläche zwischen den
Teilnetzen (der Abstand hat keine Bedeutung).

## 7. Tests

**191 → 234 bestanden**, 0 fehlgeschlagen (bestehende Tests nur angepasst, wo sich ein Vertrag geändert hat: Geografie, Statusfelder,
Abbildungsnamen). Neu u. a.: Kuratierung (Lesen, Ablehnen fehlerhafter Dateien, Kategorien, Urheber, Passung zum Paket), Paarabdeckung (fehlende Paare nur
bei bestätigter Abdeckung verneint, Strukturmaße nur dann, nichts Belegtes entfällt), Geburtsland „mehrdeutig“ und Region Marburg in Validierung, Tabellen und
kanonischen Daten, ein pilotförmiges Netzwerk (22 Kontakte, 6 Gruppen, 41 eindeutige Beziehungen, Überlappungen einfach gezählt), Grafiken (gezeichnete Linien =
bestätigte Beziehungen, identische Positionen in B1/B2, Layout unabhängig von Attributen und Gruppen, Reproduzierbarkeit über Prozessgrenzen mit verschiedenen
Hash-Seeds für alle drei Verfahren, keine Prüfmarkierungen, keine „Communities“, kollisionsfreie ID-Beschriftungen), Läufe mit Kuratierung.
Die Tests nutzen nur synthetische Daten; der Pilotfall wurde nur in den kontrollierten Läufen verwendet.

**Echte Daten:** 22 Kontakte, 6 Gruppen, 41 Beziehungen, 231 Paare (41 bestätigt, 190 unbekannt); zwei Läufe in getrennten Prozessen
ergaben byteidentische Tabellen, kanonische Daten und Abbildungen (nur der Verarbeitungsbericht unterscheidet sich durch Run-ID und Zeit).
**Implementierte Änderungen und bestandene Tests sind kein Nachweis der Datenrichtigkeit; wissenschaftlich validiert ist nichts.**

## 8. Offene Punkte

1. Paarabdeckung bestätigen (Explorator/Projektleitung) – entscheidet, ob Strukturmaße zulässig sind.
2. Funktionscodes eines Kontakts und handschriftliche Ergänzungen am Originalbogen prüfen.
3. Die als `agent_proposal` gekennzeichneten Kuratierungseinträge bestätigen oder ändern.
4. Fall registrieren, mit früherer Erhebung verknüpfen (Fall-ID, Provenienz); `PRIMARY`/`BACKUP` einrichten – bis dahin ist nichts erhalten.
5. Optional (nicht Teil dieses Laufs): erhobene Gruppen mit algorithmisch bestimmten Communities vergleichen.
6. Der Audio-Pilotlauf aus dem vorigen Bericht (§8 dort) ist weiterhin zu prüfen; ich habe diesmal nur Läufe gelöscht, die ich selbst angelegt hatte.

## 9. Git

Kein Commit, kein Push, kein Remote. Seit dem letzten Lauf existiert ein Basis-Commit des Projekts (nicht von mir); meine Änderungen liegen als
uncommittete Änderungen im Arbeitsverzeichnis (u. a. gelöschte `figures/groups.py`, neue Dateien in `src/mares/networks/`, `tests/`, `docs/`, `examples/`).
