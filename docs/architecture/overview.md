# Architekturübersicht

Zentraler Einstieg in die Architektur von MARES und die Stelle, die sagt, **welches Dokument wofür
maßgeblich ist**. Stand: 2026-10-12 (Projektfundament).

## 1. Welche Dokumente gelten

| Frage | Maßgeblich | Art |
|---|---|---|
| Regeln für die Arbeit im Repository | [`AGENTS.md`](../../AGENTS.md) | aktuelle Regel |
| Speicherbereiche, Roots, Layouts, Backup, Migration | [`storage-contract.md`](storage-contract.md) | aktueller Vertrag |
| IDs, Provenienz, Statusdimensionen, Datenmodell | [`data-contract.md`](data-contract.md) | aktueller Vertrag |
| Regeln für Intake, Erhaltung und Backup | [`intake-preservation.md`](intake-preservation.md) | aktueller Vertrag |
| Umfang und Grenzen der wissenschaftlichen Module | [`modules.md`](modules.md) | Planung (Netzwerke: implementiert) |
| Netzwerkmodul: Paketformat, Beziehungsregeln, Prüfung, Läufe | [`network-module.md`](network-module.md) | aktueller Vertrag |
| Gemeinsame Regeln für Grafiken | [`visualization-conventions.md`](visualization-conventions.md) | aktueller Vertrag |
| Methodische Grundlagen | [`../methodology/`](../methodology/README.md) | Fachdokumentation |
| Warum etwas so entschieden wurde | [`../decisions/`](../decisions/) | datierte Entscheidungen |
| Was als Nächstes ansteht | [`../plans/`](../plans/) | Pläne – Eingaben, keine Regeln |
| Was ein bestimmter Run getan hat | [`../agent-runs/`](../agent-runs/) | Journal – nie Spezifikation |

Bei einem Widerspruch gelten die Verträge unter `docs/architecture/` und `AGENTS.md`. Entscheidungen
begründen sie, Pläne und Agent-Run-Berichte ändern sie nicht. Überholter Text wird als überholt markiert
oder entfernt.

## 2. Was MARES ist

MARES – *Marburgo: Archivo de Redes y Experiencias Sociolingüísticas* – erhebt persönliche
Netzwerke, Mehrsprachigkeit und sprachliche Alltagserfahrungen lateinamerikanischer Migrant:innen:
Kontextdaten, egozentrierte Netzwerkkarten, Kontaktattribute, Alter-Alter-Beziehungen,
Audiointerviews und narrative Episoden.

Erhoben wird in Seminaren (mehrere Jahrgänge) und in regulärer Forschung. Beide benutzen
**dieselben Werkzeuge und denselben Datenbestand**; unterscheidbar bleiben die Daten durch
Provenienz-, Qualitäts- und Freigabemetadaten.

## 3. Aufbau

```text
                 Nextbox (EXCHANGE)                 Universitäts-Fileservice (PRIMARY)
                 Abgaben, Material                  autoritativer Bestand
                        │ Kopie                              ▲            │
                        ▼                                    │ verifiziert│ verifizierte Kopie
   ┌──────────── lokaler Arbeitsplatz ─────────────┐         │            ▼
   │  INTAKE     inbox → staging / quarantine  ────┼─────────┘      externe SSD (BACKUP)
   │  WORKSPACE  runs, cache, tmp                  │
   │  Repository Code, Verträge, Vorlagen,         │
   │             synthetische Beispiele            │
   └───────────────────────────────────────────────┘
```

| Schicht | Ort im Repository | Stand |
|---|---|---|
| Fundament: Pfade, Roots, Referenzen, IDs, Statusvokabular, Hashing | `src/mares/core/` | implementiert, getestet |
| Intake | `src/mares/intake/` | Vertrag vorhanden, nicht implementiert |
| Erhaltung und Backup | `src/mares/preservation/` | Vertrag vorhanden, nicht implementiert |
| Netzwerke | `src/mares/network_v0/`, `src/mares/network_v1/` (Einstieg `src/mares/networks/`) | implementiert (Import, Prüfung, Auswertung, Grafiken, Kommandozeile), getestet mit synthetischen Daten; Excel-Import, Register und Ablage in `PRIMARY` fehlen |
| Transkription | `src/mares/transcription/` | geplant |
| Exporte | `src/mares/exports/` | geplant |

## 4. Tragende Prinzipien

1. **Vier getrennte Dinge**: Quellcode, Arbeitsdaten, erhaltene Forschungsdaten, Backup – dazu der
   Austausch. Jedes hat einen eigenen benannten Root mit genau einer Rolle.
2. **Benannte Roots, eine Auflösungsstelle, kein Fallback.** Code kennt Namen; die Maschine kennt
   Orte. Ein fehlender Root ist ein Fehler oder ein expliziter Zustand, nie ein Ausweichort.
3. **Adressen sind keine Identität.** Gespeichert wird Rootname + relativer POSIX-Pfad; IDs und
   Hashes enthalten keinen Pfad. Ein Umzug des Primärspeichers ändert einen Konfigurationswert.
4. **Originale bleiben unverändert**, identifiziert durch SHA-256. Alles Verarbeitete ist eine
   eigene Version mit nachvollziehbarer Entstehung.
5. **Eine Pipeline, ein Bestand.** Lehre und Forschung unterscheiden sich in Metadaten, nicht in
   Werkzeugen. Die Herkunft eines Falls ändert sich nie.
6. **Unabhängige Statusdimensionen.** Provenienz, Instrument-Version, Datenversion, Qualität,
   Freigabe und zulässige Nutzung werden getrennt geführt; ebenso Erhaltung und Backup.
7. **Datenschutz ist Architektur.** Forschungsdaten sind nie im Repository; Schlüssel zu
   Pseudonymen liegen nur in `restricted/`; keine Audiodaten an externe Dienste.
8. **Nichts wird geraten, still korrigiert oder automatisch gelöscht.**

## 5. Abgrenzung

MARES folgt den Workspace-Konventionen des Arbeitsplatzes und übernimmt Architekturprinzipien von
CO.RA.PAN und CO.PRE.PAN, nicht deren Umfang: keine Produktions-Gates, keine Providerpolitik, keine
Auditprozesse, kein gemeinsames Vertragsbündel. Begründung:
[`../decisions/ADR-0001_2026-10-12_projektfundament.md`](../decisions/ADR-0001_2026-10-12_projektfundament.md).
