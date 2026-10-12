# Intake- und Preservation-Vertrag

**Status: verbindliche Regeln für eine noch nicht implementierte Verarbeitung.** Die Pakete
`mares.intake` und `mares.preservation` sind leer. Dieses Dokument legt fest, was ihre
Implementierung einhalten muss.

## 1. Ablauf

Der einfache Weg einer Datei:

```text
INBOX → INTAKE_VALIDATED → RAW_PRESERVED → BACKUP_VERIFIED → DERIVED → QUALITY_REVIEWED → RESEARCH_APPROVED
```

Das ist eine Lesehilfe, **keine Zustandskette**. Die tatsächliche Verarbeitung verzweigt, und die
Stationen gehören zu verschiedenen, voneinander unabhängigen Dimensionen
([`data-contract.md`](data-contract.md) §4):

| Station | Dimension | Bezieht sich auf | Zustände |
|---|---|---|---|
| INBOX, INTAKE_VALIDATED | Intake | Einreichung | `RECEIVED` · `INTAKE_VALIDATED` · `NEEDS_REVIEW` · `QUARANTINED` · `REJECTED` |
| RAW_PRESERVED | Erhaltung | Asset | `NOT_PRESERVED` · `PENDING` · `RAW_PRESERVED` |
| BACKUP_VERIFIED | Backup | Asset | `NO_COPY` · `COPY_UNVERIFIED` · `BACKUP_VERIFIED` |
| DERIVED | Verarbeitung | Datensatzversion | `RUN-…`, `DS-…@vN` |
| QUALITY_REVIEWED | Datenqualität | Fall in einer Datensatzversion | `UNREVIEWED` … `NOT_USABLE` |
| RESEARCH_APPROVED | Freigabe | Fall in einer Datensatzversion | `NOT_DECIDED` … `WITHDRAWN` |

Folgen daraus: Ein Asset kann `RAW_PRESERVED` und ohne Backup sein. Abgeleitete Daten dürfen
entstehen, bevor ein Backup verifiziert ist. Ein qualitätsgeprüfter Fall ist nicht automatisch
freigegeben. Kein Status wird gesetzt, weil ein anderer erreicht wurde.

## 2. Wo was liegt

| Schritt | Liest | Schreibt |
|---|---|---|
| Eingang | `EXCHANGE` (Abgabeordner) oder direkte Übergabe | `INTAKE/inbox` – als **Kopie**; die Quelle bleibt unverändert |
| Intake-Prüfung | `INTAKE/inbox` | `INTAKE/staging` oder `INTAKE/quarantine`; Bericht nach `INTAKE/reports` |
| Erhaltung | `INTAKE/staging` | `PRIMARY/preservation/raw`, `PRIMARY/preservation/manifests`, Register |
| Backup | `PRIMARY` | `BACKUP`, `BACKUP/backup_manifests` |
| Ableitung | `PRIMARY/preservation`, `PRIMARY/derived` | `WORKSPACE/runs` (Arbeit), dann `PRIMARY/derived` |
| Freigabe | `PRIMARY/derived`, Register | `PRIMARY/releases` |

## 3. Regeln

**Originale**

1. Originaldateien werden nie überschrieben, umbenannt, umkodiert oder „repariert“. Erhalten wird
   Byte für Byte, was eingereicht wurde.
2. Inhaltsintegrität ist SHA-256 über die Dateibytes.
3. Erhalten (`RAW_PRESERVED`) ist ein Asset erst, wenn die Bytes auf `PRIMARY` geschrieben, **von
   dort zurückgelesen** und gegen den Hash geprüft sind und das Manifest geschrieben ist. Ist
   `PRIMARY` nicht erreichbar, entsteht kein Erfolg; die Datei bleibt in `INTAKE/staging` und der
   Zustand ist `PENDING`.
4. Rohdaten bleiben von kanonischen Arbeitsdaten und abgeleiteten Ergebnissen getrennt.

**Intake**

5. Wiederholtes Intake ist idempotent: dieselbe Datei erneut einzulesen erzeugt kein zweites Asset
   und keinen abweichenden Zustand.
6. Identische Inhalte werden am Hash erkannt und nur einmal erhalten. Jedes **Einreichungsereignis**
   bleibt trotzdem nachvollziehbar: wer, wann, über welchen Weg, mit welchem Originalnamen.
7. Keine Fallzuordnung durch Raten – nicht aus Dateinamen, Ordnernamen, Zeitstempeln oder
   Ähnlichkeit. Eine Zuordnung stammt aus einer ausdrücklichen Angabe (Abgabeordner und
   Begleitangaben) oder aus einer Entscheidung im Review.
8. Unklare Zuordnungen gehen ins Review (`NEEDS_REVIEW`), beschädigte oder unlesbare Dateien in die
   Quarantäne (`QUARANTINED`). Beides sind sichtbare, abfragbare Zustände.
9. Keine stillschweigenden Datenkorrekturen. Wer einen Wert ändert, erzeugt einen dokumentierten
   Verarbeitungsschritt mit eigener Ausgabe; das Original bleibt, wie es war.

**Läufe**

10. Jeder Verarbeitungslauf referenziert Eingaben, Parameter, Softwareversion und Ausgaben
    ([`data-contract.md`](data-contract.md) §6).

**Backup**

11. Erhaltungserfolg ist nicht Backup-Erfolg; `RAW_PRESERVED` sagt nichts über eine Zweitkopie.
12. Backups werden unabhängig verifiziert (gegen das Inventar von `PRIMARY`, vom Backup
    zurückgelesen), und Restore ist durch Stichproben prüfbar
    ([`storage-contract.md`](storage-contract.md) §4.2).
13. `BACKUP` und `EXCHANGE` werden nie stillschweigend als Datenquelle benutzt, wenn `PRIMARY` fehlt.

**Löschen**

14. Keine automatischen destruktiven Bereinigungen – nicht in `INTAKE`, nicht in `PRIMARY`, nicht
    in `BACKUP`, nicht in `EXCHANGE`. Löschen ist eine ausdrücklich entschiedene, protokollierte
    Handlung einer Person; vorher ist geprüft, dass nichts die einzige Kopie ist.

## 4. Spätere Schnittstellen

Vorgesehene Operationen, als Grenzen der künftigen Implementierung. Namen und Signaturen sind
Entwurf; die Verträge darüber sind es nicht.

| Operation | Eingabe | Ergebnis | Schreibt |
|---|---|---|---|
| `intake.receive` | Ordner in `INTAKE/inbox`, Einreichungsangaben (Kohorte, Abgabe-Pseudonym, Weg) | Einreichung `SUB-…` mit Dateiliste und Hashes | Register, Bericht |
| `intake.validate` | Einreichung | je Datei: `INTAKE_VALIDATED`, `NEEDS_REVIEW`, `QUARANTINED` oder `REJECTED`, mit Grund | `staging/` bzw. `quarantine/`, Bericht |
| `intake.assign` | Datei, Fall-ID, entscheidende Person | Zuordnungsereignis | Register |
| `preservation.preserve` | validierte Datei | Asset `AST-…`, Zustand `RAW_PRESERVED` oder `PENDING` | `preservation/raw`, Manifest, Register |
| `preservation.verify` | Asset(s) | je Asset: Hash stimmt / stimmt nicht / nicht erreichbar | Prüfbericht; **ändert keine Daten** |
| `backup.copy` | Inventar von `PRIMARY` | Kopierbeleg | `BACKUP` (nur ergänzend) |
| `backup.verify` | Kopierbeleg | `BACKUP_VERIFIED` oder Abweichungsliste | `backup_manifests/` |
| `backup.restore_test` | Stichprobe | je Datei: wiederhergestellt und Hash stimmt | Protokoll |

Alle Operationen erhalten ihre Orte ausschließlich über `mares.core.roots.Roots` und speichern Orte
ausschließlich als logische Referenzen.

## 5. Nicht entschieden

- Dateiformat und Schema von Manifest und Register.
- Endgültiges Layout unter `preservation/raw`.
- Welche Begleitangaben eine studentische Abgabe mitbringen muss, damit die Fallzuordnung ohne
  Review möglich ist (hängt am Erhebungsinstrument).
