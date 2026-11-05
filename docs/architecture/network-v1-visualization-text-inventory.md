# Textinventar der neun Standardgrafiken von network_v1 – Ist-Stand

Bestandsaufnahme **aller sichtbaren Texte** der Standardgrafiken G1, G2, G3, P1–P5 und X1, aus dem
Quellcode extrahiert, als Grundlage für die gemeinsame redaktionelle Prüfung. Keine
Umformulierungsvorschläge: Das Dokument beschreibt den Iststand, es ist keine Vorgabe. Maßgeblich für
Inhalt und Regeln der Grafiken bleibt [`network-v1.md`](network-v1.md) §6.

Stand: Kanonisierung von X1, 2026-11-05 ([`ADR-0016`](../decisions/ADR-0016_2026-11-05_netzwerk-v1-x1-kanonisch.md)).
G1–G3 und P1–P5 sind gegenüber dem Stand davor unverändert, X1 ist nach der redaktionellen Bereinigung
erfasst. Zeilenangaben gelten für diesen Stand und verschieben sich bei späteren Änderungen; die
genannten Funktionen und Konstanten bleiben der Anker.

**Konventionen**

- Codeorte als `Pfad:Zeile`, relativ zum Repository.
- `\n` in einem Wortlaut = Zeilenumbruch in der Grafik.
- `{platzhalter}` = dynamischer Teil; „statisch“ = fester Wortlaut im Code.
- Beispiele nur neutral oder aus den Testfällen (für X1 auch die erfundenen Orte des synthetischen
  Ortsverzeichnisses der Tests); keine Angaben aus authentischen Fällen. Grundlage: der synthetische
  Testfall `002_test_synthetic`
  (`examples/synthetic/network_v1/002_test_synthetic/`; 32 Kontakte, 5 Gruppen,
  `case_type: test`, `provenance: fully_synthetic`, `data_quality: SYNTHETIC`).
- Kursiv/grau („MUTED“) wird angegeben, wo der Code einen Text so auszeichnet, weil es die
  Lesart (Hinweis statt Kategorie) mitbestimmt.

---

## A. Gemeinsame Texte und Regeln

### A.1 Seitenaufbau (gemeinsame Komponente `base.page`)

Jede der neun Grafiken wird über `page()` gesetzt (`src/mares/network_v1/figures/base.py:315-360`):

| Element | Wortlaut / Muster | Herkunft / Bedingung |
|---|---|---|
| Titel | `{titel}` (fett, 16 pt, oben links) | Argument `title` von `page()`; `src/mares/network_v1/figures/base.py:349`. Wortlaut je Grafik in Teil B. |
| Untertitel | `{untertitel}` (grau, 10,5 pt) | Argument `subtitle`; `src/mares/network_v1/figures/base.py:350-351`. Optional: X1 übergibt keinen Untertitel, der Kopf ist dann niedriger (`HEADER_H_TITLE_ONLY`). |
| Fallkennzeichen oben rechts | siehe A.2 | `case_badge(ctx)`; `src/mares/network_v1/figures/base.py:352-355`. |
| Hinweiszeilen (Notes) | je Grafik verschieden, siehe Teil B | `src/mares/network_v1/figures/base.py:319`: leere Notes werden verworfen, **höchstens die ersten zwei** werden gezeichnet; `:356-358` (unten links, über der Fußzeile, 8 pt). Kein automatischer Zeilenumbruch. |
| Fußzeile | siehe A.3 | `footer_line(ctx)` oder der Wortlaut des Arguments `footer` (nur X1); `src/mares/network_v1/figures/base.py:359` (grau, 7,5 pt). |
| Legende | Abschnitte `(Titel, Einträge)`; Layout `side` (rechts, nur G1) oder `bottom` (unter dem Hauptbereich) | `draw_legend`, `src/mares/network_v1/figures/base.py:267-301`; Abschnittstitel fett (`:276`, `:290`); Einträge der Art `text` grau (`:280`, `:298`). Abschnitte ohne Einträge entfallen (`:217`, `:287`). |

### A.2 Fallkennzeichen (Badge oben rechts)

`case_badge`, `src/mares/network_v1/figures/base.py:149-156`. `number` = die ersten drei Zeichen von
`case_code` (`:152`). Ob Testfall: `metadata.case_type == "test"` (`:129-130`).

| Variante | Wortlaut | Bedingung | Gestaltung |
|---|---|---|---|
| Testfall, vollsynthetisch | `TESTFALL {number}* · SYNTHETISCH` – Beispiel 002: `TESTFALL 002* · SYNTHETISCH` | `case_type == "test"` und `provenance == "fully_synthetic"`; `base.py:154-155` | weiße Schrift auf rotem Grund (`TEST_RED`), `base.py:353-355` |
| Testfall, aus v0 fiktionalisiert | `TESTFALL {number}* · FIKTIONALISIERT` (z. B. `TESTFALL 001* · FIKTIONALISIERT`) | `provenance == "v0_derived_fictionalized"`; `base.py:154` | wie oben |
| Testfall, sonstige/fehlende Provenienz | `TESTFALL {number}* · FIKTIV` | jeder andere `provenance`-Wert (Rückfallwert des `.get`); `base.py:154` | wie oben |
| Realer Fall mit Anzeigecode | `FALL · {display_code}` | `case_type != "test"` und `metadata.display_code` gesetzt; `base.py:156` | schwarze Schrift, weißer Grund, dunkler Rahmen |
| Realer Fall ohne Anzeigecode | `FALL · MARES-{number}` (z. B. `FALL · MARES-000`) | `display_code` fehlt oder leer; `base.py:156` | wie oben |

### A.3 Fußzeile (Metadatenzeile)

`footer_line`, `src/mares/network_v1/figures/base.py:159-165`; in G1–G3 und P1–P5 identisch. X1 setzt eine eigene, kürzere Fußzeile (siehe X1).

| Element | Wortlaut / Muster | Herkunft / Bedingung |
|---|---|---|
| Grundmuster | `MARES · network_v1 · {anzahl_kontakte} Kontakte · {anzahl_gruppen} Gruppen` – Beispiel 002: `MARES · network_v1 · 32 Kontakte · 5 Gruppen` | `base.py:161`. `{anzahl_kontakte}` = `len(case.contacts)` (alle Kontakte, auch solche ohne zuordenbaren Wohnort), `{anzahl_gruppen}` = `len(case.groups)`. Keine Singularform („1 Kontakte“, „1 Gruppen“, „0 Gruppen“ möglich). |
| Zusatz Datenqualität | ` · Datenqualität: {data_quality}` | `base.py:162-164`: nur wenn **kein Testfall** (`not ctx.is_test`) **und** `metadata.data_quality` nicht leer. Bei Testfällen nie (002 hat `data_quality: SYNTHETIC`, erscheint aber nicht). `{data_quality}` ist der Rohwert aus `metadata.json`. |

### A.4 Legende „Beziehungstyp“ (gemeinsame Komponente `base.relation_entries`)

`relation_entries`, `src/mares/network_v1/figures/base.py:97-102`; Beschriftungen aus
`codes.RELATION_TYPE` (`src/mares/network_v1/codes.py:58-65`), Farben `base.py:59-66`.
Verwendet in G1, G2, G3, P1, P2, P5 und X1 (nicht in P3, P4).

| Eintrag | Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Abschnittstitel | `Beziehungstyp` | Literal **an sechs Stellen** wiederholt: `src/mares/network_v1/figures/maps.py:704` (X1), `src/mares/network_v1/figures/networks.py:137` (G1), `:432` (G2), `:827` (G3), `src/mares/network_v1/figures/matrices.py:48` (P1, P2), `:183` (P5). |
| Code 1 | `Familie` | `codes.py:59`; immer gezeigt (alle sechs Typen erscheinen unabhängig davon, ob sie im Fall vorkommen; `base.py:99`). |
| Code 2 | `Partner:in` | `codes.py:60` |
| Code 3 | `Freund:in` | `codes.py:61` |
| Code 4 | `Bekannte:r` | `codes.py:62` |
| Code 5 | `Professionell / institutionell` | `codes.py:63` |
| Code 6 | `Sonstige Beziehung` | `codes.py:64` |
| fehlender Beziehungstyp | `keine Angabe` (weißer Punkt, gepunkteter Rand) | `base.py:100-101`: nur wenn mindestens **ein Kontakt des Falls** keinen gültig erfassten Beziehungstyp hat. Geprüft über alle Kontakte des Falls, auch über solche, die in der jeweiligen Grafik nicht gezeichnet werden (z. B. Kontakte ohne zuordenbaren Wohnort in P1/P2). Alle Fehlarten (NS, KA, NA, leer, ungültig) fallen hierunter; keine Unterscheidung. |

### A.5 Kontakt-IDs, Knoten und Punkte

| Element | Wortlaut / Muster | Herkunft / Bedingung |
|---|---|---|
| Kontakt-ID im Netzwerkknoten (G1, G2, G3, X1) | `{contact_id}` (z. B. `A01`), fett, 7 pt, im Kreis | `draw_nodes`, `src/mares/network_v1/figures/base.py:375-381` (Text `:380`). Schriftfarbe nach Kontrast zur Füllfarbe. |
| Kontakt-ID neben Matrixpunkt (P1, P2, P5) | `{contact_id}` (z. B. `A01`), 7,6 pt, rechts neben dem Punkt | `point_matrix`, `src/mares/network_v1/figures/base.py:604`. Mehrere Kontakte einer Zelle nebeneinander und in Zeilen, nach ID sortiert (`:594`). Keine Kürzung. |

### A.6 Fehlende Werte und Abdeckung

| Element | Wortlaut / Muster | Herkunft / Bedingung |
|---|---|---|
| Nicht zuordenbarer Wohnort (Matrizen) | `Wohnort nicht zuordenbar (nicht dargestellt): {id1}, {id2}.` – Beispiel neutral: `Wohnort nicht zuordenbar (nicht dargestellt): A07, A12.` | `Context.unresolved_note`, `src/mares/network_v1/figures/base.py:138-140`; Parameter `where` hat den Vorgabewert `nicht dargestellt`, kein Aufrufer übergibt einen anderen. Leer (und damit keine Notiz), wenn alle Wohnorte zuordenbar sind. Verwendet in P1, P2 (`matrices.py:48`), P3, P4 (`matrices.py:94`). |
| Nicht zuordenbarer Wohnort (G2) | ` Wohnort nicht zuordenbar: {id1}, {id2}.` (an Hinweis 1 angehängt) | Eigene, **zweite Implementierung** mit anderem Wortlaut (ohne „(nicht dargestellt)“): `src/mares/network_v1/figures/networks.py:439`. Nur für Kontakte ohne zuordenbaren Wohnort **und** ohne bestätigte Verbindung. |
| Abdeckungszeile Kontaktpaare | `Kontaktpaare: {pairs} · bestätigt {confirmed} · verneint {denied} · unbekannt {unknown}.` – Beispiel neutral: `Kontaktpaare: 10 · bestätigt 3 · verneint 2 · unbekannt 5.` | `Context.coverage_line`, `src/mares/network_v1/figures/base.py:142-146`. `{pairs}` = n·(n−1)/2 aller Kontakte (`derive.py:119`); `{unknown}` = ausdrücklich „?“ + Paare ohne jede Aussage (`derive.py:63-65`). **Konfliktpaare** (1 und 0 zugleich) werden in keiner der drei Teilzahlen gezählt und nicht genannt (`derive.py:127`); die Teilsummen ergeben dann nicht `{pairs}`. Leer, wenn `pairs == 0` (weniger als zwei Kontakte). Verwendet in G2 (`networks.py:441`) und G3 (`networks.py:833`). |
| Fehlende Antwort als Zeile, Punktmatrix | `keine Angabe` (kursiv, grau) | Zeilenlabel; Stil `base.py:585-586` (Schlüssel `missing`). Wortlaut aus `matrices.py:43` (P1/P2) bzw. `base.py:705` (`closeness_rows`, P5). |
| Fehlende Antwort als Zeile, Heatmatrix | `ohne Angabe` (kursiv, grau) | `src/mares/network_v1/figures/base.py:680`. **Abweichender Wortlaut** gegenüber „keine Angabe“ der Punktmatrizen. Siehe P3/P4. |
| Fehlende Nähe in G1 | `Nähe ohne Angabe` (kursiv, grau, unter dem äußeren Bogen) | `src/mares/network_v1/figures/networks.py:162`. |
| Kurzcodes fehlender Werte | `NS`, `KA`, `NA`, `n. e.`; Rückfallwert `–` | `MISSING_SHORT`, `src/mares/network_v1/figures/networks.py:663`; Rückfall `:671`. **Nur in G3** (Zugehörigkeit einer Gruppe) sichtbar. Zuordnung: `Missing.UNKNOWN`→`NS`, `NO_ANSWER`→`KA`, `NOT_APPLICABLE`→`NA`, `NOT_COLLECTED` (leere Zelle)→`n. e.` (`codes.py:26-30`). `–` erscheint, wenn weder ein Wert noch eine Fehlart vorliegt (ungültiger Code, `Cell.error`). |
| Auflösung der Kurzcodes | `NS = weiß nicht`, `KA = keine Antwort`, `NA = nicht anwendbar`, `n. e. = nicht erhoben` | In der G3-Legende gebildet aus `codes.MISSING_LABELS` (`src/mares/network_v1/codes.py:34-39`: `weiß nicht (NS)`, `keine Antwort (KA)`, `nicht anwendbar (NA)`, `nicht erhoben`) durch Abschneiden ab ` (` (`networks.py:824`). Nur die im Fall vorkommenden Codes, in der Reihenfolge NS, KA, NA, n. e. (`networks.py:822`). |
| Fehlarten in allen anderen Grafiken | – | In G1, G2, P1–P5 werden NS, KA, NA und leer **nicht unterschieden**; alle erscheinen als „keine Angabe“ / „ohne Angabe“ / „Nähe ohne Angabe“ bzw. weißer Punkt mit gepunktetem Rand. |

### A.7 Wiederkehrende Kategorien und Achsen-/Spaltenbeschriftungen

**Wohnortbereiche** – `AREA_LABELS`, `src/mares/network_v1/places.py:49-56`, Reihenfolge `AREA_ORDER` (`places.py:48`):

| Bereich | Wortlaut in G2 (einzeilig) | Wortlaut in P1–P4 (Spaltenkopf, umbrochen) | Herkunft |
|---|---|---|---|
| `MARBURG` | `Marburg (Stadt)` | `Marburg\n(Stadt)` | `places.py:50`; Umbruch `src/mares/network_v1/figures/base.py:483` |
| `MITTELHESSEN` | `übriges Mittelhessen` | `übriges\nMittelhessen` | `places.py:51`; `base.py:483` |
| `GERMANY_OTHER` | `übriges Deutschland` | `übriges\nDeutschland` | `places.py:52`; `base.py:483` |
| `EUROPE_OTHER` | `übriges Europa` | `übriges\nEuropa` | `places.py:53`; `base.py:483` |
| `OUTSIDE_EUROPE` | `außerhalb Europas` | `außerhalb\nEuropas` | `places.py:54`; `base.py:483` |
| `UNRESOLVED` | (`nicht zuordenbar` – nie als Band/Spalte gezeigt) | – | `places.py:55`; ausgeschlossen `base.py:481-484`, `networks.py:267-268` |

| Element | Wortlaut / Muster | Herkunft / Bedingung |
|---|---|---|
| Klammer über den ersten zwei Bereichen | `Marburg und Mittelhessen` (grau) | Zweifach implementiert: `src/mares/network_v1/figures/base.py:513` (P1–P4, wenn Marburg- und Mittelhessen-Spalte vorhanden – bei `area_columns()` immer) und `src/mares/network_v1/figures/networks.py:457` (G2). Gleicher Wortlaut zusätzlich als `PRIMARY_LABELS` in `src/mares/network_v1/places.py:76` (dort nicht für die Grafiken verwendet). |
| Spaltenkopf Matrix | `{spaltenlabel}\nn = {anzahl}` – Beispiel: `übriges\nEuropa\nn = 4` | `_headers`, `src/mares/network_v1/figures/base.py:506`. Bedeutung von `{anzahl}` je Grafik verschieden (siehe Teil B). `0` wird angezeigt (`counts.get(key, 0)`). |
| Achsentitel der Zeilen (Punktmatrix) | `{y_title}` (fett, über den Zeilenlabels links) | `base.py:514-515`; Wortlaut je Grafik. |

**Persönliche Nähe** – Zeilen der Punktmatrizen P1 und P5 (`closeness_rows`,
`src/mares/network_v1/figures/base.py:700-706`; Texte aus `codes.CLOSENESS`,
`src/mares/network_v1/codes.py:45-53`, Dezimalkomma über `closeness_label`, `codes.py:219-221`).
Halbstufen erscheinen nur als Zahl, ganze Stufen als `Zahl · Bezeichnung` (`base.py:702`):

| Wert | Zeilenlabel | Ungenutzter Codetext (`codes.CLOSENESS`) |
|---|---|---|
| 1 | `1 · sehr nah` | – |
| 1,5 | `1,5` | `zwischen sehr nah und nah` (`codes.py:47`, nicht sichtbar) |
| 2 | `2 · nah` | – |
| 2,5 | `2,5` | `zwischen nah und weniger nah` (`codes.py:49`, nicht sichtbar) |
| 3 | `3 · weniger nah` | – |
| 3,5 | `3,5` | `zwischen weniger nah und außerhalb` (`codes.py:51`, nicht sichtbar) |
| 4 | `4 · außerhalb der Kreise` | – |
| fehlt | `keine Angabe` (kursiv, grau) | `base.py:705`, nur wenn `include_missing` |

Die G1-Legende beschreibt dieselbe Skala mit **anderem, verkürztem Wortlaut** (`4 außerhalb` statt
`4 · außerhalb der Kreise`), siehe G1.

**Kontakthäufigkeit** – Zeilen von P2 aus `codes.CONTACT_FREQUENCY`
(`src/mares/network_v1/codes.py:66-72`), **ohne** Codezahl: `(Fast) täglich`, `Wöchentlich`,
`Mehrmals monatlich`, `Etwa monatlich`, `Wenige Male/Jahr oder seltener`.

**Zugehörigkeit (G3)** – Legende `1 = sehr stark bis 5 = überhaupt nicht …`
(`networks.py:821`); die Codetexte `codes.BELONGING` (`codes.py:111`: `Sehr stark`, `Stark`,
`Mittel`, `Wenig`, `Überhaupt nicht`) werden in den Grafiken **nicht** verwendet; im Gruppenlabel
steht nur die Zahl.

### A.8 Methodische Standardhinweise (Übersicht)

Die Hinweise sind je Grafik fest im Code (Teil B); keiner ist zentral definiert. Wiederkehrende Aussagen:

| Aussage | Wortlaut | Ort(e) |
|---|---|---|
| Bereiche sind Kategorien | `Wohnortbereiche sind Kategorien, keine Entfernungen; …` | zweifach mit verschiedener Fortsetzung: `src/mares/network_v1/figures/networks.py:440` (G2), `src/mares/network_v1/figures/matrices.py:58` (P1) |
| Fehlende Linie ≠ kein Kontakt | `Linien zeigen bestätigte Verbindungen; fehlende Linien bedeuten nicht zwangsläufig keinen Kontakt. ` | `networks.py:441` (nur G2) |
| Mitgliedschaft ≠ Verbindung | `Gruppen umfassen die von Ego zugeordneten Kontakte; gemeinsame Mitgliedschaft ist keine Verbindung.` | `networks.py:832` (nur G3) |
| Mehrfachnennungen | `Mehrfachnennungen möglich` | `base.py:695` (Legende P3/P4) und `matrices.py:184` (Hinweis P5, längere Fassung) |
| Anteile ≠ 100 % | `… Anteile summieren sich daher nicht zu 100 %.` | `matrices.py:154` (nur P4) |
| Basis n | `n = Kontakte des Bereichs mit Angabe; …` | `matrices.py:117` (nur P3; P4 verwendet dieselbe Basis ohne diesen Hinweis) |

### A.9 Texte außerhalb der Grafiken (Run-Protokoll, nicht in der Abbildung)

Diese Texte stehen in `figures_index.json` bzw. im Run-Datensatz, **nicht** in einer Grafik.

| Element | Wortlaut | Herkunft / Bedingung |
|---|---|---|
| FigureSpec-Titel G1 | `Persönliches Beziehungsnetz` | `src/mares/network_v1/figures/__init__.py:50` |
| FigureSpec-Titel G2 | `Geografisches Beziehungsnetz` | `__init__.py:52` |
| FigureSpec-Titel P1 | `Wohnortbereich und persönliche Nähe` | `__init__.py:54` |
| FigureSpec-Titel P2 | `Wohnortbereich und Kontakthäufigkeit` | `__init__.py:56` |
| FigureSpec-Titel P3 | `Kommunikationsformen nach Wohnortbereich` | `__init__.py:58` |
| FigureSpec-Titel P4 | `Sprachen nach Wohnortbereich` | `__init__.py:60` |
| FigureSpec-Titel P5 | `Beziehungsfunktionen und persönliche Nähe` | `__init__.py:62` |
| FigureSpec-Titel X1 | `Geografische Verteilung des persönlichen Netzwerks` | `src/mares/network_v1/figures/__init__.py`, Eintrag `X1` |
| FigureSpec-Titel G3 | `Gruppenstruktur und Zugehörigkeit` | `__init__.py:64` |
| Standardsatz | `{code} {titel}`, z. B. `G1 Persönliches Beziehungsnetz` | `src/mares/network_v1/run.py:184` (`standard_set`); Reihenfolge G1, G2, P1, P2, P3, P4, P5, G3, X1 (`__init__.py:49-68`). |
| Seitentitel vs. FigureSpec-Titel | Seitentitel = `{code} · {FigureSpec-Titel}` bei G1–G3 und P1–P5; X1 ohne Code (Seitentitel = FigureSpec-Titel); der Wortlaut nach dem Code ist bei allen acht identisch, aber **getrennt implementiert** (FigureSpec in `__init__.py`, Seitentitel als eigenes Literal in `networks.py`/`matrices.py`). | Vergleich `__init__.py:50-64` mit `networks.py:145, 442, 834`, `matrices.py:56, 65, 115, 152, 182` |
| Eingaben (`inputs`) | G1 `A: Nähe`, `A: Beziehungstyp` · G2 `A: Wohnort, Wohnland`, `C: bestätigte Verbindungen` · P1 `A: Wohnort, Wohnland`, `A: Nähe` · P2 `A: Wohnort, Wohnland`, `A: Kontakthäufigkeit` · P3 `A: Wohnort, Wohnland`, `B: Kommunikationsformen` · P4 `A: Wohnort, Wohnland`, `B: Sprachen, andere Sprachen` · P5 `A: Bedeutung/Funktionen`, `A: Nähe` · G3 `C: Gruppen, Mitglieder, Status, Zugehörigkeit`, `C: bestätigte Verbindungen` | `__init__.py:50-64`; Eintrag `inputs` im Index (`__init__.py:95`). |
| Status | `rendered` / `skipped` | `__init__.py:98`, `:104` |
| Skip-Grund G1 | `keine erhobene persönliche Nähe` | `__init__.py:51`: kein Kontakt mit erfasster Nähe |
| Skip-Grund G2 | `kein Wohnort zuordenbar` | `__init__.py:53`: alle Wohnorte `UNRESOLVED` (G2 wird **nicht** übersprungen, wenn es keine bestätigten Verbindungen gibt) |
| Skip-Gründe P1 | `kein Wohnort zuordenbar`, sonst `keine erhobene persönliche Nähe` | `__init__.py:55` (Prüfreihenfolge: Wohnort zuerst) |
| Skip-Gründe P2 | `kein Wohnort zuordenbar`, sonst `keine erhobene Kontakthäufigkeit` | `__init__.py:57` |
| Skip-Grund P3 | `keine erhobenen Kommunikationsformen` | `__init__.py:59` (P3 prüft **keinen** Wohnort) |
| Skip-Grund P4 | `keine erhobenen Sprachen` | `__init__.py:61` (P4 prüft **keinen** Wohnort) |
| Skip-Grund P5 | `keine erhobenen Beziehungsfunktionen` | `__init__.py:63` |
| Skip-Gründe X1 | `keine Kartengrundlagen übergeben`; `Ortsverzeichnis fehlt ({ROOT}:network_v1/reference/gazetteer.csv)` und/oder `Basiskarte fehlt (WORKSPACE:cache/basemaps/ne_50m_admin_0_countries.geojson)` (mit `; ` verbunden); sonst `kein Wohnort zuordenbar` | `_x1_missing`, `src/mares/network_v1/figures/__init__.py`; Texte der fehlenden Dateien aus `load_geo`, `src/mares/network_v1/run.py` |
| Skip-Grund G3 | `keine Gruppen erhoben` | `__init__.py:65` |
| Dateiname | `{case_code}_{figurcode}_{name}.{ext}`, z. B. `002_test_synthetic_G1_persoenliches_netz.png`; Namensteile `persoenliches_netz`, `geografisches_netz`, `wohnort_naehe`, `wohnort_haeufigkeit`, `wohnort_kommunikation`, `wohnort_sprachen`, `funktionen_naehe`, `gruppen_zugehoerigkeit`, `geografische_verteilung` | `base.py:168-173`, `__init__.py:50-64`. Nicht in der Grafik sichtbar. |

---

## B. Texte je Grafik

### G1 · Persönliches Beziehungsnetz

Code: `g1`, `src/mares/network_v1/figures/networks.py:134-166`. Legende `side` (rechts).

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `G1 · Persönliches Beziehungsnetz` | statisch; `networks.py:145` (gemeinsame Komponente `base.page`) |
| Untertitel | `Kontakte nach persönlicher Nähe und Beziehungstyp` | statisch; `networks.py:145` |
| Fallkennzeichen | siehe A.2 | `base.case_badge` |
| Zentrum | `Ego` (weiß, fett, auf dunklem Kreis) | statisch; `networks.py:164` |
| Ringnummern | `1`, `2`, `3`, `4` (grau, oben auf den ganzzahligen Ringen) | dynamisch aus `codes.CLOSENESS_LEVELS`, nur ganze Werte; `networks.py:152-158`. Halbstufenringe (1,5/2,5/3,5) gestrichelt, **ohne** Beschriftung. |
| Beschriftung äußerer Bogen | `Nähe ohne Angabe` (kursiv, grau) | nur wenn mindestens ein Kontakt keine erfasste Nähe hat; `networks.py:160-162` |
| Knotenbeschriftung | `{contact_id}` (z. B. `A01`) | gemeinsame Komponente `base.draw_nodes` (`base.py:380`); Farbe = Beziehungstyp, weiß/gepunktet ohne Angabe |
| Sektoren nach Beziehungstyp | – (keine Beschriftung) | Winkelsektoren ohne Text; `networks.py:64-80`. Die Zuordnung ist nur über Farbe und Legende lesbar. |
| Legende Abschnitt 1 – Titel | `Beziehungstyp` | `networks.py:137`; gemeinsame Komponente `base.relation_entries` (A.4) |
| Legende Abschnitt 1 – Einträge | sechs Beziehungstypen, ggf. `keine Angabe` | A.4 |
| Legende Abschnitt 2 – Titel | `Persönliche Nähe` | statisch; `networks.py:138` |
| Legende Abschnitt 2 – Eintrag 1 (durchgezogene Linie) | `1 sehr nah · 2 nah ·\n3 weniger nah · 4 außerhalb` | statisch; `networks.py:139`. Verkürzt gegenüber `codes.CLOSENESS` (`außerhalb der Kreise`, `codes.py:52`) und P1/P5-Zeilen (`4 · außerhalb der Kreise`). |
| Legende Abschnitt 2 – Eintrag 2 (gestrichelte Linie) | `Zwischenwerte 1,5 · 2,5 · 3,5` | statisch; `networks.py:140`. Wird auch gezeigt, wenn kein Kontakt einen Zwischenwert hat. |
| Hinweis | `Abstand zu Ego = persönliche Nähe; Winkelbereiche ordnen die Kontakte nach Beziehungstyp. Die genaue Position innerhalb eines Sektors hat keine zusätzliche inhaltliche Bedeutung.` | statisch, eine Zeile; `networks.py:143-144` |
| Zweiter Hinweis | – | G1 hat keinen zweiten Hinweis: keine Abdeckungszeile, keine Wohnort-Notiz. |
| Verbindungen | – | G1 zeichnet keine Kontakt-Kontakt-Verbindungen (`networks.py:135`), daher kein Hinweis dazu. |
| Fußzeile | `MARES · network_v1 · {n} Kontakte · {k} Gruppen[ · Datenqualität: {q}]` | gemeinsame Komponente `base.footer_line` (A.3) |
| Sonderfall: Kontakt ohne Beziehungstyp | eigener Sektor (am Ende der Reihenfolge), weißer Knoten mit gepunktetem Rand, Legendeneintrag `keine Angabe` | `networks.py:54`, `base.py:100-101` |
| Sonderfall: Kontakt ohne Nähe | Knoten auf äußerem gepunktetem Bogen, Text `Nähe ohne Angabe` | `networks.py:110`, `:160-162` |
| Sonderfall: keine Nähe im Fall | Grafik entfällt; Run-Protokoll `keine erhobene persönliche Nähe` | `__init__.py:51` |

### G2 · Geografisches Beziehungsnetz

Code: `g2`, `src/mares/network_v1/figures/networks.py:423-485`. Legende `bottom`.

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `G2 · Geografisches Beziehungsnetz` | statisch; `networks.py:442` |
| Untertitel | `Kontakte nach Wohnortbereich und bestätigte Verbindungen zwischen ihnen` | statisch; `networks.py:442` |
| Fallkennzeichen | siehe A.2 | `base.case_badge` |
| Bandköpfe (fünf Bereiche) | `{AREA_LABEL}\nn = {anzahl}` – z. B. `Marburg (Stadt)\nn = 9`, `außerhalb Europas\nn = 0` | dynamisch; `networks.py:450-453`. Bereichsnamen einzeilig aus `AREA_LABELS` (A.7). `{anzahl}` = alle Kontakte mit diesem Bereich; `0` wird gezeigt (alle fünf Bänder sind immer da). |
| Klammer | `Marburg und Mittelhessen` (grau) | statisch; `networks.py:454-457`; Doppelimplementierung zu `base.py:513` |
| Teilgruppenlabel (gleicher Ort / gleiches Land) | `{ort_oder_land}` bei einem Kontakt; `{ort_oder_land} · {anzahl}` bei mehreren – z. B. `Bogotá · 3`, `Gießen` | dynamisch; `Subgroup.label_text`, `networks.py:228-232`; Label `subgroup_label`, `:238-246`: in `übriges Mittelhessen` und `übriges Deutschland` der **erfasste Ortsname** (`residence_place`, wie notiert), im Ausland der **erfasste Ländername** (`residence_country`), ersatzweise der ISO-3-Code. Im Band `Marburg (Stadt)` kein Label (`:184`, `:254`). Ohne erfassten Ort/Land kein Label. Keine Kürzung. Schreibvarianten (Groß-/Kleinschreibung, Umlaute) werden zusammengefasst, gezeigt wird die erste vorkommende Schreibung (`:255-256`). Gezeichnet `:472-473`. |
| Teilgruppenfläche | – (heller Kasten mit Rand, ohne Text) | nur wenn Label vorhanden **und** mehr als ein Mitglied; `networks.py:467-471` |
| Zonenbeschriftung untere Zone | `keine bestätigte Verbindung zu anderen Kontakten erfasst` (kursiv, grau, links über gestrichelter Trennlinie) | statisch; `networks.py:458-462`; nur wenn es zuordenbare Kontakte ohne bestätigte Verbindung gibt |
| Zeile unter den Bändern | `Wohnort nicht zuordenbar (keinem Bereich zugeordnet):` (kursiv, grau), rechts davon die Knoten | statisch, `UNPLACED_LABEL` `networks.py:420`; gezeichnet `:463-464`; nur für Kontakte ohne zuordenbaren Wohnort **mit** bestätigter Verbindung |
| Knotenbeschriftung | `{contact_id}` | gemeinsame Komponente `base.draw_nodes` |
| Legende Abschnitt 1 | `Beziehungstyp` + Einträge | `networks.py:432`; gemeinsame Komponente `base.relation_entries` (A.4) |
| Legende Abschnitt 2 – Titel | `Verbindungen` | statisch; `networks.py:433` |
| Legende Abschnitt 2 – Eintrag 1 (durchgezogen) | `im selben Bereich ({within})` – z. B. `im selben Bereich (4)` | dynamisch; `networks.py:434`; `{within}` = bestätigte Verbindungen zwischen Kontakten desselben (zuordenbaren) Bereichs (`:427`); auch `(0)` |
| Legende Abschnitt 2 – Eintrag 2 (gestrichelt) | `zwischen Bereichen ({between})` bzw. `zwischen Bereichen ({between}) · ohne Bereich ({unassigned})` | dynamisch; `networks.py:428-430`, `:435`. Zusatz ` · ohne Bereich ({unassigned})` nur, wenn mindestens eine bestätigte Verbindung einen Kontakt ohne zuordenbaren Wohnort berührt. Solche Verbindungen werden gestrichelt wie „zwischen Bereichen“ gezeichnet (`:477-483`). |
| Legende Abschnitt 3 (ohne Titel) | `gleicher Wohnort bzw. Wohnland` (Flächensymbol) | statisch; `networks.py:437`; immer gezeigt |
| Hinweis 1 | `Wohnortbereiche sind Kategorien, keine Entfernungen; Flächen bündeln Kontakte mit gleichem Wohnort bzw. Wohnland.` | statisch; `networks.py:440` |
| Hinweis 1 – Zusatz | ` Wohnort nicht zuordenbar: {ids}.` – z. B. ` Wohnort nicht zuordenbar: A07.` | dynamisch, an Hinweis 1 angehängt; `networks.py:439`; nur für Kontakte ohne zuordenbaren Wohnort **ohne** bestätigte Verbindung (diese werden nicht gezeichnet). Eigenimplementierung, nicht `Context.unresolved_note` (A.6). |
| Hinweis 2 | `Linien zeigen bestätigte Verbindungen; fehlende Linien bedeuten nicht zwangsläufig keinen Kontakt. {coverage_line}` – z. B. `… keinen Kontakt. Kontaktpaare: 10 · bestätigt 3 · verneint 2 · unbekannt 5.` | statischer Teil `networks.py:441` + gemeinsame Komponente `Context.coverage_line` (A.6). Bei leerer Abdeckungszeile bleibt ein Leerzeichen am Ende. |
| Fußzeile | wie A.3 | gemeinsame Komponente `base.footer_line` |
| Sonderfall: verneinte und unbekannte Paare | keine Linie; nur Zahlen in Hinweis 2 | `networks.py:3-5` (Modul-Docstring), Kanten nur `confirmed_edges` (`:32-33`) |
| Sonderfall: keine bestätigten Verbindungen | Legende `im selben Bereich (0)`, `zwischen Bereichen (0)`; alle Kontakte in der unteren Zone mit deren Beschriftung | `networks.py:427-435`, `:458-462` |
| Sonderfall: alle Wohnorte nicht zuordenbar | Grafik entfällt; Run-Protokoll `kein Wohnort zuordenbar` | `__init__.py:53` |

### G3 · Gruppenstruktur und Zugehörigkeit

Code: `g3`, `src/mares/network_v1/figures/networks.py:818-882`. Legende `bottom`.

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `G3 · Gruppenstruktur und Zugehörigkeit` | statisch; `networks.py:834` |
| Untertitel | `Von Ego benannte Gruppen, ihre Mitglieder und Egos Zugehörigkeit` | statisch; `networks.py:834` |
| Fallkennzeichen | siehe A.2 | `base.case_badge` |
| Gruppenlabel Zeile 1 | `{group_id} · {anzeigename} ({mitglieder})` – z. B. `C02 · Freundeskreis Universität ({n})` (fett, in Gruppenfarbe) | dynamisch; `group_label_lines`, `networks.py:680-682`; gezeichnet `:876`. `{mitglieder}` = Zahl der Mitglieder laut Mitgliedschaften. |
| Gruppenlabel – Anzeigename | erfasste Gruppenbezeichnung, bereinigt | `display_name`, `networks.py:674-677`: (a) ein Testdaten-Zusatz in Klammern am Ende wird entfernt (Regex `TEST_SUFFIX`, `:662`; z. B. `Kreis 1 (fiktive Bezeichnung)` → `Kreis 1`; erfasst `(fiktiv…)` / `(synthetisch…)` mit höchstens einem Folgewort); (b) leer → `ohne Bezeichnung` (`:676`); (c) länger als 34 Zeichen (`NAME_MAX`, `:660`) → auf 33 Zeichen gekürzt + `…` (`:677`). Die Daten bleiben unverändert. |
| Gruppenlabel Zeile 2 – Punkte | fünf Punkte, der erfasste Wert gefüllt | gemeinsame Komponente `base.ordinal_dots` (`base.py:394-405`); kein Punkt gefüllt ohne Wert |
| Gruppenlabel Zeile 2 – Text | `{wert}` (`1`…`5`, fett) oder Kurzcode `NS` / `KA` / `NA` / `n. e.` (kursiv, grau), ersatzweise `–` | `belonging_text`, `networks.py:666-671`; gezeichnet `:880-881`; Kurzcodes A.6 |
| Führungslinie | – (dünne Linie mit Punkt in Gruppenfarbe, ohne Text) | wenn das Label weiter als 0,12 in von der Umrisslinie liegt; `networks.py:870-873` |
| Gruppenumrisse | – (farbige Umrisse ohne Text) | `networks.py:844-852`; einheitliche Linienstärke ohne Bedeutung (`:652`) |
| Knotenbeschriftung | `{contact_id}` | gemeinsame Komponente `base.draw_nodes` |
| Zeile lose Kontakte | `keiner Gruppe zugeordnet, keine bestätigte Verbindung:` (kursiv, grau), rechts davon die Knoten | statisch, `LOOSE_LABEL` `networks.py:659`; gezeichnet `:857-861`; nur wenn es Kontakte ohne Gruppe und ohne bestätigte Verbindung gibt |
| Legende Abschnitt 1 | `Beziehungstyp` + Einträge | `networks.py:827`; gemeinsame Komponente `base.relation_entries` (A.4) |
| Legende Abschnitt 2 – Titel | `Zugehörigkeit zu einer Gruppe` | statisch; `networks.py:828` |
| Legende Abschnitt 2 – Eintrag 1 (Skala, Beispielwert 2 markiert) | `1 = sehr stark bis 5 = überhaupt nicht; der markierte Punkt zeigt den erhobenen Wert` | statisch; `networks.py:821` |
| Legende Abschnitt 2 – Eintrag 2 (Skala ohne Markierung) | `kein Wert ({named}): kein Punkt markiert` – z. B. `kein Wert (KA = keine Antwort, n. e. = nicht erhoben): kein Punkt markiert` | dynamisch; `networks.py:822-825`; nur wenn mindestens eine Gruppe keine Zugehörigkeit hat **und** eine Fehlart erfasst ist; `{named}` = vorkommende Kurzcodes mit Auflösung aus `codes.MISSING_LABELS` (A.6). Bei einem ungültigen Wert (`Cell.error`, `missing is None`) würde die Sortierung `key=list(MISSING_SHORT).index` (`networks.py:822`) mit `None` scheitern; ob ein solcher Fall die Grafik überhaupt erreicht, hängt von der vorgelagerten Validierung ab (nicht geprüft). Der Kurztext `–` (`:671`) ist damit in G3 praktisch nur erreichbar, wenn dieser Pfad nicht durchlaufen wird. |
| Legende Abschnitt 3 (ohne Titel) – Linie | `bestätigte Verbindung` | statisch; `networks.py:829`; immer gezeigt |
| Legende Abschnitt 3 – Ringsymbol | `Mitglied mehrerer Gruppen` | statisch; `networks.py:830`; nur wenn mindestens ein Kontakt Ringsegmente erhält (`membership_marked`, `:803-815`: mehrere Gruppen, die nicht ineinander verschachtelt sind) |
| Hinweis 1 | `Gruppen umfassen die von Ego zugeordneten Kontakte; gemeinsame Mitgliedschaft ist keine Verbindung.` | statisch; `networks.py:832` |
| Hinweis 2 | `{coverage_line}` – z. B. `Kontaktpaare: 10 · bestätigt 3 · verneint 2 · unbekannt 5.` | gemeinsame Komponente `Context.coverage_line`; `networks.py:833`; entfällt bei weniger als zwei Kontakten. Hier **ohne** den Satz zu fehlenden Linien (anders als G2). |
| Fußzeile | wie A.3 | gemeinsame Komponente `base.footer_line` |
| Sonderfall: verschachtelte Gruppe | engere Umrisslinie, Label darf auf der umgebenden Fläche liegen; keine Ringsegmente für deren Mitglieder | `networks.py:489-492`, `:542-549`, `:803-815` |
| Sonderfall: Gruppe ohne Mitglieder | kein Umriss und **kein Label** (nur Gruppen mit Umriss erhalten Labels) | `networks.py:840-843`, `:759` |
| Gruppenstatus T/P/N/NS | – (nicht als Text sichtbar) | wirkt nur über abgeleitete Verbindungen (`derive.py:5-9`); `codes.GROUP_STATUS` (`codes.py:105-110`) wird nicht angezeigt |
| Sonderfall: keine Gruppen | Grafik entfällt; Run-Protokoll `keine Gruppen erhoben` | `__init__.py:65` |

### P1 · Wohnortbereich und persönliche Nähe

Code: `p1` + `_area_point_figure`, `src/mares/network_v1/figures/matrices.py:37-59`;
gemeinsame Komponente `base.point_matrix`. Legende `bottom`.

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `P1 · Wohnortbereich und persönliche Nähe` | statisch; `matrices.py:56` |
| Untertitel | `Wie nah stehen Kontakte an verschiedenen Wohnorten?` | statisch; `matrices.py:56` |
| Fallkennzeichen | siehe A.2 | `base.case_badge` |
| Klammer | `Marburg und Mittelhessen` | gemeinsame Komponente `base._headers` (`base.py:513`) |
| Spaltenköpfe | `Marburg\n(Stadt)\nn = {n}`, `übriges\nMittelhessen\nn = {n}`, `übriges\nDeutschland\nn = {n}`, `übriges\nEuropa\nn = {n}`, `außerhalb\nEuropas\nn = {n}` | `base.area_columns` (`base.py:481-484`) + `base._headers` (`base.py:506`). `{n}` = alle Kontakte mit zuordenbarem Wohnort im Bereich, **auch ohne Nähe-Angabe** (`_area_counts`, `matrices.py:33-34`, `:49`). Immer alle fünf Spalten, `n = 0` möglich. |
| Zeilentitel | `Persönliche Nähe` (fett) | statisch; `matrices.py:57`; gezeichnet `base.py:514-515` |
| Zeilen | `1 · sehr nah`, `1,5`, `2 · nah`, `2,5`, `3 · weniger nah`, `3,5`, `4 · außerhalb der Kreise` | gemeinsame Komponente `base.closeness_rows(False)` (A.7); `matrices.py:57`. Alle sieben Zeilen immer, auch leer. |
| Zeile fehlende Nähe | `keine Angabe` (kursiv, grau, mit Abstand abgesetzt) | `matrices.py:42-44`: nur wenn ein gezeigter Kontakt keine Nähe hat. Literal hier eigens (nicht über `closeness_rows(True)`). |
| Zellinhalt | Punkt in Beziehungstypfarbe + `{contact_id}` | `base.py:598-605` |
| Legende | `Beziehungstyp` + Einträge | `matrices.py:48`; gemeinsame Komponente `base.relation_entries` (A.4) |
| Hinweis 1 | `Wohnortbereiche sind Kategorien, keine Entfernungen; persönliche Nähe und Wohnort sind getrennte Merkmale.` | statisch; `matrices.py:58` |
| Hinweis 2 | `Wohnort nicht zuordenbar (nicht dargestellt): {ids}.` | gemeinsame Komponente `Context.unresolved_note`; `matrices.py:48`; nur wenn Kontakte ohne zuordenbaren Wohnort existieren |
| Fußzeile | wie A.3 | gemeinsame Komponente `base.footer_line` |
| Sonderfall: kein Wohnort zuordenbar | Grafik entfällt; `kein Wohnort zuordenbar` | `__init__.py:55` |
| Sonderfall: keine Nähe erfasst | Grafik entfällt; `keine erhobene persönliche Nähe` | `__init__.py:55` |

### P2 · Wohnortbereich und Kontakthäufigkeit

Code: `p2` + `_area_point_figure`, `src/mares/network_v1/figures/matrices.py:37-51`, `:62-69`.
Legende `bottom`.

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `P2 · Wohnortbereich und Kontakthäufigkeit` | statisch; `matrices.py:65` |
| Untertitel | `Wie häufig besteht Kontakt zu Personen an verschiedenen Wohnorten?` | statisch; `matrices.py:65` |
| Fallkennzeichen | siehe A.2 | `base.case_badge` |
| Klammer | `Marburg und Mittelhessen` | `base.py:513` |
| Spaltenköpfe | wie P1 (`{bereich}\nn = {n}`) | `base.area_columns` + `base._headers`; `{n}` = alle zuordenbaren Kontakte des Bereichs, auch ohne Häufigkeitsangabe |
| Zeilentitel | `Kontakthäufigkeit` (fett) | statisch; `matrices.py:66` |
| Zeilen | `(Fast) täglich`, `Wöchentlich`, `Mehrmals monatlich`, `Etwa monatlich`, `Wenige Male/Jahr oder seltener` | `codes.CONTACT_FREQUENCY` (`codes.py:66-72`), übernommen `matrices.py:63`; ohne Codezahlen |
| Zeile fehlende Häufigkeit | `keine Angabe` (kursiv, grau) | `matrices.py:42-44`; nur wenn ein gezeigter Kontakt keine Häufigkeit hat |
| Zellinhalt | Punkt in Beziehungstypfarbe + `{contact_id}` | `base.py:598-605` |
| Legende | `Beziehungstyp` + Einträge | `matrices.py:48`; gemeinsame Komponente `base.relation_entries` |
| Hinweis 1 | `Kontakthäufigkeit ist eine geordnete Kategorie; die Zeilenabstände sind keine gemessenen Zeitabstände.` | statisch; `matrices.py:68` |
| Hinweis 2 | `Wohnort nicht zuordenbar (nicht dargestellt): {ids}.` | gemeinsame Komponente `Context.unresolved_note`; `matrices.py:48` |
| Fußzeile | wie A.3 | gemeinsame Komponente `base.footer_line` |
| Sonderfall: kein Wohnort zuordenbar | Grafik entfällt; `kein Wohnort zuordenbar` | `__init__.py:57` |
| Sonderfall: keine Häufigkeit erfasst | Grafik entfällt; `keine erhobene Kontakthäufigkeit` | `__init__.py:57` |

### P3 · Kommunikationsformen nach Wohnortbereich

Code: `p3` + `_heat_figure`, `src/mares/network_v1/figures/matrices.py:89-118`;
gemeinsame Komponente `base.heat_matrix`. Legende `bottom` (`HEAT_LEGEND`).

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `P3 · Kommunikationsformen nach Wohnortbereich` | statisch; `matrices.py:115` |
| Untertitel | `Auf welchen Wegen wird mit Kontakten an verschiedenen Wohnorten kommuniziert?` | statisch; `matrices.py:115` |
| Fallkennzeichen | siehe A.2 | `base.case_badge` |
| Klammer | `Marburg und Mittelhessen` | `base.py:513` |
| Spaltenköpfe | `{bereich}\nn = {n}` (fünf Bereiche, umbrochen wie P1) | `base.area_columns` + `base._headers` (`base.py:655`). `{n}` = zuordenbare Kontakte des Bereichs **mit** Angabe zu Kommunikationsformen (`bases`, `matrices.py:72-86`) – andere Bedeutung als in P1/P2. |
| Abschnittstitel (Zeilengruppen, grau, fett, rechtsbündig) | `Persönliche Kommunikation`, `Synchron auf Distanz`, `Asynchron`, `Weitere Formen` | statisch; `COMMUNICATION_SECTIONS`, `matrices.py:100-105`; gezeichnet `base.py:661-664` |
| Zeilen | `Persönlich` (unter „Persönliche Kommunikation“), `Videoanruf`, `Telefonat` (unter „Synchron auf Distanz“), `Sprachnachrichten`, `Textnachrichten / Chat` (unter „Asynchron“), `Sonstiges` (unter „Weitere Formen“) | `codes.COMMUNICATION_FORMS` (`codes.py:85-92`), zugeordnet `matrices.py:113`; alle immer gezeigt |
| Zellinhalt | `{anzahl}` (fett; weiß bei Anteil > 60 %) | `base.heat_cell` (`base.py:619-627`), gezeichnet `base.py:671-675`. `0` → leere weiße Zelle; Spalte mit `n = 1` → neutral grau, `1` oder leer; Spalte mit `n = 0` → leer. Die Zahl ist absolut; die Farbintensität = Anteil an `n`. |
| Zeile fehlende Angabe | `ohne Angabe` (kursiv, grau); Zellen gestrichelt mit `{anzahl}` (grau) oder leer | `base.py:678-687`; nur wenn mindestens ein zuordenbarer Kontakt keine Angabe hat (alle Fehlarten zusammen; ebenso Kontakte ohne Zeile in Tabelle B, `matrices.py:109-111`) |
| Legende (ohne Titel) – Farbskala | `Farbintensität = Anteil im jeweiligen Wohnortbereich (0–100 %)` | statisch; gemeinsame Komponente `HEAT_LEGEND`, `base.py:693` |
| Legende – Fläche | `n = 1: neutral` | statisch; `base.py:694` |
| Legende – Text | `Zahlen = Anzahl der Kontakte · leer = keine Nennung · Mehrfachnennungen möglich` (grau) | statisch; `base.py:695` |
| Legende Beziehungstyp | – (nicht vorhanden) | `HEAT_LEGEND` enthält keine Beziehungstypen |
| Hinweis 1 | `n = Kontakte des Bereichs mit Angabe; fehlende Angaben stehen getrennt und zählen nie als „nein“.` | statisch; `matrices.py:117` |
| Hinweis 2 | `Wohnort nicht zuordenbar (nicht dargestellt): {ids}.` | gemeinsame Komponente `Context.unresolved_note`; `matrices.py:94` |
| Fußzeile | wie A.3 | gemeinsame Komponente `base.footer_line` |
| Sonderfall: keine Kommunikationsformen erfasst | Grafik entfällt; `keine erhobenen Kommunikationsformen` | `__init__.py:59` |
| Sonderfall: alle Wohnorte nicht zuordenbar | Grafik wird **nicht** übersprungen; alle Spalten `n = 0`, Zellen leer, Hinweis 2 nennt alle IDs | `__init__.py:59` prüft keinen Wohnort |

### P4 · Sprachen nach Wohnortbereich

Code: `p4` + `language_rows` + `_heat_figure`, `src/mares/network_v1/figures/matrices.py:89-96`,
`:121-155`; gemeinsame Komponente `base.heat_matrix`. Legende `bottom` (`HEAT_LEGEND`).

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `P4 · Sprachen nach Wohnortbereich` | statisch; `matrices.py:152` |
| Untertitel | `In welchen Sprachen wird mit Kontakten an verschiedenen Wohnorten kommuniziert?` | statisch; `matrices.py:152` |
| Fallkennzeichen | siehe A.2 | `base.case_badge` |
| Klammer | `Marburg und Mittelhessen` | `base.py:513` |
| Spaltenköpfe | `{bereich}\nn = {n}` | wie P3; `{n}` = zuordenbare Kontakte des Bereichs mit Sprachangabe |
| Abschnittstitel | – (keiner) | `sections=[(None, rows)]`, `matrices.py:153` |
| Zeilen – feste Sprachen | `Spanisch`, `Deutsch`, `Englisch`, `Portugiesisch` | `codes.LANGUAGES` ohne Code 5 (`codes.py:94-100`, `matrices.py:129`); immer gezeigt |
| Zeilen – benannte andere Sprachen | `{sprachname}` wie erfasst (Freitext aus `other_languages`), z. B. `Französisch` | dynamisch; `matrices.py:124-130`; eine Zeile je Name, sortiert nach Häufigkeit absteigend, dann alphabetisch. Schreibvarianten werden **nicht** zusammengefasst. Keine Kürzung. |
| Zeile – andere Sprache ohne Namen | `Andere Sprache (ohne Bezeichnung)` | statisch; `matrices.py:144-145`; nur wenn Code 5 ohne benannte Sprache vorkommt. Der Codetext `Andere Sprache` (`codes.py:99`) erscheint sonst nicht. |
| Zellinhalt | `{anzahl}` wie P3 | `base.heat_cell` |
| Zeile fehlende Angabe | `ohne Angabe` | `base.py:678-687`, wie P3 |
| Legende (ohne Titel) | `Farbintensität = Anteil im jeweiligen Wohnortbereich (0–100 %)` · `n = 1: neutral` · `Zahlen = Anzahl der Kontakte · leer = keine Nennung · Mehrfachnennungen möglich` | gemeinsame Komponente `HEAT_LEGEND`, `base.py:691-697` (identisch zu P3) |
| Hinweis 1 | `Mehrsprachige Kontakte zählen in jeder verwendeten Sprache; Anteile summieren sich daher nicht zu 100 %.` | statisch; `matrices.py:154` |
| Hinweis 2 | `Wohnort nicht zuordenbar (nicht dargestellt): {ids}.` | gemeinsame Komponente `Context.unresolved_note`; `matrices.py:94` |
| Basis-Hinweis | – (der P3-Hinweis `n = Kontakte des Bereichs mit Angabe …` fehlt in P4) | Vergleich `matrices.py:117` / `:154` |
| Sprachgebrauch (M/S, überwiegend …) | – (nicht sichtbar) | `codes.LANGUAGE_USE_FLAGS`, `codes.language_use_label` (`codes.py:102`, `:249-254`) werden in P4 nicht verwendet |
| Fußzeile | wie A.3 | gemeinsame Komponente `base.footer_line` |
| Sonderfall: keine Sprachen erfasst | Grafik entfällt; `keine erhobenen Sprachen` | `__init__.py:61` |

### P5 · Beziehungsfunktionen und persönliche Nähe

Code: `p5`, `src/mares/network_v1/figures/matrices.py:158-187`; gemeinsame Komponente
`base.point_matrix`. Legende `bottom`.

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `P5 · Beziehungsfunktionen und persönliche Nähe` | statisch; `matrices.py:182` |
| Untertitel | `Welche Funktionen haben nahe und weniger nahe Kontakte?` | statisch; `matrices.py:182` |
| Fallkennzeichen | siehe A.2 | `base.case_badge` |
| Klammer | – (keine) | `point_geometry(..., bracket=False)`, `matrices.py:181`; `base.py:570` |
| Spaltenköpfe (immer) | `Persönlicher\nRückhalt / Rat\nn = {n}`, `Gemeinsame\nAktivitäten /\nGespräche\nn = {n}`, `Praktische Hilfe\nim Alltag\nn = {n}`, `Sprachliche Hilfe /\nÜbersetzung\nn = {n}`, `Sonstiges\nn = {n}` | `FUNCTION_LABELS`, `matrices.py:158-161`, + `base._headers` (`base.py:506`). Wortlaut = `codes.FUNCTIONS` (`codes.py:73-80`) mit händischen Umbrüchen – **zweite Implementierung desselben Wortlauts**. `{n}` = Zahl der Nennungen dieser Funktion (`Counter(i.column …)`, `matrices.py:185`); `n = 0` möglich. |
| Spaltenkopf (bedingt) | `Nichts davon\nn = {n}` | nur wenn mindestens ein Kontakt Code 0 hat; `matrices.py:174`; mit Abstand abgesetzt (`:178`) |
| Spaltenkopf (bedingt) | `keine Angabe\nn = {n}` | nur wenn mindestens ein Kontakt keine Funktionsangabe hat; `matrices.py:160`, `:172`, `:174`. Normal gesetzt (nicht kursiv/grau – anders als die Zeile `keine Angabe`). |
| Zeilentitel | `Persönliche Nähe` (fett) | statisch; `matrices.py:186` |
| Zeilen | `1 · sehr nah`, `1,5`, `2 · nah`, `2,5`, `3 · weniger nah`, `3,5`, `4 · außerhalb der Kreise` | gemeinsame Komponente `base.closeness_rows` (A.7); `matrices.py:176` |
| Zeile fehlende Nähe | `keine Angabe` (kursiv, grau) | `base.py:704-705`; nur wenn ein Kontakt keine Nähe hat |
| Zellinhalt | Punkt in Beziehungstypfarbe + `{contact_id}`; derselbe Kontakt in jeder seiner Funktionsspalten | `matrices.py:169-172`, `base.py:598-605` |
| Legende | `Beziehungstyp` + Einträge | `matrices.py:183`; gemeinsame Komponente `base.relation_entries` |
| Hinweis | `Mehrfachnennungen möglich; Kontakte können in mehreren Funktionsspalten erscheinen.` | statisch; `matrices.py:184` |
| Wohnort-Hinweis | – (keiner) | P5 zeigt alle Kontakte unabhängig vom Wohnort; kein `unresolved_note` |
| Freitext zu „Sonstiges“ | – (nicht sichtbar) | `codes.FUNCTION_OTHER` (`codes.py:82`) wird nicht angezeigt |
| Fußzeile | wie A.3 | gemeinsame Komponente `base.footer_line` |
| Sonderfall: keine Funktionen erfasst | Grafik entfällt; `keine erhobenen Beziehungsfunktionen` | `__init__.py:63` |
| Sonderfall: keine Nähe im Fall | Grafik wird **nicht** übersprungen; alle Punkte in der Zeile `keine Angabe` | `__init__.py:63` prüft nur Funktionen |

### X1 · Geografische Verteilung des persönlichen Netzwerks

Code: `x1`, `src/mares/network_v1/figures/maps.py:694-749` (Layout `x1_layout`, Beschriftungen
`Place.head` / `tail` / `sub`, `maps.py:177-216`). Legende `bottom`. Stand nach der redaktionellen
Bereinigung der Kanonisierung.

| Element | Aktueller sichtbarer Wortlaut | Herkunft / Bedingung |
|---|---|---|
| Titel | `Geografische Verteilung des persönlichen Netzwerks` | statisch; `maps.py:712`. **Ohne** Grafikcode (anders als G1–G3, P1–P5). |
| Untertitel | – (keiner) | `page(..., subtitle=None)`, `maps.py:712`; der Kopf ist niedriger (`base.HEADER_H_TITLE_ONLY`). |
| Fallkennzeichen | siehe A.2 | gemeinsame Komponente `base.case_badge` |
| Panelüberschriften | `{Region} · n = {anzahl}` – Regionen `Amerika`, `Afrika`, `Asien`, `Ozeanien`, `Weitere Regionen`, `Europa (ohne Deutschland)`, `Deutschland`; z. B. `Amerika · n = 7`, `Deutschland · n = 21` | Regionstitel `REGIONS`, `maps.py:81-87`; Muster `Panel.title`, `maps.py:261`; fett oben links im Panel. Amerika, Europa und Deutschland immer (auch mit `n = 0`), die übrigen nur bei Bedarf. `{anzahl}` = im Panel gezeichnete Kontakte. |
| Ortsbeschriftung Zeile 1 – fett | `{ort}` bzw. `{ort} und Umgebung` (Ortsgruppe); bei nur bekanntem Wohnland der deutsche Ländername | `Place.head`, `maps.py:177-181`; Ortsname wie erfasst (`residence_place`, Schreibung des größten Ortes der Gruppe); Ländername `NAME_DE` der Basiskarte, sonst das erfasste Wohnland (`maps.py:617`). Mit weißem Halo und blasser, rahmenloser Fläche. |
| Ortsbeschriftung Zeile 1 – Rest | ` · {land}` (außerhalb Deutschlands), ` · nur Land bekannt` (nur Wohnland bekannt), ` · n = {anzahl}` (ab zwei Kontakten) – z. B. `Bogotá · Kolumbien · n = 3`, `Madrid · Spanien`, `Marburg · n = 8`, `Marburg und Umgebung · n = 14`, `Berlin` | `Place.tail`, `maps.py:183-195`. `{land}` = erfasstes Wohnland (`residence_country`), ersatzweise `NAME_DE` (`maps.py:619`); bei einer Ortsgruppe über eine Grenze mehrere Länder mit ` / `. Im Panel Deutschland kein Land. Ein einzelner Kontakt erhält **keine** Zahl. |
| Ortsbeschriftung zweizeilig | `{ort}` / `{land} · n = {anzahl}` | `Place.title`, `maps.py:198-202`; nur wo die einzeilige Fassung keinen freien Platz am Kreis findet (Platzierungsregel). |
| Ortsbeschriftung Zeile 2 (Ortsgruppe) | `{ort} {anzahl} · {ort} · …` (kleiner, grau), umbrochen ab etwa 1,7 Zoll – z. B. `Marburg 10 · Cölbe · Kirchhain` / `Lahntal · Wehrda` | `Place.sub`, `maps.py:205-216`; Zahl nur bei Orten mit mehr als einem Kontakt; nur bei Ortsgruppen. |
| Knotenbeschriftung | `{contact_id}` | gemeinsame Komponente `base.draw_nodes` |
| Ortspunkte, Linien, hohle Ringe, Flächen | – (ohne Text) | `x1`, `maps.py:721-735` |
| Legende Abschnitt 1 | `Beziehungstyp` + Einträge | `maps.py:704`; gemeinsame Komponente `base.relation_entries` (A.4), einschließlich `keine Angabe` bei fehlendem Beziehungstyp |
| Legende Abschnitt 2 – Eintrag 1 | `Wohnort (Ortspunkt)` | statisch; `maps.py:705`; immer |
| Legende Abschnitt 2 – Eintrag 2 | `○ weiterer Ort einer Ortsgruppe` (grau) | statisch; `maps.py:706`; nur wenn eine Ortsgruppe weitere Orte mit eigenem Punkt hat |
| Legende Abschnitt 2 – Eintrag 3 | `nur Wohnland bekannt (Lage unscharf)` (gestrichelte Fläche) | statisch; `maps.py:707`; nur wenn ein Kontakt nur mit Wohnland erfasst ist |
| Hinweis 1 | `Wohnort nicht darstellbar: {ids}.` – z. B. `Wohnort nicht darstellbar: A22.` | dynamisch; `maps.py:710-711`; nur wenn Kontakte nicht gezeichnet werden können – Wohnort nicht zuordenbar **oder** Ort ohne Eintrag im Ortsverzeichnis, zusammen in Kontaktreihenfolge, ohne Grund. **Eigene Formulierung**, nicht `Context.unresolved_note` (A.6). |
| Hinweis 2 (Quelle) | `Kartengrundlage: Natural Earth.` | statisch; `maps.py:711`; immer. Vollständige Quellenangabe in [`network-v1.md`](network-v1.md) §6. |
| Fußzeile | `MARES · network_v1 · {anzahl_kontakte} Kontakte` – z. B. `MARES · network_v1 · 32 Kontakte` | eigene Fußzeile, `maps.py:713` (Argument `footer` von `base.page`). Keine Gruppenzahl, **kein Datenqualitätsstatus**, auch bei authentischen Fällen nicht. `{anzahl_kontakte}` = alle Kontakte des Falls. |
| Sonderfall: Ortsverzeichnis oder Basiskarte fehlt | Grafik entfällt; Run-Protokoll `Ortsverzeichnis fehlt (…)` bzw. `Basiskarte fehlt (…)` | A.9 |
| Sonderfall: kein Wohnort zuordenbar | Grafik entfällt; `kein Wohnort zuordenbar` | `_x1_missing`, `figures/__init__.py` |

Bei der Kanonisierung entfernt (nur noch in der Dokumentation): Grafikcode im Titel; Untertitel
`Wo leben die Kontakte? Wohnorte nach Region (experimentell)`; Legendeneinträge `Kontakte des Ortes,
daneben gesetzt` und `Zahl = Kontakte am Ort`; Hinweis `Experimentelle Zusatzgrafik (Fassung …), keine
Standardgrafik. Lage = Ortspunkt, Kontakte daneben; „und Umgebung“: Nachbarorte zusammengefasst; Panels
mit eigenem Maßstab; keine Verbindungslinien (siehe G2). Karte: Natural Earth.`; Hinweis `Ort ohne
Koordinaten im Ortsverzeichnis: …`; Gruppenzahl und Datenqualität in der Fußzeile.

---

## C. Mehrfach implementierte oder abweichende Wortlaute (Übersicht)

| Wortlaut | Orte | Bemerkung |
|---|---|---|
| `Beziehungstyp` | `networks.py:137, 432, 827`; `matrices.py:48, 183`; `maps.py:704` | identisch, sechs Literale |
| `Marburg und Mittelhessen` | `base.py:513`; `networks.py:457`; `places.py:76` | identisch, zwei zeichnende Stellen |
| Titeltext je Grafik | `__init__.py:50-64` und `networks.py:145, 442, 834`, `matrices.py:56, 65, 115, 152, 182` | identisch bis auf Präfix `{code} · ` |
| Funktionsnamen | `codes.py:73-80`; `matrices.py:158-161` | gleicher Wortlaut, zweite Fassung mit Umbrüchen |
| Nähe-Skala | `codes.py:45-53`; `base.py:700-706`; `networks.py:139-140` | G1-Legende verkürzt (`4 außerhalb`) |
| Fehlende Antwort | `keine Angabe` (`base.py:101, 691`; `matrices.py:43, 160`), `ohne Angabe` (`base.py:680`), `Nähe ohne Angabe` (`networks.py:162`), `kein Wert (…)` (`networks.py:825`) | vier Formulierungen |
| Nicht zuordenbarer Wohnort | `base.py:140` (`… (nicht dargestellt): …`); `networks.py:439` (`Wohnort nicht zuordenbar: …`); `networks.py:420` (`… (keinem Bereich zugeordnet):`) | drei Formulierungen; X1 zusätzlich `Wohnort nicht darstellbar: …` (`maps.py:711`) |
| `Persönliche Nähe` | `networks.py:138` (Legendentitel G1); `matrices.py:57, 186` (Zeilentitel P1, P5) | identisch |
| `Mehrfachnennungen möglich` | `base.py:695`; `matrices.py:184` | identisch als Teilsatz |
| Fußzeile | `base.py:159-165` (G1–G3, P1–P5); `maps.py:713` (X1) | X1 ohne Gruppenzahl und ohne Datenqualität |
| `n = {anzahl}` | Spaltenköpfe (`base._headers`), Bandköpfe G2, Panelüberschriften und Ortsbeschriftungen X1 | gleiches Muster, verschiedene Bezugsgrößen (siehe die Abschnitte) |
