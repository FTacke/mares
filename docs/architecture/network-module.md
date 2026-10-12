# Netzwerkmodul

**Status: implementiert (Stand 2026-10-12), Paketformat als Entwurf.** Dieses Dokument legt fest, was
`mares.networks` liest, wie es Beziehungen konstruiert, was es prüft und ausgibt und was es ausdrücklich
nicht berechnet. Es ergänzt [`modules.md`](modules.md) (Umfang) und [`data-contract.md`](data-contract.md)
(IDs, Statusdimensionen); die Entscheidungen dahinter stehen in
[`ADR-0002`](../decisions/ADR-0002_2026-10-12_netzwerkmodul.md). Grafiken:
[`visualization-conventions.md`](visualization-conventions.md). Der erste Fall:
[`../methodology/pilot-case-001-2.md`](../methodology/pilot-case-001-2.md).

Code: [`src/mares/networks/`](../../src/mares/networks/__init__.py)

## 1. Soll und Ist

| | Ist (implementiert, getestet mit synthetischen Daten) | Nicht vorhanden |
|---|---|---|
| Eingang | Import eines CSV-Pakets (§3) aus `INTAKE` oder `PRIMARY` | Import der Excel-Erhebungssheets; Registrierung des Falls |
| Prüfung | Validator mit Fehlern, Warnungen, offenen Forschungsfragen (§5) | fachliche Prüfung gegen die Originalbögen |
| Netzwerk | Alter-Alter-Beziehungen aus bestätigten Gruppen, explizite Ja/Nein/Unbekannt-Angaben im Modell (§4) | Format für explizit erfragte Paare im Paket |
| Auswertung | beschreibende Häufigkeiten, Gruppengrößen, Mehrfachzugehörigkeiten (§6) | Kennzahlen, die eine vollständige Erhebung voraussetzen |
| Ausgabe | ein Lauf je Aufruf unter `WORKSPACE/runs/<RUN-ID>/` mit Berichten, Tabellen, sechs Grafiken (§7) | Ablage in `PRIMARY/derived/`, Datensatzversion `DS-…` |

Die Ergebnisse eines Laufs sind **regenerierbare Arbeitsdaten**. Sie sind weder erhalten noch gesichert und
tragen keine Datensatzversion, solange `PRIMARY` und das Register fehlen.

## 2. Identitäten

Das Modell hält Dinge getrennt, die in der Quelle verschmolzen sind ([`model.py`](../../src/mares/networks/model.py)):

| Objekt | Bedeutung | Anmerkung |
|---|---|---|
| Fall (`CaseIdentity`) | MARES-Fall | `source_label` (historische Kennung, z. B. `001-2`) und **optionale** `canonical_case_id`. Die Quellkennung ist **keine** Fall-ID; es wird nie zugeordnet, solange kein Register existiert. Die Verknüpfung einer Folgeerhebung mit der früheren Erhebung ist offen. |
| Sitzung (`SurveySession`) | eine konkrete Erhebung | Datum, Erhebungsart, Paketversion, Herkunftsvermerk (z. B. studentische Erhebung); bleibt Teil der Provenienz |
| Kontakt (`Contact`) | eine von Ego genannte Person | kanonische ID `A01`, `A02`, … **ohne Obergrenze**; dazu `source_block` und `source_local_id` der Quelle |
| Kontaktattribut | Merkmal eines Kontakts | Codes bleiben Zeichenketten; leer = nicht erhoben |
| Gruppe, Mitgliedschaft | eingezeichnete Umrandung und wer darin liegt | Bewertung `confirmed` / `needs_review`; Mitgliedschaft `confirmed` / `candidate` |
| Beziehung (`Tie`) | ungeordnetes Paar mit Zustand | `yes` / `no` / `unknown` / nicht erhoben (§4) |
| Quelldatei (`SourceFile`) | Eingabedatei mit SHA-256 | die Verarbeitungsversion ist der Lauf (`RUN-…`), nicht das Modell |

**Kanonische Kontakt-IDs** sind der Rang in der Quellreihenfolge (Blatt, dann lokale Nummer), unabhängig von der
Blattnummerierung: Blatt 1 `A01`–`A15` und Blatt 2 `A01`–`A07` ergeben `A01`–`A22`
([`identity.py`](../../src/mares/networks/identity.py)). Die Quellposition bleibt erhalten.

## 3. Paketformat `mares-network-package/v0-draft`

Ein Paket ist ein Ordner. Das Format ist ein **Importvertrag des Moduls**, kein Erhebungsinstrument; es wird bei
der Festlegung der Instrument-Version überprüft.

**Technik:** UTF-8 mit oder ohne BOM; Spaltentrenner `;`; LF oder CRLF; mehrere Codes in einer Zelle durch `|`;
ein **leeres Feld heißt nicht erhoben** – nie `0`, nie `nein`, nie ein Standardwert.

| Datei | Pflicht | Inhalt |
|---|---|---|
| `contacts.csv` | ja | Kontakte und Attribute (Spalten unten) |
| `groups.csv` | ja | `group_id; label; map_label; assessment; comment` – `assessment` ∈ `confirmed`, `needs_review` |
| `group_memberships.csv` | ja | `group_id; contact_id; status; derivable_edge; source` – `status` ∈ `confirmed`, `candidate` |
| `codebook.csv` | ja | `field; code; meaning_de`: gültige Codes je Feld |
| `manifest.json` | ja | Herkunft: `source_case_label`, `source_date`, `source_interview_type`, `package_version`, `contact_count`, … |
| `observed_edges.csv` | nein | Kantentabelle als **Importbeleg** (§4), kein zweiter Datenweg |
| `review_items.csv` | nein (Warnung) | bekannte Unklarheiten: `review_id; priority; reference; field; description; recommended_action` |
| `source_clarifications.csv` | nein | ausdrückliche Bestätigungen von Gruppen (`group_id; member_contact_ids; …`), gegen die Mitgliedschaften geprüft |
| `SHA256SUMS.txt` | nein (Warnung) | Prüfsummen der Paketdateien |

**`contacts.csv`:** Identität `source_case_label`, `contact_id`, `source_block`, `source_local_id` (Pflicht);
Attribute (erwartet = Warnung, wenn leer; optional = nur gezählt):

| Spalte | Modellattribut | Codebuchfeld | Mehrfach | Stufe |
|---|---|---|---|---|
| `relation_codes` | relation | `relation` | ja | erwartet |
| `birth_country_iso3`, `birth_country_source` | birth_country, birth_country_source | – (ISO-3166-1-Alpha-3) | nein | optional |
| `residence_city`, `residence_country_iso3` | residence_city, residence_country | – | nein | erwartet |
| `contact_frequency_code` | contact_frequency | `contact_frequency` | nein | erwartet |
| `table_ring_near_value` | closeness | `closeness_1_5` | nein | erwartet |
| `media_codes` | media | `media` | ja | optional |
| `language_codes` | language | `language` | ja | erwartet |
| `language_mode_code` | language_mode | `language_mode` | nein | optional |
| `function_codes` | function | `function` | ja | optional |
| `name_generator_codes` | name_generator | `name_generator` | ja | optional |
| `review_flags` | review_flags | – | `;` oder `\|` | optional |

**Mehrfachcodes und Bereiche** ([`codes.py`](../../src/mares/networks/codes.py)): `1|2|3` bleibt Liste; ein wohldefinierter
aufsteigender Bereich wird zu Einzelcodes aufgelöst (`1-6`, `1–6`, `G1-G3`, `G1-3`) und als Hinweis vermerkt;
Duplikate, leere Elemente, absteigende oder unplausibel weite Bereiche sind Syntaxfehler. Gültigkeit entscheidet
das **Codebuch des Pakets**, nicht der Code: ein Bereich, der über das Codebuch hinausreicht, ist ein Fehler.

**Nähe:** maßgeblich ist ausschließlich `table_ring_near_value` (Codebuch `closeness_1_5`, Werte 1–5). Die Position
auf der handgezeichneten Karte und ihre abweichende Legende werden weder gelesen noch umgerechnet.

## 4. Netzwerkkonstruktion ([`build.py`](../../src/mares/networks/build.py))

1. Eine **bestätigte Gruppe** ist eine Clique: alle bestätigten Mitglieder innerhalb derselben Umrandung kennen sich
   (Erklärung der Projektseite). Daraus entstehen Beziehungen `yes` mit Basis `clique_rule`.
2. Identische Paare aus mehreren Gruppen sind **eine** Beziehung; die Gruppen bleiben als Herkunft erhalten.
   Eine in andere Gruppen eingebettete Gruppe fügt keine eigenen Beziehungen hinzu.
3. Gruppen mit `needs_review` und Mitgliedschaften mit `candidate` erzeugen **keine** Beziehung.
4. **Ein Paar ohne Beleg ist nicht erhoben (unbekannt), nie `no`.** Das Modell hat keinen Weg, Abwesenheit in `no` zu
   verwandeln; nur eine ausdrückliche Angabe (`Tie(..., NO, EXPLICIT)`) ist `no`. Gefragt, aber unbekannt ist `unknown`.
   Die vier Zustände bleiben getrennt ([`data-contract.md`](data-contract.md) §5).
5. Widerspricht eine ausdrückliche Angabe einer Cliquen-Beziehung, wird kein Netzwerk gebaut (Fehler).
6. Die Kantentabelle des Pakets ist ein **Beleg**: Der Validator vergleicht sie mit der Ableitung (fehlende, nicht
   ableitbare, doppelte, selbstbezügliche Kanten; abweichende Gruppen; Anzahl laut Manifest). Eine Abweichung ist ein
   harter Fehler; übernommen wird immer die Ableitung.

Das Modell kann explizite Ja/Nein/Unbekannt-Angaben speichern (`build_network(dataset, explicit_ties=…)`). Ein
Dateiformat dafür gibt es noch nicht.

## 5. Validierung ([`validate.py`](../../src/mares/networks/validate.py))

Drei Klassen, die nie vermischt werden:

| Klasse | Bedeutung | Wirkung |
|---|---|---|
| **Harte Fehler** | Format- oder Konsistenzverletzung | der Lauf verarbeitet nichts weiter; Status `FAILED_VALIDATION` |
| **Warnungen** | nutzbar, aber zu wissen (fehlendes erwartetes Attribut, nicht auflösbare Herkunftsangabe, Markierung ohne Review-Eintrag, fehlende Prüfsummen) | Verarbeitung läuft; Status `PASSED_WITH_WARNINGS` |
| **Offene Forschungsfragen** | dokumentierte Unsicherheit über die Quelle (`review_items.csv`; dazu `SW-01`–`SW-03`: Fall-ID, Provenienz, fehlende Quellenprüfung) | blockiert nichts; wird nie von der Software entschieden |

Geprüft werden unter anderem: eindeutige und kanonisch fortlaufende Kontakt-IDs, Übereinstimmung mit der
Quellposition, Quellkennung zwischen Manifest und Tabelle, Kontaktzahl laut Manifest; Codes gegen das Codebuch,
Einzelwertfelder, Duplikate; ISO-Ländercodes, Ort/Land-Plausibilität ohne erfundene Werte; Gruppen- und
Mitgliedschaftsreferenzen, Statuskonsistenz; Klärungen gegen Mitgliedschaften; Prüfsummen; Kantenbeleg (§4).

**Der Validator setzt nie einen Qualitätsstatus.** Ein bestandener technischer Test ist keine wissenschaftliche
Validierung: die Datenqualität bleibt `UNREVIEWED`, die Freigabe `NOT_DECIDED`, bis Personen entscheiden
([`data-contract.md`](data-contract.md) §4). Provenienz, Datenqualität und Freigabe bleiben getrennte Dimensionen.

## 6. Auswertung ([`analysis.py`](../../src/mares/networks/analysis.py))

Erlaubt und implementiert: Anzahl und Merkmale der Kontakte; Verteilungen aller Codefelder (leere Kategorien
bleiben sichtbar, „nicht erfasst“ wird getrennt gezählt); Wohnort, geografische Einordnung (Referenzort,
übriges Deutschland, außerhalb, unbekannt – Regel in [`geo.py`](../../src/mares/networks/geo.py), Parameter
`--local-place`); Wohnland × Geburtsland; exakte Sprachrepertoires; Anzahl belegter Beziehungen und Paare ohne
Angabe (als Zählung); Gruppengrößen; Mehrfachzugehörigkeit.

**Bewusst nicht berechnet** (`REFUSED_METRICS`): Dichte, Kohäsion, Segregation und Homophilie, Zentralitäten,
Komponentenstatistiken. Sie sind bei unvollständiger Alter-Alter-Erhebung nicht interpretierbar. Jede strukturelle
Ausgabe trägt den Erhebungs- und Vollständigkeitsstatus (`SurveyStatus`: Quelle, Sitzung, Alter-Alter-Erhebung,
Vollständigkeit, Datenqualität). Ein Netzwerk gilt nur als vollständig, wenn jedes Paar eine ausdrückliche Angabe hat.

## 7. Ausführung

```text
.venv\Scripts\python -m mares.networks <Schritt> --package ROOT:relativer/Pfad [--local-place NAME] [--formats svg,png,pdf]
```

| Schritt | zusätzlich zum vorherigen |
|---|---|
| `validate` | Prüfbericht (`validation_report.md/.json`) |
| `import` | kanonisches Netzwerk (`canonical/dataset.json`, `contacts.csv`, `ties.csv`, `group_memberships.csv`) |
| `analyze` | beschreibende Tabellen (`analysis/*.csv`, `tables.md`, `survey_status.json`) |
| `figures` | sechs Abbildungen in `figures/` (SVG, PNG, PDF) |
| `run` | Verarbeitungsbericht (`processing_report.md`) |

`--package` ist eine **logische Referenz** (`INTAKE:inbox/<Lieferung>/contents`); erlaubt sind nur `INTAKE` und
`PRIMARY`. `BACKUP`, `EXCHANGE`, `WORKSPACE` und `LEGACY_IMPORT` sind nie Datenquelle. Ausgaben entstehen nur unter
`WORKSPACE/runs/<RUN-ID>/`; ein Lauf überschreibt nichts, und ein erneuter Aufruf ist ein neuer Lauf. Exit-Status:
0 abgeschlossen, 2 Paket fehlerhaft oder nicht lesbar, 1 Lauf nicht startbar (Root nicht konfiguriert o. Ä.).

**`run_record.json`** hält fest ([`data-contract.md`](data-contract.md) §6): Lauf-ID, Beginn und Ende, Schritt und
Ergebnis; Eingaben als logische Referenz mit SHA-256 und Größe jeder Datei; Quellkennung, Sitzung, Paketversion;
Softwareversion (Paketversion, Git-Stand, Version der Abhängigkeiten); Parameter; Datenqualitätsstatus (technische
Prüfung, Zahl der Fehler, Warnungen, offenen Fragen; `UNREVIEWED`, `NOT_PRESERVED`, `NO_COPY`); Erhebungsstatus;
Ausgaben als logische Referenz mit SHA-256; bekannte methodische Grenzen. Er enthält keine Maschinenpfade.
Ein Lauf ist reproduzierbar: gleiche Eingabe und Parameter ergeben byteidentische Tabellen und Grafiken.

## 8. Code-Karte

| Modul | Aufgabe |
|---|---|
| `codes.py` | Mehrfachcodes, Bereiche, Codebuch |
| `identity.py` | kanonische Kontakt-IDs aus Quellpositionen |
| `package.py` | Lesen des Pakets, Spaltenspezifikation |
| `model.py`, `geo.py` | Modell; Länder- und Ortsregeln |
| `validate.py`, `build.py` | Prüfung; Netzwerkkonstruktion |
| `analysis.py`, `canonical.py`, `report.py` | Auswertung; kanonische Ausgabe; Berichte |
| `figures/` | gemeinsame Konventionen (`style.py`), Layout (`common.py`), sechs Abbildungen |
| `run.py`, `cli.py` | Lauf und Kommandozeile |

## 9. Offen

Kanonische Fall-ID und Verknüpfung mit der früheren Erhebung; Import der Excel-Sheets und Festlegung der
Instrument-Version; Format expliziter Alter-Alter-Angaben; Ablage nach `PRIMARY/derived/networks` mit
Datensatzversion; Kennzahlen bei vollständiger Erhebung (methodische Entscheidung); Vokabular der zulässigen Nutzung.
