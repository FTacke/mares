# Textinventar der elf Standardgrafiken von network_v1 – Ist-Stand

Bestandsaufnahme **aller sichtbaren Texte** der Standardgrafiken G1–G5, P1–P5 und X1, aus dem Quellcode
extrahiert. Das Dokument beschreibt den implementierten Stand, es ist keine Vorgabe; maßgeblich für Inhalt und
Regeln bleibt [`network-v1.md`](network-v1.md) §5 und §6.

Stand: redaktionelle Vereinheitlichung vom 2026-11-05
([`ADR-0018`](../decisions/ADR-0018_2026-11-05_netzwerk-v1-redaktioneller-standard.md)), ergänzt um G4 und G5 am 2026-11-06
([`ADR-0022`](../decisions/ADR-0022_2026-11-06_netzwerk-v1-g4-g5-kanonisch.md)). Die vorige Fassung (Iststand
vor der Vereinheitlichung) ist über Git nachvollziehbar. Zeilenangaben gelten für diesen Stand und verschieben sich bei
späteren Änderungen; die genannten Funktionen und Konstanten bleiben der Anker.

**Konventionen**

- Codeorte als `Pfad:Zeile`, relativ zum Repository; `base.py` = `src/mares/network_v1/figures/base.py`,
  ebenso `networks.py`, `matrices.py`, `maps.py`, `birth_country.py`, `__init__.py`; `codes.py` und `places.py` liegen in
  `src/mares/network_v1/`.
- `\n` in einem Wortlaut = Zeilenumbruch in der Grafik; `{platzhalter}` = dynamischer Teil; „statisch“ = fester
  Wortlaut im Code.
- Beispiele nur neutral oder aus den Testfällen (Testfall `002_test_synthetic`, 32 Kontakte; für X1 die erfundenen
  Orte des synthetischen Ortsverzeichnisses der Tests); keine Angaben aus authentischen Fällen.
- Grau („MUTED“) oder kursiv wird angegeben, wo der Code einen Text so auszeichnet.

---

## A. Gemeinsame Texte und Regeln

### A.1 Seitenaufbau (gemeinsame Komponente `base.page`, `base.py:333`)

| Element | Wortlaut / Muster | Herkunft / Bedingung |
|---|---|---|
| Titel | der Titel der Grafik aus `TITLES` (fett, 16 pt, oben links), **ohne Grafikcode** | `TITLES`, `base.py:98-108`; `page(ctx, code, …)` setzt `TITLES[code]`. Dieselbe Tabelle liefert die Titel im Register (`__init__.py`, `FigureSpec.title`). |
| Untertitel | – (keiner, in keiner Grafik) | Der Kopf ist einheitlich niedrig (`HEADER_H = 0.62`, `base.py:51`). |
| Fallkennzeichen oben rechts | siehe A.2 | `case_badge`, `base.py:170` |
| Hinweiszeilen | je Grafik, siehe Teil B; leere Hinweise entfallen, höchstens zwei | `page`; unten links über der Fußzeile, 8 pt |
| Fußzeile | siehe A.3 | `footer_line`, `base.py:180` |
| Legende | Abschnitte `(Titel, Einträge)`; `side` (rechts, nur G1) oder `bottom` (unter dem Hauptbereich, alle übrigen) | `draw_legend`; Abschnittstitel fett, Einträge der Art `text` grau; Abschnitte ohne Einträge entfallen |

### A.2 Fallkennzeichen (`case_badge`, `base.py:170-178`)

`number` = die ersten drei Zeichen von `case_code`; Testfall = `metadata.case_type == "test"`.

| Variante | Wortlaut | Bedingung | Gestaltung |
|---|---|---|---|
| Testfall, vollsynthetisch | `TESTFALL {number}* · SYNTHETISCH` – z. B. `TESTFALL 002* · SYNTHETISCH` | `provenance == "fully_synthetic"` | weiße Schrift auf rotem Grund |
| Testfall, aus v0 fiktionalisiert | `TESTFALL {number}* · FIKTIONALISIERT` | `provenance == "v0_derived_fictionalized"` | wie oben |
| Testfall, sonstige Provenienz | `TESTFALL {number}* · FIKTIV` | jeder andere `provenance`-Wert | wie oben |
| Authentischer Fall mit Anzeigecode | `FALL · {display_code}` | kein Testfall, `display_code` gesetzt | schwarze Schrift, weißer Grund, dunkler Rahmen |
| Authentischer Fall ohne Anzeigecode | `FALL · MARES-{number}` | `display_code` fehlt oder leer | wie oben |

### A.3 Fußzeile (`footer_line`, `base.py:180-183`) – in allen elf Grafiken gleich

| Element | Wortlaut / Muster | Herkunft / Bedingung |
|---|---|---|
| Fußzeile | `MARES · network_v1 · {n} Kontakte` – z. B. `MARES · network_v1 · 32 Kontakte` | `{n}` = alle Kontakte des Falls (`len(case.contacts)`, auch solche ohne zuordenbaren Wohnort). Keine Gruppenzahl, keine Datenqualität, kein Prüfstatus; diese stehen in Metadaten und Run-Records. Keine Singularform („1 Kontakte“ möglich). |

### A.4 Legende „Beziehungstyp“ (`relation_section` / `relation_entries`, `base.py:113-127`)

Verwendet in G1, G2, G3, P1, P2, P5 und X1 (nicht in P3, P4), überall über `relation_section`. **Dynamisch:** nur die
Beziehungstypen, die mindestens ein Kontakt des Falls mit gültigem Code hat, in der festen Reihenfolge der Tabelle A
und mit fester Farbe ([`ADR-0017`](../decisions/ADR-0017_2026-11-05_netzwerk-v1-dynamische-beziehungstyp-legende.md));
ermittelt über alle Kontakte des Falls, nicht je Grafik.

| Eintrag | Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Abschnittstitel | `Beziehungstyp` | `relation_section`, `base.py:125-127` (ein Literal) |
| Code 1–6 | `Familie`, `Partner:in`, `Freund:in`, `Bekannte:r`, `Professionell / institutionell`, `Sonstige Beziehung` | `codes.RELATION_TYPE` (`codes.py:58-65`); je Eintrag nur, wenn im Fall vorhanden |
| fehlender Beziehungstyp | `keine Angabe` (weißer Punkt, gepunkteter Rand) | nur wenn mindestens ein Kontakt des Falls keinen gültigen Typ hat (alle Fehlarten zusammen; geprüft über alle Kontakte, auch nicht gezeichnete) |

### A.5 Kontakt-IDs

| Element | Wortlaut / Muster | Herkunft / Bedingung |
|---|---|---|
| ID im Netzwerkknoten (G1, G2, G3, X1) | `{contact_id}` (z. B. `A01`), fett, 7 pt | `draw_nodes`; Schriftfarbe nach Kontrast |
| ID und Geburtslandkürzel im Knoten (G4, G5) | `{contact_id}` (fett, 7 pt), darunter `{iso3}` (5,4 pt) – z. B. `A07` / `PER`; ohne Angabe `k. A.`, genannt aber nicht codiert `–` | `_code_nodes`, `birth_country.py`; Schriftfarbe Schwarz oder Weiß nach höherem Kontrast (mindestens 4,5:1) |
| ID neben Matrixpunkt (P1, P2, P5) | `{contact_id}`, 7,6 pt | `point_matrix`; mehrere Kontakte einer Zelle nebeneinander und in Zeilen, nach ID sortiert |

### A.6 Fehlende Angaben

| Element | Wortlaut / Muster | Herkunft / Bedingung |
|---|---|---|
| Fehlender erhobener Wert | `keine Angabe` | `MISSING_LABEL`, `base.py:109` – ein Wortlaut für alle Grafiken: Beziehungstyp-Legende, Zeile der Punktmatrizen (P1, P2, P5; kursiv, grau), Spalte in P5, Zeile der Heatmaps (P3, P4; kursiv, grau, gestrichelte Zellen), Bogen fehlender Nähe in G1 (kursiv, grau). Fehlende Werte zählen nie als „nein“. |
| Nicht zuordenbarer Wohnort | `Wohnort nicht zuordenbar: {ids}.` – z. B. `Wohnort nicht zuordenbar: A22.` | `Context.unresolved_note`, `base.py:163-167`; Hinweis in P1–P4 (alle nicht zuordenbaren Kontakte) und G2 (nur die nicht gezeichneten, d. h. ohne bestätigte Verbindung); nur wenn es solche Kontakte gibt. |
| Nicht zuordenbarer Wohnort (Zeile in G2) | `Wohnort nicht zuordenbar:` (kursiv, grau), rechts davon die Knoten | `UNPLACED_LABEL`, `networks.py:418`; nur für Kontakte ohne zuordenbaren Wohnort **mit** bestätigter Verbindung |
| Nicht darstellbarer Wohnort (X1) | `Wohnort nicht darstellbar: {ids}.` | `maps.py:711`; umfasst auch Orte ohne Eintrag im Ortsverzeichnis |
| Kurzcodes fehlender Zugehörigkeit (nur G3) | `NS`, `KA`, `NA`, `n. e.`; Rückfallwert `–` | `MISSING_SHORT`, `networks.py:656`; Auflösung in der Legende aus `codes.MISSING_LABELS` (`codes.py:34-39`) ohne Klammerzusatz: `NS = weiß nicht`, `KA = keine Antwort`, `NA = nicht anwendbar`, `n. e. = nicht erhoben` |

### A.7 Wiederkehrende Kategorien und Spaltenbeschriftungen

**Wohnortbereiche** – `AREA_LABELS` (`places.py:49-56`), in G2 einzeilig, in P1–P4 umbrochen (`area_columns`,
`base.py:496`): `Marburg (Stadt)`, `übriges Mittelhessen`, `übriges Deutschland`, `übriges Europa`,
`außerhalb Europas`; `nicht zuordenbar` ist nie eine Spalte oder ein Band.

| Element | Wortlaut / Muster | Herkunft / Bedingung |
|---|---|---|
| Klammer über den ersten zwei Bereichen | `Marburg und Mittelhessen` (grau) | `BRACKET_LABEL`, `base.py:110`; gezeichnet in `_headers` (`base.py:528`, P1–P4) und in G2 (`networks.py:450`) |
| Spaltenkopf Matrix | `{bereich}\nn = {anzahl}` – z. B. `übriges\nEuropa\nn = 3` | `_headers`, `base.py:521`; Bezugsgröße je Grafik (Teil B); `n = 0` wird gezeigt |
| Zeilentitel Punktmatrix | `{y_title}` (fett) | je Grafik |

**Persönliche Nähe** – Zeilen von P1 und P5 (`closeness_rows`, `base.py:716`; Texte aus `codes.CLOSENESS`,
`codes.py:45-53`): `1 · sehr nah`, `1,5`, `2 · nah`, `2,5`, `3 · weniger nah`, `3,5`, `4 · außerhalb der Kreise`;
`keine Angabe` nur bei Bedarf. G1 beschreibt dieselbe Skala in der Legende (siehe G1).

**Kontakthäufigkeit** – Zeilen von P2 aus `codes.CONTACT_FREQUENCY` (`codes.py:66-72`), ohne Codezahl:
`(Fast) täglich`, `Wöchentlich`, `Mehrmals monatlich`, `Etwa monatlich`, `Wenige Male/Jahr oder seltener`.

### A.8 Heatmap-Legende P3/P4 (`HEAT_LEGEND`, `base.py:706-713`) – eine gemeinsame Definition

| Eintrag | Wortlaut | Gestaltung |
|---|---|---|
| Farbskala | `Farbintensität = Anteil im Wohnortbereich (0–100 %)` | fünf Felder von weiß bis blau |
| Zahlen | `Zahl = Kontakte · Mehrfachnennungen möglich` | Text (grau) |
| neutrale Spalte | `n = 1: neutral` | graue Fläche |
| Bezugsgröße | `n = Kontakte mit Angabe im jeweiligen Wohnortbereich` | Text (grau) |

### A.9 Texte außerhalb der Grafiken (Register, Run-Protokoll)

| Element | Wortlaut | Herkunft |
|---|---|---|
| Registertitel | identisch mit dem Grafiktitel (`TITLES`) | `FigureSpec.title`, `__init__.py` |
| Standardsatz | `{code} {titel}`, Reihenfolge G1, G2, P1, P2, P3, P4, P5, G3, X1, G4, G5 | `run.py` (`standard_set`) |
| Skip-Gründe | G1 `keine erhobene persönliche Nähe`; G2 `kein Wohnort zuordenbar`; P1 `kein Wohnort zuordenbar` bzw. `keine erhobene persönliche Nähe`; P2 `kein Wohnort zuordenbar` bzw. `keine erhobene Kontakthäufigkeit`; P3 `keine erhobenen Kommunikationsformen`; P4 `keine erhobenen Sprachen`; P5 `keine erhobenen Beziehungsfunktionen`; G3 `keine Gruppen erhoben`; X1 `keine Kartengrundlagen übergeben`, `Ortsverzeichnis fehlt (…)`, `Basiskarte fehlt (…)`, `kein Wohnort zuordenbar`; G4 `keine Gruppen erhoben`, `kein Geburtsland erhoben`; G5 wie G4, dazu `kein Kontakt mit Wohnort in Marburg oder Mittelhessen`, `keine Gruppe mit Mitgliedern in Marburg oder Mittelhessen` | `__init__.py`, `birth_country.py`, `run.load_geo` |
| Was G5 auslässt | `details` des G5-Eintrags: `contacts_shown`, `contacts_total`, `not_shown_by_area` (IDs je Wohnortbereich), `unresolved_residence`, `groups_without_local_members`, `groups_partly_shown` (`{gruppe}: {n} von {gesamt}`) | `g5_details`, `birth_country.py`; in `figures_index.json` und `run_record.json`, nicht in der Grafik |
| Abdeckung der Kontaktpaare | Paare, bestätigt, verneint, unbekannt | nicht mehr in G2/G3; vollständig in `validation_report.md` („Abdeckung der Kontaktpaare“), `validation_report.json` und `run_record.json` (`coverage`) |
| Dateiname | `{case_code}_{code}_{name}.{ext}`, z. B. `002_test_synthetic_G1_persoenliches_netz.png` | `file_name`, `__init__.py` |

---

## B. Texte je Grafik

### G1 · Persönliches Beziehungsnetz (`g1`, `networks.py:135`; Legende `side`)

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `Persönliches Beziehungsnetz` | `TITLES["G1"]` |
| Untertitel | – | – |
| Zentrum | `Ego` (weiß, fett) | statisch; `networks.py:162` |
| Ringnummern | `1`, `2`, `3`, `4` (grau, oben auf den ganzzahligen Ringen) | aus `codes.CLOSENESS_LEVELS`; Zwischenringe gestrichelt, ohne Zahl |
| Bogen fehlender Nähe | `keine Angabe` (kursiv, grau, unter dem äußeren gepunkteten Bogen) | `MISSING_LABEL`, `networks.py:160`; nur wenn ein Kontakt keine Nähe hat |
| Knoten | `{contact_id}` | A.5 |
| Legende 1 | `Beziehungstyp` + Einträge | A.4 |
| Legende 2 – Titel | `Persönliche Nähe` | statisch; `networks.py:139` |
| Legende 2 – Linie durchgezogen | `1 sehr nah · 2 nah ·\n3 weniger nah ·\n4 außerhalb der Kreise` | statisch; `networks.py:140` (dreizeilig wegen der Legendenbreite) |
| Legende 2 – Linie gestrichelt | `Zwischenwerte: 1,5 · 2,5 · 3,5` | statisch; `networks.py:141`; immer, weil die gestrichelten Ringe immer gezeichnet sind |
| Hinweise | – (keine) | – |
| Fußzeile | A.3 | – |
| Sonderfall | Kontakt ohne Beziehungstyp: eigener Sektor, weißer Knoten, Legendeneintrag `keine Angabe` | `networks.py`, A.4 |

### G2 · Geografisches Beziehungsnetz (`g2`, `networks.py:421`; Legende `bottom`)

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `Geografisches Beziehungsnetz` | `TITLES["G2"]` |
| Untertitel | – | – |
| Bandköpfe | `{bereich}\nn = {anzahl}` – z. B. `Marburg (Stadt)\nn = 11`; alle fünf Bänder, `n = 0` möglich | `networks.py:445`; `{anzahl}` = Kontakte mit diesem Bereich |
| Klammer | `Marburg und Mittelhessen` | A.7 |
| Ortsgruppen | `{ort_oder_land}` (ein Kontakt) bzw. `{ort_oder_land} · {anzahl}` – z. B. `Gießen · 2`, `Kolumbien · 4`, `Kassel` | `label_text`, `networks.py:227-230`; in übriges Mittelhessen und übriges Deutschland der erfasste Ort, im Ausland das erfasste Wohnland; in Marburg (Stadt) kein Label |
| Untere Zone | `keine bestätigte Verbindung zu anderen Kontakten erfasst` (kursiv, grau) | statisch; `networks.py:454`; nur wenn es zuordenbare Kontakte ohne bestätigte Verbindung gibt |
| Zeile ohne Bereich | `Wohnort nicht zuordenbar:` + Knoten | A.6; nur bei nicht zuordenbaren Kontakten mit bestätigter Verbindung |
| Legende 1 | `Beziehungstyp` + Einträge | A.4 |
| Legende 2 – Titel | `Verbindungen` | statisch; `networks.py:428` |
| Legende 2 – durchgezogen | `innerhalb eines Bereichs` | statisch; `networks.py:429`; keine Anzahl |
| Legende 2 – gestrichelt | `zwischen Bereichen` bzw. `zwischen Bereichen · ohne Bereich` | `networks.py:430-431`; Zusatz nur, wenn eine bestätigte Verbindung einen Kontakt ohne Bereich berührt (gleiche Strichart) |
| Legende 3 | `gleicher Wohnort / gleiches Wohnland` (Flächensymbol) | statisch; `networks.py:433` |
| Hinweis | `Wohnort nicht zuordenbar: {ids}.` | A.6; `networks.py:436`; nur für nicht gezeichnete Kontakte |
| Fußzeile | A.3 | – |
| Entfallen | Kategorienhinweis zu Wohnortbereichen, Satz zu fehlenden Linien, Abdeckungszeile der Kontaktpaare, Verbindungszahlen in der Legende | Abdeckung: A.9 |

### G3 · Gruppenstruktur und Zugehörigkeit (`g3`, `networks.py:811`; Legende `bottom`)

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `Gruppenstruktur und Zugehörigkeit` | `TITLES["G3"]` |
| Untertitel | – | – |
| Gruppenlabel Zeile 1 | `{group_id} · {anzeigename} ({mitglieder})` – z. B. `C02 · Freundeskreis Universität (6)` (fett, Gruppenfarbe) | `group_label_lines`, `networks.py:673`; Anzeigename ohne Testdaten-Zusatz `(fiktiv…)`/`(synthetisch…)`, leer → `ohne Bezeichnung`, über 34 Zeichen gekürzt mit `…` (`display_name`, `networks.py:667-670`) |
| Gruppenlabel Zeile 2 | fünf Punkte, der erhobene Wert gefüllt; daneben `{wert}` (`1`…`5`, fett) oder Kurzcode `NS`/`KA`/`NA`/`n. e.` (kursiv, grau) | `ordinal_dots`, `belonging_text`; A.6 |
| Lose Kontakte | `keiner Gruppe zugeordnet, keine bestätigte Verbindung:` (kursiv, grau) + Knoten | `LOOSE_LABEL`, `networks.py:652`; nur bei Bedarf |
| Legende 1 | `Beziehungstyp` + Einträge | A.4 |
| Legende 2 – Skala | `Zugehörigkeit: 1 sehr stark – 5 überhaupt nicht` (Punktskala, zweiter Punkt markiert) | statisch; `networks.py:814`; kein Abschnittstitel |
| Legende 2 – fehlende Werte | `{code} = {bedeutung}` mit ` · ` verbunden – z. B. `KA = keine Antwort` (Punktskala ohne Markierung) | `networks.py:815-818`; nur die vorkommenden Kurzcodes, in der Folge NS, KA, NA, n. e. |
| Legende 3 | `bestätigte Verbindung` (Linie); `Mitglied mehrerer Gruppen` (Ringsymbol, nur bei Bedarf) | statisch; `networks.py:822-823` |
| Hinweise | – (keine) | – |
| Fußzeile | A.3 | – |
| Entfallen | Erklärung der Punktanzeige, Satz „gemeinsame Mitgliedschaft ist keine Verbindung“, Abdeckungszeile | Abdeckung: A.9; Definition in `network-v1.md` §6 |

### G4 · Gruppenstruktur nach Geburtsland (`g4`, `birth_country.py`; Legende `bottom`)

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `Gruppenstruktur nach Geburtsland` | `TITLES["G4"]` |
| Untertitel | – | – |
| Gruppenlabels, lose Kontakte | wie G3 | G3 |
| Knoten | `{contact_id}` / `{iso3}` | A.5 |
| Legende 1 – Titel | `Geburtsland` | statisch |
| Legende 1 – Einträge | `{erhobener Name} ({iso3})` – z. B. `Peru (PER)`; genannt, nicht codiert `{Name} (nicht codiert)`; zuletzt `keine Angabe` | `legend_entries`; nur dargestellte Länder, jedes einzeln, feste Reihenfolge (feste Länder in Tabellenfolge, dann übrige nach Code); Farbe fest je Code (`COUNTRY_COLORS`, `EXTENSION`) |
| Legende 2, 3 | wie G3 (Zugehörigkeitsskala, fehlende Kurzcodes, `bestätigte Verbindung`, `Mitglied mehrerer Gruppen`) | `belonging_sections`, `networks.py` |
| Hinweise | – (keine) | – |
| Fußzeile | A.3 | – |

### G5 · Lokale Gruppenstruktur nach Geburtsland (`g5`, `birth_country.py`; Legende `bottom`)

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `Lokale Gruppenstruktur nach Geburtsland` | `TITLES["G5"]` |
| Untertitel | – | – |
| Gruppenlabel Zeile 1 | `{group_id} · {anzeigename} ({n})` oder, wenn nicht alle Mitglieder lokal wohnen, `({n} von {gesamt})` – z. B. `C04 · Lateinamerikanischer Verein (5 von 7)` | `_label_lines`, `birth_country.py` |
| Gruppenlabel Zeile 2, lose Kontakte | wie G3 | G3 |
| Knoten, Legenden | wie G4; die Länderlegende nur mit den lokal dargestellten Ländern | `legend_entries` |
| Hinweis | `Lokaler Ausschnitt: {n} von {gesamt} Kontakten (Marburg und Mittelhessen).` – z. B. `Lokaler Ausschnitt: 18 von 32 Kontakten (Marburg und Mittelhessen).` | `local_note`, `birth_country.py`; immer |
| Fußzeile | A.3 (alle Kontakte des Falls) | – |
| Nicht in der Grafik | nicht zuordenbare Wohnorte, nicht dargestellte Gruppen | A.9 („Was G5 auslässt“) |

### P1 · Wohnortbereich und persönliche Nähe (`p1`, `matrices.py:54`; Legende `bottom`)

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `Wohnortbereich und persönliche Nähe` | `TITLES["P1"]` |
| Untertitel | – | – |
| Klammer, Spaltenköpfe | `Marburg und Mittelhessen`; `{bereich}\nn = {n}` | A.7; `{n}` = zuordenbare Kontakte des Bereichs (auch ohne Nähe-Angabe) |
| Zeilentitel | `Persönliche Nähe` | `matrices.py:56` |
| Zeilen | Nähe 1 … 4 einschließlich Zwischenwerte (A.7); `keine Angabe` nur bei Bedarf | `closeness_rows`, `matrices.py:43` |
| Zellen | Punkt in Beziehungstypfarbe + `{contact_id}` | A.5 |
| Legende | `Beziehungstyp` + Einträge | A.4 |
| Hinweis | `Wohnort nicht zuordenbar: {ids}.` | A.6; nur bei Bedarf |
| Fußzeile | A.3 | – |
| Entfallen | „Wohnortbereiche sind Kategorien, keine Entfernungen; persönliche Nähe und Wohnort sind getrennte Merkmale.“ | – |

### P2 · Wohnortbereich und Kontakthäufigkeit (`p2`, `matrices.py:59`; Legende `bottom`)

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `Wohnortbereich und Kontakthäufigkeit` | `TITLES["P2"]` |
| Untertitel | – | – |
| Klammer, Spaltenköpfe | wie P1 | A.7 |
| Zeilentitel | `Kontakthäufigkeit` | `matrices.py:62` |
| Zeilen | fünf Häufigkeitskategorien (A.7), immer alle; `keine Angabe` nur bei Bedarf | `codes.CONTACT_FREQUENCY` |
| Zellen, Legende, Hinweis, Fußzeile | wie P1 | – |
| Entfallen | „Kontakthäufigkeit ist eine geordnete Kategorie; die Zeilenabstände sind keine gemessenen Zeitabstände.“ | – |

### P3 · Kommunikationsformen nach Wohnortbereich (`p3`, `matrices.py:102`; Legende `bottom`)

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `Kommunikationsformen nach Wohnortbereich` | `TITLES["P3"]` |
| Untertitel | – | – |
| Klammer, Spaltenköpfe | `Marburg und Mittelhessen`; `{bereich}\nn = {n}` | A.7; `{n}` = zuordenbare Kontakte des Bereichs **mit** Angabe zu Kommunikationsformen |
| Abschnittstitel (grau, fett) | `Persönliche Kommunikation`, `Synchron auf Distanz`, `Asynchron`, `Weitere Formen` | `COMMUNICATION_SECTIONS`, `matrices.py:94` |
| Zeilen | `Persönlich`, `Videoanruf`, `Telefonat`, `Sprachnachrichten`, `Textnachrichten / Chat`, `Sonstiges` | `codes.COMMUNICATION_FORMS` (`codes.py:85-92`) |
| Zellen | `{anzahl}` (fett; weiß bei Anteil über 60 %); 0 = leere weiße Zelle; Spalte mit `n = 1` neutral grau | `heat_cell`, `heat_matrix` (`base.py:651`) |
| Zeile fehlender Angaben | `keine Angabe` (kursiv, grau); gestrichelte Zellen mit `{anzahl}` | `base.py:695`; nur bei Bedarf; nie als „nein“ gezählt |
| Legende | A.8 (vier Einträge) | `HEAT_LEGEND` |
| Hinweis | `Wohnort nicht zuordenbar: {ids}.` | A.6; nur bei Bedarf |
| Fußzeile | A.3 | – |
| Entfallen | „n = Kontakte des Bereichs mit Angabe; fehlende Angaben stehen getrennt und zählen nie als „nein“.“ (die Bezugsgröße steht jetzt in der Legende) | – |

### P4 · Sprachen nach Wohnortbereich (`p4`, `matrices.py:140`; Legende `bottom`)

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `Sprachen nach Wohnortbereich` | `TITLES["P4"]` |
| Untertitel | – | – |
| Klammer, Spaltenköpfe | wie P3; `{n}` = zuordenbare Kontakte des Bereichs mit Sprachangabe | A.7 |
| Zeilen | `Spanisch`, `Deutsch`, `Englisch`, `Portugiesisch` (immer); jede benannte weitere Sprache wie erfasst (häufigste zuerst, dann alphabetisch); `Andere Sprache (ohne Bezeichnung)` bei Code 5 ohne Namen | `codes.LANGUAGES` (`codes.py:94-100`); `language_rows`, `matrices.py:136` |
| Zellen, Zeile fehlender Angaben | wie P3 | – |
| Legende | A.8 (identisch mit P3) | `HEAT_LEGEND` |
| Hinweis 1 | `Mehrfachnennungen möglich; Anteile summieren sich nicht auf 100 %.` | statisch; `matrices.py:144` |
| Hinweis 2 | `Wohnort nicht zuordenbar: {ids}.` | A.6; nur bei Bedarf |
| Fußzeile | A.3 | – |

### P5 · Beziehungsfunktionen und persönliche Nähe (`p5`, `matrices.py:153`; Legende `bottom`)

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `Beziehungsfunktionen und persönliche Nähe` | `TITLES["P5"]` |
| Untertitel | – | – |
| Spaltenköpfe | `Persönlicher\nRückhalt / Rat`, `Gemeinsame\nAktivitäten /\nGespräche`, `Praktische Hilfe\nim Alltag`, `Sprachliche Hilfe /\nÜbersetzung`, `Sonstiges`, jeweils mit `\nn = {n}`; bedingt `Nichts davon` und `keine Angabe` (abgesetzt) | `FUNCTION_LABELS`, `matrices.py:147` (Umbrüche zu `codes.FUNCTIONS`); `{n}` = Zahl der Nennungen; keine Klammer |
| Zeilentitel | `Persönliche Nähe` | `matrices.py:174` |
| Zeilen | Nähe 1 … 4 (A.7); `keine Angabe` nur bei Bedarf | `closeness_rows` |
| Zellen | Punkt + `{contact_id}`; ein Kontakt erscheint in jeder seiner Funktionsspalten | A.5 |
| Legende | `Beziehungstyp` + Einträge | A.4 |
| Hinweis | `Mehrfachnennungen möglich.` | statisch; `matrices.py:172` |
| Fußzeile | A.3 | – |

### X1 · Geografische Verteilung des persönlichen Netzwerks (`x1`, `maps.py:694`; Legende `bottom`)

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `Geografische Verteilung des persönlichen Netzwerks` | `TITLES["X1"]`; `maps.py:712` |
| Untertitel | – | – |
| Panelüberschriften | `{Region} · n = {anzahl}` – Regionen `Amerika`, `Afrika`, `Asien`, `Ozeanien`, `Weitere Regionen`, `Europa (ohne Deutschland)`, `Deutschland`; z. B. `Amerika · n = 7` | `REGIONS`, `Panel.title`; Amerika, Europa, Deutschland immer, die übrigen nur bei Bedarf |
| Ortsbeschriftung Zeile 1 | fett `{ort}` bzw. `{ort} und Umgebung` (bei nur bekanntem Wohnland der Ländername), dahinter ` · {land}` (außerhalb Deutschlands), ` · nur Land bekannt`, ` · n = {anzahl}` (ab zwei Kontakten) – z. B. `Bogotá · Kolumbien · n = 3`, `Marburg und Umgebung · n = 14`, `Madrid · Spanien`, `Berlin` | `Place.head`, `Place.tail` (`maps.py`); bei Bedarf zweizeilig `{ort}` / `{land} · n = {anzahl}` |
| Ortsbeschriftung Zeile 2 | `{ort} {anzahl} · {ort} · …` (kleiner, grau), nur bei Ortsgruppen – z. B. `Marburg 10 · Cölbe · Kirchhain` | `Place.sub` |
| Legende 1 | `Beziehungstyp` + Einträge | A.4 |
| Legende 2 | `Wohnort (Ortspunkt)`; bedingt `○ weiterer Ort einer Ortsgruppe` (grau) und `nur Wohnland bekannt (Lage unscharf)` (gestrichelte Fläche) | `maps.py:705-707` |
| Hinweis 1 | `Wohnort nicht darstellbar: {ids}.` | A.6; nur bei Bedarf |
| Hinweis 2 | `Kartengrundlage: Natural Earth.` | statisch; `maps.py:711`; vollständige Quellenangabe in `network-v1.md` §6.1 |
| Fußzeile | A.3 | – |

---

## C. Verbleibende Mehrfach- oder Sonderformulierungen

| Wortlaut | Orte | Bemerkung |
|---|---|---|
| `Wohnort nicht zuordenbar: …` / `Wohnort nicht darstellbar: …` | `base.py:163-167`; `maps.py:711` | bewusst verschieden: X1 umfasst auch Orte ohne Ortsverzeichniseintrag |
| `Mehrfachnennungen möglich` | `HEAT_LEGEND` (P3, P4); Hinweis P4; Hinweis P5 | in P4 zweimal sichtbar (Legende und Hinweis), wie vereinbart |
| Funktionsnamen | `codes.py:73-80`; `matrices.py:147` | gleicher Wortlaut, zweite Fassung mit Umbrüchen |
| Nähe-Skala | `codes.py:45-53`; `closeness_rows`; G1-Legende `networks.py:140-141` | G1-Legende mit Umbrüchen und ohne Mittelpunkt nach der Zahl |
| `Persönliche Nähe` | G1-Legendentitel; Zeilentitel P1, P5 | identisch |
| `n = {anzahl}` | Spaltenköpfe P1–P5, Bandköpfe G2, Panelüberschriften und Ortsbeschriftungen X1 | gleiches Muster, verschiedene Bezugsgrößen |
