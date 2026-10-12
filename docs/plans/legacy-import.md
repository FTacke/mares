# Plan: kontrollierter Import des provisorischen Altbestands

**Status: offen; nicht begonnen.** Dieser Plan beschreibt einen späteren, eigenen Run. Im
Bootstrap-Run wurde der Altbestand weder verändert noch übernommen.

## Ausgangslage (2026-10-12)

Auf dem Projektarbeitsplatz liegt unter `C:\dev\mares_provisorisch` ein noch nicht systematisch
organisierter Bestand an Forschungsdaten und Projektdokumenten aus der Zeit vor dieser
Infrastruktur: 28 Dateien in 4 Hauptordnern, rund 300 MB. Darunter fünf Audiodateien (MP3, M4A,
FLAC), im Übrigen PDF- und Word-Dokumente, eine Präsentation und Textdateien. Der Ordner ist kein
Git-Repository.

Ein Inventar (relativer Pfad, Größe, Änderungszeit, SHA-256) wurde lesend erstellt und liegt
**außerhalb des Repositorys** unter `INTAKE/reports`. Es enthält die Originaldateinamen und gehört
deshalb nicht in Git; diese Datei nennt bewusst keine Dateinamen.

Der Ordner ist bis zum Import **nur lesend** zu behandeln (`AGENTS.md` §3).

## Voraussetzungen

1. `PRIMARY` ist eingerichtet, die Rechte für `restricted/` sind geklärt
   ([`external-storage-setup.md`](external-storage-setup.md)).
2. Register, Intake und Erhaltung sind implementiert und mit synthetischen Daten getestet.
3. Die Einwilligungslage der Altfälle ist gesichtet (durch die Projektleitung, nicht durch einen
   Agenten).

## Vorgehen

1. **Root setzen.** `MARES_LEGACY_IMPORT_ROOT` zeigt auf den Altbestand; der Root ist als nur
   lesend deklariert.
2. **Inventar prüfen.** Aktuelles Inventar gegen das vom 2026-10-12 vergleichen; Abweichungen
   klären, bevor irgendetwas übernommen wird.
3. **Sichten und klassifizieren** – durch eine Person: je Datei entweder *Forschungsdatum*
   (Aufnahme, Erhebungsbogen, Einwilligung, Transkript), *Projektdokument* (Planung, Literatur,
   Präsentation; kein Forschungsdatum, gehört nicht in `preservation/`) oder *unklar*.
4. **Fälle registrieren.** Für jede befragte Person eine Fall-ID vergeben, mit Provenienz
   (`RESEARCH` oder `TEACHING`, Kontext, erhebende Person, Instrument-Version – für Pilotmaterial
   gegebenenfalls eine eigens benannte Vor-Version). Die Zuordnung Datei → Fall wird ausdrücklich
   entschieden, nie aus Dateinamen erraten.
5. **Einreichen wie jede andere Abgabe.** Die Dateien werden in `INTAKE/inbox` **kopiert** und
   durchlaufen den normalen Intake; kein Sonderweg. Unklare Dateien gehen ins Review.
6. **Erhalten und verifizieren.** `RAW_PRESERVED` nach Rücklesen von `PRIMARY`; Einwilligungen
   nach `restricted/consent`.
7. **Backup und Verifikation.**
8. **Abgleich.** Jede Datei des Inventars ist entweder erhalten (Asset-ID, gleicher SHA-256),
   als Projektdokument bewusst nicht übernommen, oder im Review. Nichts bleibt ungeklärt.
9. **Altbestand stilllegen.** Erst nach Schritt 8 und einer ausdrücklichen Entscheidung: der Ordner
   wird unverändert nach `C:\dev\mares\legacy\mares_provisorisch` verschoben und bleibt dort nur
   lesend. Gelöscht wird nichts.

## Nicht Teil des Imports

Transkription der Altaufnahmen, Netzwerkauswertung, jede inhaltliche Korrektur. Bereits vorhandene
Transkripte werden als eigene Assets erhalten, nicht überschrieben oder neu erzeugt.

## Offen

- Ob das frühere Pilotprojekt-Material im Nextbox-Verzeichnis weiteren Altbestand enthält.
- Wie Pilotinstrumente ohne formale Version bezeichnet werden.
