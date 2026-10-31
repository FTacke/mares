# `network_v1` – Datenstandard, Prüfung und Standardgrafiken

**Status: implementiert und mit zwei Testfällen technisch geprüft (2026-10-31); fachlich nicht validiert.** Code:
[`src/mares/network_v1/`](../../src/mares/network_v1/__init__.py). Abgrenzung zu v0: [`network-versions.md`](network-versions.md).
Begründung: [`ADR-0005`](../decisions/ADR-0005_2026-10-31_netzwerk-v0-v1.md).

**Grundlage.** Die finalen Erhebungsbögen und der Codierschlüssel von v1 liegen **nicht** im Repository (`templates/` ist leer).
Codes und Regeln folgen den Festlegungen des Auftrags vom 2026-10-31. Sobald die Bögen vorliegen, sind sie die primäre
Spezifikation; Abweichungen werden dann hier und im Code gemeinsam geändert. Offen ist vor allem der Kontextbogen (§2.6).
Die narrativen Interviews gehören nicht zu diesem Datenmodell.

## 1. Ablauf

```text
Erhebungsbögen ──(Übertragung)──> data/*.csv + metadata.json ──> Prüfung ──> Ableitungen ──> acht Standardgrafiken
                                   (Fallordner)                   validate.py   derive.py      figures/ → graphics/
```

Die Übertragung der ausgefüllten Bögen in die CSV-Tabellen ist (noch) Handarbeit; ein Import aus einer Excel-Vorlage ist nicht gebaut.

## 2. Fallordner `mares-network-case/v1`

`<Fall>/data/`: UTF-8 (mit oder ohne BOM), Spaltentrenner `;`, Kopfzeile. Eine Zelle mit `;` steht in Anführungszeichen
(`"M;S"`). Mehrere Codes in einer Zelle: `,` oder `;` (`1, 3`); `|` ist der v0-Trenner und wird abgelehnt. Eine leere Tabelle ist
eine Kopfzeile. Beispiel: [`examples/synthetic/network_v1/002_test_synthetic/`](../../examples/synthetic/network_v1/002_test_synthetic/data/metadata.json).

| Datei | Inhalt |
|---|---|
| `metadata.json` | `format`, `dataset_version`, `case_code`, `case_type`, `provenance`, `empirical_analysis_eligible`, `survey` (`design`, `instrument_version`, `survey_date`, `data_origin`), `data_quality`, `limitations`, `description`, `field_origins` |
| `contacts.csv` | Tabelle A (§2.1) |
| `communication.csv` | Tabelle B (§2.2) |
| `groups.csv`, `group_memberships.csv`, `alter_connections.csv` | Tabelle C (§2.3) |
| `context.csv` | Kontextbogen (§2.6) |
| `places.csv` | optional: ausdrückliche Einordnung deutscher Orte (§3) |

`<Fall>/graphics/` enthält ausschließlich die fertigen Standardgrafiken (§6). Prüfberichte, Ableitungstabellen und das
Laufprotokoll liegen unter `WORKSPACE/runs/<RUN-ID>/`.

### 2.1 Tabelle A – `contacts.csv`

`contact_id; label; closeness; relation_type; contact_frequency; functions; birth_country; birth_country_iso3; residence_place;
residence_country; residence_country_iso3; comment`

| Feld | Werte |
|---|---|
| `contact_id` | `A01`, `A02`, … fortlaufend, ohne Obergrenze; eine ID = genau ein Kontakt des Falls |
| `label` | Pseudonym oder Rolle; keine Nachnamen, keine Kontaktdaten (E-Mail- oder Telefonmuster sind ein Fehler); erscheint nie in Grafiken |
| `closeness` | 1 sehr nah · 2 nah · 3 weniger nah · 4 außerhalb der Kreise; Zwischenwerte 1,5 · 2,5 · 3,5 (Komma oder Punkt). Ausdrücklich erfragt, **nie aus der Kartenposition**. Der Rohtext bleibt erhalten, gerechnet wird mit dem Zahlenwert. Eine 5 ist ein Fehler mit Hinweis auf die v0-Skala |
| `relation_type` | genau eine: 1 Familie · 2 Partner:in · 3 Freund:in · 4 Bekannte:r · 5 professioneller/institutioneller Kontakt · 6 sonstige |
| `contact_frequency` | 1 (fast) täglich · 2 wöchentlich · 3 mehrmals monatlich · 4 etwa monatlich · 5 wenige Male im Jahr oder seltener |
| `functions` | mehrere: 1 Rückhalt/Rat · 2 gemeinsame Aktivitäten/Gespräche · 3 praktische Hilfe · 4 sprachliche Hilfe/Übersetzung · 5 sonstige; **0 nichts davon ist exklusiv** |
| Geburtsland, Wohnort, Wohnland | Originalangabe als Text, daneben ISO-3166-alpha-3-Code; der Wohnortbereich wird abgeleitet (§3) |

### 2.2 Tabelle B – `communication.csv`

`contact_id; communication_forms; languages; other_languages; language_use; comment`

- `communication_forms` (mehrere): 1 persönlich · 2 Videoanruf · 3 Telefonat · 4 Sprachnachrichten · 5 Textnachrichten/Chat · 6 Sonstiges. Plattformen sind keine Kategorie.
- `languages` (mehrere): 1 Spanisch · 2 Deutsch · 3 Englisch · 4 Portugiesisch · 5 andere Sprache – mit Namen in `other_languages` (mehrere, Text).
- `language_use`: bei **genau einer** Sprache regelkonform **leer**; bei mehreren: 1–5 (überwiegende Sprache, muss eine der genannten sein), `M` regelmäßige Mischung, `S` abhängig von Situation/Medium, `M;S` beides.
- `comment`: Freitext, besonders zu `S` und „Sonstiges“.

### 2.3 Tabelle C – Gruppen und Verbindungen

- `groups.csv`: `group_id` (`C01`, …); `label` (selbst gewählt); `connection_status` T alle verbunden · P teilweise · N keine Verbindungen · NS weiß nicht; `belonging` 1 sehr stark … 5 überhaupt nicht – **nur Egos Zugehörigkeit zur Gruppe**, keine Stärke einer Kontakt-Kontakt-Beziehung.
- `group_memberships.csv`: `group_id; contact_id`; Mehrfachmitgliedschaft erlaubt.
- `alter_connections.csv`: `contact_a; contact_b; status; source; comment` mit `status` 1 bestätigt · 0 kein Kontakt · ? unbekannt; `source` z. B. die Gruppe, zu der die Aussage gemacht wurde.

### 2.4 Paarregeln ([`derive.py`](../../src/mares/network_v1/derive.py))

1. **T** setzt alle Paare der Gruppe auf 1, **N** auf 0 (Quelle `<Gruppe>:T` bzw. `:N`).
2. **P** und **NS** setzen nichts; nur ausdrücklich bestätigte oder verneinte Einzelpaare zählen, alle anderen bleiben `?`.
3. Gemeinsame Gruppenmitgliedschaft allein ist **keine** Verbindung.
4. Verbindungen zwischen Gruppen und zu ungruppierten Kontakten stehen als Einzelpaare in `alter_connections.csv`.
5. Alle Aussagen zu einem Paar werden abgeglichen: 1 neben 0 ist ein **Widerspruch** (Fehler, nie stillschweigend aufgelöst); `?` neben 1 oder 0 widerspricht nicht; gleichlautende Mehrfachangaben sind ein Hinweis.
6. Ein Paar ohne Aussage ist unbekannt, nie 0. Jedes abgeleitete Paar behält seine Quellen (`derived/pairs.csv` im Lauf).
7. Abdeckung = bestätigte + verneinte Paare von allen n(n−1)/2 Paaren; sie steht auf jeder Netzwerkgrafik.

### 2.5 Fehlende und nicht anwendbare Angaben ([`codes.py`](../../src/mares/network_v1/codes.py))

| Eintrag | Bedeutung |
|---|---|
| Wert | erhoben |
| `NS` | unbekannt (in `connection_status` ein eigener Status „weiß nicht“) |
| `KA` | keine Antwort |
| `NA` | nicht anwendbar |
| leer | nicht erhoben – außer beim Sprachgebrauch mit genau einer Sprache (regelkonform leer) |

Kein fehlender Wert wird zu 0 oder „nein“. `NS`/`KA`/`NA` stehen allein, nie neben Codes.

### 2.6 Kontextbogen – `context.csv`

Langformat `field; value; comment`; eine Mehrfachantwort ist **eine Zeile je Antwort**. Felder (vorläufig, bis der Bogen vorliegt):
`origin_country`, `age`, `stay_duration`, `migration_context`*, `residence_place`, `marburg_relation`*, `occupation`*, `housing`,
`daily_languages`*, `language_use:<Lebensbereich>`, `language_confidence:<Sprache>` (* mehrfach zulässig). Werte bleiben, wie
erhoben; Skalen des Bogens werden nicht erfunden. Kontextdaten gehen in keine Standardgrafik ein.

## 3. Geografische Zuordnung ([`places.py`](../../src/mares/network_v1/places.py))

| Darstellungsbereich | Primärkategorie | Regel |
|---|---|---|
| Marburg (Stadt) | Marburg und Mittelhessen | deutscher Wohnort = Stadt Marburg |
| übriges Mittelhessen | Marburg und Mittelhessen | Gemeinde der Landkreise Marburg-Biedenkopf, Gießen, Lahn-Dill-Kreis, Limburg-Weilburg, Vogelsbergkreis (Verzeichnis: 101 Gemeinden, Stand 2026-10) |
| übriges Deutschland | übriges Deutschland | deutsche Großstadt (> 100 000 Einwohner, alle außerhalb) oder Eintrag in `places.csv` |
| übriges Europa | übriges Europa | Wohnland in Europa nach UN-Geoschema, nicht Deutschland |
| außerhalb Europas | außerhalb Europas | jedes andere gültige Wohnland |
| nicht zuordenbar | – | kein oder ungültiger Ländercode; deutscher Ort ohne Treffer; mehrdeutiger Ortsname („Neustadt“, „Weimar“); regionale Angabe („Nähe Marburg“) |

Nichts wird geraten: Ein deutscher Ort, der weder im Verzeichnis noch unter den Großstädten steht (auch ein Stadtteil wie
„Wehrda“), braucht einen Eintrag in `places.csv` (`residence_place; area; basis` mit `area` ∈ `marburg`,
`mittelhessen_other`, `germany_other` und einer Begründung). Die Originalangaben bleiben unverändert; Bereich und Grundlage stehen in
`derived/contacts.csv`. Groß-/Kleinschreibung, ß/ss und ö/oe werden nicht unterschieden.

## 4. Prüfung ([`validate.py`](../../src/mares/network_v1/validate.py))

| Stufe | Wirkung | Beispiele |
|---|---|---|
| Fehler | keine Grafiken; Status `FAILED` | doppelte oder ungültige Kontakt-/Gruppen-IDs; unbekannte IDs in Gruppen oder Paaren; ungültige Codes; 0 neben anderen Funktionen; Nähe außerhalb 1–4/halbe Schritte; widersprüchliche Paaraussagen; Selbstpaare; fehlende Pflichtdateien/-spalten; ungültiges JSON; überwiegende Sprache nicht unter den Sprachen; Kontaktdaten in der Bezeichnung; v0-Spalten, v0-Dateien, `dataset_version: network_v0`, Nähe 5; inkonsistente Metadaten (Testfall als empirisch, `case_type`/`provenance`/Ordner passen nicht) |
| Warnung | Grafiken entstehen, mit Hinweis | nicht erhobene Angaben (je Feld zusammengefasst); Wohnort nicht zuordenbar; fehlender Gruppenstatus oder fehlende Zugehörigkeit; Gruppe mit < 2 Mitgliedern; mehrere Sprachen ohne Sprachgebrauch; Sprachgebrauch bei genau einer Sprache; fehlende Tabelle-B-Zeile; fehlende Dokumentation eines empirischen Falls; unbekannte Kontextfelder |
| Hinweis | nur Bericht | gleichlautende Mehrfachaussagen; P-Gruppe ohne Einzelaussagen; ungenutzter `places.csv`-Eintrag; Geburtsland ohne Code |

## 5. Wissenschaftliche Regeln der Grafiken

Nur erhobene oder regelbasiert eindeutig ableitbare Werte; keine Kante aus bloßer Gruppenzugehörigkeit; unbekannte Paare erscheinen nicht als
„kein Kontakt“, und jede Netzwerkgrafik nennt die Abdeckung; persönliche Nähe und geografischer Bereich bleiben getrennte Achsen; Nähe,
Häufigkeit und Zugehörigkeit in ihrer Codierrichtung (1 = am nächsten/häufigsten/stärksten oben bzw. am stärksten); ordinale Codes als
Kategorien, nie als Messachse; Mehrfachnennungen erhalten und mehrfach gezählt; „ohne Angabe“ getrennt von „nein“ bzw. „0 · nichts davon“;
gleiche Farben, Legenden und Skalen für alle Fälle (Bereiche: Blautöne für Marburg/Mittelhessen, hellblau übriges Deutschland, Orangetöne
außerhalb; Beziehungstypen: eigene Farben); keine Namen; kleine Fallzeile (Fallcode, Kontakte, Gruppen, Datenstatus) und bei Testfällen das
Kennzeichen „TESTFALL · FIKTIVE DATEN“; Layoutkennzahlen sind keine Befunde. Layouts sind deterministisch (gleiche Daten → byteidentische Dateien).

## 6. Die acht Standardgrafiken ([`figures/`](../../src/mares/network_v1/figures/__init__.py))

Datei: `<Fallcode>_<Grafikcode>_<Bezeichnung>.png` (optional zusätzlich `.svg`), z. B. `002_test_synthetic_G1_persoenliches_netz.png`.
Fehlen die Daten einer Grafik, entsteht keine Datei; der Lauf nennt den Grund (`figures_index.json`).

| Code | Datei | Eingänge | Darstellung |
|---|---|---|---|
| G1 | `G1_persoenliches_netz` | A: Nähe, Beziehungstyp; C: bestätigte Paare | Ego im Zentrum, Abstand = erhobene Nähe (Ringe 1–4, Zwischenwerte gestrichelt), Farbe = Beziehungstyp; nur der Winkel ist ein reproduzierbares Layout; Kontakte ohne Nähe außerhalb der Ringe; Kanten, die nahe an Ego vorbeiführen, sind gebogen |
| G2 | `G2_geografisches_netz` | A: Wohnort/Wohnland; C: bestätigte Paare | Bänder je Bereich (Breite ∝ √Kontaktzahl), Kanten im Bereich durchgezogen, über Bereiche gestrichelt gebogen; **keine Ego-Linien**; Kontakte ohne bestätigte Verbindung in einer eigenen unteren Zeile |
| P1 | `P1_wohnort_naehe` | A: Bereich, Nähe | Punktmatrix, Zeilen 1 · 1,5 · … · 4 (1 oben), Kontakt-IDs, Spalte „nicht zuordenbar“ und Zeile „keine Angabe“ nur bei Bedarf |
| P2 | `P2_wohnort_haeufigkeit` | A: Bereich, Häufigkeit | Punktmatrix, Zeilen 1–5 als Kategorien |
| P3 | `P3_wohnort_kommunikation` | A: Bereich; B: Formen | Matrix „k von n“, Schattierung = Anteil, n = Kontakte des Bereichs mit Angabe, Zeile „ohne Angabe“ |
| P4 | `P4_wohnort_sprachen` | A: Bereich; B: Sprachen, andere Sprachen | wie P3; benannte andere Sprachen einzeln (höchstens drei, Rest „weitere“), M/S nicht dargestellt |
| P5 | `P5_funktionen_naehe` | A: Funktionen, Nähe | Punktmatrix Funktionen 1–5 × Nähe; Mehrfachfunktionen mehrfach; „0 · nichts davon“ und „keine Angabe“ abgesetzt |
| G3 | `G3_gruppen_zugehoerigkeit` | C: Gruppen, Mitglieder, Status, Zugehörigkeit, bestätigte Paare | links Gruppenkarte (Umrandungen um die Mitglieder, eingebettete Gruppen gestrichelt, Mehrfachmitglieder mit Farbring, Nichtmitglieder werden aus fremden Umrandungen geschoben, ungruppierte Kontakte außen), rechts Ego → Gruppen mit Linienstärke = Zugehörigkeit, Kreisgröße/Zahl = Mitglieder |

Ausgelegt und an den Testfällen geprüft für bis zu 32 Kontakte und 6 Gruppen; für 30–40 Kontakte vorgesehen, mit mehr als 40 nicht geprüft.

## 7. Testfälle und empirische Fälle

| Fall | `case_type` | `provenance` | `empirical_analysis_eligible` | Herkunft |
|---|---|---|---|---|
| `001_test_v0_fictionalized` | `test` | `v0_derived_fictionalized` | `false` | Struktur des v0-Pilotfalls, umcodiert und fiktionalisiert ([`network-versions.md`](network-versions.md) §4); nur im Storage-Root, nie im Repository |
| `002_test_synthetic` | `test` | `fully_synthetic` | `false` | erfunden; Quelle im Repository, erwartete Eigenschaften in `tests/test_network_v1_case002.py` |

**Empirisch** ist ein Fall nur mit `dataset_version: network_v1`, `case_type` `pilot` oder `regular`, `provenance: survey` und
`empirical_analysis_eligible: true` ([`case.is_empirical`](../../src/mares/network_v1/case.py)); Übersichten und Fallzahlen verwenden
ausschließlich diesen Filter (`v1 list --empirical`, `run.empirical_cases`). Der Validator lehnt Widersprüche ab (Testfall als empirisch,
synthetische Herkunft als Pilot, Testfall unter `cases/`).

**Weg vom Pilot zum regulären Fall.** Ein echter v1-Pilot entsteht unter `pilots/<NNN_kurzname>/` mit `case_type: pilot`,
`provenance: survey`, vollständigem `survey`-Block (Design `network_v1`, Instrument-Version, Erhebungsdatum, Datenherkunft),
`data_quality` und `limitations`; ob er empirisch auswertbar ist, entscheidet eine Person (`empirical_analysis_eligible`). Reguläre
Erhebungen liegen unter `cases/` mit `case_type: regular` und demselben Datenmodell. Prüfstatus und Läufe stehen in den Run-Records.

## 8. Befehle

```text
.venv\Scripts\python -m mares.networks v1 validate --case INTAKE:network_v1/pilots/<Fall>
.venv\Scripts\python -m mares.networks v1 render   --case INTAKE:network_v1/pilots/<Fall> [--formats png,svg]
.venv\Scripts\python -m mares.networks v1 render-all --root INTAKE [--formats png,svg]
.venv\Scripts\python -m mares.networks v1 list --root INTAKE [--empirical]
.venv\Scripts\python -m mares.networks v1 install-test-cases --root INTAKE [--v0-package INTAKE:inbox/<Lieferung>/contents]
```

Fälle nur aus `INTAKE` oder `PRIMARY`. `render` ersetzt in `graphics/` genau die Standarddateien des Falls und löscht nichts; fremde Dateien
werden im Run-Record gemeldet. `install-test-cases` ersetzt nur Testfälle. Exit-Status 0 erledigt, 2 Prüffehler, 1 nicht startbar.
