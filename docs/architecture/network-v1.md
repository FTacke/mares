# `network_v1` – Datenstandard, Prüfung und Standardgrafiken

**Status: implementiert und mit zwei Testfällen technisch geprüft (2026-10-31, Gestaltung überarbeitet am selben Tag, G1–G3
nachgeschärft nach [`ADR-0007`](../decisions/ADR-0007_2026-10-31_netzwerk-v1-g1-g3.md), G1/G3 abgeschlossen nach
[`ADR-0008`](../decisions/ADR-0008_2026-10-31_netzwerk-v1-g1-sektoren-g3-beschriftung.md), Karte X1 als neunte Standardgrafik seit
[`ADR-0016`](../decisions/ADR-0016_2026-11-05_netzwerk-v1-x1-kanonisch.md), 2026-11-05; G4 und G5 nach Geburtsland als zehnte und elfte
seit [`ADR-0022`](../decisions/ADR-0022_2026-11-06_netzwerk-v1-g4-g5-kanonisch.md), 2026-11-06); fachlich nicht validiert.** Code:
[`src/mares/network_v1/`](../../src/mares/network_v1/__init__.py). Abgrenzung zu v0: [`network-versions.md`](network-versions.md).
Begründung: [`ADR-0005`](../decisions/ADR-0005_2026-10-31_netzwerk-v0-v1.md), Gestaltung:
[`ADR-0006`](../decisions/ADR-0006_2026-10-31_netzwerk-v1-gestaltung.md).

**Grundlage.** Maßgeblich ist die leere Erhebungsvorlage
[`templates/network_v1/05_MARES_Netzwerk_Tabelle_v1.pdf`](../../templates/network_v1/05_MARES_Netzwerk_Tabelle_v1.pdf) (Tabellen A, B, C,
Erweiterungsblätter A+ und B+, Codierschlüssel; Instrument-Version `INS-netzwerk-tabelle@v1`). Die Codelisten stehen einmal, im Code
([`codes.py`](../../src/mares/network_v1/codes.py)); dieses Dokument beschreibt Regeln und verweist auf die Vorlage, statt die Listen zu
wiederholen. Der Kontextbogen ist nicht Teil der Vorlage; seine Felder bleiben vorläufig (§2.6). Die narrativen Interviews gehören nicht
zu diesem Datenmodell.

## 1. Ablauf

```text
Erhebungsbögen ──(Übertragung)──> data/*.csv + metadata.json ──> Prüfung ──> Ableitungen ──> elf Standardgrafiken
                                   (Fallordner)                   validate.py   derive.py      figures/ → graphics/
```

Die Übertragung der ausgefüllten Bögen in die CSV-Tabellen ist (noch) Handarbeit; ein Import aus einer Excel-Vorlage ist nicht gebaut.

## 2. Fallordner `mares-network-case/v1`

`<Fall>/data/`: UTF-8 (mit oder ohne BOM), Spaltentrenner `;`, Kopfzeile. Eine Zelle mit `;` steht in Anführungszeichen
(`"M;S"`). Mehrere Codes in einer Zelle: `,` oder `;` (`1, 3`); `|` ist der v0-Trenner und wird abgelehnt. Eine leere Tabelle ist
eine Kopfzeile. Beispiel: [`examples/synthetic/network_v1/002_test_synthetic/`](../../examples/synthetic/network_v1/002_test_synthetic/data/metadata.json).

| Datei | Inhalt |
|---|---|
| `metadata.json` | `format`, `dataset_version`, `case_code`, `case_type`, `provenance`, `empirical_analysis_eligible`, `survey` (`design`, `instrument_version`, `survey_date`, `data_origin`), `data_quality`, `limitations`, `description`, `field_origins`, `closing` (§2.3), optional `display_code` (§5.6) und `corpus` (§7) |
| `contacts.csv` | Tabelle A (§2.1) |
| `communication.csv` | Tabelle B (§2.2) |
| `groups.csv`, `group_memberships.csv`, `alter_connections.csv` | Tabelle C (§2.3) |
| `context.csv` | Kontextbogen (§2.6) |
| `places.csv` | optional: ausdrückliche Einordnung deutscher Orte (§3) |

`<Fall>/graphics/` enthält ausschließlich die fertigen Standardgrafiken (§6), je Format genau eine Datei je Grafik. Ältere
Ein Fallordner enthält nur `data/` und `graphics/`; experimentelle Ausgaben haben derzeit keinen Ort im Fallordner (die früheren
`<Fall>/experimental/`-Bestände von X1 und G3 nach Geburtsland sind nach deren Kanonisierung entfernt, ADR-0022). Prüfberichte, Ableitungstabellen und das
Laufprotokoll liegen unter `WORKSPACE/runs/<RUN-ID>/`.

### 2.1 Tabelle A – `contacts.csv`

`contact_id; label; closeness; relation_type; contact_frequency; functions; birth_country; birth_country_iso3; residence_place;
residence_country; residence_country_iso3; comment`

| Feld | Werte |
|---|---|
| `contact_id` | `A01`, `A02`, … fortlaufend, ohne Obergrenze; eine ID = genau ein Kontakt des Falls |
| `label` | Pseudonym oder Rolle; keine Nachnamen, keine Kontaktdaten (E-Mail- oder Telefonmuster sind ein Fehler); erscheint nie in Grafiken |
| `closeness` | 1–4, Zwischenwerte als `1,5`/`2,5`/`3,5` (Komma oder Punkt) **oder** wie auf dem Bogen als Spanne `1–2`/`2–3`/`3–4`. Ausdrücklich erfragt, **nie aus der Kartenposition**. Der Rohtext bleibt erhalten, gerechnet wird mit dem Zahlenwert. Eine 5 ist ein Fehler mit Hinweis auf die v0-Skala |
| `relation_type` | ein Code 1–6 (der Bogen fragt nur die Hauptbeziehung). Sind auf dem Bogen ausdrücklich mehrere Codes eingetragen, bleiben sie erhalten (Warnung `relation_type_several`; Darstellung als geteilter Knoten, in G1 ein eigener Sektor direkt nach dem ersten Typ; [`ADR-0026`](../decisions/ADR-0026_2026-11-09_netzwerk-v1-mehrere-beziehungstypen-und-student-pilot-ls-gh-jz.md)) |
| `contact_frequency` | ein Code 1–5, 1 = am häufigsten |
| `functions` (Bogen: „Bedeutung“) | mehrere Codes 1–5; **0 „Nichts davon“ ist exklusiv**; bei 5 „Sonstiges“ wird eine Erläuterung in `comment` erwartet (Hinweis) |
| Geburtsland, Wohnort, Wohnland | Originalangabe als Text, daneben ISO-3166-alpha-3-Code; der Wohnortbereich wird abgeleitet (§3) |

### 2.2 Tabelle B – `communication.csv`

`contact_id; communication_forms; languages; other_languages; language_use; comment`

- `communication_forms` (mehrere Codes 1–6). Plattformen sind keine Kategorie; ein Telefonat (auch über WhatsApp) bleibt ein Telefonat.
- `languages` (mehrere Codes 1–5). Code 5 „Andere Sprache“ wird benannt: auf dem Bogen im Kommentar, im Fallordner als eigene Spalte
  `other_languages` (mehrere, Text) – eine Übertragungskonvention, damit benannte Sprachen auswertbar bleiben.
- `language_use`: bei **genau einer** Sprache regelkonform **leer** (ableitbar); bei mehreren: 1–5 (überwiegende Sprache, muss eine der
  genannten sein), `M`, `S` oder `M;S`.
- `comment`: Freitext. Bei `S` und bei Kommunikation 6 „Sonstiges“ erwartet der Bogen eine Erläuterung; fehlt sie, gibt es einen Hinweis.

### 2.3 Tabelle C – Gruppen und Verbindungen

- `groups.csv`: `group_id` (`C01`, …); `label` (selbst gewählt); `connection_status` T alle verbunden · P teilweise · N keine Verbindungen · NS weiß nicht; `belonging` 1 sehr stark … 5 überhaupt nicht – **nur Egos Zugehörigkeit zur Gruppe**, keine Stärke einer Kontakt-Kontakt-Beziehung.
- `group_memberships.csv`: `group_id; contact_id`; Mehrfachmitgliedschaft erlaubt.
- `alter_connections.csv`: `contact_a; contact_b; status; source; comment` mit `status` 1 bestätigt · 0 kein Kontakt · ? unbekannt; `source` z. B. die Gruppe, zu der die Aussage gemacht wurde. Hierher gehören die Ausnahmen bei P und die „Weiteren Verbindungen“ des Bogens.
- `metadata.closing` = Block ABSCHLUSS von Tabelle C: `n_contacts`, `n_groups`, `contact_naming` (`completed` | `ended_early`),
  `ended_early_reason`, `connections` (`complete` = vollständig geklärt | `partial` = teilweise ungeklärt). Die Zahlen werden mit den
  übertragenen Tabellen verglichen; „vollständig geklärt“ neben unbekannten Paaren innerhalb von Gruppen ist eine Warnung. Für Pilot- und
  reguläre Fälle ist der Block zu dokumentieren.

### 2.4 Paarregeln ([`derive.py`](../../src/mares/network_v1/derive.py))

1. **T** setzt alle Paare der Gruppe auf 1, **N** auf 0 (Quelle `<Gruppe>:T` bzw. `:N`).
2. **P** und **NS** setzen nichts; nur ausdrücklich bestätigte oder verneinte Einzelpaare zählen, alle anderen bleiben `?`.
3. Gemeinsame Gruppenmitgliedschaft allein ist **keine** Verbindung.
4. Verbindungen zwischen Gruppen und zu ungruppierten Kontakten stehen als Einzelpaare in `alter_connections.csv`.
5. Alle Aussagen zu einem Paar werden abgeglichen: 1 neben 0 ist ein **Widerspruch** (Fehler, nie stillschweigend aufgelöst); `?` neben 1 oder 0 widerspricht nicht; gleichlautende Mehrfachangaben sind ein Hinweis.
6. Ein Paar ohne Aussage ist unbekannt, nie 0. Jedes abgeleitete Paar behält seine Quellen (`derived/pairs.csv` im Lauf).
7. Abdeckung = bestätigte + verneinte Paare von allen n(n−1)/2 Paaren; sie steht im Prüfbericht (`validation_report.md`, „Abdeckung der Kontaktpaare“) und im Run-Record (`coverage`), nicht in den Grafiken (§5.7).

### 2.5 Fehlende und nicht anwendbare Angaben ([`codes.py`](../../src/mares/network_v1/codes.py))

| Eintrag | Bedeutung |
|---|---|
| Wert | erhoben |
| `NS` | die befragte Person weiß es nicht (in `connection_status` ein eigener Status „No sabe“) |
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
| Warnung | Grafiken entstehen, mit Hinweis | nicht erhobene Angaben (je Feld zusammengefasst); Wohnort nicht zuordenbar; fehlender Gruppenstatus oder fehlende Zugehörigkeit; Gruppe mit < 2 Mitgliedern; mehrere Sprachen ohne Sprachgebrauch; Sprachgebrauch bei genau einer Sprache; fehlende Tabelle-B-Zeile; fehlende Dokumentation eines empirischen Falls (auch `closing`); Abschlusszahlen weichen von den Tabellen ab; unbekannte Kontextfelder |
| Hinweis | nur Bericht | gleichlautende Mehrfachaussagen; P-Gruppe ohne Einzelaussagen; ungenutzter `places.csv`-Eintrag; Geburtsland ohne Code; erwartete Erläuterung fehlt (Funktion 5, Kommunikation 6, `S`); vorzeitig beendet ohne Grund |

## 5. Gestaltung der Grafiken

Alles Gemeinsame steht an einer Stelle: [`figures/base.py`](../../src/mares/network_v1/figures/base.py). Begründung der Festlegungen:
[`ADR-0006`](../decisions/ADR-0006_2026-10-31_netzwerk-v1-gestaltung.md).

### 5.1 Wissenschaftliche Regeln

Nur erhobene oder regelbasiert eindeutig ableitbare Werte; Linien nur für bestätigte Paare, nie aus bloßer Gruppenzugehörigkeit; eine fehlende
Linie heißt nicht „kein Kontakt“ (die Abdeckung der Paare steht im Prüfbericht und Run-Record); persönliche Nähe und Wohnortbereich bleiben getrennte Achsen;
ordinale Codes als Kategorien in Codierrichtung (1 oben bzw. am stärksten), nie als Messachse; Mehrfachnennungen mehrfach gezählt; fehlende
Angaben getrennt von „nein“ und von „0 · Nichts davon“; keine Namen; Layouts deterministisch (gleiche Daten → byteidentische Dateien);
Layoutlagen haben keine Bedeutung.

### 5.2 Seite

Titel oben links (ohne Grafikcode, kein Untertitel), Fallkennzeichnung oben rechts, darunter die Hauptdarstellung (sie bekommt den
Großteil der Fläche), eine der zwei Legenden, höchstens zwei kurze Hinweise, eine Fußzeile `MARES · network_v1 · <n> Kontakte` (§5.7).
Die Herkunft eines Werts steht in dieser Dokumentation, nicht in Achsenbeschriftungen. Schriftgrößen,
Knoten- und Punktgrößen und Abstände sind Konstanten in `base.py`.

### 5.3 Farben

| Aufgabe | Festlegung |
|---|---|
| Beziehungstyp (Knoten und Punkte in G1, G2, G3, P1, P2, P5) | 1 Familie `#D55E00` · 2 Partner:in `#CC79A7` · 3 Freund:in `#009E73` · 4 Bekannte:r `#56B4E9` · 5 Professionell / institutionell `#0072B2` · 6 Sonstige Beziehung `#6B7280` (Okabe-Ito, Grau für die Restkategorie); feiner neutraler Rand; ohne Angabe: weiß, gepunkteter Rand |
| Wohnortbereiche, Gruppenflächen, Ortsflächen | nur sehr helle Hintergründe; sie konkurrieren nie mit den Knotenfarben |
| Gruppen in G3 | gedämpfte Umrissfarben nur zur Unterscheidung, eine einheitliche Linienbreite; die Zugehörigkeit steht als Punktskala in der Beschriftung (§6) |
| Zugehörigkeitsskala in G3 | fünf kleine Punkte gleicher Größe und gleichen Abstands, nur umrandet (grau); der erhobene Wert als ein gefüllter neutral-dunkler Punkt, daneben die Zahl; keine Füllstände, keine Farbintensität; erklärt einmal in der Legende |
| Anteile in P3/P4 | eine ruhige Blauskala; Spalten mit n = 1 neutral |

Farbe bedeutet in Knoten immer nur den Beziehungstyp – nie Region, Nähe oder Stärke.

### 5.4 Legenden

Genau zwei Layouts: `side` (senkrecht rechts, G1) und `bottom` (waagerecht unter der Grafik, alle übrigen). Reihenfolge, Bezeichnungen und
Farben der Beziehungstypen sind überall gleich und stammen aus `codes.RELATION_TYPE`. **Die Beziehungstyp-Legende zeigt nur die Typen,
die im Fall vorkommen** – in der festen Reihenfolge der Tabelle A, jeder Typ mit seiner festen Farbe, unabhängig davon, welche anderen
vorkommen; ein Typ, den kein Kontakt des Falls hat, entfällt. Kontakte ohne gültigen Beziehungstyp werden keinem Typ zugeschlagen: weißer
Knoten mit gepunktetem Rand und der Eintrag „keine Angabe“. Ermittelt einmal je Fall in der gemeinsamen Komponente
(`base.relation_entries`), gleich für G1, G2, G3, P1, P2, P5 und X1; Knotenfarben und Grafik bleiben davon unberührt
([`ADR-0017`](../decisions/ADR-0017_2026-11-05_netzwerk-v1-dynamische-beziehungstyp-legende.md)). P3/P4 zeigen in der
Legende die Farbskala.

### 5.5 Geografie in Grafiken

Fünf Darstellungsbereiche in fester Reihenfolge Marburg (Stadt) → übriges Mittelhessen → übriges Deutschland → übriges Europa → außerhalb
Europas; die ersten beiden tragen die gemeinsame Klammer „Marburg und Mittelhessen“. Vor „außerhalb Europas“ steht ein etwas größerer
Abstand – ein Kategorienschritt, keine Entfernung. **„Nicht zuordenbar“ ist keine Region:** keine Spalte, kein gleichrangiges Band. In den
Matrizen wird der Kontakt in einem Hinweis genannt („Wohnort nicht zuordenbar: A22.“). In G2 gilt dasselbe für Kontakte ohne bestätigte
Verbindung; hat ein solcher Kontakt bestätigte Verbindungen, steht er unter den Bändern in einer Zeile ohne Fläche und Rahmen („Wohnort
nicht zuordenbar:“), damit keine Verbindung verloren geht – die Legende nennt diese Linien („zwischen Bereichen · ohne Bereich“).

### 5.6 Fallkennzeichnung und Dateinamen

Oben rechts, aus den Metadaten: Testfälle `TESTFALL <Nummer>* · SYNTHETISCH` bzw. `· FIKTIONALISIERT` (rot hinterlegt), echte Fälle
`FALL · <display_code>` oder, ohne `display_code`, `FALL · MARES-<Nummer>`. Nie ein Name, nie der lange Ordnername. Dateien:
`<Fallcode>_<Grafikcode>_<Bezeichnung>.png` (optional `.svg`).

### 5.7 Redaktionelle Regeln für alle elf Grafiken

Begründung: [`ADR-0018`](../decisions/ADR-0018_2026-11-05_netzwerk-v1-redaktioneller-standard.md); jeder sichtbare Text mit Herkunft:
[`network-v1-visualization-text-inventory.md`](network-v1-visualization-text-inventory.md).

- **Titel** nur inhaltlich, aus einer Tabelle (`base.TITLES`, dieselbe für das Register); die Codes G1 … X1 stehen in Register,
  Dateinamen, Metadaten und Dokumentation, nie im sichtbaren Titel. **Kein Untertitel.**
- **Fußzeile** einheitlich `MARES · network_v1 · <n> Kontakte` (alle erfassten Kontakte des Falls). Gruppenzahl, Datenqualität,
  Prüfstatus und Provenienz stehen in Metadaten, Prüfbericht und Run-Record; Testfälle kennzeichnet das Fallkennzeichen.
- **Fehlende Angaben** heißen überall `keine Angabe`; Kontakte, die mangels Wohnortbereich nicht dargestellt werden, nennt
  `Wohnort nicht zuordenbar: <IDs>.`, in X1 `Wohnort nicht darstellbar: <IDs>.` (auch Orte ohne Ortsverzeichniseintrag). Hinweise
  erscheinen nur, wenn die Bedingung zutrifft.
- **Legenden** erklären Zeichen, keine Methode. Die Heatmap-Legende von P3/P4 ist eine gemeinsame Definition (`base.HEAT_LEGEND`) und
  nennt die Bezugsgröße („n = Kontakte mit Angabe im jeweiligen Wohnortbereich“).
- **Methodische Erläuterungen** stehen hier, nicht in den Grafiken. Sie gelten unverändert, auch wo die Grafik sie nicht mehr nennt:
  - G1: Abstand zu Ego = persönliche Nähe; die Winkelbereiche ordnen nach Beziehungstyp, die Lage innerhalb eines Sektors hat keine
    Bedeutung (§6).
  - G2, P1–P4: Wohnortbereiche sind Kategorien, keine Entfernungen; persönliche Nähe und Wohnort sind getrennte Merkmale (§5.1, §5.5).
  - G2, G3: Linien zeigen bestätigte Paare; eine fehlende Linie heißt nicht „kein Kontakt“; gemeinsame Gruppenmitgliedschaft ist keine
    Verbindung (§2.4). Die Abdeckung der Paare (bestätigt, verneint, unbekannt) steht im Prüfbericht und im Run-Record.
  - G3: Die Punktskala zeigt genau den erhobenen Wert der Zugehörigkeit, eine einzelne Selbsteinschätzung, nicht die interne Vernetzung.
  - P2: Kontakthäufigkeit ist eine geordnete Kategorie; Zeilenabstände sind keine gemessenen Zeitabstände.
  - P3/P4: fehlende Angaben stehen getrennt und zählen nie als „nein“; P4: Mehrsprachige zählen in jeder Sprache.
  - P5: Ein Kontakt erscheint in jeder seiner Funktionsspalten.
  - X1: Panels mit eigenem Maßstab; Kontakte schematisch neben dem Ortspunkt; „und Umgebung“ nach dem Ortsverzeichnis (§6.1).

## 6. Die elf Standardgrafiken ([`figures/`](../../src/mares/network_v1/figures/__init__.py))

Fehlen die Daten einer Grafik, entsteht keine Datei; der Lauf nennt den Grund (`figures_index.json`). Die Grafikfunktionen lesen
Skalen, Kategorien, Farben und Bereichsnamen aus einem **Versionsprofil** (`base.Scheme`; für v1 die hier beschriebenen Werte); `network_v0`
nutzt dieselben Funktionen G1, G2, P1–P5, G3 und X1 mit seinem eigenen Profil ([`network-module.md`](network-module.md) §7.1). Gemeinsame Bausteine: Punktmatrix
(P1, P2, P5: gleiche Punkt- und Beschriftungsgröße, Kontakte einer Zelle nebeneinander und in Zeilen, nie überlappend) und Heatmap (P3, P4).
Reihenfolge im Register: G1, G2, P1, P2, P3, P4, P5, G3, X1, G4, G5. Alle sichtbaren Texte der elf Grafiken mit Herkunft und Bedingung:
[`network-v1-visualization-text-inventory.md`](network-v1-visualization-text-inventory.md) (Iststand, Grundlage der redaktionellen Prüfung).

| Code | Datei | Darstellung | Legende |
|---|---|---|---|
| G1 | `G1_persoenliches_netz` | **nur Nähe und Beziehungstyp, keine Kontakt-Kontakt-Linien** (die zeigen G2 und G3). Ego im Zentrum, Abstand = erhobene Nähe (Ringe 1–4 durchgezogen, 1,5/2,5/3,5 gestrichelt); **Winkelsektoren nach Beziehungstyp**: feste Folge Familie, Partner:in, Freund:in, Bekannte:r, Professionell/institutionell, Sonstige, (keine Angabe), gegen den Uhrzeigersinn ab der Ringbeschriftung oben; Sektorbreite ∝ Zahl der Kontakte des Typs, fehlende Typen ohne Breite, aber an ihrem Platz in der Folge; auf jedem Ring die Kontakte eines Typs über ihren Sektor verteilt (ID-Reihenfolge) und nur so weit auseinandergeschoben, dass sich keine Knoten berühren (Reihenfolge bleibt). Keine Sektorlinien, keine Hintergrundflächen. Nur der Winkel ist Layout, kein Kontakt wird auf einen anderen Nähewert verschoben; Ringzahlen bleiben frei; Kontakte ohne Nähe auf einem äußeren Bogen (nur bei Bedarf). Legende „Persönliche Nähe“: „1 sehr nah · 2 nah · 3 weniger nah · 4 außerhalb der Kreise“ und „Zwischenwerte: 1,5 · 2,5 · 3,5“; kein Hinweis (die Lesart steht in §5.7) | side |
| G2 | `G2_geografisches_netz` | Bänder je Bereich (Breite folgt der Kontaktzahl); darin **geografische Untergruppen**: übriges Mittelhessen und übriges Deutschland nach Wohnort, Ausland nach Wohnland – mehrere Kontakte in einer hellen, fein umrandeten Fläche mit „Ort · Anzahl“ darüber, ein einzelner Kontakt ohne Fläche mit dem Ortsnamen darüber; Marburg ohne weitere Untergliederung. Verbundene Kontakte einer Untergruppe liegen auf einer Ellipse (keine Linie läuft durch einen dritten Knoten). Sitzen drei oder mehr Untergruppen nebeneinander, steht jede zweite tiefer (keine Linie durch einen fremden Knoten, keine Ortsbeschriftung auf einer Linie). Linien im Bereich durchgezogen, zwischen Bereichen dünn, hell, gestrichelt. Unbekannte Wohnorte: nie ein Band (§5.5). Untere Zone: Kontakte ohne bestätigte Verbindung (keine Aussage über tatsächliche Kontakte). Untergruppen sind nur gemeinsame Geografie, keine sozialen Gruppen | bottom |
| P1 | `P1_wohnort_naehe` | Punktmatrix Bereich × Nähe (1, 1,5 … 4; „keine Angabe“ nur bei Bedarf) | bottom |
| P2 | `P2_wohnort_haeufigkeit` | derselbe Baustein, Zeilen = Kontakthäufigkeit 1–5 | bottom |
| P3 | `P3_wohnort_kommunikation` | Heatmap; Zelle = Anzahl der Kontakte, Farbe = Anteil an n des Bereichs; 0 = leere weiße Zelle; Spalte mit n = 1 neutral; Zeilen ohne Codes, visuell gegliedert (persönlich · synchron auf Distanz: Video, Telefon · asynchron: Sprach-, Textnachrichten · weitere Formen), keine Summen; „keine Angabe“ nur wenn vorhanden; Legende: Farbintensität, Zahl, n = 1, Bezugsgröße n (§5.7) | bottom (Farbskala) |
| P4 | `P4_wohnort_sprachen` | derselbe Baustein; Zeilen Spanisch, Deutsch, Englisch, Portugiesisch und **jede** benannte weitere Sprache; M/S bleiben im Datenmodell, ohne eigene Grafik | bottom (Farbskala) |
| P5 | `P5_funktionen_naehe` | Punktmatrix Funktionen × Nähe, Bezeichnungen ohne Codes, n je Spalte; „Nichts davon“ und „keine Angabe“ nur, wenn sie vorkommen, abgesetzt | bottom |
| G3 | `G3_gruppen_zugehoerigkeit` | **eine** große Gruppenkarte: Kontakte als Knoten, die von Ego benannten Gruppen als Umrandungen mit heller Fläche; alle Umrandungen gleich stark. Beschriftung als Block aus zwei Zeilen: `C04 · <Bezeichnung> (3)` und darunter `○●○○○ 2` – **fünfstufige Punktskala** (1 links … 5 rechts), genau der erhobene Wert gefüllt, daneben die Zahl; kein „Zugehörigkeit“, keine verbalen Stufen, kein „Kontakte“ je Gruppe (die Legende erklärt die Skala einmal: „Zugehörigkeit: 1 sehr stark – 5 überhaupt nicht“). Ohne Wert kein Punkt gefüllt, statt der Zahl das Kürzel des Fehlens (`KA`, `NS`, `NA`, `n. e.`), in der Legende aufgelöst. Die Bezeichnung erscheint wie erhoben, nur ohne Testdaten-Zusatz („(fiktive Bezeichnung)“, „(synthetisch)“) und bei mehr als 34 Zeichen gekürzt – nur in der Darstellung, die Daten bleiben unverändert. Die Skala zeigt eine einzelne Selbsteinschätzung, nicht die interne Vernetzung. **Platzierung:** der Block liegt unmittelbar außerhalb der eigenen Umrandung (Kandidaten rundum in festem Abstand), nicht auf Knoten, Verbindungen, anderen Beschriftungen, Umrandungslinien oder fremden Gruppenflächen; die Flächen der Gruppen, die eine eingebettete Gruppe umschließen, zählen für deren Beschriftung nicht als fremd. Ist kein naher Platz frei, verbindet eine kurze feine Linie in der Gruppenfarbe Block und Umrandung (deren Kreuzungen mit fremden Umrandungen zählen mit). Links und rechts der Karte bleibt Platz für Beschriftungen am Rand. Eine ganz in anderen liegende Gruppe bekommt eine engere Umrandung und keinen eigenen Ankerplatz (ihre Mitglieder liegen in der Schnittfläche der umgebenden Gruppen). Farbige Ringe nur für Mehrfachmitglieder, deren Mitgliedschaften die Umrandungen nicht schon zeigen (nicht bei eingebetteten Gruppen). Nichtmitglieder werden aus fremden Umrandungen geschoben; ungruppierte Kontakte mit Verbindungen außen, ohne Gruppe und ohne Verbindung in einer Zeile unten („keiner Gruppe zugeordnet, keine bestätigte Verbindung:“). T/P/N/NS wirken nur über die abgeleiteten Linien | bottom |
| X1 | `X1_geografische_verteilung` | Karte: wo die Kontakte leben – Panels Amerika · Europa (ohne Deutschland) · Deutschland (weitere Regionen bei Bedarf), Ortspunkt an der wahren Lage, die Kontakte daneben nach Beziehungstyp gefärbt, keine Verbindungslinien; Einzelheiten §6.1 | bottom |
| G4 | `G4_gruppen_geburtsland` | die Gruppenkarte von G3 unverändert (Kontakte, Gruppen, Verbindungen, Positionen, Umrisse, Beschriftung), Knotenfarbe = Geburtsland, im Knoten A-ID und ISO-Kürzel; Einzelheiten §6.2 | bottom |
| G5 | `G5_lokale_gruppen_geburtsland` | dieselbe Darstellung für die Kontakte mit Wohnortbereich Marburg (Stadt) oder übriges Mittelhessen (Filter, kein Positionsprinzip), kompakt angeordnet; ein Hinweis „Lokaler Ausschnitt: n von N Kontakten (Marburg und Mittelhessen).“; Einzelheiten §6.2 | bottom |

Ausgelegt und an den Testfällen geprüft für 22 und 32 Kontakte mit 5–6 Gruppen; für 30–40 Kontakte vorgesehen, mit mehr nicht geprüft.

**Experiment, kein Standard:** eine kartografische Variante von G2 (Amerika, Europa, Ausschnitt Mittelhessen) liegt als Pilotskript unter
[`pilots/network_v1_map/`](../../pilots/network_v1_map/README.md); sie läuft nur mit dem synthetischen Testfall 002, schreibt nur nach
`WORKSPACE/runs/` und gehört nicht zu den Standardgrafiken.

### 6.1 X1 – Geografische Verteilung des persönlichen Netzwerks

Code: [`figures/maps.py`](../../src/mares/network_v1/figures/maps.py). Seit
[`ADR-0016`](../decisions/ADR-0016_2026-11-05_netzwerk-v1-x1-kanonisch.md) Standardgrafik; entwickelt als experimentelle Zusatzgrafik in
den Fassungen 1 bis 2.8 ([`ADR-0010`](../decisions/ADR-0010_2026-11-05_netzwerk-v1-experimentelle-grafik-x1.md),
[`ADR-0011`](../decisions/ADR-0011_2026-11-05_netzwerk-v1-x1-fassung-2.md),
[`ADR-0012`](../decisions/ADR-0012_2026-11-05_netzwerk-v1-x1-fassung-2-1.md),
[`ADR-0013`](../decisions/ADR-0013_2026-11-05_netzwerk-v1-x1-zentren-und-laender.md),
[`ADR-0014`](../decisions/ADR-0014_2026-11-05_netzwerk-v1-x1-regionale-ortsgruppen.md),
[`ADR-0015`](../decisions/ADR-0015_2026-11-05_netzwerk-v1-x1-ortspunkt-frei.md); Verlauf in den Run-Berichten unter
`docs/agent-runs/2026-11-05_network-v1-*x1*`). Entsteht mit `render`/`render-all` wie jede Standardgrafik als
`<Fall>/graphics/<Fallcode>_X1_geografische_verteilung.png|svg`.

**Kartenquellen.** Der Fallauf liest vor dem Anlegen des Run-Ordners das Ortsverzeichnis `ROOT:network_v1/reference/gazetteer.csv`
(im Root des Falls) und die Basiskarte `WORKSPACE:cache/basemaps/ne_50m_admin_0_countries.geojson` und vermerkt beide mit SHA-256 unter
`map_sources` im Run-Record und in `figures_index.json`. Fehlt eine Datei, wird X1 übersprungen (`skipped`, Grund „Ortsverzeichnis
fehlt (…)“ bzw. „Basiskarte fehlt (…)“), nie aus einer anderen Quelle gezeichnet; eine fehlerhafte Datei stoppt den Lauf. Basiskarte:
Natural Earth, 1:50m Cultural Vectors, Admin 0 – Countries (gemeinfrei, <https://www.naturalearthdata.com/>; Nutzungsbedingungen:
<https://www.naturalearthdata.com/about/terms-of-use/>), einmalig in den regenerierbaren Cache geladen (Befehl in
[`pilots/network_v1_map/README.md`](../../pilots/network_v1_map/README.md)). Die Grafik nennt knapp „Kartengrundlage: Natural Earth.“

**Texte.** Titel „Geografische Verteilung des persönlichen Netzwerks“ ohne Grafikcode, kein Untertitel; Fallkennzeichnung wie bei
allen Grafiken (§5.6). Legende: Beziehungstypen (gemeinsame Komponente) und „Wohnort (Ortspunkt)“, bei Bedarf „○ weiterer Ort einer
Ortsgruppe“ und „nur Wohnland bekannt (Lage unscharf)“. Hinweise nur „Wohnort nicht darstellbar: A22.“ (wenn Kontakte nicht gezeichnet
werden können) und „Kartengrundlage: Natural Earth.“ Fußzeile „MARES · network_v1 · {n} Kontakte“ – ohne Gruppenzahl und ohne
Datenqualität, auch bei authentischen Fällen: Datenstatus und Prüfung stehen in den Metadaten und Run-Records. Die folgenden
methodischen Festlegungen (eigene Maßstäbe der Panels, schematisch daneben gesetzte Kontakte, Zusammenfassung benachbarter Orte) stehen
nur hier, nicht in der Grafik.

| Code | Datei | Inhalt | Legende |
|---|---|---|---|
| X1 | `X1_geografische_verteilung` (Fassung 2.8) | **Wo leben die Kontakte?** Kartenpanels von links nach rechts Amerika · Europa (ohne Deutschland) · Deutschland, immer alle drei, oben bündig; **Deutschland ist das größte Panel**, die übrigen sind 0,8-mal so hoch. **Ausschnitte nach den Daten:** Umriss aller Orte des Panels plus Rand, mindestens eine Orientierungsgröße (Amerika 30° × 30°, Europa 13° × 10°, Deutschland 9° × 7,5°), Seitenverhältnis 0,65–1,5; Deutschland bleibt im Deutschland-Rahmen; ein Panel ohne Kontakte zeigt seinen Standardausschnitt (Amerika: Mexiko bis Südamerika, Europa: Portugal bis etwas östlich von Deutschland). Panels haben eigene Maßstäbe; Entfernungen sind zwischen Panels nicht vergleichbar (steht nicht in der Grafik). Weitere Weltregionen (Afrika, Asien, Ozeanien, Weitere) nur bei Bedarf zwischen Amerika und Europa. Zuordnung über den Wohnortbereich (§3): Deutschland, übriges Europa, sonst Kontinent des Wohnlands. **Keine Kontakt-Kontakt- und keine Ego-Linien**; Knotenfarbe = Beziehungstyp. **Ortspunkt** (dunkel, weiß umrandet) **an der wahren Lage, immer sichtbar**; die Kontakte stehen **daneben** auf einer sehr hellen Fläche (bis 10 ein Ring, sonst Ringe zu 6, 12, …; nach Ort und Beziehungstyp sortiert), mit einer feinen Linie an den Ortspunkt angebunden – auch ein einzelner Kontakt. **Fläche und Label bilden ein Callout:** das Label dockt direkt am Rand der Fläche an (Ortsname fett, Land und Zahl kompakt in derselben Zeile, z. B. „Bogotá · Kolumbien · n = 3“, ein einzelner Kontakt ohne Zahl; Einzelorte einer Gruppe kleiner und grauer darunter; bei Bedarf zweizeilig), ohne Rahmen, nur mit weißem Halo und einer sehr blassen, weich gerundeten Fläche. X1 zeigt die geografische Verteilung, nicht exakte Kontaktpositionen. **„… und Umgebung“** (Darstellungsentscheidung, maßstabsabhängig): Ein Ort kommt zu dem Ort, dem ihn das Ortsverzeichnis in `group_with` zuordnet (Stadtteil, Umlandgemeinde oder Nachbarstadt eines größeren Ortes; zentral gepflegt und begründet), wenn dieser Ort im selben Panel Kontakte hat, höchstens 40 km Luftlinie entfernt ist und beide Punkte im Panel weniger als etwa 15 mm auseinanderliegen – auf einem größeren Maßstab bleiben sie getrennt; eine Stufe, keine Ketten; ohne Zuordnung bleibt jeder Ort für sich, weiter entfernte Städte werden nie zusammengefasst. Die Kontakte stehen nach Ort sortiert im Ring; die wahren Punkte der weiteren Orte bleiben als kleine hohle Ringe sichtbar. Kasten „Marburg und Umgebung · n = 14“, darunter klein und heller die Einzelorte („Marburg 10 · Cölbe · …“). **Land im Kasten:** außerhalb Deutschlands „Bogotá · Kolumbien · n = 3“ bzw. „Madrid · Spanien“, im Deutschland-Panel nur der Ort; keine Länderbeschriftung auf der Karte. Die Gruppierung ist eine Darstellungsentscheidung; die erhobenen Wohnorte bleiben unverändert. **Platzierung mit Vorrang** (je Panel Ort für Ort, größte zuerst; **Fläche und Label werden gemeinsam platziert**: die Fläche kommt an die nächstgelegene zulässige Position, an der ihre vollständige Beschriftung unmittelbar am Kreis frei Platz findet – benachbarte Gruppen werden dafür auseinandergezogen, die Ortspunkte nie; danach eine Nachbesserungsrunde für alle Labels): (1) Ortspunkte und Ortsnamen bleiben frei – keine Fläche, kein Knoten und kein Label auf einem Ortspunkt (auch nicht auf den hohlen Ringen weiterer Orte einer Gruppe), kein Knoten und keine Fläche auf einem Label; (2) Ortsgruppen sauber getrennt – Flächen überlappen nicht, Linien kreuzen sich nicht und laufen nicht unter Flächen, Labels oder über fremde Ortspunkte; (3) **geografische Leserichtung**, soweit layoutseitig vermeidbar: Bei nahen Orten (Punkte im Panel unter etwa 38 mm auseinander) kehren weder Flächen noch Labels eine klare Nord-Süd- oder West-Ost-Relation um (klar = Versatz mindestens 1,5-mal so groß wie quer dazu; ein nördlicherer Ort wird nicht unter einem südlicheren beschriftet), bei diagonal zueinander liegenden Orten nicht die Gesamtrichtung; dafür werden auch die Flächen umgesetzt, und ein früh gesetzter Ort lässt die Seite der noch folgenden Nachbarn frei. Eine Umkehrung wiegt etwa 5 cm zusätzliche Linienlänge auf, nie ein verdecktes Element; (4) erst dann möglichst nah am Ortspunkt. Jedes Label liegt – von seiner Mitte aus gemessen – näher an der eigenen Fläche als an jeder fremden. Linien und Punkte liegen über allen Flächen, die Knoten oben. Asymmetrische Positionen ergeben sich aus diesen Regeln, nicht aus Ortsnamen; Titel bei Bedarf zweizeilig (Ort / Land und Zahl); Seitenverhältnis eines Panels mindestens 0,8. Nur Wohnland bekannt: Länderpunkt der Basiskarte, gestrichelte Fläche, „· nur Land bekannt“, nie eine erfundene Stadt. Nicht zuordenbarer Wohnort und Ort ohne Eintrag im Ortsverzeichnis: nicht gezeichnet, gemeinsam genannt („Wohnort nicht darstellbar: …“). Koordinaten nur aus dem Ortsverzeichnis `ROOT:network_v1/reference/gazetteer.csv` (`place; country_iso3; lat; lon; basis; group_with`, `group_with` = zugeordneter Ort derselben Länderangabe oder leer, von Hand gepflegt, im Root der Fälle, nie im Repository, kein Geocoding-Dienst); Basiskarte Natural Earth 1:50m (gemeinfrei) in `WORKSPACE/cache/basemaps/`. Frühere Entwicklungsstände sind nicht mehr als Dateien vorhanden (entfernt nach ADR-0022), nachvollziehbar über ADRs und Run-Berichte | bottom |

### 6.2 G4 und G5 – Gruppenstruktur nach Geburtsland (gesamt und lokal)

Code: [`figures/birth_country.py`](../../src/mares/network_v1/figures/birth_country.py). Seit
[`ADR-0022`](../decisions/ADR-0022_2026-11-06_netzwerk-v1-g4-g5-kanonisch.md) Standardgrafiken; entwickelt als Experiment
([`ADR-0019`](../decisions/ADR-0019_2026-11-06_netzwerk-v1-experiment-g3-geburtsland.md) bis
[`ADR-0021`](../decisions/ADR-0021_2026-11-06_netzwerk-v1-g3-herkunft-zwei-ansichten.md)). Original-G3 (Farbe nach Beziehungstyp) bleibt
unverändert; G4 und G5 nutzen dieselbe Gruppenlogik.

- **Grundlage:** die G3-Implementierung selbst. Layout, Umrisse, Umrissfarben, Beschriftung, Zugehörigkeitsskala und Ringsegmente
  bleiben; nur die Knotenfarbe ist das erhobene Geburtsland (`birth_country_iso3`, in der Legende der erhobene Name). Keine Ableitung
  von Nationalität, ethnischer Zugehörigkeit oder Selbstidentifikation, keine zusätzlichen Verbindungen oder Mitgliedschaften.
- **Knoten:** A-ID (fett) und darunter kleiner das ISO-3166-Alpha-3-Kürzel; Knoten 22 statt 20 pt, keine Beschriftung außerhalb.
  Die Schriftfarbe ist Schwarz oder Weiß, je nachdem, was den höheren Kontrast hat (mindestens 4,5:1 bei jeder Länderfarbe).
  - Ohne Angabe (leer, NS/KA/NA): weißer Knoten mit gepunktetem Rand und `k. A.`, nie ein erfundener Code.
  - Ein genanntes, aber nicht codiertes Land: neutrales Grau, `–`, in der Legende „Name (nicht codiert)“.
- **Farben:** fest je ISO-Code (`COUNTRY_COLORS`), in jedem Fall und beiden Ansichten gleich, nie nach Reihenfolge oder Häufigkeit
  vergeben.
  - DEU, COL, PER, MEX, ECU, CHL, CUB, VEN, ESP und ARG unterscheiden sich paarweise bei normalem Sehen deutlich (OKLab-ΔE ≥ 16).
  - Unter Protan-/Deutan-Simulation ist VEN/ESP mit ΔE 6,1 das knappste Paar. Das ist nur mit zweiter Kennzeichnung zulässig, und
    die leistet das Kürzel im Knoten.
  - Zehn weitere Länder (BRA, BOL, URY, PRY, DOM, GTM, ITA, GBR, FRA, POL) sind ebenfalls fest zugeordnet.
  - Jeder andere Code erhält über seinen Code eine der Ergänzungsfarben (`EXTENSION`). Keine davon ist die Farbe eines festen Landes
    (ΔE ≥ 10). Zwei solche Länder können sich eine Farbe teilen; das Kürzel trennt sie.
  - Keine graue Sammelkategorie, keine Flaggen- oder Symbolfarben; die Beziehungstyp-Palette bleibt unberührt.
- **Legende** unter dem Netzwerk, mit kompaktem Zeilenumbruch. Sie nennt jedes dargestellte Land einzeln („Peru (PER)“), in fester
  Reihenfolge: die festen Länder in obiger Folge, dann die übrigen nach Code, `keine Angabe` zuletzt. In der Lokalansicht stehen nur
  die lokal dargestellten Länder darin. Dazu kommen Zugehörigkeitsskala, bestätigte Verbindung und, falls vorhanden,
  Mehrfachmitgliedschaft.
- **G4** (`Gruppenstruktur nach Geburtsland`): Kontakte, Gruppen, bestätigte Verbindungen und Positionen wie G3. Übersprungen ohne
  Gruppen („keine Gruppen erhoben“) oder ohne ein einziges erhobenes Geburtsland („kein Geburtsland erhoben“).
- **G5** (`Lokale Gruppenstruktur nach Geburtsland`): ein geografisch gefilterter Ausschnitt des persönlichen Netzwerks,
  keine Darstellung der lokalen Bevölkerung oder Gemeinschaft. Übersprungen wie G4 und zusätzlich ohne lokalen Kontakt oder ohne
  Gruppe mit lokalem Mitglied.
  - **Auswahl:** nur Kontakte mit Wohnortbereich Marburg (Stadt) oder übriges Mittelhessen (§3). Der Wohnort ist nur Filter, nie
    Position; keine Zonen, keine Karten.
  - **Teilnetz:** Mitgliedschaften und bestätigte Verbindungen sind auf die dargestellten Kontakte beschränkt. Gruppen ohne lokales
    Mitglied entfallen (nur im Register genannt, s. u.). Gruppen-IDs und Umrissfarben bleiben die des Falls.
  - **Zahlen:** Das Gruppenlabel nennt lokale und gesamte Mitgliederzahl, wo sie sich unterscheiden (`(5 von 7)`). Ein einziger
    Hinweis: „Lokaler Ausschnitt: n von N Kontakten (Marburg und Mittelhessen).“ Die Fußzeile zählt alle Kontakte des Falls.
  - **Was fehlt und warum:** nicht in der Grafik, sondern im G5-Eintrag von `figures_index.json` und `run_record.json` (`details`:
    nicht dargestellte Kontakte je Wohnortbereich, nicht zuordenbare Wohnorte, Gruppen ohne lokales Mitglied, teilweise dargestellte
    Gruppen).
  - **Kompakte Anordnung:** Das G3-Layout läuft auf dem Teilnetz. Teile ohne gemeinsame Verbindung oder Gruppe rücken zusammen,
    rechts oder unterhalb, je nachdem, was näher am Seitenverhältnis der Fläche liegt; ihr Abstand hat keine Bedeutung. Innerhalb
    eines Teils bleibt alles wie im G3-Layout.
  - **Fläche:** Sie richtet sich nach dem Teilnetz: typischer Nachbarabstand höchstens 0,8 Zoll, bei Bedarf auf den Inhalt
    verschmälert, mindestens 8,6 × 4,6 Zoll. Die Knoten werden dabei nicht größer.
- **Dateien:** `<Fall>/graphics/<Fall>_G4_gruppen_geburtsland.{png,svg}` und `<Fall>_G5_lokale_gruppen_geburtsland.{png,svg}`, wie
  alle Standardgrafiken.

## 7. Testfälle und empirische Fälle

| Fall | `case_type` | `provenance` | `empirical_analysis_eligible` | Herkunft |
|---|---|---|---|---|
| `001_test_v0_fictionalized` | `test` | `v0_derived_fictionalized` | `false` | Struktur des v0-Pilotfalls, umcodiert und fiktionalisiert ([`network-versions.md`](network-versions.md) §4); nur im Storage-Root, nie im Repository |
| `002_test_synthetic` | `test` | `fully_synthetic` | `false` | erfunden; Quelle im Repository, erwartete Eigenschaften in `tests/test_network_v1_case002.py` |

**Empirisch** ist ein Fall nur mit `dataset_version: network_v1`, `case_type` `pilot` oder `regular`, `provenance: survey` und
`empirical_analysis_eligible: true` ([`case.is_empirical`](../../src/mares/network_v1/case.py)); Übersichten und Fallzahlen verwenden
ausschließlich diesen Filter (`v1 list --empirical`, `run.empirical_cases`). Der Validator lehnt Widersprüche ab (Testfall als empirisch,
synthetische Herkunft als Pilot, Testfall unter `cases/`).

**Getrenntes Korpus `student_pilot`** ([`ADR-0009`](../decisions/ADR-0009_2026-11-04_netzwerk-v1-korpus-student-pilot.md)).
Authentische studentische Peer-Pilotfälle (methodische Piloten mit Studierenden, nicht die Studienpopulation) liegen unter
`network_v1/student_pilot/<NNN_kurzname>/` mit `corpus: student_pilot`, `case_type: pilot`, `provenance: survey` und
`empirical_analysis_eligible: false`. `NNN` zählt die Fälle des Korpus, der Kurzname ist das pseudonyme Kürzel der befragten Person
(z. B. `001_mt`); Kürzel der erhebenden Person und Formularcode stehen im `survey`-Block. Der Validator lehnt Abweichungen ab (Ordner und
`corpus` passen nicht, anderer `case_type`, `empirical_analysis_eligible: true`); `case.is_empirical` schließt jeden Fall mit `corpus` aus.
Die Fälle werden wie alle anderen geprüft und gerendert, die Kennzeichnung oben rechts kommt aus `display_code` (z. B.
`FALL · STUDENT_PILOT MT`), nie eine Testrahmung. Fallübergreifende Auswertungen des Korpus sind nicht gebaut. Stand 2026-11-09: vier
Fälle (`001_mt`, `002_ls`, `003_gh`, `004_jz`); der Einwilligungsstatus steht je Fall in `survey.consent`.

**Weg vom Pilot zum regulären Fall.** Ein echter v1-Pilot entsteht unter `pilots/<NNN_kurzname>/` mit `case_type: pilot`,
`provenance: survey`, vollständigem `survey`-Block (Design `network_v1`, Instrument-Version, Erhebungsdatum, Datenherkunft),
`data_quality` und `limitations`; ob er empirisch auswertbar ist, entscheidet eine Person (`empirical_analysis_eligible`). Reguläre
Erhebungen liegen unter `cases/` mit `case_type: regular` und demselben Datenmodell. Prüfstatus und Läufe stehen in den Run-Records.

## 8. Befehle

```text
.venv\Scripts\python -m mares.networks v1 validate --case INTAKE:network_v1/pilots/<Fall>    (ebenso cases/, student_pilot/)
.venv\Scripts\python -m mares.networks v1 render   --case INTAKE:network_v1/pilots/<Fall> [--formats png,svg]
.venv\Scripts\python -m mares.networks v1 render-all --root INTAKE [--formats png,svg]
.venv\Scripts\python -m mares.networks v1 list --root INTAKE [--empirical]
.venv\Scripts\python -m mares.networks v1 install-test-cases --root INTAKE [--v0-package INTAKE:inbox/<Lieferung>/contents]
```

Fälle nur aus `INTAKE` oder `PRIMARY`. `render` ersetzt in `graphics/` genau die elf Standarddateien des Falls und löscht nichts; fremde Dateien
werden im Run-Record gemeldet. `install-test-cases` ersetzt nur Testfälle. Exit-Status 0 erledigt, 2 Prüffehler, 1 nicht startbar.
