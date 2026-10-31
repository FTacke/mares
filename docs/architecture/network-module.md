# Netzwerkmodul – `network_v0`

> **Seit 2026-10-31 ist dies die Pipeline `network_v0`** (früheres Erhebungsdesign, Paketformat
> `mares-network-package/v0-draft`, Nähe 1–5 mit 5 = sehr nah). Sie bleibt unverändert nutzbar; ihre Befehle
> (`python -m mares.networks <Schritt>`, gleichbedeutend `python -m mares.networks v0 <Schritt>`) gelten weiter. Die neue,
> eigenständige Netzwerkerhebung ist `network_v1`: [`network-v1.md`](network-v1.md); Abgrenzung beider Versionen:
> [`network-versions.md`](network-versions.md).

**Status: implementiert (Stand 2026-10-12), Paketformat als Entwurf.** Dieses Dokument legt fest, was
`mares.network_v0` liest, wie es Beziehungen konstruiert, was es prüft und ausgibt und was es ausdrücklich
nicht berechnet. Es ergänzt [`modules.md`](modules.md) (Umfang) und [`data-contract.md`](data-contract.md)
(IDs, Statusdimensionen); die Entscheidungen dahinter stehen in
[`ADR-0002`](../decisions/ADR-0002_2026-10-12_netzwerkmodul.md) und
[`ADR-0003`](../decisions/ADR-0003_2026-10-12_erhebungsmethode-und-kuratierung.md). Grafiken:
[`visualization-conventions.md`](visualization-conventions.md). Der erste Fall:
[`../methodology/pilot-case-001-2.md`](../methodology/pilot-case-001-2.md).

Code: [`src/mares/network_v0/`](../../src/mares/network_v0/__init__.py)

## 1. Soll und Ist

| | Ist (implementiert, getestet mit synthetischen Daten) | Nicht vorhanden |
|---|---|---|
| Eingang | Import eines CSV-Pakets (§3) und einer optionalen Kuratierung (§3.1) aus `INTAKE` oder `PRIMARY` | Import der Excel-Erhebungssheets; Registrierung des Falls |
| Prüfung | Validator mit Fehlern, Warnungen und Prüfhinweisen in vier Kategorien (§5) | fachliche Prüfung gegen die Originalbögen |
| Netzwerk | Alter-Alter-Beziehungen aus bestätigten Gruppen; Erhebungsmethode, Dokumentationsform und Paarabdeckung getrennt geführt (§4) | Format für einzeln erfragte Paare im Paket |
| Auswertung | beschreibende Häufigkeiten, Gruppengrößen, Mehrfachzugehörigkeiten; Strukturmaße nur bei bestätigter Paarabdeckung (§6) | Kennzahlen bei unbelegter Abdeckung |
| Ausgabe | ein Lauf je Aufruf unter `WORKSPACE/runs/<RUN-ID>/` mit Berichten, Tabellen, Review-Register, dreizehn Grafiken (§7) | Ablage in `PRIMARY/derived/`, Datensatzversion `DS-…` |

Die Ergebnisse eines Laufs sind **regenerierbare Arbeitsdaten**. Sie sind weder erhalten noch gesichert und
tragen keine Datensatzversion, solange `PRIMARY` und das Register fehlen.

## 2. Identitäten

Das Modell hält Dinge getrennt, die in der Quelle verschmolzen sind ([`model.py`](../../src/mares/network_v0/model.py)):

| Objekt | Bedeutung | Anmerkung |
|---|---|---|
| Fall (`CaseIdentity`) | MARES-Fall | `source_label` (historische Kennung, z. B. `001-2`) und **optionale** `canonical_case_id`. Die Quellkennung ist **keine** Fall-ID; es wird nie zugeordnet, solange kein Register existiert. Die Verknüpfung einer Folgeerhebung mit der früheren Erhebung ist offen. |
| Sitzung (`SurveySession`) | eine konkrete Erhebung | Datum, Erhebungsart, Paketversion, Herkunftsvermerk (z. B. studentische Erhebung); bleibt Teil der Provenienz |
| Kontakt (`Contact`) | eine von Ego genannte Person | kanonische ID `A01`, `A02`, … **ohne Obergrenze**; dazu `source_block` und `source_local_id` der Quelle. **Die ID verknüpft alle Tabellen**, nie ein Name oder eine Beschriftung. |
| Kontaktattribut | Merkmal eines Kontakts | Codes bleiben Zeichenketten; leer = nicht erhoben; Rohwerte bleiben erhalten, abgeleitete Kategorien stehen daneben |
| Gruppe, Mitgliedschaft | eingezeichnete Umrandung und wer darin liegt | Bewertung `confirmed` / `needs_review`; Mitgliedschaft `confirmed` / `candidate` |
| Beziehung (`Tie`) | ungeordnetes Paar mit Zustand | `yes` / `no` / `unknown` / nicht erhoben (§4) |
| Kuratierung (`Curation`) | datierte Aussagen *über* ein Paket | Erhebungsmethode, Paarabdeckung, Kategorien der Prüfhinweise (§3.1) |
| Quelldatei (`SourceFile`) | Eingabedatei mit SHA-256 | die Verarbeitungsversion ist der Lauf (`RUN-…`), nicht das Modell |

**Kanonische Kontakt-IDs** sind der Rang in der Quellreihenfolge (Blatt, dann lokale Nummer), unabhängig von der
Blattnummerierung: Blatt 1 `A01`–`A15` und Blatt 2 `A01`–`A07` ergeben `A01`–`A22`
([`identity.py`](../../src/mares/network_v0/identity.py)). Die Quellposition bleibt erhalten. Abweichende
Namensschreibungen oder Beschriftungen zwischen Quellen sind **kein** Datenproblem, solange der Kontaktcode die
Zuordnung eindeutig macht; Namen kommen weder ins Modell noch in Abbildungen.

## 3. Paketformat `mares-network-package/v0-draft`

Ein Paket ist ein Ordner. Das Format ist ein **Importvertrag des Moduls**, kein Erhebungsinstrument; es wird bei
der Festlegung der Instrument-Version überprüft. **Originaldateien eines Pakets werden nie verändert.**

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

**Mehrfachcodes und Bereiche** ([`codes.py`](../../src/mares/network_v0/codes.py)): `1|2|3` bleibt Liste; ein wohldefinierter
aufsteigender Bereich wird zu Einzelcodes aufgelöst (`1-6`, `1–6`, `G1-G3`, `G1-3`) und als Hinweis vermerkt;
Duplikate, leere Elemente, absteigende oder unplausibel weite Bereiche sind Syntaxfehler. Gültigkeit entscheidet
das **Codebuch des Pakets**, nicht der Code: ein Bereich, der über das Codebuch hinausreicht, ist ein Fehler.

**Nähe:** maßgeblich ist ausschließlich `table_ring_near_value` (Codebuch `closeness_1_5`, Werte 1–5). Die Position
auf der handgezeichneten Karte und ihre abweichende Legende werden weder gelesen noch umgerechnet.

**Geburtsland und Wohnort** ([`geo.py`](../../src/mares/network_v0/geo.py)): Rohwerte bleiben erhalten; die Auswertung
leitet daneben Kategorien ab.

| Angabe | Auswertungskategorie |
|---|---|
| ISO-Code gesetzt | der Code |
| kein Code, Quelle nennt mehrere Länder („A/B“, „A oder B“) | `mehrdeutig` – weder ein Land gewählt noch zwei gezählt noch als fehlend behandelt |
| kein Code, Quelle nennt ein Land | `nicht kodiert` (Warnung) |
| nichts erfasst | `–` |
| Wohnort = Referenzort exakt (z. B. Marburg) | `Marburg` |
| regionale Angabe zum Referenzort („Nähe/Raum/Region/Umgebung Marburg“) | `Region Marburg` – Wohnland Deutschland, nicht die Stadt, kein erfundener Ort |
| übriger Ort in Deutschland / anderes Land / kein Land | übriges Deutschland / außerhalb / unbekannt |

### 3.1 Kuratierung `mares-network-curation/v0-draft`

Aussagen, die das Paket nicht trägt und die eine Person später trifft, stehen in einer **eigenen, datierten JSON-Datei**
([`curation.py`](../../src/mares/network_v0/curation.py)), nie in den Originaldateien. Ein Lauf liest sie mit
`--curation ROOT:rel`, prüft sie streng und hält ihren SHA-256 im Run-Record fest. Beispiel:
[`examples/synthetic/network-curation-0000/`](../../examples/synthetic/network-curation-0000/curation.json).

- `survey`: `elicitation` (`asked_per_pair` | `not_stated`), `documentation` (`group_outlines` | `not_stated`),
  `group_rule` (`all_members_know_each_other`), `pair_coverage` (`not_established` | `complete`), `basis`
  (Pflicht, sobald eine Aussage getroffen wird).
- `dispositions`: je Prüfhinweis (`ref` = Review-ID oder `flag:<Kontakt>:<MARKIERUNG>`) eine Kategorie (§5), der Urheber
  (`project_lead` oder `agent_proposal`), die Begründung und eine Notiz.
- Ohne Kuratierung gilt: Methode nicht angegeben, Paarabdeckung nicht belegt, Hinweise nach der empfohlenen Aktion
  des Pakets – und nichts wird als erledigt behandelt, was niemand entschieden hat.

## 4. Netzwerkkonstruktion ([`build.py`](../../src/mares/network_v0/build.py))

**Erhebungsmethode, Dokumentationsform und Paarabdeckung sind drei verschiedene Aussagen.**

| Aussage | Frage | Pilotfall |
|---|---|---|
| Erhebungsmethode | Was hat der Explorator getan? | Beziehungen zwischen den Netzwerkpersonen **einzeln erfragt** (Projektleitung) |
| Dokumentationsform | Wie ist es aufgeschrieben? | als **Gruppenumrandungen** der Netzwerkkarte zusammengefasst |
| Paarabdeckung | Wurde **jedes** Paar erfasst? | **nicht belegt** – 41 von 231 Paaren sind bestätigt |

Regeln:

1. Eine **bestätigte Gruppe** ist eine Clique: alle bestätigten Mitglieder innerhalb derselben Umrandung kennen sich.
   Die Cliquenregel rekonstruiert die Paarliste aus der Dokumentationsform; sie ist zulässig, weil die erhobenen
   Beziehungen die Gruppe tragen. Daraus entstehen Beziehungen `yes` mit Basis `clique_rule`.
2. Identische Paare aus mehreren Gruppen sind **eine** Beziehung; die Gruppen bleiben als Herkunft erhalten. Eine in andere
   Gruppen eingebettete Gruppe fügt keine eigenen Beziehungen hinzu.
3. Gruppen mit `needs_review` und Mitgliedschaften mit `candidate` erzeugen **keine** Beziehung.
4. **Ein Paar ohne Beleg ist unbekannt, nie `no`.** Fehlende Paare werden nur dann `no` (Basis `coverage_complete`), wenn die
   Kuratierung `pair_coverage: complete` mit Begründung festhält; sonst kann nur eine ausdrückliche Angabe `no` sein.
   Gefragt, aber unbekannt ist `unknown`. Die Zustände bleiben getrennt ([`data-contract.md`](data-contract.md) §5).
5. Widerspricht eine ausdrückliche Angabe einer Cliquen-Beziehung, wird kein Netzwerk gebaut (Fehler). **Eine belegte
   Beziehung wird in keinem Zustand entfernt.**
6. Die Kantentabelle des Pakets ist ein **Beleg**: Der Validator vergleicht sie mit der Ableitung (fehlende, nicht
   ableitbare, doppelte, selbstbezügliche Kanten; abweichende Gruppen; Anzahl laut Manifest). Eine Abweichung ist ein
   harter Fehler; übernommen wird immer die Ableitung.

Das Modell kann zusätzlich explizite Ja/Nein/Unbekannt-Angaben speichern (`build_network(dataset, explicit_ties=…)`).

## 5. Validierung ([`validate.py`](../../src/mares/network_v0/validate.py))

Getrennt gehalten werden harte Fehler, Warnungen und Prüfhinweise:

| Klasse | Bedeutung | Wirkung |
|---|---|---|
| **Harte Fehler** | Format- oder Konsistenzverletzung | der Lauf verarbeitet nichts weiter; Status `FAILED_VALIDATION` |
| **Warnungen** | nutzbar, aber zu wissen (fehlendes erwartetes Attribut, genanntes, aber nicht kodiertes Geburtsland, Markierung ohne Eintrag und ohne Kuratierung, fehlende Prüfsummen) | Verarbeitung läuft; Status `PASSED_WITH_WARNINGS` |
| **Prüfhinweise** | dokumentierte Unsicherheit über die Quelle (`review_items.csv`, Markierungen, `SW-01`–`SW-03`) | blockieren nichts; Kategorie nach §5.1 |

### 5.1 Vier Kategorien der Prüfhinweise

| Kategorie | Bedeutung | zählt als offene Datenfrage |
|---|---|---|
| `open_decision` | offene, entscheidungsrelevante Datenfrage | **ja** |
| `documented_ambiguity` | dokumentierte Mehrdeutigkeit der Quelle; Rohwert erhalten, nichts aufgelöst | nein |
| `accepted_imprecision` | akzeptierte Unschärfe der Erhebung | nein |
| `resolved` | geklärt / abgeschlossen | nein |

Die Kategorie kommt aus der Kuratierung (Aussage einer Person, mit Urheber und Begründung); ohne sie aus der
empfohlenen Aktion des Pakets (`rule_confirmed` → geklärt, `accepted_as_approximate` → akzeptierte Unschärfe, sonst
offen). **Die Software entscheidet keinen Hinweis.** Der Prüfbericht führt jede Kategorie in einem eigenen Abschnitt;
`review/review_register.csv` hält alle Hinweise mit Kategorie, Urheber und Begründung.

Geprüft werden unter anderem: eindeutige und kanonisch fortlaufende Kontakt-IDs, Übereinstimmung mit der
Quellposition, Quellkennung zwischen Manifest und Tabelle, Kontaktzahl laut Manifest; Codes gegen das Codebuch,
Einzelwertfelder, Duplikate; ISO-Ländercodes, Ort/Land-Plausibilität ohne erfundene Werte; Gruppen- und
Mitgliedschaftsreferenzen, Statuskonsistenz; Klärungen gegen Mitgliedschaften; Prüfsummen; Kantenbeleg (§4);
Passung der Kuratierung zum Paket (Quellkennung = Fehler, Version und unbekannte Verweise = Warnung).

**Der Validator setzt nie einen Qualitätsstatus.** Ein bestandener technischer Test ist keine wissenschaftliche
Validierung: die Datenqualität bleibt `UNREVIEWED`, die Freigabe `NOT_DECIDED`, bis Personen entscheiden
([`data-contract.md`](data-contract.md) §4). Provenienz, Datenqualität und Freigabe bleiben getrennte Dimensionen.

## 6. Auswertung ([`analysis.py`](../../src/mares/network_v0/analysis.py))

Erlaubt und implementiert: Anzahl und Merkmale der Kontakte; Verteilungen aller Codefelder (leere Kategorien
bleiben sichtbar, „nicht erfasst“ wird getrennt gezählt); Wohnort und geografische Einordnung (Referenzort,
Region, übriges Deutschland, außerhalb, unbekannt – Parameter `--local-place`); Geburtsland mit Status; Wohnland ×
Geburtsland; exakte Sprachrepertoires; Anzahl bestätigter, verneinter und nicht erfasster Paare (als Zählung);
Gruppengrößen; Mehrfachzugehörigkeit.

**Strukturmaße** (Dichte, Komponenten und ihre Größen, Kontakte ohne Beziehung, mittlerer und höchster Grad;
Tabelle `structure`) werden **nur bei bestätigter Paarabdeckung** berechnet, weil erst dann ein fehlendes Paar etwas
bedeutet. Sie beschreiben einen einzelnen, nicht zufällig gezogenen persönlichen Fall (explorativ, keine
Verallgemeinerung, keine Inferenz). Bei nicht belegter Abdeckung sind Dichte, Kohäsion, Segregation und
Zentralitäten **nicht berechnet** (`REFUSED_METRICS`); jede strukturelle Ausgabe sagt das und trägt den Erhebungs- und
Vollständigkeitsstatus (`SurveyStatus`: Quelle, Sitzung, Erhebungsmethode, Dokumentationsform, Paarabdeckung,
Datenqualität).

## 7. Ausführung

```text
.venv\Scripts\python -m mares.networks <Schritt> --package ROOT:relativer/Pfad [--curation ROOT:rel/curation.json] [--local-place NAME] [--formats svg,png,pdf]
    [--profiles clean,analysis] [--language-view mode|mode:<code>|lang:<code>|multilingual] [--tie-highlight between|within|none]
```

| Schritt | zusätzlich zum vorherigen |
|---|---|
| `validate` | Prüfbericht (`validation_report.md/.json`), `review/review_register.csv` |
| `import` | kanonisches Netzwerk (`canonical/dataset.json`, `contacts.csv`, `ties.csv`, `group_memberships.csv`) mit Rohwerten und abgeleiteten Kategorien |
| `analyze` | beschreibende Tabellen (`analysis/*.csv`, `tables.md`, `survey_status.json`) |
| `figures` | neunzehn Abbildungen (SVG, PNG, PDF), gegliedert in `figures/core/` (B3, G2-B, P1, P2), `figures/supplementary/` (A, B1, B2, G1, G2-A, P3, C, D1, D2, E) und `figures/diagnostic/` (B0, B3-0, G2-0, G2-1, frühere G2-Fassung); die Abbildungen aus `core` und `supplementary` zusätzlich in der Arbeitsfassung (Profil `analysis`) unter `figures/analysis/<tier>/`; dazu das Register `figures/figures_index.json` (Gliederung: [`visualization-conventions.md`](visualization-conventions.md) §3.8) |
| `run` | Verarbeitungsbericht (`processing_report.md`) |

**Optionen der Designabbildungen.** `--profiles` (Standard beide; gilt für `core` und `supplementary`), `--language-view` (Sprachansicht von P2; Standard `mode`), `--tie-highlight` (Hervorhebung in G2; Standard `between`).
Sie ändern nur die Darstellung und stehen als `figure_options` im `run_record.json`. `figures_index.json` (`mares-figures-index/v0-draft`) ist das **Abbildungsregister des Laufs**: je Abbildung Tier, Frage, Basislayout, Kodierungen, Grenzen, Kandidaten-/Altmarkierung und Dateien; die drei räumlichen Bedeutungen
(Nähe, Struktur, Geografie); die Gliederung; und die **vollständige Provenienz und den Datenqualitätsstatus** (`provenance`), die die Bilder nur als `MARES · 001-2 · vorläufig` andeuten.

`--package` und `--curation` sind **logische Referenzen** (`INTAKE:inbox/<Lieferung>/contents`); erlaubt sind nur `INTAKE`
und `PRIMARY`. `BACKUP`, `EXCHANGE`, `WORKSPACE` und `LEGACY_IMPORT` sind nie Datenquelle. Ausgaben entstehen nur unter
`WORKSPACE/runs/<RUN-ID>/`; ein Lauf überschreibt nichts, und ein erneuter Aufruf ist ein neuer Lauf. Exit-Status:
0 abgeschlossen, 2 Paket oder Kuratierung fehlerhaft oder nicht lesbar, 1 Lauf nicht startbar (Root nicht konfiguriert o. Ä.).

**`run_record.json`** hält fest ([`data-contract.md`](data-contract.md) §6): Lauf-ID, Beginn und Ende, Schritt und
Ergebnis; Eingaben als logische Referenz mit SHA-256 und Größe jeder Datei, dazu die Kuratierung mit Hash;
Quellkennung, Sitzung, Paketversion; die Erhebungsmethode (Methode, Dokumentationsform, Paarabdeckung, Grundlage);
Softwareversion (Paketversion, Git-Stand, Version der Abhängigkeiten); Parameter (u. a. Layout, Ego-Layout und Seed);
Datenqualitätsstatus (technische Prüfung, Fehler, Warnungen, offene Datenfragen, Hinweise je Kategorie; `UNREVIEWED`,
`NOT_PRESERVED`, `NO_COPY`); Erhebungsstatus; Ausgaben als logische Referenz mit SHA-256; bekannte methodische
Grenzen. Er enthält keine Maschinenpfade. Ein Lauf ist reproduzierbar: gleiche Eingabe und Parameter ergeben
byteidentische Tabellen und Grafiken, auch über Prozessgrenzen.

## 8. Code-Karte

| Modul | Aufgabe |
|---|---|
| `codes.py` | Mehrfachcodes, Bereiche, Codebuch |
| `identity.py` | kanonische Kontakt-IDs aus Quellpositionen |
| `package.py`, `curation.py` | Lesen des Pakets; Lesen und Prüfen der Kuratierung |
| `model.py`, `geo.py` | Modell; Länder-, Orts- und Geburtslandregeln, fünfstufige geografische Klassifikation ([`geographic-classification.md`](geographic-classification.md)) |
| `validate.py`, `build.py` | Prüfung und Prüfhinweise; Netzwerkkonstruktion |
| `analysis.py`, `canonical.py`, `report.py` | Auswertung; kanonische Ausgabe; Berichte und Review-Register |
| `figures/` | Konventionen (`style.py`), Kontaktsicht und Ring-Layout (`common.py`), kraftbasierte Layouts (`layouts.py`), Netzwerkfiguren B0–B2 (`network.py`), Ego im Netzwerk B3 (`ego_layouts.py`, `ego_network.py`), geografische Zonen G1/G2 (`geo_zones.py`), Designsystem (`design.py`, `figure_notes.py`), Perspektiven P1–P3 (`perspectives.py`), geografische Beziehungsnetze G2-A/G2-B (`geo_network.py`), Abbildungsregister und Gliederung (`registry.py`), `ego.py` (Ringe A, D2), `geography.py`, `language.py`, `overview.py` |
| `run.py`, `cli.py` | Lauf und Kommandozeile |

## 9. Offen

Kanonische Fall-ID und Verknüpfung mit der früheren Erhebung; Bestätigung der Paarabdeckung für den Pilotfall; Import
der Excel-Sheets und Festlegung der Instrument-Version; Format expliziter Alter-Alter-Angaben im Paket; Ablage nach
`PRIMARY/derived/networks` mit Datensatzversion; Vokabular der zulässigen Nutzung.
