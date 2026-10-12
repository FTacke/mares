# Geplante Module

**Status: Planung, mit einer Ausnahme.** `mares.networks` ist in einer ersten Fassung implementiert
([`network-module.md`](network-module.md) beschreibt den Ist-Stand); `transcription` und `exports` sind nicht
implementiert, ihre Pakete enthalten nur ihre Beschreibung. Dieses Dokument legt die Grenzen der Module fest: was
hinein- und was herausgeht.

Gemeinsam für alle Module:

- Eingaben kommen aus `PRIMARY` (erhaltene Originale oder frühere Datensatzversionen), nie direkt
  aus `EXCHANGE`, `INTAKE/inbox` oder `BACKUP`.
- Gearbeitet wird in `WORKSPACE/runs/<RUN-ID>`; Ergebnisse gehen als neue Datensatzversion nach
  `PRIMARY/derived/…`. Jeder Lauf ist ein Verarbeitungslauf im Sinn des
  [Datenvertrags](data-contract.md) §6.
- Ein Modul behandelt `TEACHING`- und `RESEARCH`-Fälle gleich. Die Herkunft ist ein Attribut der
  Daten, kein Schalter im Code.
- Entwickelt und getestet wird mit synthetischen Fixtures.

## NETWORKS – `mares.networks`

> **Ist (2026-10-12):** der Import eines CSV-Pakets (nicht der Excel-Sheets), Validierung, Beziehungen aus
> bestätigten Gruppen, beschreibende Auswertung, sechs Grafiken und eine Kommandozeile; Ergebnisse nur nach
> `WORKSPACE/runs/`. Die Tabelle darunter beschreibt das **Soll**; Abweichungen und Grenzen stehen in
> [`network-module.md`](network-module.md). Entscheidungen: [`ADR-0002`](../decisions/ADR-0002_2026-10-12_netzwerkmodul.md).

| | |
|---|---|
| **Eingabe** | standardisierte Excel-Erhebungssheets (ein Asset je Fall, in einer bekannten Instrument-Version) |
| **Ausgabe** | kanonische Netzwerkdaten je Fall (Kontakte, Attribute, Beziehungen) → `derived/networks`; Kennzahlen → `derived/networks`; Grafiken → `derived/visualizations` |
| **Grenze** | liest keine Audiodaten; schreibt nichts nach `preservation/`; korrigiert keine Sheets, sondern meldet Validierungsbefunde |

Vorgesehene Funktionen:

- Import der Erhebungssheets;
- Validierung von Kontaktattributen und Alter-Alter-Beziehungen, mit korrekter Unterscheidung von
  *fehlend* und `unknown` ([Datenvertrag](data-contract.md) §5);
- egozentrierte Netzwerkmodelle;
- Kennzahlen (Auswahl und Definition sind eine methodische Entscheidung, noch offen);
- statische und gegebenenfalls interaktive Visualisierungen, darunter Darstellungen nach dem
  methodischen Vorbild von Vacca et al. (2016);
- Vergleich von Netzwerken nach geografischen, sozialen und sprachlichen Merkmalen.

Stack: NetworkX und Matplotlib (eingetragen); pandas bewusst nicht (ADR-0002); openpyxl kommt mit dem
Sheet-Import; Plotly beziehungsweise Cytoscape.js nur bei konkretem Bedarf.

## TRANSCRIPTION – `mares.transcription`

| | |
|---|---|
| **Eingabe** | erhaltene Audioaufnahmen (Assets), einem Fall zugeordnet |
| **Ausgabe** | verlustfreie Arbeitsfassungen; Rohtranskripte mit Zeitmarken; korrigierte Transkripte; pseudonymisierte beziehungsweise anonymisierte Forschungsfassungen → `derived/transcripts` |
| **Grenze** | das Original-Audio wird nie verändert; jede Stufe ist eine eigene Version; keine Audiodaten verlassen die Universitätsinfrastruktur |

Vorgesehene Funktionen:

- Audio-Intake und -Erhaltung (über die gemeinsame Intake-/Preservation-Schicht, kein eigener Weg);
- verlustfreie Arbeitsfassungen;
- Whisper-Transkription über den Marburger HPC-Cluster MaRC3a (Slurm);
- Zeitmarken und einfache Sprecherzuordnung;
- manuelle Nachbearbeitung mit dokumentierten Korrekturen;
- pseudonymisierte beziehungsweise anonymisierte Forschungsfassungen;
- Verknüpfung mit Fall-IDs und gegebenenfalls Kontakten.

Datenschutz, verbindlich:

- **Keine Übertragung von Audio oder Transkripten an Cloud-Anbieter oder externe APIs.**
  Transkribiert wird ausschließlich auf eigener beziehungsweise universitärer Infrastruktur.
- **Vor der ersten produktiven Nutzung von MaRC3a ist gesondert zu prüfen**, ob der Cluster für
  personenbezogene Forschungsdaten freigegeben ist und unter welchen Auflagen (Speicherorte,
  Löschfristen, Zugriff). Bis dahin läuft dort nur synthetisches Audio.
- Der Cluster ist ein weiterer Speicherort mit eigener Rolle (voraussichtlich ein zusätzlicher
  benannter Root für den Rechen-Arbeitsbereich); er wird nicht durch Pfade im Code angesprochen.

## EXPORTS – `mares.exports`

| | |
|---|---|
| **Eingabe** | Datensatzversionen aus `derived/`, Statusdimensionen aus dem Register |
| **Ausgabe** | eingefrorene, versionierte Datensätze → `releases/`; Material für die Lehre → `EXCHANGE/seminars/<Kohorte>/materials` |
| **Grenze** | exportiert nur, was Qualität, Freigabe **und** zulässige Nutzung erlauben; nie `restricted/` |

Ein Export hält fest, welche Fälle in welcher Datensatzversion enthalten sind und welche
Auswahlregel galt; die Herkunft jedes Falls bleibt als Attribut erhalten.

## In diesem Stand nicht vorhanden

Import der Excel-Erhebungssheets, Netzwerkkennzahlen auf vollständiger Grundlage, ASR, HPC-Anbindung,
Modellinstallation, Register (SQLite), Intake- und Preservation-Automatisierung, Backup-Läufe. (Die
Kommandozeile gibt es nur für das Netzwerkmodul.)
