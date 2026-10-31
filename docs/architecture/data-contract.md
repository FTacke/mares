# Datenvertrag

**Status: verbindlich für Identifikatoren, Provenienz und Statusdimensionen; Entwurf, wo
ausdrücklich so markiert.** Dieser Vertrag definiert die Datenmodelle und ihre Beziehungen. Er
beschreibt nicht die Verarbeitung ([`intake-preservation.md`](intake-preservation.md),
[`modules.md`](modules.md)) und nicht die Speicherorte ([`storage-contract.md`](storage-contract.md)).

Code: [`src/mares/core/ids.py`](../../src/mares/core/ids.py),
[`src/mares/core/model.py`](../../src/mares/core/model.py) ·
Beispiel: [`examples/synthetic/MARES-0000-001/`](../../examples/synthetic/MARES-0000-001/)

## 1. Objekte und Beziehungen

```text
Instrument-Version ──┐
                     ▼
Einreichung ──▶ Asset ◀──────── Fall ──── Provenienz (unveränderlich)
 (SUB, Ereignis) (AST, Inhalt)   │ (MARES-JJJJ-NNN)
      n : 1          n : m       ├── Kontakte A01, A02, … ── Kontaktattribute
                                 ├── Alter-Alter-Beziehungen (Paare von Kontakten)
                                 └── Statusdimensionen (§4), je eigene Ereignisse
                     │
                     ▼
        Verarbeitungslauf (RUN) ──▶ abgeleitete Objekte ──▶ Datensatzversion (DS-…@vN)
        Eingaben · Parameter · Softwareversion · Ausgaben
```

| Objekt | Was es ist | Ändert sich? |
|---|---|---|
| **Fall** | eine befragte Person (Ego) mit ihrem Netzwerk, ihren Kontextdaten und Interviews | ID und Provenienz nie; Status durch neue Ereignisse |
| **Kontakt** | eine von Ego genannte Person, nur innerhalb des Falls identifiziert | nein |
| **Asset** | eine erhaltene Originaldatei: ein bestimmter Inhalt (SHA-256) | nie |
| **Einreichung** | ein Ereignis: jemand hat zu einem Zeitpunkt Dateien abgegeben | nie (Protokoll) |
| **Verarbeitungslauf** | eine Ausführung eines Verarbeitungsschritts | nie (Protokoll) |
| **Datensatzversion** | ein benannter, versionierter Stand abgeleiteter Daten | nach Abschluss nie; Korrekturen ergeben eine neue Version |
| **Instrument-Version** | eine Fassung eines Erhebungsinstruments (Netzwerk-Sheet, Leitfaden, Fragebogen) | nie; Änderungen ergeben eine neue Version |

Ein Asset kann mehrfach eingereicht werden (n Einreichungen : 1 Asset). Ein Asset ist höchstens
einem Fall zugeordnet; die Zuordnung ist ein Registereintrag und Teil weder der Asset-ID noch des
Ablagepfads. Ein Asset ohne geklärte Zuordnung ist ein gültiger Zustand (Review), kein Fehler, der
durch Raten behoben wird.

## 2. Identifikatoren

| Objekt | Form | Beispiel | Vergabe |
|---|---|---|---|
| Fall | `MARES-<JJJJ>-<NNN>` | `MARES-2026-001` | Register; Jahr der Registrierung, laufende Nummer |
| Kontakt | `A01`, `A02`, … ohne Obergrenze; Ego ist `EGO` | `A07` | fortlaufende Nummer je Erhebung, unabhängig von der Blattnummerierung der Quelle; eindeutig nur zusammen mit der Fall-ID |
| Asset | `AST-<12 Hex>` | `AST-9f3c2a7b41d0` | zufällig, bei der ersten Erhaltung des Inhalts |
| Einreichung | `SUB-<UTC-Zeit>-<6 Hex>` | `SUB-20261012T093000Z-1a2b3c` | beim Intake |
| Verarbeitungslauf | `RUN-<UTC-Zeit>-<6 Hex>` | `RUN-20261012T093000Z-1a2b3c` | beim Start des Laufs |
| Datensatzversion | `DS-<slug>@v<N>` | `DS-networks-core@v3` | bei Abschluss; N ab 1, lückenlos |
| Instrument-Version | `INS-<slug>@v<N>` | `INS-network-sheet@v2` | bei Einsatz; `@v0` bezeichnet einen nicht eingesetzten Entwurf |
| Kohorte | `WS<JJJJ>-<JJ>` / `SS<JJJJ>` | `WS2026-27` | Semester der Lehrveranstaltung |

Regeln:

- **Eine ID wird einmal vergeben und nie wiederverwendet oder umgedeutet.** Ein zurückgezogener
  Fall behält seine ID.
- **IDs sind unabhängig von Ablagepfaden.** Kein Pfad, Laufwerk, Rootname oder Dateiname geht in
  eine ID ein; nichts leitet aus einem Ordnernamen eine Identität ab.
- **IDs tragen keine veränderlichen Eigenschaften.** Herkunft, Qualität, Freigabe und Version sind
  Attribute im Register, nicht Teile der Fall-ID. (`TEACHING`-Fälle haben keine anderen IDs als
  `RESEARCH`-Fälle.)
- **Inhalt wird durch SHA-256 identifiziert**, berechnet nur über die Bytes der Datei. Die Asset-ID
  ist der stabile Name für diesen Inhalt; gleicher Hash heißt gleiches Asset.
- **Das Jahr `0000` ist reserviert** für synthetische und Testfälle und bezeichnet nie einen echten
  Fall.
- Fall-IDs enthalten nichts Personenbezogenes. Die Zuordnung Fall ↔ Person liegt ausschließlich
  unter `restricted/identities` auf `PRIMARY`.

## 3. Provenienz

Jeder Fall hat genau eine Provenienz. Sie wird bei der Registrierung festgehalten und **ändert sich
nie**.

| Feld | `TEACHING` – studentische Erhebung | `RESEARCH` – reguläre Forschung |
|---|---|---|
| `origin` | `TEACHING` | `RESEARCH` |
| `cohort` | Semester, z. B. `WS2026-27` (Pflicht) | — |
| `context` | Lehrveranstaltung | Projekt beziehungsweise Erhebungskampagne |
| `collector` | Pseudonym der erhebenden Person oder Arbeitsgruppe | Pseudonym der erhebenden Person |
| `instrument` | Version des Erhebungsinstruments | Version des Erhebungsinstruments |

- Der Schlüssel Pseudonym ↔ Person liegt nur unter `restricted/identities`.
- **Spätere professionelle Bearbeitung ändert die Herkunft nicht.** Wird ein studentisch erhobener
  Fall nachbearbeitet, geprüft und in einen Forschungsdatensatz aufgenommen, bleibt er `TEACHING`;
  hinzu kommen Verarbeitungsläufe, Qualitätsbewertungen und Datensatzversionen.
- Es gibt **eine** Pipeline und **einen** Datenbestand für beide Herkünfte. Unterschieden wird
  durch Metadaten, nicht durch getrennte Werkzeuge, Ordner oder ID-Räume.

## 4. Sechs unabhängige Statusdimensionen

Keine dieser Eigenschaften folgt aus einer anderen, und keine wird aus einer anderen abgeleitet.

| # | Dimension | Frage | Werte | Wer setzt sie |
|---|---|---|---|---|
| 1 | **Provenienz** | Wie ist der Fall entstanden? | `TEACHING` · `RESEARCH` | Registrierung, einmalig |
| 2 | **Instrument-Version** | Womit wurde erhoben? | `INS-…@vN` | Registrierung, einmalig |
| 3 | **Daten- und Verarbeitungsversion** | Welcher Stand der Daten, wie erzeugt? | `DS-…@vN`, `RUN-…` | Verarbeitungsläufe |
| 4 | **Datenqualität** | Sind die Daten geprüft und brauchbar? | `UNREVIEWED` · `IN_REVIEW` · `VALIDATED` · `VALIDATED_WITH_RESERVATIONS` · `NOT_USABLE` | fachliche Prüfung |
| 5 | **Wissenschaftliche Freigabe** | Ist der Fall für einen Forschungsdatensatz zugelassen? | `NOT_DECIDED` · `RESEARCH_APPROVED` · `NOT_APPROVED` · `WITHDRAWN` | Projektleitung |
| 6 | **Zulässige Nutzung** | Was erlaubt die Einwilligung? | Menge zulässiger Nutzungen (§4.1) | Einwilligung; nur durch die betroffene Person erweiterbar |

Dazu kommen zwei technische Zustände je Asset, ebenfalls unabhängig voneinander und von den sechs
Dimensionen: **Erhaltung** (`NOT_PRESERVED` · `PENDING` · `RAW_PRESERVED`) und **Backup**
(`NO_COPY` · `COPY_UNVERIFIED` · `BACKUP_VERIFIED`).

Regeln:

- Jede Änderung eines Status ist ein **neues, datiertes Ereignis** mit Urheber und Begründung; der
  frühere Stand bleibt lesbar. Qualitätsbewertung und Freigabe beziehen sich auf eine bestimmte
  Datensatzversion.
- **Aufnahme in einen Forschungsdatensatz** setzt voraus: Qualität `VALIDATED` oder
  `VALIDATED_WITH_RESERVATIONS`, Freigabe `RESEARCH_APPROVED`, und die zulässige Nutzung deckt die
  Forschungsnutzung. Die Herkunft ist dafür kein Kriterium, bleibt aber in jedem Datensatz als
  Attribut erhalten und filterbar.
- **Die zulässige Nutzung begrenzt alles andere.** Keine Qualitäts- oder Freigabeentscheidung
  erweitert, was die Einwilligung erlaubt. Ein Widerruf ist ein Ereignis, das Freigaben beendet
  (`WITHDRAWN`); wie mit bereits erhaltenen Daten zu verfahren ist, entscheidet eine Person, kein
  automatischer Löschlauf.

### 4.1 Zulässige Nutzung – Entwurf

Unbekannte oder fehlende Einwilligung heißt: **keine Nutzung** über die gesicherte Aufbewahrung
hinaus (leere Menge). Vorgeschlagenes Vokabular, **abzugleichen mit den tatsächlichen
Einwilligungserklärungen** (offene Entscheidung):

`TEACHING_USE` (Auswertung in der Lehrveranstaltung) · `RESEARCH_ANALYSIS` (interne
Forschungsauswertung) · `PUBLICATION_PSEUDONYMISED` (pseudonymisierte Veröffentlichung von
Ergebnissen und Textauszügen) · `AUDIO_EXCERPTS` (Verwendung von Tonausschnitten) ·
`ARCHIVING_REUSE` (Archivierung und Nachnutzung durch Dritte)

## 5. Netzwerkdaten

- Die Zahl der Kontakte ist nicht begrenzt; das ursprüngliche Instrument sieht bis zu 15 vor, Folgeerhebungen können mehr haben
  ([ADR-0002](../decisions/ADR-0002_2026-10-12_netzwerkmodul.md)). Kanonische Kontakt-IDs sind fortlaufend; die
  Blattnummer und die lokale Nummer der Quelle bleiben als Provenienz erhalten. Kontaktattribute und Beziehungen beziehen sich auf
  Kontakt-IDs, nie auf Namen; Namen von Kontakten gehören nicht in abgeleitete Daten.
- Eine Alter-Alter-Beziehung ist ein ungeordnetes Paar zweier Kontakte desselben Falls mit genau
  einem von vier Zuständen, die nie zusammengelegt werden:

  | Zustand | Bedeutung |
  |---|---|
  | `yes` | die beiden kennen sich |
  | `no` | die beiden kennen sich nicht |
  | `unknown` | gefragt; Ego weiß es nicht |
  | *fehlend* | nicht erhoben oder nicht eingetragen |

  „Fehlend“ wird nie stillschweigend als `no` gelesen. Ein fehlendes Paar gilt nur dann als verneint, wenn belegt ist, dass die
  Erhebung **alle** Paare erfasst hat (Paarabdeckung).
- Zu jeder Alter-Alter-Erhebung gehören drei getrennte Aussagen: die **Erhebungsmethode** (z. B. Beziehungen einzeln erfragt), die
  **Dokumentationsform** (z. B. Gruppenumrandungen einer Netzwerkkarte) und die **Paarabdeckung**. Sie werden bei der
  Verarbeitung in einer eigenen, datierten Kuratierungsdatei festgehalten, nie durch Änderung der Originaldateien
  ([ADR-0003](../decisions/ADR-0003_2026-10-12_erhebungsmethode-und-kuratierung.md)).
- `001-2`-artige Quellkennungen sind keine Fall-IDs: Das Netzwerkmodell führt die Quellkennung getrennt von einer
  optionalen kanonischen Fall-ID und ordnet nie ohne Register zu.
- Welche Attribute erhoben werden und wie das Sheet aufgebaut ist, legt die Instrument-Version
  fest, nicht dieser Vertrag.

## 6. Verarbeitungsläufe und Versionen

Jeder Verarbeitungslauf hält fest:

- seine `RUN`-ID, Beginn, Ende und Ergebnis;
- **Eingaben**: Asset-IDs beziehungsweise Datensatzversionen, jeweils mit SHA-256;
- **Parameter**: vollständig, einschließlich Modell- und Konfigurationsangaben;
- **Softwareversion**: Paketversion und Git-Commit des Repositorys, Versionen der maßgeblichen
  Abhängigkeiten;
- **Ausgaben**: logische Referenzen (Root + relativer Pfad) mit SHA-256.

Rohdaten, kanonische Arbeitsdaten und abgeleitete Ergebnisse bleiben getrennt: ein Lauf liest aus
`preservation/` und schreibt nach `derived/`, nie umgekehrt. Manuelle Korrekturen sind
dokumentierte Verarbeitungsschritte mit eigener Ausgabe; nichts wird stillschweigend korrigiert.

## 7. Register

Fälle, Assets, Einreichungen, Läufe, Versionen und Statusereignisse werden in einem Register unter
`registry/` auf `PRIMARY` geführt. Vorgesehen ist SQLite; das Format ist **noch nicht festgelegt**.
Fest steht: das Register speichert Orte nur als logische Referenzen, es ist aus den Manifesten und
Ereignisprotokollen rekonstruierbar, und eine Arbeitskopie einer Datenbankdatei liegt nie im
Repository.
