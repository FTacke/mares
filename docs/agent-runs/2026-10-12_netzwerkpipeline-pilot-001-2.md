# Run-Bericht 2026-10-12 – Netzwerkpipeline und Pilotfall 001-2

> **Berichtigt:** Die Beschreibung der Alter-Alter-Erhebung in diesem Bericht (Beziehungen „aus Gruppenumrandungen abgeleitet“, Erhebung „unvollständig“)
> wurde von der Projektleitung korrigiert; die Beziehungen wurden im Interview erfragt. Siehe
> [`2026-10-12_netzwerk-vacca-bereinigung.md`](2026-10-12_netzwerk-vacca-bereinigung.md). Der Bericht bleibt als historisches Journal unverändert.

Journal eines Laufs, keine Spezifikation. Maßgeblich sind [`network-module.md`](../architecture/network-module.md),
[`visualization-conventions.md`](../architecture/visualization-conventions.md) und
[`ADR-0002`](../decisions/ADR-0002_2026-10-12_netzwerkmodul.md). Ortsangaben beschreiben den Projektarbeitsplatz.
Dieser Bericht enthält keine Forschungsdaten; Kennzahlen sind Zählungen.

## 1. Ziel und Scope

Erste funktionsfähige Netzwerkpipeline (Import, Validierung, Netzwerkmodell, beschreibende Auswertung,
Visualisierung, Tests, Dokumentation) und die kontrollierte Verarbeitung des Datenpakets der studentischen
Folgeerhebung `001-2` (22 Kontakte). Ausdrücklich nicht: Audio, Whisper/MaRC3a, externe Dienste, weitere Migration
aus dem Altbestand, Einrichtung von `PRIMARY`/`BACKUP`/`EXCHANGE`, Kennzahlen auf unvollständiger Grundlage,
Veröffentlichung, Commit/Push.

## 2. Änderung des Auftrags während des Laufs

Während des Laufs legte die Projektleitung eine **neue Paketversion (1.1)** in den Repository-Root und wies an, die
bisherigen Daten zu ersetzen und zu löschen. Folgen:

- Paket 1.0 (erste Lieferung) wurde nach INTAKE übernommen und verifiziert, dann **auf ausdrückliche Anweisung**
  samt Lieferprotokoll aus INTAKE gelöscht; nur sein ZIP-Hash und ein Ersetzungsvermerk stehen im Protokoll von 1.1.
  (Das ZIP lag bereits nicht mehr im Repository.)
- Paket 1.1 ist die Arbeitsgrundlage. Es bestätigt die zuvor unklaren Gruppen `G05` und `G06` durch eine ausdrückliche
  Angabe der Projektseite; die Zahlen im Auftrag („vier bestätigte Gruppen, zwei unklare, 22 Kanten“) gelten daher für
  Version 1.0. **Für 1.1 gelten: sechs bestätigte Gruppen, 41 Beziehungen.** Die Regel „Kandidatengruppen erzeugen
  keine Kanten“ ist unverändert implementiert und mit synthetischen Fällen getestet; auf den echten Daten wird sie
  nicht mehr ausgelöst, weil keine Kandidatengruppe mehr vorhanden ist.

## 3. Datenübernahme (Ist)

| Schritt | Ergebnis |
|---|---|
| ZIP geprüft (Zip-Test, nur flache Einträge), SHA-256 gebildet | ja; ZIP `MARES_001-2_Datenpaket_2026-10-12_v1.1.zip`, SHA-256 `638c9cb6783b503a3e3f4a3d6152d697cfa9556b121e9c7910ea43517b284b96`, 8 398 Bytes |
| Kopie nach `INTAKE/inbox/MARES_001-2_Datenpaket_2026-10-12_v1.1/`, Gleichheit mit der Quelle durch Hash geprüft | ja |
| Entpackt nach `…/contents/`, `SHA256SUMS.txt` des Pakets gegen alle Dateien geprüft | ja, alle in der Liste aufgeführten Dateien stimmen |
| Lieferprotokoll mit Hashes, Größen, Zeitpunkt | `INTAKE/reports/delivery_MARES_001-2_Datenpaket_2026-10-12_v1.1.json` |
| Dateien schreibgeschützt (Dateiattribut) | ja; nur als Vorsichtsmaßnahme, keine Erhaltung |
| ZIP aus dem Repository-Root entfernt | ja, nach der Hash-Prüfung der Kopie |
| Forschungsdaten im Git-Bestand | keine; geprüft über `git ls-files -co --exclude-standard` und einen Test |

**Zustand:** Intake `RECEIVED` (nicht nach dem Intake-Vertrag geprüft: der Intake-Code existiert nicht), Erhaltung
`NOT_PRESERVED`, Backup `NO_COPY`. `PRIMARY`, `BACKUP`, `EXCHANGE` sind weiterhin nicht konfiguriert; es wurde kein
Erhaltungs- oder Backup-Erfolg behauptet. Die einzige Kopie des Pakets liegt in `INTAKE`.

## 4. Implementierte Änderungen

Code (`src/mares/networks/`): `codes` (Mehrfachcodes, Bereiche, Codebuch), `identity` (kanonische IDs), `package`
(Import), `model`, `geo`, `validate`, `build` (Cliquenregel, Zustände yes/no/unknown/nicht erhoben), `analysis`,
`canonical`, `report`, `run`, `cli`, `figures/` (`style`, `common`, `ego`, `groups`, `geography`, `language`,
`overview`). Aufruf: `python -m mares.networks validate|import|analyze|figures|run --package ROOT:rel`.

Verträge und Dokumente: ADR-0002; `data-contract.md` (Kontaktzahl ohne Obergrenze, Quellkennung ≠ Fall-ID);
neu `network-module.md`, `visualization-conventions.md`, `methodology/pilot-case-001-2.md`; geändert `overview.md`,
`modules.md`, `storage-contract.md` (Ist-Tabelle), `README.md`, `methodology/README.md`, `examples/synthetic/README.md`.
`ids.py`: `MAX_CONTACTS` entfällt, `A`+≥2 Ziffern, `contact_number`. `pyproject.toml`: NetworkX, Matplotlib,
Skript `mares-networks`. Synthetisches Beispielpaket `examples/synthetic/network-package-0000/`.

## 5. Entscheidungen

Siehe ADR-0002. Hervorzuheben: kein pandas (strikte Unterscheidung leer/null/nicht erhoben); Ausgabe nur nach
`WORKSPACE`, Eingabe nur aus `INTAKE`/`PRIMARY`; die Kantentabelle des Pakets ist Importbeleg, die Ableitung aus den
Gruppen die einzige Netzwerkwahrheit; „Marburg“ nur bei exakt benanntem Ort (ungefähre Angaben nicht präzisiert,
Parameter `--local-place`); der Validator setzt nie einen Qualitätsstatus; Mehrsprachigkeit wird nie zu einer
Hauptsprache verdichtet; Kontakte ohne Nähewert liegen in einem eigenen Band, nicht in einer Zone.

## 6. Tests und Ergebnisse

**Bestandene Tests** (kein Beleg für die Richtigkeit der Daten): `python -m pytest` – **191 bestanden**, 0
fehlgeschlagen (vorher 62; keine Regression; zwei bestehende ID-Tests wurden an die geänderte ID-Regel angepasst).
Neue Tests: Codes und Bereiche, Import (BOM/Zeilenenden, Blattnummerierung, 1–150 Kontakte), Validator (Fehler,
Warnungen, offene Fragen getrennt), Netzwerkbau (Clique, Überlappung, Kandidaten, unbekannt ≠ nein, Widerspruch),
Auswertung (keine Dichtemaße), Grafiken (Bau für beliebige Kontaktzahlen, Byte-Reproduzierbarkeit, keine Notizen oder
Freitexte, gezeichnete Kanten = belegte Kanten, Zonenlage, Unabhängigkeit vom Hash-Seed des Prozesses), Läufe (Ausgabe
nur im Run-Ordner, Quellroots, Run-Record), Privatsphäre (keine Forschungsdaten, nur synthetische Pakete mit Jahr 0000).

**Lauf auf dem echten Paket** (`INTAKE:inbox/…/contents`, letzter Lauf `RUN-20261012T122525Z-24c8c7` in
`WORKSPACE/runs/`): technische Prüfung `PASSED_WITH_WARNINGS`; 0 Fehler, 2 Warnungen, 13 offene Forschungsfragen
(15 Einträge inklusive der drei vom Modul erzeugten, davon zwei „im Paket entschieden“). Gelesen: 22 Kontakte mit
eindeutigen IDs `A01`–`A22`, Quellblatt und lokale Nummer erhalten; sechs bestätigte Gruppen; **41 Beziehungen, aus
den Gruppen abgeleitet und mit der Kantentabelle des Pakets identisch** (inklusive Gruppenherkunft; von 231
möglichen Paaren sind 41 belegt, 190 ohne Angabe); Nähewerte ausschließlich aus der Tabelle; Prüfsummen der Lieferung
stimmen. Die bekannten Lesartenprobleme erscheinen im Prüfbericht (mehrdeutige Herkunftsangabe, mögliche zusätzliche
Funktionscodes, abweichende Personenbeschriftung, Sprachmodus-Ergänzungen, nicht übertragener Freitext).
Zwei Läufe in getrennten Prozessen ergaben byteidentische Tabellen, kanonische Daten und Grafiken (43 Dateien; nur der
Verarbeitungsbericht unterscheidet sich durch Run-ID und Zeit).

**Sichtprüfung:** alle sechs Abbildungen wurden als PNG angesehen. Behoben wurden: Beschriftungskollisionen der
Sprachkürzel (A/D2), überlappende Gruppenlabels bei den verschachtelten Gruppen (B), überlappende Spaltenköpfe und
runde statt elliptische Punkte (D1), Titelüberlappung und Leerraum (B, C, E). Gefunden und behoben wurde außerdem eine
Nicht-Reproduzierbarkeit des Gruppenlayouts zwischen Prozessen (Hash-Reihenfolge von Mengen), die der Test innerhalb
eines Prozesses nicht sah; dafür gibt es jetzt einen Prozess-übergreifenden Test.

**Wissenschaftlich validiert: nichts.** Die Daten sind ein manuell extrahierter Entwurf; die Datenqualität ist
`UNREVIEWED`. Die Bestätigung der Gruppen `G05`/`G06` beruht auf einer Angabe der Projektseite, nicht auf einer
Prüfung der Originalbögen.

## 7. Erreichter Status

Implementiert und getestet: Pipeline, Prüfung, Netzwerkmodell, Auswertung, sechs Grafiken, Kommandozeile,
Dokumentation. Verarbeitet: ein Datenpaket (Pilotfall `001-2`, Version 1.1) im lokalen Arbeitsbereich.
Nicht erreicht (und nicht Teil des Auftrags): Erhaltung, Backup, Register, fachliche Validierung.

## 8. Fehler in diesem Lauf

Beim Aufräumen eigener Probeläufe löschte ich mit dem Muster `runs/RUN-*` im Arbeitsbereich auch Teile des Ordners
`RUN-20261012T115507Z-7c373f`, den ich **nicht** angelegt hatte: ein Lauf des Audio-Pilots
(`pilots/audio_enhancement`), der zu diesem Zeitpunkt noch aktiv war (Docker hielt die drei Logdateien offen, nur diese
blieben). Welche Zwischen- und Ergebnisdateien dort lagen, ist nicht mehr feststellbar; sie sind nicht
wiederherstellbar. Der Ordner gehört zu `WORKSPACE` (regenerierbare Laufzeitdaten), der Pilotlauf muss voraussichtlich neu
gestartet werden. Ich habe nichts weiter an diesem Ordner verändert. Konsequenz für künftige Aufräumarbeiten: nur
Pfade löschen, die der Lauf selbst mit exaktem Namen angelegt hat – nie per Muster, nie ohne vorheriges Ansehen.

## 9. Offene Punkte und nächste Schritte

1. Pilotlauf des Audio-Pilots neu starten bzw. prüfen, was fehlt (siehe §8).
2. Fall registrieren (kanonische Fall-ID, Provenienz: Kohorte, Erhebende, Instrument-Version) und die Folgeerhebung mit
   der früheren Erhebung verknüpfen.
3. Daten gegen die Originalbögen prüfen; die offenen Reviewfragen entscheiden (Qualitätsstatus ist eine Entscheidung
   einer Person).
4. `PRIMARY` und `BACKUP` einrichten ([`../plans/external-storage-setup.md`](../plans/external-storage-setup.md)), dann
   Intake und Erhaltung implementieren; erst danach ist die Lieferung erhalten.
5. Entscheiden, ob eine explizite Alter-Alter-Erhebung nachgeholt wird (Voraussetzung für strukturelle Kennzahlen);
   Format dafür festlegen.
6. Import der Excel-Erhebungssheets nach Festlegung der Instrument-Version; Ablage der Ergebnisse als
   Datensatzversion in `PRIMARY/derived/networks`.
7. Hinweis: Im Repository-Root liegt eine große Audiodatei (`.m4a`); sie ist durch `.gitignore` geschützt, gehört aber
   als Forschungsmaterial nicht in den Checkout. Ich habe sie nicht angefasst.

## 10. Git

Kein Commit, kein Push, kein Remote. Alle neuen und geänderten Dateien sind uncommittet im Arbeitsverzeichnis.
