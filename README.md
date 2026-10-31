# MARES

**Marburgo: Archivo de Redes y Experiencias Sociolingüísticas** – Forschungsdaten-Infrastruktur
eines soziolinguistischen Forschungs- und Lehrprojekts der Universität Marburg.

MARES untersucht persönliche Netzwerke, Mehrsprachigkeit und sprachliche Alltagserfahrungen
lateinamerikanischer Migrant:innen. Erhoben werden Kontextdaten, egozentrierte Netzwerkkarten,
Kontaktattribute, Alter-Alter-Beziehungen sowie Audiointerviews und narrative Episoden – in
Seminaren mehrerer Jahrgänge und in regulärer Forschung, mit denselben Werkzeugen und in einem
gemeinsamen Datenbestand.

> **Status (2026-10-12).** Vorhanden sind Verzeichnisstruktur, Architektur- und Datenverträge, der
> Resolver für benannte Storage-Roots, Identifikatoren und Statusvokabular – und das **Netzwerkmodul**:
> Import eines CSV-Pakets, Validierung, Beziehungen aus bestätigten Gruppen, beschreibende Auswertung,
> neunzehn Grafiken in drei Gruppen – `core`, `supplementary`, `diagnostic` – (darunter kraftbasierte Netzwerkdarstellungen ohne und mit Ego, geografische Zonen und Beziehungsnetze, drei analytische Perspektiven P1–P3) in einem einheitlichen, reduzierten Designsystem und eine Kommandozeile, getestet mit synthetischen Daten. **Nicht vorhanden** sind
> Intake, Erhaltung, Backup-Läufe, der Import der Excel-Sheets, Register und Transkription. Eine erste
> Datenlieferung (Pilotfall `001-2`) liegt im lokalen Eingang `INTAKE`, ist aber weder nach dem
> Intake-Vertrag geprüft noch erhalten oder gesichert; der Primärspeicher, das Backup und der
> Austauschordner sind geplant, aber nicht eingerichtet.
>
> **Entstehung.** Das technische Fundament (Struktur, Verträge, Resolver) entstand am 2026-10-12 zunächst
> ohne Netzwerkpipeline ([Bootstrap-Bericht](docs/agent-runs/2026-10-12_bootstrap.md)); das Netzwerkmodul
> wurde am selben Tag darauf aufgesetzt ([Netzwerk-Bericht](docs/agent-runs/2026-10-12_netzwerkpipeline-pilot-001-2.md)).
> Der erste Git-Commit fasst beide Stände zusammen; die Entstehungsfolge steht in diesen Berichten, nicht in der Git-Historie.

## Einstieg

| Frage | Dokument |
|---|---|
| Welche Regeln gelten hier? | [`AGENTS.md`](AGENTS.md) |
| Wie ist das System aufgebaut, welches Dokument gilt wofür? | [`docs/architecture/overview.md`](docs/architecture/overview.md) |
| Wo liegen welche Daten? | [`docs/architecture/storage-contract.md`](docs/architecture/storage-contract.md) |
| Wie sind Fälle, IDs, Herkunft und Status modelliert? | [`docs/architecture/data-contract.md`](docs/architecture/data-contract.md) |
| Wie kommen Daten hinein und werden gesichert? | [`docs/architecture/intake-preservation.md`](docs/architecture/intake-preservation.md) |
| Wie funktioniert das Netzwerkmodul (Paketformat, Regeln, Läufe)? | [`docs/architecture/network-module.md`](docs/architecture/network-module.md) |
| Wie werden Grafiken gestaltet? | [`docs/architecture/visualization-conventions.md`](docs/architecture/visualization-conventions.md) |
| Was ist der Pilotfall `001-2`, und was schränkt ihn ein? | [`docs/methodology/pilot-case-001-2.md`](docs/methodology/pilot-case-001-2.md) |
| Was ist geplant? | [`docs/architecture/modules.md`](docs/architecture/modules.md), [`docs/plans/`](docs/plans/) |

## Architektur in Kürze

```text
Repository   Code, Verträge, Vorlagen, synthetische Beispiele      (dieser Checkout)
WORKSPACE    regenerierbare Laufzeitdaten                          (lokal, außerhalb des Checkouts)
INTAKE       Eingang, Staging, Quarantäne, Berichte                (lokal, außerhalb des Checkouts)
PRIMARY      autoritativer Forschungsdatenbestand                  (Universitäts-Fileservice)
BACKUP       unabhängige, verifizierte Zweitkopie                  (externer Datenträger)
EXCHANGE     kontrollierter Austausch mit Studierenden             (Nextbox)
```

Code kennt nur diese Namen. Wo ein Root auf einer Maschine liegt, steht in deren `.env`; ein
fehlender Root ist ein Fehler oder ein expliziter Zustand, nie ein stiller Ausweichort. Gespeicherte
Orte sind Rootname + relativer Pfad, sodass ein Umzug des Primärspeichers keinen Datensatz ändert.

Forschungsdaten liegen **nie** in diesem Repository.

## Layout

```text
src/mares/
  core/            Pfade, Storage-Roots, logische Referenzen, IDs, Statusvokabular, Hashing
  intake/          (geplant) Eingang und Prüfung
  preservation/    (geplant) Erhaltung und Backup
  networks/        Netzwerkpaket-Import, Prüfung, Beziehungen, Auswertung, Grafiken, Kommandozeile
  transcription/   (geplant) Audio und Transkription
  exports/         (geplant) versionierte Datensätze
tests/             Tests des Fundaments; brauchen keinen Root, kein Netz, keine Daten
config/            Deklaration der Storage-Roots (Namen, keine Pfade)
templates/         Erhebungsinstrumente als leere, versionierte Vorlagen
examples/synthetic/  erfundene Beispieldaten
docs/
  architecture/    aktuelle Verträge und Übersicht
  methodology/     methodische Grundlagen
  decisions/       datierte Architekturentscheidungen
  plans/           Vorhaben
  agent-runs/      Berichte einzelner Agent-Runs (siehe AGENTS.md, Regel 21)
```

## Einrichtung

Voraussetzung: Python ≥ 3.11 und Git. Laufzeitabhängigkeiten (NetworkX, Matplotlib) installiert `pip install -e` mit.

```text
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
copy .env.example .env
```

In `.env` die Roots dieser Maschine eintragen: absolute, bereits existierende Ordner außerhalb
jedes Git-Checkouts. Für Entwicklung und Tests genügen `MARES_WORKSPACE_ROOT` und
`MARES_INTAKE_ROOT`; alles andere darf leer bleiben. Das Paket läuft aus dem Checkout (editierbare
Installation), weil es `config/` relativ zu sich selbst findet.

Zustand der Roots anzeigen:

```text
.venv\Scripts\python -c "from mares.core.roots import Roots; [print(n, s.value) for n, s in Roots.load().status().items()]"
```

## Netzwerke auswerten

Ein Netzwerkpaket (CSV-Ordner im Format `mares-network-package/v0-draft`) liegt in `INTAKE` oder
`PRIMARY`. Ein Aufruf erzeugt einen neuen Lauf unter `WORKSPACE/runs/<RUN-ID>/`:

```text
.venv\Scripts\python -m mares.networks validate --package INTAKE:inbox/<Lieferung>/contents
.venv\Scripts\python -m mares.networks run      --package INTAKE:inbox/<Lieferung>/contents --curation INTAKE:inbox/<Ordner>/curation.json
```

`validate` → `import` → `analyze` → `figures` → `run` bauen aufeinander auf (`run` erzeugt zusätzlich den
Verarbeitungsbericht). `--curation` (optional) ist eine datierte Datei mit Aussagen *über* das Paket – Erhebungsmethode, Paarabdeckung,
Kategorie der Prüfhinweise –; das Paket selbst bleibt unverändert. Ein Paket mit harten Fehlern wird nicht weiterverarbeitet. Zum Ausprobieren dient
`examples/synthetic/network-package-0000/` (in einen `INTAKE`-Ordner kopieren). Die Abbildungen B3, G2 und P1–P3 erscheinen in zwei Profilen (`clean` in `figures/`, `analysis` in `figures/analysis/`); `--language-view`, `--tie-highlight` und `--profiles` wählen Sprachansicht, Beziehungshervorhebung und Profile (Designsystem: [`docs/architecture/visualization-conventions.md`](docs/architecture/visualization-conventions.md) §3.4–3.5). Einzelheiten:
[`docs/architecture/network-module.md`](docs/architecture/network-module.md) §7.

## Tests

```text
.venv\Scripts\python -m pytest
```

Die Tests lesen weder `.env` noch echte Roots. Sie prüfen den Resolver mit temporären Ordnern, die
Identifikatoren, das synthetische Beispiel, dass kein Maschinenpfad in operativen Dateien steht,
dass der Code aus einem Checkout an anderer Stelle funktioniert, und dass Git lokale Konfiguration
und Forschungsdaten ignoriert.

## Spätere Nutzung

Die folgenden Schritte bauen in dieser Reihenfolge auf dem Fundament auf; jeder ist ein eigener,
abgegrenzter Run:

1. Externe Roots einrichten ([`docs/plans/external-storage-setup.md`](docs/plans/external-storage-setup.md)).
2. Erhebungsinstrument (Netzwerk-Sheet) als versionierte Vorlage festlegen.
3. Register, Intake und Erhaltung implementieren; danach Backup mit Verifikation.
4. Altbestand kontrolliert importieren ([`docs/plans/legacy-import.md`](docs/plans/legacy-import.md)).
5. Netzwerk: Import der Excel-Sheets, Ablage in `PRIMARY`, Kennzahlen bei vollständiger Erhebung (CSV-Import, Validierung und Visualisierung gibt es bereits).
6. Transkription, nach geklärter Freigabe der Recheninfrastruktur für personenbezogene Daten.
