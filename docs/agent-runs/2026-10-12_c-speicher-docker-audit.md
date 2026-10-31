# Run-Bericht: Speicherverbrauch des Audio-Piloten auf C:, Docker-Audit und Speicherbegrenzung

**Datum:** 2026-10-12 · **Status:** PARTIAL – Ursache gefunden, MARES-Bestand bereinigt, Wachstum
begrenzt; Windows hat noch keinen Speicher zurückerhalten, weil die Kompaktierung des
Docker-Abbilds alle Container anderer Projekte anhalten würde und gesondert freizugeben ist.

Der Bericht trennt **implementierte Änderungen**, **bestandene Tests** und **gemessene Werte**.
Wissenschaftlich validiert wird hier nichts; es geht um Speicherplatz.

## 1. Ziel und Scope

Am 12.10.2026 fiel der freie Speicher auf C: binnen 22 Minuten von 118,7 auf 50,4 GiB, während der
Audio-Enhancement-Pilot ([Bericht](2026-10-12_audio-enhancement-pilot.md)) eingerichtet wurde.
Zu klären war, was davon MARES verursacht hat, was sicher gelöscht werden kann und wie sich das
nicht wiederholt. Andere Projekte auf dem Rechner wurden nur über Metadaten (Größen, Zeiten,
Docker-Labels) abgegrenzt; nichts von ihnen wurde geöffnet, geändert oder angehalten.

## 2. Zustand beim Start (15:38)

- Kein MARES-Prozess und kein MARES-Container aktiv. Der Pilot ist abgeschlossen (alle Schritte
  des Laufs `RUN-20261012T115507Z-7c373f` liegen vor, 442 MiB in `WORKSPACE/runs`); es gab nichts
  zu pausieren und keinen unbegrenzten Schreibprozess.
- Fünf laufende Container, alle fremd (Compose-Projekte `corapan`, `app`, `promat_webapp`).
- Docker Desktop 29.2.1 auf WSL 2.6.3, eine Distribution `docker-desktop`; Abbild
  `docker_data.vhdx` unter `%LOCALAPPDATA%\Docker\wsl\disk`, nicht sparse, keine `.wslconfig`.
- C: 74,7 GiB frei – also bereits 24 GiB mehr als am Tiefpunkt, ohne dass etwas gelöscht wurde.

## 3. Root Causes

### 3.1 Wachstum des Docker-Abbilds (bestätigt)

Das Abbild wuchs von 15,3 auf 53,07 GiB (+37,8 GiB). Das Dateisystem darin war zu 51,7 GiB belegt;
es gab also keinen Leerraum, das Wachstum war echte Belegung. Sie stammt vollständig von MARES:

| MARES-Bestand in Docker | Größe | Entstanden bei |
|---|---:|---|
| Volume `mares-aep`, Paketcache `uv-cache` | 14,4 GiB | `aep.py setup` |
| Volume, CrispVoice (drei eigene Umgebungen) | 12,6 GiB | `aep.py setup` |
| Volume, fünf Modellumgebungen | 4,7 GiB | `aep.py setup` |
| Volume, Modellgewichte | 4,5 GiB | `aep.py setup` |
| Image `mares-aep:1` und dessen Build-Cache | 1,3 GiB (Schichten geteilt) | `aep.py build` |
| **Summe** | **≈ 37,5 GiB** | |

Das Volume wurde um 13:54 Uhr angelegt, die letzte Umgebung um 14:07 Uhr; das deckt sich mit dem
22-Minuten-Fenster. Verantwortlich war damit **die Einrichtung (`setup`)**, nicht die
Audioverarbeitung: `crispvoice`, `transcribe` und `resemble` schreiben nur in den Laufordner
(442 MiB) und in flüchtige Container-Schichten, die mit `--rm` verschwinden.

Vier Ursachen im Einzelnen:

1. **Paketcache ohne Aufbewahrungsgrenze im Volume.** `UV_CACHE_DIR` lag im Volume, und wegen
   `UV_LINK_MODE=copy` sind die Umgebungen vollständige Kopien. Jedes Paket lag doppelt vor, der
   Cache wurde nach dem Setup nie gelöscht.
2. **GPU-Bibliotheken auf einem Rechner ohne GPU.** Das `setup.sh` von CrispVoice legt CPU-Wheels
   nur für seine Hauptumgebung fest. Die beiden anderen zogen CUDA-Builds von torch mit zusammen
   6,1 GiB NVIDIA-Bibliotheken (und deren Kopie im Cache).
3. **Mehrfach vorhandene Frameworks.** Acht Umgebungen mit je eigenem torch; das ist für die
   Isolation der Modelle gewollt, kostet aber rund 10 GiB.
4. **Das Abbild schrumpft nicht.** Was Docker einmal geschrieben hat, belegt C: weiter, auch wenn
   es im Container gelöscht wird.

### 3.2 Die weiteren rund 30 GiB (nicht bewiesen)

Rechnung: 68,3 GiB Verlust, davon 37,8 GiB Abbild, bleiben 30,5 GiB.

- **Mindestens 24 GiB davon waren vorübergehend** und sind ohne jede Bereinigung zurückgekommen
  (Tiefpunkt 50,4 GiB, um 15:38 Uhr 74,7 GiB).
- **Wahrscheinlichste Erklärung: Schattenkopiespeicher.** Das Systemprotokoll enthält genau im
  Zeitfenster, um 14:01:58 Uhr, das Volsnap-Ereignis 25: Die Schattenkopien von C: wurden
  verworfen, weil ihr Speicher unter der Schreiblast nicht rechtzeitig vergrößert werden konnte.
  Schattenkopien wachsen, wenn belegte Blöcke massenhaft überschrieben werden, und geben ihren
  Platz frei, sobald sie verworfen werden. **Evidenzgrenze:** Die Größe des Schattenkopiespeichers
  lässt sich nur mit Administratorrechten lesen (`vssadmin` wurde verweigert und nicht umgangen),
  und ein Verlauf des freien Speichers liegt mir nicht vor. Der Zusammenhang ist plausibel, aber
  nicht gemessen.
- **Zweiter Kandidat:** die von Windows verwaltete Auslagerungsdatei (jetzt 12,0 GiB, zuletzt um
  15:06 Uhr geändert). Die Schritte `resemble`, `crispvoice` und `transcribe` liefen parallel mit
  zusammen über 20 GB RAM in der WSL-VM. Eine zeitweilige Vergrößerung ist nicht protokolliert.
- **Ausgeschlossen als große Verbraucher:** MARES außerhalb von Docker (Workspace gesamt
  0,66 GiB, davon Laufordner 0,44 GiB), WSL-Swap (40 MiB), Temp-Verzeichnis dieses Projekts.
- **Dauerhafter Rest von etwa 6,5 GiB:** nicht MARES. Heute geänderte Großdateien außerhalb von
  Docker gehören zu anderen Anwendungen und Projekten (unter anderem 3,9 GiB Aufnahmen einer
  laufenden Kampagne, eine 4,0-GiB-Datei und 4,6 GiB Protokolle von Microsoft-Anwendungen). Eine
  genaue Zuordnung zum Zeitfenster ist aus Metadaten nicht möglich.

### 3.3 Warum die Schutzmaßnahmen nicht griffen

- `aep.py` prüfte den freien Speicher weder vor noch während eines Befehls.
- Der Storage-Vertrag regelt die Roots; das Docker-Volume liegt außerhalb davon und wurde von
  keiner Regel und keiner Messung erfasst.
- Die 50-GiB-Grenze des Nachbarprojekts ist dessen Regel; MARES hatte keine eigene.

## 4. Bereinigung

Dry-Run (`aep.py clean`), danach Ausführung (`aep.py clean --apply`). Einziger Kandidat, der alle
sechs Prüfpunkte erfüllt:

| Kandidat | Größe | Prüfung |
|---|---:|---|
| `uv-cache` im Volume `mares-aep` | 14 759 MiB | nur MARES; kein Container am Volume; 0 Symlinks und 0 Hardlinks aus Umgebungen in den Cache; kein Verweis in `pyvenv.cfg` oder `.pth`; aus dem Netz wiederherstellbar |

Nach dem Löschen starten alle acht Python-Umgebungen und importieren NumPy beziehungsweise torch.
Ein zweiter Aufruf löscht nichts mehr (idempotent).

**Bewusst nicht gelöscht:**

- Umgebungen, Gewichte, Modellcode: werden für die offene Hörbewertung und weitere Läufe gebraucht.
- Laufordner des Piloten: enthält nicht bitgleich wiederherstellbare Fassungen.
- Zwei weitere Laufordner von 15:22 Uhr und `cache/audio-enhancement-pilot` (0,2 GiB) im
  Workspace: stammen nicht aus dieser Sitzung, Zweck nicht geprüft.
- Build-Cache: die MARES-Einträge teilen ihre Schichten mit dem Image, der Gewinn wäre gering;
  ein gezieltes Löschen einzelner Einträge wäre nur über ein Builder-Prune möglich.
- Alles Fremde, darunter das Image `mmcauliffe/montreal-forced-aligner` (7,7 GB, 8 Monate alt,
  kein Container): Herkunft unbekannt, nicht MARES.

## 5. Speicherbilanz

Gemessen um 15:38 Uhr (vorher) und nach der Bereinigung (nachher). GiB, wo nicht anders vermerkt.

| Bereich | Vorher | Nachher | Freigegeben |
|---|---:|---:|---:|
| C: freier Speicher | 74,39 | 74,38 | **0** (Windows) |
| Docker-VHDX (Dateigröße) | 53,07 | 53,07 | 0 |
| Belegung im Abbild | 51,7 | 37,3 | 14,4 (nur Docker-intern) |
| MARES-Container | 0 | 0 | – (keine vorhanden) |
| Images und Build-Caches (MARES) | 1,3 | 1,3 | 0 |
| Docker-Volume `mares-aep` | 36,2 | 21,8 | 14,4 |
| MARES-Runtime (`WORKSPACE`) | 0,66 | 0,66 | 0 |
| Sonstige MARES-Caches | 0 | 0 | – |

**Docker-intern freigegeben: 14,4 GiB. Von Windows zurückgewonnen: 0 GiB.** Der freie Platz im
Abbild wird von Docker wiederverwendet; das Abbild wächst also erst wieder, wenn mehr als 14,4 GiB
neu geschrieben werden. Die 24 GiB, die C: seit dem Tiefpunkt zurückerhalten hat, stammen nicht
aus dieser Bereinigung (Abschnitt 3.2).

## 6. Kompaktierung des Abbilds: gesondert freizugeben

Nicht durchgeführt. Jedes unterstützte Verfahren verlangt, Docker Desktop und WSL zu beenden; das
hält die fünf Container der anderen Projekte an, und das Kompaktieren selbst braucht
Administratorrechte. Beides war nicht freigegeben.

Operator-Schritte, wenn ein Wartungsfenster mit den anderen Projekten abgestimmt ist:

1. Prüfen, dass kein Projekt gerade auf seine Container angewiesen ist (`docker ps`).
2. Docker Desktop beenden, dann `wsl --shutdown`.
3. In einer Administrator-PowerShell entweder `Optimize-VHD -Path <docker_data.vhdx> -Mode Full`
   (Hyper-V-Modul) oder mit `diskpart`: `select vdisk file="<docker_data.vhdx>"`,
   `attach vdisk readonly`, `compact vdisk`, `detach vdisk`.
4. Docker Desktop starten; die Container der anderen Projekte gegebenenfalls wieder hochfahren
   (Docker Desktop startet hier nicht automatisch mit).

Erwarteter Gewinn: bis zu 14,4 GiB (Abbild von 53,1 auf etwa 38,7 GiB). Nicht gemessen.

## 7. Implementierte Änderungen

Alle unter `pilots/audio_enhancement/`, dazu ein Test:

- **`capacity.py` (neu):** Untergrenze 60 GiB, die nach einem Befehl frei bleiben muss; Stopplinie
  55 GiB für laufende Befehle; Obergrenzen des Bedarfs je Befehl und Umgebung; Wächter-Thread.
  Die Grenzen liegen über den 50 GiB des Nachbarprojekts, damit MARES aus eigener Kraft stoppt und
  nicht darauf angewiesen ist, dass andere Platz schaffen.
- **`aep.py`:** `build`, `setup` und `step` prüfen vorher den freien Platz auf den Laufwerken von
  `WORKSPACE` und Docker-Abbild und verweigern mit Exit-Code 75. Während `setup` und `step` wird
  alle 10 Sekunden gemessen; unter der Stopplinie wird genau der eigene, benannte Container
  gestoppt. Neu: `storage` (Belegung), `clean` (Dry-Run, `--apply`, feste Liste löschbarer Pfade,
  verweigert bei benutztem Volume). Container und Image tragen das Label `mares.project=aep`.
- **`container/setup_envs.sh`:** Der Paketcache wird nach jeder Umgebung und bei jedem Ende des
  Skripts gelöscht, auch nach Abbruch. Fertige Umgebungen tragen einen Marker und werden
  übersprungen. CrispVoice wird mit `UV_TORCH_BACKEND=cpu` eingerichtet; Reste eines
  abgebrochenen CrispVoice-Setups werden vorher entfernt.
- **`README.md`:** Abschnitt „Speicherplatz“ mit Aufbewahrung je Bestandsklasse.

Die sechs vorhandenen Umgebungen wurden als fertig markiert, damit ein späteres `setup` sie nicht
neu lädt.

**Anderer Storage-Root:** nicht empfohlen. D: ist ausgeschlossen, ein weiterer Root wäre eine neue
Abhängigkeit. Nach der Korrektur braucht eine vollständige Einrichtung rund 22 GiB dauerhaft (mit
CPU-Wheels für CrispVoice rund 16 GiB) statt 37 GiB.

## 8. Tests und Nachweise

| Nachweis | Art | Ergebnis |
|---|---|---|
| `pytest` gesamt | automatisch | 244 bestanden, davon 10 neu (`tests/test_aep_capacity.py`) |
| Verweigerung bei knappem Platz | real | `setup` bei 74,4 GiB frei: verweigert (Bedarf 30, Grenze 60), Exit 75, kein Container gestartet |
| Wächter stoppt einmal, auch bei nicht messbarem Laufwerk, und endet mit dem Befehl | automatisch | bestanden |
| `clean` erreicht weder Gewichte noch Laufordner noch Pfade außerhalb des Volumes | automatisch | bestanden |
| Tatsächliche Freigabe und Idempotenz | real | 14 759 MiB frei, zweiter Lauf 0 MiB |
| Umgebungen nach der Bereinigung benutzbar | real | alle acht starten |
| CPU-Wheels für CrispVoice | Trockenlauf der Paketauflösung | torch `+cpu`, keine NVIDIA-Pakete |
| Fremde Container | real | alle fünf unverändert „Up 4 days“ |

**Nicht geprüft:** Der Stopp eines echten Containers durch den Wächter und ein vollständiges
`setup` mit dem geänderten Skript wurden nicht ausgeführt; beides hätte neue Downloads oder
Audioverarbeitung verlangt. Ob CrispVoice mit CPU-Wheels dieselben Ergebnisse liefert, ist
ebenfalls offen: geprüft ist nur, dass sich die Pakete auflösen lassen.

## 9. Auswirkungen auf andere Projekte

Soweit geprüft: keine. Kein fremder Container, kein fremdes Image oder Volume und keine fremde
Datei wurde geändert; es gab kein Prune, kein Beenden von Docker oder WSL und keine
Administratoraktion. Gestartet wurden nur kurzlebige eigene Container, meist ohne Netz, zum
Messen, Löschen und für den Trockenlauf der Paketauflösung. Ein versehentlich mit erweiterten
Rechten gestarteter Messcontainer führte nur `true` aus und endete sofort.

## 10. Status und offene Punkte

- **Audio-Pilot:** abgeschlossen und unverändert, Hörbewertung weiter offen.
- **Commit und Push:** nicht erfolgt (nur auf Anforderung). `pilots/` ist bisher insgesamt nicht
  versioniert.

Offen, jeweils eine Entscheidung des Operators:

1. Wartungsfenster für die Kompaktierung (Abschnitt 6); erst dann erhält Windows 14,4 GiB zurück.
2. CrispVoice mit CPU-Wheels neu einrichten (`clean env:crispvoice --apply`, dann
   `setup crispvoice`): spart rund 6 GiB im Abbild, braucht Netz und vorübergehend bis zu 14 GiB.
   Bei 74,4 GiB frei liegt das knapp über der Grenze.
3. Das Docker-Volume in den Storage-Vertrag aufnehmen; bisher kennt
   [`storage-contract.md`](../architecture/storage-contract.md) nur die Roots.
4. Ursache der vorübergehenden 24 GiB mit Administratorrechten belegen
   (`vssadmin list shadowstorage`), falls sie sich wiederholt.
5. Bei 74 GiB frei bleibt für MARES ein Spielraum von 14 GiB bis zur eigenen Grenze. Eine
   vollständige Neueinrichtung des Piloten ist damit derzeit gesperrt, einzelne Schritte sind es
   nicht.
