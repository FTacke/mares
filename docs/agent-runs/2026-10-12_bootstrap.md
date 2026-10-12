# Run-Bericht 2026-10-12 – Bootstrap des Projektfundaments

Journal eines Laufs, keine Spezifikation. Maßgeblich sind die Verträge unter
[`../architecture/`](../architecture/overview.md). Ortsangaben beschreiben den Projektarbeitsplatz.

## Auftrag

Projektstruktur, Architektur- und Datenverträge und ein minimales Python-Fundament für MARES
anlegen. Ausdrücklich nicht: Netzwerk- oder Transkriptionsfunktionen, HPC, Migration vorhandener
Daten.

## Gelesen (ausschließlich lesend)

- Workspace-Konventionen: `C:\dev\README.md`, `C:\dev\AGENTS.md`.
- CO.PRE.PAN: README, `CLAUDE.md`, `.env.example`, `.gitignore`, `.gitattributes`,
  `pyproject.toml`, `config/storage_targets.yml`, `src/coprepan/storage_roots.py`, der gemeinsame
  Vertrag `contracts/crosscorpus-storage-v1/CONTRACT.md`.
- CO.RA.PAN: `.env.example`, `config/storage_targets.yml`, Backup-Teil von
  `config/storage_retention.yml`, Topologie- und Backup-Abschnitte von
  `docs/architecture/STORAGE_TARGETS_AND_PRESERVATION.md`; aus den `.env`-Dateien nur die Zeilen der
  Root-Variablen (keine Zugangsdaten).
- Oberste Verzeichnisebene von Gruppenlaufwerk, Backup-SSD und Nextbox-Verzeichnis.

In den Referenzprojekten wurde nichts geschrieben, kein Test und kein Job gestartet. Während des
Laufs änderten sich in CO.RA.PAN Dateien unter `config/kisski_runs/` und `.git` – das sind Spuren
der dort laufenden eigenen Prozesse, nicht dieses Laufs.

## Ist: angelegt

```text
C:\dev\mares\                    gewöhnlicher Ordner, kein Git-Repository
├── mares\                       einziges Git-Repository (Branch main, kein Commit, kein Remote)
├── mares_workspace\             runs\  cache\  tmp\                    (leer)
└── mares_storage\               inbox\  staging\  quarantine\  reports\
                                 reports\legacy_inventory_2026-10-12.tsv
```

Im Repository:

| Bereich | Dateien |
|---|---|
| Einstieg | `README.md`, `AGENTS.md`, `CLAUDE.md` |
| Git und Konfiguration | `.gitignore`, `.gitattributes`, `.env.example`, `pyproject.toml`, `config/storage_roots.toml` |
| Code | `src/mares/core/{paths,roots,refs,ids,model,hashing}.py`; `intake`, `preservation`, `networks`, `transcription`, `exports` als Pakete mit Beschreibung, ohne Code |
| Tests | `tests/test_roots.py`, `tests/test_refs_and_ids.py`, `tests/test_repository_contract.py` |
| Synthetische Daten | `examples/synthetic/MARES-0000-001/{case.json,contacts.csv,ties.csv}` |
| Verträge | `docs/architecture/{overview,storage-contract,data-contract,intake-preservation,modules}.md` |
| Weitere Dokumente | `docs/decisions/ADR-0001_2026-10-12_projektfundament.md`, `docs/plans/{external-storage-setup,legacy-import}.md`, `docs/methodology/README.md`, `templates/README.md` |

Lokal und gitignored: `.env` (nur `MARES_WORKSPACE_ROOT` und `MARES_INTAKE_ROOT` gesetzt) und
`.venv` (editierbare Installation mit pytest).

## Ist: Storage-Roots

| Root | Zustand laut Resolver | Bemerkung |
|---|---|---|
| `WORKSPACE` | `AVAILABLE` | `C:\dev\mares\mares_workspace` |
| `INTAKE` | `AVAILABLE` | `C:\dev\mares\mares_storage` |
| `PRIMARY` | `NOT_CONFIGURED` | auf dem Gruppenlaufwerk existiert kein MARES-Ordner; nicht angelegt |
| `BACKUP` | `NOT_CONFIGURED` | auf der SSD existiert kein MARES-Bereich; nicht angelegt |
| `EXCHANGE` | `NOT_CONFIGURED` | im Nextbox-Verzeichnis existiert kein Ordner `MARES`; nicht angelegt |
| `LEGACY_IMPORT` | `NOT_CONFIGURED` | Altbestand vorhanden, bewusst nicht konfiguriert |

**Kein externes Verzeichnis wurde angelegt.** Gründe und offene Schritte:
[`../plans/external-storage-setup.md`](../plans/external-storage-setup.md).

## Abweichungen von der Zielskizze

- Der lokale Bereich `mares_storage` heißt als Root `INTAKE` (Variable `MARES_INTAKE_ROOT`): der
  Name nennt die Funktion, der Ordnername folgt der Workspace-Konvention.
- Zusätzlicher optionaler, nur lesender Root `LEGACY_IMPORT` für den Altbestand, damit auch der
  spätere Import über einen konfigurierten Root läuft.
- `templates/` und `docs/methodology/` enthalten je nur eine kurze README, weil Instrument und
  Methodikdokumente noch nicht festgelegt sind.
- Die Root-Deklaration ist TOML statt YAML (Standardbibliothek, keine Abhängigkeit).
- Die Pakete der geplanten Module enthalten bewusst keine Schnittstellen im Code; die Schnittstellen
  stehen im Intake-/Preservation-Vertrag.

## Validierung

| # | Prüfung | Ergebnis |
|---|---|---|
| 1 | Struktur entspricht den Workspace-Konventionen | ja: Familienordner ohne Git, `<repo>`, `<repo>_workspace`, `<repo>_storage` |
| 2 | Genau ein neues Git-Repository | ja: einziges `.git` unter `C:\dev\mares` ist `mares\mares\.git` |
| 3 | Workspace und Storage außerhalb des Repositorys | ja; beide sind keine Git-Arbeitsverzeichnisse |
| 4 | Git ignoriert lokale Konfiguration, Secrets, Caches, Daten | ja: `.env`, `.venv`, Caches als ignoriert gemeldet; 17 Beispielpfade per `git check-ignore` ignoriert, 9 Vertrags-/Vorlagenpfade verfolgbar |
| 5 | Resolver mit synthetischen Roots | ja (`tests/test_roots.py`) |
| 6 | Fehlende und ungültige Roots werden abgefangen | ja: nicht gesetzt, relativ, Dateisystem-Root, im Checkout, überlappend, unerreichbar, nur lesend, nicht deklariert |
| 7 | Unabhängig vom Checkout-Pfad | ja: Test kopiert Code und Konfiguration an einen anderen Ort und führt ihn dort aus |
| 8 | Keine Maschinenpfade im operativen Code | ja: Test über `src`, `config`, `tests`, `templates`, `examples` und die Konfigurationsdateien |
| 9 | Verträge widerspruchsfrei | gegengelesen: Rootnamen, Statuswerte und ID-Formen stimmen zwischen Verträgen, `config/storage_roots.toml`, `core/model.py`, `core/ids.py` und dem Beispiel überein; Tests binden `.env.example` an die Deklaration und das Beispiel an die Vokabulare |
| 10 | `mares_provisorisch` unverändert | ja: SHA-256 aller 28 Dateien sowie Größen und Änderungszeiten aller 35 Einträge vor und nach dem Lauf identisch |
| 11 | Kein Referenzprojekt verändert | nur Lesebefehle ausgeführt; siehe oben |
| 12 | Keine Netzwerk-, ASR- oder Backup-Verarbeitung gestartet | ja; es existiert kein solcher Code |

Tests: `python -m pytest` im neuen Repository – **62 bestanden**, 0 fehlgeschlagen (System-Python
3.12 und die `.venv` mit editierbarer Installation).

## Altbestand

Für `C:\dev\mares_provisorisch` wurde ein Inventar (SHA-256, Größe, Änderungszeit, relativer Pfad;
28 Dateien, rund 300 MB) erstellt und außerhalb des Repositorys unter
`mares_storage\reports\legacy_inventory_2026-10-12.tsv` abgelegt. Dafür wurden die Dateien gelesen,
nicht geöffnet oder ausgewertet. Nichts wurde verschoben, umbenannt, gelöscht oder kopiert.

## Nicht implementiert (bewusst)

Register (SQLite), Intake, Erhaltung, Backup-Läufe und -Verifikation, Netzwerkimport, Kennzahlen,
Visualisierung, Transkription, HPC-Anbindung, Exporte, Kommandozeile, Volume-Prüfung zwischen
`PRIMARY` und `BACKUP` (gehört zur Backup-Verifikation).

## Offene Entscheidungen

1. Ort des MARES-Ordners auf dem Gruppenlaufwerk und Zugriffsrechte für `restricted/` (HRZ).
2. Ordnername des Backup-Bereichs auf der SSD; Verschlüsselung des Datenträgers.
3. Nextbox: Verhältnis zum vorhandenen Pilotprojekt-Ordner; Abgabeverfahren und Pseudonyme.
4. Vokabular der zulässigen Nutzung, abzugleichen mit den Einwilligungserklärungen.
5. Format von Manifest und Register; endgültiges Layout unter `preservation/raw`.
6. Freigabe von MaRC3a für personenbezogene Forschungsdaten.

Kein Blocker für die weitere Entwicklung mit synthetischen Daten. Für die Arbeit mit echten Daten
ist Punkt 1 Voraussetzung.

## Git

Repository initialisiert (Branch `main`). Kein Commit, kein Remote, kein Push.

**Nachtrag (2026-10-12, nach dem Lauf).** Dieser Bericht beschreibt den Stand des Fundaments
*ohne* Netzwerkpipeline. Noch am selben Tag wurde das Netzwerkmodul aufgesetzt
([Bericht](2026-10-12_netzwerkpipeline-pilot-001-2.md)); dabei wurden auch Fundamentdateien erweitert
(`pyproject.toml`, `README.md`, einzelne Architekturdokumente, `core/ids.py`). Weil vor dem
ersten Commit keine Zwischenstände gesichert wurden, fasst der erste Git-Commit Fundament und Netzwerkmodul
zusammen; die obige Beschreibung bleibt als historischer Stand erhalten. Der Audio-Pilot
(`pilots/audio_enhancement/`) ist nicht Teil dieses Commits.
