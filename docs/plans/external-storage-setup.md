# Plan: externe Storage-Roots einrichten

**Status: offen.** Stand der Prüfung: 2026-10-12, ausschließlich lesend. Der Sollzustand steht im
[Storage-Vertrag](../architecture/storage-contract.md); dieser Plan nennt, was vor der Einrichtung
zu klären und dann zu tun ist. Die Ortsangaben beschreiben den Projektarbeitsplatz.

Im Bootstrap-Run wurde **kein externes Verzeichnis angelegt**. Für keinen der drei Roots waren
Zielort, Berechtigungen und Bestand so eindeutig geklärt, dass das gefahrlos gewesen wäre.

## 1. `PRIMARY` – Universitäts-Fileservice (K:, später New_FS)

Befund: Das Gruppenlaufwerk ist eingebunden und lesbar (Schreibrechte wurden nicht geprüft, weil nichts geschrieben wurde). Auf oberster Ebene liegen
der Projektordner von CO.RA.PAN, ein Institutsordner und Quota-Berichte; **einen MARES-Ordner gibt
es nicht.** Das Laufwerk ist eine gemeinsam genutzte Freigabe (zu etwa 85 % belegt, rund 213 GB
frei), kein MARES-eigenes Kontingent.

Zu klären:

1. **Ort des Projektroots**: eigener Ordner auf oberster Ebene der Freigabe (wie CO.RA.PAN) oder
   unterhalb des Institutsordners? Vorschlag: eigener Ordner `MARES` auf oberster Ebene.
2. **Zugriffsrechte**: Wer liest die Freigabe heute? `restricted/` (Einwilligungen,
   Identitätsschlüssel) braucht engere Rechte als der Rest – mit dem HRZ zu klären, bevor dort
   etwas abgelegt wird. **Bis dahin keine Einwilligungen oder Schlüssellisten auf die Freigabe.**
3. **Sicherung durch die Universität**: Gibt es Snapshots oder Backups der Freigabe, und mit
   welcher Aufbewahrung? (Beeinflusst nicht den Vertrag, aber die Risikobewertung.)
4. **New_FS**: Zeitpunkt und Zielpfad sind nicht bekannt. Bis er existiert, bleibt er ein Plan; er
   wird nirgends konfiguriert.

Dann:

1. Ordner anlegen und die Struktur aus Storage-Vertrag §4.1 erzeugen (durch eine Person oder einen
   eigens dafür beauftragten Run; künftig ein kleines `init`-Kommando).
2. Rechte für `restricted/` setzen und prüfen.
3. `MARES_PRIMARY_ROOT` in der `.env` setzen – bevorzugt als UNC-Pfad der Freigabe, nicht als
   Laufwerksbuchstabe, damit der Wert nicht von einer Laufwerkszuordnung abhängt.
4. Zustand prüfen (`Roots.load().status()`), Topologietabelle im Storage-Vertrag §2 fortschreiben.

## 2. `BACKUP` – externe SSD (D:)

Befund: Die SSD ist aktiv und hält unter `projects\<Projektfamilie>\<Projekt>\…` die Sicherungen
der anderen Projekte; reichlich freier Platz. **Einen MARES-Bereich gibt es nicht.**

Zu klären:

1. **Ordnername**: `projects\mares` (Projekt = Familie, wie in der Vorgabe skizziert) oder
   `projects\mares\mares` (strikt nach dem Muster Familie\Projekt der anderen Projekte)? Vorschlag:
   `projects\mares` als `BACKUP`-Root.
2. **Verschlüsselung**: Das Backup enthält laut Vorgabe auch `restricted/`. Ist der Datenträger
   verschlüsselt (z. B. BitLocker)? Wenn nicht, wird `restricted/` vorerst nicht dorthin gesichert
   oder der Datenträger wird verschlüsselt.
3. **Rhythmus und Auslöser** der Sicherung (manuell nach jedem Intake, periodisch?).

Dann: Ordner und Struktur aus Storage-Vertrag §4.2 anlegen, `MARES_BACKUP_ROOT` setzen. Das ist
sinnvoll erst, wenn `PRIMARY` in Betrieb ist, denn ein Backup entsteht als verifizierte Kopie **aus**
`PRIMARY`. Die Backup-Werkzeuge (Kopieren, Verifizieren, Restore-Test) gehören zum
Preservation-Run; es wird keine projektübergreifende Backup-Architektur gebaut.

## 3. `EXCHANGE` – Nextbox

Befund: Im synchronisierten Nextbox-Verzeichnis des Arbeitsplatzes gibt es **keinen Ordner
`MARES`**. Es existiert ein Ordner eines früheren Pilotprojekts mit ähnlichem Namen; sein Inhalt
wurde nicht geöffnet.

Nicht angelegt, weil jeder dort erzeugte Ordner sofort auf den Server synchronisiert wird und die
Freigaben ohnehin in der Weboberfläche gesetzt werden müssen.

Zu klären:

1. Verhältnis zum vorhandenen Pilotprojekt-Ordner: bleibt er daneben bestehen, und enthält er
   Material, das als weiterer Altbestand zu behandeln ist ([`legacy-import.md`](legacy-import.md))?
2. Abgabeverfahren: je Person/Gruppe ein eigener, einzeln freigegebener Ordner unter
   `submissions/<Abgabe-Pseudonym>/` (Vertrag §4.3). Zu entscheiden ist, ob Studierende einen
   Upload-Link („Dateiablage“, nur hochladen) oder eine persönliche Freigabe erhalten.
3. Vergabe der Abgabe-Pseudonyme und wo ihre Zuordnung zu Personen geführt wird
   (`restricted/identities`, also erst nach §1 Punkt 2).

Dann: Ordner `MARES` mit `seminars/WS2026-27/{materials,submissions,feedback}` und
`research_exchange/` anlegen, Freigaben setzen, `MARES_EXCHANGE_ROOT` setzen.

## 4. `LEGACY_IMPORT`

Wird erst für den Import-Run konfiguriert ([`legacy-import.md`](legacy-import.md)), nicht vorher.
