# Regeln für die Arbeit in diesem Repository

Gilt für alle, die hier arbeiten – Menschen und Coding-Agenten. Dies ist die einzige Regelsammlung;
`CLAUDE.md` verweist nur hierher. Architektur und Verträge:
[`docs/architecture/overview.md`](docs/architecture/overview.md).

MARES verarbeitet **personenbezogene Forschungsdaten** (Interviews, Netzwerke, Einwilligungen von
Migrant:innen). Die meisten Regeln folgen daraus.

## 1. Forschungsdaten

1. **Forschungsdaten liegen nie im Git-Repository** – keine Aufnahmen, Erhebungssheets,
   Einwilligungen, Transkripte, Register oder Auszüge daraus, auch nicht „nur zum Testen“.
   `.gitignore` ist die zweite Verteidigungslinie, nicht die erste.
2. **Echte Forschungsdaten liegen nur im dafür berechtigten Storage** (`PRIMARY`, davor `INTAKE`).
   Temporäre Arbeitsdaten und Datenbankdateien liegen im `WORKSPACE`, außerhalb des Repositorys.
3. **Sensible Daten gehen nicht an Coding-Agenten oder externe Dienste**, solange das nicht
   ausdrücklich freigegeben ist. Ein Agent liest keine Inhalte von Forschungsdaten (Audio,
   ausgefüllte Sheets, Einwilligungen, Transkripte) und gibt sie nicht wieder; er arbeitet mit
   Code, Verträgen und synthetischen Daten. Keine Audiodaten an Cloud-Anbieter oder externe APIs.
4. **Keine Secrets, keine Forschungsdaten und keine personenbezogenen Dateinamen in Logs,
   Fehlermeldungen, Commit-Nachrichten oder versionierter Dokumentation.** Berichte, die solche
   Namen brauchen, liegen unter `INTAKE/reports`, nicht im Repository.
5. **Originale werden nie überschrieben, nichts wird still korrigiert, nichts automatisch
   gelöscht.** Details: [`docs/architecture/intake-preservation.md`](docs/architecture/intake-preservation.md).

## 2. Speicherorte

6. **Operative Dateizugriffe laufen ausschließlich über konfigurierte Roots**
   (`mares.core.roots.Roots`). Kein Modul baut eigene absolute Pfade, liest `.env` selbst oder
   erreicht Nachbarordner über `..`.
7. **Kein Maschinenpfad in versioniertem Code oder versionierter Konfiguration** – kein
   Laufwerksbuchstabe, keine UNC-Freigabe, kein Home-Verzeichnis. Dokumentation und Agent-Run-Berichte
   dürfen Orte einer Maschine beschreiben. Ein Test prüft das; eine begründete Ausnahme trägt den
   Marker `path-literal-ok` in derselben Zeile.
8. **Kein Fallback.** Ein fehlender oder unbrauchbarer Root ist ein Fehler oder ein expliziter
   Zustand. `BACKUP` und `EXCHANGE` (Nextbox) werden nie stillschweigend als Datenquelle benutzt.
9. **Gespeicherte Orte sind logische Referenzen** (Rootname + relativer POSIX-Pfad). Pfade gehen
   nie in IDs, Hashes oder Cache-Schlüssel ein.
10. **Externe Roots werden nicht nebenbei angelegt oder verändert.** Verzeichnisse auf dem
    Fileservice, der Backup-SSD oder in Nextbox entstehen in einem dafür vorgesehenen Schritt nach
    [`docs/plans/external-storage-setup.md`](docs/plans/external-storage-setup.md).

## 3. Altbestand

11. `C:\dev\mares_provisorisch` (auf dem Projektarbeitsplatz) ist provisorischer Altbestand und
    **nur lesend**: nichts verschieben, umbenennen, löschen, transkribieren oder ins Repository
    kopieren. Der Import ist ein eigener, kontrollierter Run nach
    [`docs/plans/legacy-import.md`](docs/plans/legacy-import.md).

## 4. Code und Tests

12. **Tests greifen nie auf Forschungsdaten zu** und brauchen keinen konfigurierten Root, kein Netz
    und kein Modell. Sie benutzen temporäre Verzeichnisse und `examples/synthetic/`.
13. **Neue Funktionen werden mit synthetischen Fixtures entwickelt und getestet.** Synthetische
    Fälle tragen das Jahr `0000`.
14. **Keine unnötigen Abhängigkeiten oder Infrastruktur.** Eine Abhängigkeit kommt mit dem Code,
    der sie benutzt. Keine Datenbank, kein Webdienst, kein Container, kein CLI-Framework auf Vorrat.
15. **Ein Vertrag wird mit dem Code geändert, der ihn betrifft** – nicht nur der Code. Wer von
    `docs/architecture/` abweichen muss, ändert zuerst das Dokument und hält den Grund unter
    `docs/decisions/` fest.

## 5. Git und Dokumentation

16. Ein kanonischer Checkout; keine zweiten Klone. Parallele Arbeit über Branches, Worktrees nur
    außerhalb des Arbeitsverzeichnisses (`<Projektfamilie>\worktrees\mares\<name>`).
17. Commit und Push nur auf Anforderung; Commits mit expliziten Pfadangaben, nie `git add -A`.
    Vorhandene Änderungen im Arbeitsverzeichnis können von jemand anderem stammen.
18. Dokumentation auf Deutsch; Code, Bezeichner und Docstrings auf Englisch.
19. Aktuelle Regeln stehen in `docs/architecture/`, Begründungen in `docs/decisions/`, Vorhaben in
    `docs/plans/`, Berichte einzelner Runs in `docs/agent-runs/` (Regel 21).
20. Soll und Ist werden getrennt benannt. Was geplant ist, wird nicht als vorhanden beschrieben.
21. **Run-Berichte.** Für jeden substanziellen Claude-Code-Run, der Implementierung, Architektur,
    Migration, Datenverarbeitung, umfangreiche Reparaturen oder systematische Audits umfasst, wird
    ein datierter Abschlussbericht unter `docs/agent-runs/` erstellt – unmittelbar zum Abschluss des
    Runs, als Datei `YYYY-MM-DD_kurze-beschreibung.md`. Er enthält mindestens: Ziel und Scope;
    tatsächlich durchgeführte Änderungen beziehungsweise Untersuchungen; relevante technische oder
    methodische Entscheidungen; durchgeführte Tests und Ergebnisse; erreichten Status; offene
    Punkte, Einschränkungen und gegebenenfalls nächste Schritte.
    - Der Bericht unterscheidet ausdrücklich zwischen **implementierten Änderungen**,
      **bestandenen Tests** und **wissenschaftlich validierten Ergebnissen**; das eine folgt nicht
      aus dem anderen.
    - Kurze Routineänderungen, minimale Dokumentationskorrekturen und triviale Anpassungen brauchen
      keinen Bericht.
    - Ein Bericht dokumentiert einen historischen Vorgang und ist keine normative Spezifikation;
      aktuelle Entscheidungen und Verträge stehen in `docs/decisions/` und `docs/architecture/`.
      Bereits Dokumentiertes wird referenziert, nicht wiederholt.
    - Ein Bericht enthält keine personenbezogenen Forschungsdaten, Secrets oder sonstigen
      vertraulichen Inhalte (Regel 4 gilt auch hier).

## 6. Arbeiten

```text
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest
```
