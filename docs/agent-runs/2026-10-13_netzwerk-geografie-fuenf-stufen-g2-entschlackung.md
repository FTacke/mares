# Run-Bericht 2026-10-13 – Fünfstufige Geografie, geografische Beziehungsnetze G2-A/G2-B, entschlackte Abbildungen

Journal eines Laufs, keine Spezifikation. Maßgeblich sind [`geographic-classification.md`](../architecture/geographic-classification.md),
[`visualization-conventions.md`](../architecture/visualization-conventions.md) §3.3–3.8, [`network-module.md`](../architecture/network-module.md) §7 und
[`ADR-0004`](../decisions/ADR-0004_2026-10-13_geografie-fuenf-stufen-und-g2.md). Ortsangaben beschreiben den Projektarbeitsplatz. Dieser Bericht enthält keine Forschungsdaten; Kennzahlen sind Zählungen und Layoutmaße.

## 1. Ziel und Scope

Eine wissenschaftlich sinnvollere geografische Netzwerkdarstellung (Europa nicht mit transkontinentalen Beziehungen zusammenfassen; die Beziehungen *zwischen den Kontakten* in den Vordergrund) und konsequent
reduzierte reguläre Abbildungen; ein kleineres, gegliedertes Repertoire. Nicht Teil: Audio, narrative Episoden, Instrumente, Datenmigration, neue Infrastruktur, Commit/Push. Reale Analysen nur unter `WORKSPACE`.

## 2. Durchgeführte Änderungen (implementiert)

1. **Geografische Klassifikation** (`geo.py`): `ABROAD` entfällt; neu `EUROPE_OTHER` und `OUTSIDE_EUROPE`. Europa geografisch nach UN-Geoschema (`EUROPE_ISO3`), nicht EU. Kein oder ungültiger ISO-Code → `UNKNOWN`
   („Wohnort nicht zuordenbar“), nie geraten. Pilotfall: Marburg 8 · Region Marburg 1 · übriges Deutschland 9 · **übriges Europa 1 (Wien)** · **außerhalb Europas 3 (Kolumbien)**. Wohnort und Wohnland bleiben Attribute;
   der biografische Bezug ist als getrennte Dimension dokumentiert und **nicht** klassifiziert. Die Änderung wirkt zentral (Farben, Tabellen, kanonische Ausgabe, alle Abbildungen).
2. **G2 neu** (`figures/geo_network.py`), **ohne Ego-Linien** (Ego ist nicht Teil des Graphen):
   - **G2-A** geografische Bänder: Breite folgt der Kontaktzahl (ein Kontakt = schmales Band), Spalten bei vielen Kontakten, Bänder direkt beschriftet, nur eine Linienlegende, Beziehungen zwischen den Bereichen dunkel, innerhalb hell.
   - **G2-B** geografisch eingeschränktes Kraftlayout: Ego als Bezugspunkt, fünf radiale Zonen (konzentrische Ellipsen, gepunktet, leicht getönt, Namen in einer Lücke bei 12 Uhr), Kontakte per NumPy-Kraftlayout der bestätigten Beziehungen,
     Radius auf ein Fenster seiner Zone beschränkt, drei feste Starts, bester Wert gewinnt; deterministisch und hash-seed-unabhängig.
   - Vergleichsabbildung `fig_G2_1_vergleich_a_b`; die frühere G2-Fassung (mit Ego-Linien) bleibt als `diagnostic` erhalten.
3. **Entschlackung:** vier Schriftgrößen (16/10/9/8 pt), Kurzkennung `MARES · 001-2 · vorläufig`, kurzer Titel, höchstens ein knapper Untertitel, ein kurzer Hinweis; P1/P3 mit kleinen Punkten statt farbiger Kacheln;
   Legenden ohne Fallzahlen, Klammerbemerkungen und Ortslisten. Die älteren Abbildungen (A, B1, B2, G1, C, D1, D2, E) tragen das Profil `clean` im Rahmen (`design.frame_for`, `design.lean_sections`); `analysis` bewahrt
   ihren früheren Wortlaut. Volle Provenienz und Datenqualität stehen im Register `figures_index.json` (`provenance`).
4. **Gliederung** (`figures/registry.py`): `core` / `supplementary` / `diagnostic`; Ausgabe `figures/<tier>/`, Arbeitsfassungen `figures/analysis/<tier>/`; Register mit Tier, Frage, Kodierung, Grenzen, Kandidat/Alt-Markierung.
5. **Doku:** neu `geographic-classification.md`, `ADR-0004`; angepasst `visualization-conventions.md`, `network-module.md`, README, `modules.md`.

Letzter Lauf: `C:\dev\mares\mares_workspace\runs\RUN-20261013T184525Z-bb1b40\figures\` (Pilotfall `001-2`, mit Kuratierung; 22 Kontakte, 41 bestätigte Beziehungen, 6 Gruppen; 128 Dateien).

## 3. Entscheidungen

Wissenschaftlich: fünf Stufen; geografisches Europa (Russland Europa; Türkei, Zypern, Kaukasus, Kasachstan nicht – Konvention, **nicht abgestimmt**); Überseegebiete mit ihrem Kontinent; kein Raten; Ego-Linien nur in B3;
radialer Abstand = Kategorie, nie Kilometer/Nähe/Graphdistanz; die horizontale Streckung der Zonen (1,3) ist reine Seitenformat-Konvention. Gestalterisch: Schrift DejaVu Sans, Hervorhebung „zwischen Bereichen“ als Standard,
Tönung statt Rahmen, Punkte statt Kacheln, kleinere Seite für G2-B.

**Wahl des G2-Kandidaten (Sichtprüfung am Pilotfall, nicht endgültig):**

| Maß | G2-A | G2-B |
|---|---:|---:|
| Kreuzungen | 24 | 30 |
| Knotenabstand (rel. zur mittleren Beziehungslänge) | 0,45 | 0,46 |
| Gruppenkompaktheit (kleiner = Gruppen bleiben zusammen) | 0,39 | 0,25 |

G2-A: ruhig, ID-Lesbarkeit gut, wenige Kreuzungen, bleibt aber schematisch und die Gruppen zeigen sich nur an der Höhe. G2-B: wirkt weniger schematisch, die sozialen Teilnetze bleiben als Einheiten erkennbar
(das Teilnetz über Deutschland und außerhalb Europas als Bündel dunkler Linien über die Zonengrenzen, die Marburger Gruppe kompakt), aber mehr Leerfläche und mehr Kreuzungen. **G2-B ist der Kandidat (`core`),
G2-A bleibt `supplementary`; beide Prototypen sind erhalten. Das Standardlayout bestimmt der Projektleiter.**

**Textmenge** (Zeichen aller Texte im Bild, Pilotfall, `clean` gegenüber `analysis`): B3 329 / 1634 · G2-B 391 / 1289 · P1 407 / 817 · P2 385 / 949; über alle vierzehn regulären Abbildungen 9 633 / 19 333 (−50 %). Die Kernabbildungen tragen
in `clean` rund 330–410 Zeichen: Titel, Untertitel, Legende, Hinweis, IDs, Zonennamen.

## 4. Tests (bestanden – nicht gleichbedeutend mit wissenschaftlicher Validierung)

**372 Tests bestanden** (vorher 333): neu `test_networks_geo_classification.py` (9), `test_networks_geo_network.py` (30); angepasst waren Tests, die den früheren Auftritt, die vier Kategorien oder die flache Ausgabe prüften.
Geprüft: Wien = übriges Europa, Kolumbien = außerhalb Europas, EU-unabhängiges Europa, Grenzfälle, Unbekanntes nicht geraten, konfigurierbarer Bezugspunkt, Daten unverändert; 22 Kontakte und 41 Beziehungen (synthetisch, über alle fünf Stufen);
G2 ohne Ego-Linien, genau die bestätigten Beziehungen, innerhalb/zwischen korrekt, Radius im Fenster der Zone, Namenssektor frei, Gruppenkompaktheit, deterministisch und hash-seed-unabhängig, nur lokal / nur transkontinental / sehr ungleich /
überlappende Gruppen / fehlende Wohnorte, 1 bis 100 Kontakte; Gliederung (jede Abbildung in einem Tier, ein Kandidat, Register mit Frage und Grenzen, Provenienz), beide Profile byte-reproduzierbar, `clean` kürzer als `analysis`,
`analysis` bewahrt den früheren Wortlaut. **Nicht** automatisch geprüft: Lesbarkeit und Gestaltung (Sichtprüfung am Bildschirm, nicht verkleinert/gedruckt).

## 5. Status, Einschränkungen, offen

Implementiert und getestet; wissenschaftlich **nicht** validiert. Die Abbildungen zeigen Konstellationen, keine Erklärungen; die geografische Einordnung ist kein Maß sozialer Integration oder Segregation.

- **Entscheidung beim Projektleiter:** Standard-G2 (A oder B), Konvention für Türkei/Kaukasus/Kasachstan, Standardhervorhebung „zwischen Bereichen“, Medienklassen (aus dem vorigen Lauf, Agenten-Vorschlag).
- **Grenzen:** G2-B lässt bei wenigen Kontakten viel Fläche leer; die Gruppenkompaktheit ist eine Darstellungsgröße, kein Befund; die Heimat der Erhebung ist fest Deutschland (`home_country` fehlt); der biografische Bezug ist nicht umgesetzt;
  die älteren Abbildungen sind nur im Rahmen und in den Legenden entschlackt (keine Neugestaltung); `fig_E` bleibt textreich (acht Panels).
- **Bewusste Änderungen bestehender Ausgaben:** die Kategoriewerte der kanonischen Ausgabe (`europe_other`, `outside_europe` statt `abroad`) und die Farben/Legenden der Abbildungen A, B1–B3, C, D2; frühere Läufe bleiben unverändert (`66da3a`, `d38358`).
- **Aufgeräumt:** meine fünf Zwischenläufe dieses Auftrags und `tmp/preview-g2` (exakte Namen); fremde Läufe (`7c373f`, Audio-Pilot) unberührt.
