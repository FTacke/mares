# Run-Bericht 2026-10-13 – Visualisierungsdesign und analytische Perspektiven P1–P3

Journal eines Laufs, keine Spezifikation. Maßgeblich sind [`visualization-conventions.md`](../architecture/visualization-conventions.md) §3.4–3.6 und
[`network-module.md`](../architecture/network-module.md) §7. Ortsangaben beschreiben den Projektarbeitsplatz. Dieser Bericht enthält keine
Forschungsdaten; Kennzahlen sind Zählungen.

## 1. Ziel und Scope

Ein einheitliches Visualisierungsdesign (Profile `clean` und `analysis`) für die Netzwerkabbildungen; B3 und G2 als Designreferenzen überarbeiten; drei
analytische Perspektiven ergänzen – **P1** räumliche Einordnung × subjektive Nähe, **P2** sprachliche Praktiken in sozialen Teilgruppen, **P3** Wohnort ×
Kontakthäufigkeit × Medien. Nicht Teil: narrative Interviews, Verknüpfung mit Episoden, Änderung der Instrumente, Datenmigration, neue Kennzahlen, neue
Infrastruktur. Kein Commit, kein Push. Reale Analysen nur unter `WORKSPACE`; keine Forschungsdaten im Repository.

## 2. Durchgeführte Änderungen (implementiert)

| Bereich | Änderung |
|---|---|
| Designsystem | neu `figures/design.py` (Konstanten, `clean_frame`, `legend_strip`, `zone_name`, `stamp_text`, Profile), `figures/figure_notes.py` (Frage, Kodierung, Grenzen je Abbildung) |
| B3 | `ego_network.py`: `DrawStyle`, Profil `clean` (größere Zeichnung, kompakte Legende, ein Hinweis, kurzer Titel „Persönliches Beziehungsnetz“); Profil `analysis` = bisherige B3, byteidentisch |
| G2 | `geo_zones.py`: `_bands_clean` (Bänder direkt beschriftet, größere Fläche, einzeilige Linienlegende), konfigurierbare Hervorhebung `highlight` (`between` / `within` / `None`), benannte Linienkollektionen |
| P1, P3 | `figures/perspectives.py`: Matrix Wohnort-Kategorie × Nähe bzw. Kontakthäufigkeit, Chips je Kontakt, Medien als Symbole (●▲■), `matrix_cells` testbar, Hervorhebungsmenge `highlight` |
| P2 | `perspectives.py`: B2/B3-Layout, `LanguageView` (`mode`, `mode:<c>`, `lang:<c>`, `multilingual`), Ring für mehrere Sprachen, Ego–Kontakt-Linie in Sprachfarbe |
| Hilfen | `network.py`: `place_labels(font_pt, node_pt)`, `draw_groups(tag_pt, node_pt, …)` parametrisierbar |
| Pipeline | `run.py`: `FigureOptions`, `DESIGN_FIGURES`, Profilordner (`figures/analysis/`), `figures_index.json` (`mares-figures-index/v0-draft`), Optionen im `run_record.json`; `cli.py`: `--profiles`, `--language-view`, `--tie-highlight` |
| Doku | `visualization-conventions.md` (§3.4–3.6, Tabellen), `network-module.md` (§7, Code-Karte), `README.md`, `modules.md` |

Die Ausgabe: sechzehn Abbildungen in `figures/` (A, B1, B2, B0, B3, B3_0, G1, G2_0, G2, P1, P2, P3, C, D1, D2, E), davon B3, G2, P1–P3 zusätzlich als `analysis`-Fassung.
Letzter Lauf: `C:\dev\mares\mares_workspace\runs\RUN-20261013T140037Z-d38358\figures\` (Pilotfall `001-2`, mit Kuratierung; 22 Kontakte, 41 bestätigte Beziehungen, 6 erhobene Gruppen).

## 3. Entscheidungen

Wissenschaftlich (Details und Begründung: Konventionen §3.5/3.6): Wohnort als Kategorie, nicht Kilometer; Nähe nur als erhobener Tabellenwert, fehlende Werte als eigene Zeile „nicht erfasst“;
Matrix statt Ringbild für P1/P3; Sprachmodus und genannte Sprachen getrennt; Sprache gehört zur Ego–Kontakt-Beziehung (färbt Kontakte und Ego-Linien, nie Kontakt–Kontakt-Linien); Mehrsprachigkeit bleibt;
Medien sind Mehrfachangaben, die Häufigkeit gilt nicht je Medium; Hervorhebung ändert nie Position oder Beziehung.

Gestalterisch: Schrift **DejaVu Sans** (Source Sans 3 nicht verfügbar, keine Schrift ins Repository); Tokens zentral in `design.py`; **Standardhervorhebung in G2 = „zwischen Bereichen“**
(Agenten-Vorschlag, konfigurierbar; das Projektteam sollte sie bestätigen oder ändern); Medienklassen (persönlich = Code 1, Telefon = 4, digital = 2, 3, 5, 6, 7) als **Agenten-Vorschlag** in `perspectives.MEDIA_CLASSES`
nach dem Codebuch des Pilotpakets – bei einer anderen Instrumentversion zu prüfen; kürzere Statuszeile im Profil `clean`.

Korrektur an einer bestehenden Abbildung: `place_labels` berücksichtigte die Knotengröße nicht; die Beschriftungsplatzierung folgt jetzt dem übergebenen Knotendurchmesser. Dadurch änderte sich einmalig die
Zeichnung von `fig_B3_0_layoutvergleich` im Detail (Arbeitsabbildung); alle anderen bestehenden Abbildungen (A, B1, B2, B0, G1, G2_0, C, D1, D2, E) sind byteidentisch (getestet bzw. verglichen).

## 4. Tests (bestanden – nicht gleichbedeutend mit wissenschaftlicher Validierung)

- Gesamtlauf: **333 Tests bestanden** (vorher 289), davon 44 neue in `tests/test_networks_design_perspectives.py`.
- Angepasst wurden bestehende Tests, die den alten Standardauftritt von B3/G2 prüften (Texte jetzt mit `profile="analysis"`, Linienkollektionen über Labels statt Zeichenreihenfolge; Abbildungszahl 13 → 16 bzw. 10 → 14).
- Neu geprüft: Profile und Zonennamen; `clean` knapper als `analysis` bei gleichen Daten; Titel kurz; B3-`clean` mit gleichen Positionen, Gruppen und Beziehungen wie `analysis`;
  G2-Hervorhebung ändert Stärke/Farbe/Reihenfolge, nie Segmente (41 Beziehungen bleiben, Ego-Linien bleiben die schwächsten); jeder Kontakt in genau einer Matrixzelle; „nicht erfasst“; leere Zeilen sichtbar;
  Medienklassen; Sprachansichten (Mehrdeutigkeit, unbekannt ≠ nicht genannt); P2 gleiche Positionen in allen Ansichten und wie B3; konfigurierbarer Bezugsort statt „Marburg“; 1, 2, 3, 40, 100 Kontakte; alle Merkmale fehlend;
  überlappende Gruppen; Byte-Reproduzierbarkeit, auch zwischen Prozessen (Hash-Seed 1, 2, 3); bestehende Abbildungen unverändert; kein Freitext; `figures_index.json`, `FigureOptions`, CLI.

## 5. Sichtprüfung (Pilotfall, nicht Teil der automatischen Tests)

Geprüft wurden B3, G2 (Hervorhebung zwischen/innerhalb), P1, P2 (`mode`, `lang:1`, `multilingual`) und P3, jeweils `clean`, P3/P1 auch `analysis`. Behoben wurden: Legendenbezeichnungen mit „(ungefähre Angabe)“, zu hohe Zeichenflächen,
zu schwacher Kontrast von Ego- und zurückgenommenen Linien, Höhe von G2, Beschriftungsformulierungen. Offene Kleinigkeit: In P2 liegen bei G04/G06 die Gruppenbeschriftungen nahe bei A05 (Überlappung der Gruppen im Layout, kein Fehler).
Die Lesbarkeit im verkleinerten Zustand (Folie/Druck) wurde nur am Bildschirm geprüft.

## 6. Status, Einschränkungen, nächste Schritte

Implementiert und getestet; wissenschaftlich **nicht** validiert – die Abbildungen machen Konstellationen sichtbar und behaupten keine Ursachen; ein Fall trägt keine Inferenz.
Offen: Bestätigung der Medienklassen und der Standardhervorhebung durch das Projektteam; Übernahme des Designs in A, B1/B2, C–E (bewusst nicht Teil); Ergänzung der Kontakt-IDs-Hervorhebung in P2/G2, falls später
einzelne Kontakte gezeigt werden sollen; die Schrift *Source Sans 3*, falls sie verteilt werden soll; Paarabdeckung des Pilotfalls ist weiter nicht bestätigt (siehe frühere Berichte). Narrative Verknüpfungen sind nicht angelegt.
