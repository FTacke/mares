# ADR-0001 – Projektfundament: Struktur, Storage-Roots, ein Bestand für Lehre und Forschung

**Datum:** 2026-10-12 · **Status:** in Kraft

Diese Entscheidung begründet die Verträge unter `docs/architecture/`. Maßgeblich für die aktuelle
Regel sind die Verträge selbst; dieses Dokument hält fest, was entschieden wurde und warum.

## Kontext

MARES beginnt mit einem unsortierten Altbestand und soll über Jahre studentische Erhebungen
mehrerer Seminarjahrgänge und professionelle Forschung tragen. Die Daten sind personenbezogen und
teils besonders schutzwürdig. Auf demselben Arbeitsplatz bestehen zwei große Korpusprojekte
(CO.RA.PAN, CO.PRE.PAN) mit einer ausgereiften, aber umfangreichen Speicher- und
Erhaltungsarchitektur und gemeinsame Workspace-Konventionen.

## Entscheidungen

1. **Projektfamilie mit einem Repository.** `mares\` ist ein gewöhnlicher Ordner mit dem einzigen
   Git-Repository `mares\mares` und den Geschwistern `mares_workspace` und `mares_storage`. Der
   Familienordner ist gerechtfertigt, weil Laufzeit- und Eingangsdaten von Anfang an außerhalb des
   Checkouts liegen müssen.

2. **Sechs benannte Roots, ein Resolver, kein Fallback.** `WORKSPACE`, `INTAKE`, `PRIMARY`,
   `BACKUP`, `EXCHANGE`, `LEGACY_IMPORT`; deklariert in `config/storage_roots.toml`, aufgelöst nur
   von `mares.core.roots`. Der lokale Eingangsbereich heißt als Root `INTAKE` (Funktion); sein
   Ordner heißt `mares_storage` (Workspace-Konvention `<repo>_storage`).

3. **`PRIMARY` statt `PRESERVATION`.** Der Root heißt nach seiner Stellung, weil er mehr enthält
   als erhaltene Originale: auch abgeleitete Daten, Register, geschützte Unterlagen und Releases.
   Die Erhaltung ist ein Teilbereich (`preservation/`).

4. **Prinzipien der Korpusprojekte übernommen, nicht ihr Apparat.** Übernommen: Rollen statt Orte,
   Fail-closed-Auflösung, logische Referenzen, Inhalts-Hashes, Rücklesen vor Erfolg, Backup nur als
   verifizierte Kopie auf anderem Volume, Migration als verifizierte Kopie. Nicht übernommen:
   Holdings, Spool, Distribution, Zielidentitätsmarker, Konformitätsbündel, Produktions-Gates,
   Providerpolitik, Auditprozesse. MARES ist keine Partei von `crosscorpus-storage/v1`.
   *Grund:* MARES hat wenige, kleine, manuell eingereichte Fälle; sein Risiko ist Vertraulichkeit
   und Nachvollziehbarkeit, nicht Durchsatz.

5. **Ein Bestand und eine Pipeline für `TEACHING` und `RESEARCH`.** Die Herkunft ist ein
   unveränderliches Attribut des Falls, kein eigener Ordner, ID-Raum oder Codepfad.
   *Grund:* Studentisch erhobene Fälle sollen ohne Kopieren oder Umschlüsseln in
   Forschungsdatensätze aufgenommen werden können; getrennte Pipelines würden auseinanderlaufen.

6. **Sechs unabhängige Statusdimensionen**, dazu Erhaltung und Backup als getrennte technische
   Zustände. Der lineare Ablauf `INBOX → … → RESEARCH_APPROVED` ist eine Lesehilfe, keine
   Zustandskette.

7. **Fall-IDs ohne Herkunft, Pfad oder Personenbezug** (`MARES-JJJJ-NNN`); Asset-IDs zufällig;
   Inhalt durch SHA-256. Das Jahr `0000` ist für synthetische Fälle reserviert.

8. **Ablage erhaltener Originale unabhängig von Fall und Dateiname.** Zuordnung und Originalname
   stehen im Manifest und Register. *Grund:* Zuordnungen werden korrigiert; personenbezogene
   Dateinamen sollen nicht in Verzeichnisbäumen stehen; identische Inhalte werden einmal erhalten.

9. **TOML für die Root-Deklaration, keine Laufzeitabhängigkeit.** `tomllib` ist Teil der
   Standardbibliothek (Python ≥ 3.11); ein handgeschriebener YAML-Leser wie in den Korpusprojekten
   entfällt.

10. **Dokumentation deutsch, Code englisch.** Verträge und Regeln werden von der Projektleitung
    und Mitarbeitenden gelesen; Bezeichner bleiben anschlussfähig.

11. **Externe Roots werden im Bootstrap nicht angelegt.** Für Fileservice, Backup-SSD und Nextbox
    waren Zielort oder Berechtigungen nicht eindeutig geklärt
    ([`../plans/external-storage-setup.md`](../plans/external-storage-setup.md)).

## Folgen

- Echte Daten können erst verarbeitet werden, wenn `PRIMARY` eingerichtet ist; bis dahin ist nur
  Entwicklung mit synthetischen Daten möglich. Das ist gewollt.
- Das Paket läuft aus dem Checkout (editierbare Installation), weil `config/` relativ zum Code
  gefunden wird.
- Erhaltene Originale sind im Dateibaum nicht nach Fällen lesbar; die Sicht nach Fällen liefert das
  Register.

## Offen

Vokabular der zulässigen Nutzung (an die Einwilligungserklärungen gebunden); Format von Manifest
und Register; endgültiges Layout unter `preservation/raw`; Ort und Rechte des Primärspeichers;
Verschlüsselung des Backup-Datenträgers; Freigabe von MaRC3a für personenbezogene Daten.
