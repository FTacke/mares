# Storage-Vertrag

**Status: verbindlich.** Dieser Vertrag legt fest, welche Speicherbereiche MARES hat, wie sie
benannt und aufgelöst werden und was in ihnen liegen darf. Den tatsächlichen Stand der Einrichtung
nennt §2; alles andere ist Sollzustand.

Code: [`src/mares/core/roots.py`](../../src/mares/core/roots.py),
[`src/mares/core/refs.py`](../../src/mares/core/refs.py) ·
Deklaration: [`config/storage_roots.toml`](../../config/storage_roots.toml)

## 1. Rollen

```text
Quellcode  !=  Arbeitsdaten  !=  erhaltene Forschungsdaten  !=  Backup  !=  Austausch
```

Ein Root ist eine **Funktion**, kein Laufwerk und kein Ordnername. Jeder Root hat genau eine Rolle.

| Root | Variable | Pflicht | Funktion | Niemals |
|---|---|---|---|---|
| *(Repository)* | — (aus dem Code abgeleitet) | — | Code, Konfiguration, Dokumentation, Vorlagen, synthetische Beispiele | Ablage für Forschungs- oder Laufzeitdaten |
| `WORKSPACE` | `MARES_WORKSPACE_ROOT` | ja | regenerierbare Laufzeitdaten: `runs/`, `cache/`, `tmp/` | Archiv, Backup, einzige Kopie von irgendetwas |
| `INTAKE` | `MARES_INTAKE_ROOT` | ja | lokaler Eingang vor `PRIMARY`: `inbox/`, `staging/`, `quarantine/`, `reports/` | Archiv; Ort, an dem Daten „fertig“ sind |
| `PRIMARY` | `MARES_PRIMARY_ROOT` | ja | **autoritativer** Forschungsdatenbestand (§4.1) | Arbeitsverzeichnis für Zwischenstände |
| `BACKUP` | `MARES_BACKUP_ROOT` | nein | unabhängige, separat verifizierte Zweitkopie von `PRIMARY` (§4.2) | Primärquelle, Arbeitsquelle, Fallback |
| `EXCHANGE` | `MARES_EXCHANGE_ROOT` | nein | kontrollierter Dateiaustausch über Nextbox (§4.3) | Primärarchiv, Backup |
| `LEGACY_IMPORT` | `MARES_LEGACY_IMPORT_ROOT` | nein | provisorischer Altbestand, **nur lesend**, nur für den Import-Run | Ziel irgendeines Schreibzugriffs |

„Pflicht“ heißt: Code, der den Root braucht, bricht mit einem Fehler ab, der die Variable nennt.
`PRIMARY` ist Pflicht für jede Arbeit mit echten Daten; Tests und reine Entwicklungsarbeit brauchen
ihn nicht, weil sie ihn nie anfordern.

## 2. Topologie: Soll und Ist (Stand 2026-10-12)

Die Pfade in dieser Tabelle beschreiben **eine Maschine** (den Projektarbeitsplatz). Sie stehen in
keiner versionierten Konfiguration und in keinem Code. Die Tabelle wird fortgeschrieben, wenn ein
Root in Betrieb genommen wird; ein geplanter Ort wird nie so beschrieben, als existiere er.

| Root | Ort | Ist | Konfiguriert |
|---|---|---|---|
| Repository | `C:\dev\mares\mares` | vorhanden | — |
| `WORKSPACE` | `C:\dev\mares\mares_workspace` | **vorhanden**; enthält Läufe unter `runs/` (Netzwerkläufe, ein Pilotlauf) | ja (`.env`) |
| `INTAKE` | `C:\dev\mares\mares_storage` | **vorhanden**; Altbestandsinventar und Lieferprotokoll in `reports/`, eine Datenlieferung (Pilotfall `001-2`) in `inbox/` – nicht nach dem Intake-Vertrag geprüft, nicht erhalten | ja (`.env`) |
| `PRIMARY` | geplant: eigener MARES-Projektordner auf dem Gruppenlaufwerk der Universität (auf dem Arbeitsplatz als `K:` eingebunden), später New_FS | **nicht angelegt** | nein |
| `BACKUP` | geplant: MARES-Bereich im bestehenden Forschungsbackup auf der externen SSD (`D:\projects\…`) | **nicht angelegt** | nein |
| `EXCHANGE` | geplant: Ordner `MARES` im synchronisierten Nextbox-Verzeichnis | **nicht angelegt** | nein |
| `LEGACY_IMPORT` | `C:\dev\mares_provisorisch` | vorhanden, unverändert | nein (bewusst, bis zum Import-Run) |

Was vor der Inbetriebnahme der drei externen Roots zu klären ist:
[`docs/plans/external-storage-setup.md`](../plans/external-storage-setup.md).

## 3. Auflösung

1. **Eine Stelle löst auf.** `mares.core.roots.Roots` ist der einzige Leser der
   `MARES_*_ROOT`-Variablen und die einzige Stelle, die aus einem Rootnamen einen physischen Pfad
   macht. Kein anderes Modul baut absolute Pfade, liest `.env` oder sucht Nachbarordner über `..`.
2. **Versioniert sind Namen, die Maschine kennt die Orte.** `config/storage_roots.toml` nennt Root
   und Variable. Der Wert steht in der gitignorierten `.env` des Checkouts oder in der
   Prozessumgebung (die Prozessumgebung gewinnt). `.env.example` listet alle Variablen ohne Werte.
3. **Kein Fallback.** Es gibt keinen Standardort, keine Host-Erkennung, kein Ausweichen in den
   Checkout, auf einen anderen Root oder ein anderes Laufwerk. Ein gesetzter, aber unbrauchbarer
   Wert ist eine Ablehnung, nie ein Anlass für Ersatz.
4. **Zustände.** Die Auflösung ergibt genau einen Zustand; nur `AVAILABLE` erlaubt Weiterarbeit.

   | Zustand | Bedeutung |
   |---|---|
   | `NOT_DECLARED` | diesen Root gibt es in der Deklaration nicht |
   | `NOT_CONFIGURED` | deklariert, Variable leer. Für optionale Roots ein legitimer, expliziter Zustand |
   | `UNUSABLE` | Wert gesetzt, aber nicht zulässig: relativ, ein Dateisystem-Root, im Checkout, oder überlappt einen anderen Root |
   | `UNREACHABLE` | Wert gesetzt, Verzeichnis jetzt nicht erreichbar |
   | `READ_ONLY` | erreichbar, aber Schreiben nötig und nicht möglich (oder Root als nur lesend deklariert) |
   | `AVAILABLE` | benutzbar |

5. **Unerreichbar ist nicht leer.** Aus einem nicht erreichbaren Root wird nie geschlossen, dass
   etwas fehlt, leer oder erledigt ist.
6. **Auflösung legt nichts an.** Ein fehlendes Verzeichnis heißt „nicht verfügbar“ (ein nicht
   verbundenes Netzlaufwerk sieht genau so aus). Einen Root anzulegen ist ein bewusster Schritt
   einer Person.
7. **Roots überlappen nicht.** Kein Root ist gleich einem anderen oder liegt in einem anderen; kein
   Root liegt im Checkout. Der Vergleich ist lexikalisch und ignoriert Groß-/Kleinschreibung.
8. **Laufspezifische Pfade** (Ausgabeordner eines Laufs) sind Eingaben eines Aufrufs, relativ zu
   einem Root, nie globale Konfiguration.

### Persistierte Referenzen

Wo ein Ort gespeichert wird (Manifest, Register, Bericht, den Code liest), steht **Rootname +
relativer POSIX-Pfad**, nie eine Adresse:

```json
{"root": "PRIMARY", "rel": "preservation/manifests/AST-9f3c2a7b41d0.json"}
```

Kein Laufwerk, kein `\`, kein `..`, kein führender `/` (`mares.core.refs.StorageRef` erzwingt das).
Ein Pfad – absolut oder relativ – ist nie Teil einer ID, eines Inhalts-Hashes oder eines
Cache-Schlüssels.

## 4. Layouts

### 4.1 `PRIMARY`

```text
<PRIMARY>/
├── preservation/
│   ├── raw/            unveränderte Originaldateien, schreibgeschützt behandelt
│   └── manifests/      je Asset: SHA-256, Größe, Originalname, Einreichungen, Zeitpunkt
├── derived/
│   ├── networks/       kanonische Netzwerkdaten, Kennzahlen
│   ├── visualizations/
│   ├── transcripts/
│   └── analyses/
├── registry/           Metadatenregister: Fälle, Assets, Läufe, Versionen, Statusereignisse
├── restricted/
│   ├── consent/        Einwilligungen
│   └── identities/     Schlüssel Pseudonym ↔ Person (Teilnehmende, Erhebende)
└── releases/           eingefrorene Datensatzversionen
```

- Unter `preservation/raw/` hängt der Ablagepfad einer Datei **nicht** von Fall, Herkunft oder
  Originalname ab, sondern nur von ihrem Inhalt beziehungsweise ihrer Asset-ID. Fallzuordnung und
  Originalname stehen im Manifest und im Register; sie können korrigiert werden, ohne dass eine
  erhaltene Datei bewegt wird. Vorgesehen ist inhaltsadressierte Ablage
  (`raw/sha256/<2 Zeichen>/<hash>`); die endgültige Form legt der Preservation-Run fest.
- Alles unter `derived/` ist einer Datensatzversion und einem Verarbeitungslauf zugeordnet
  ([`data-contract.md`](data-contract.md)) und aus `preservation/` reproduzierbar.
- `restricted/` enthält die einzigen Daten, die Pseudonyme auflösen. Es wird nie nach `derived/`,
  `releases/`, `EXCHANGE`, `WORKSPACE` oder in einen Bericht kopiert und braucht auf dem
  Fileservice eigene, engere Zugriffsrechte als der Rest.

### 4.2 `BACKUP`

```text
<BACKUP>/
├── preservation/
├── derived/
├── registry/
├── restricted/
└── backup_manifests/   Kopierbelege, Verifikations- und Restore-Protokolle
```

- Ein Backup ist eine Kopie, die **existiert und verifiziert wurde**: aus `PRIMARY` erzeugt und
  gegen dessen Inventar geprüft (Pfad, Größe, SHA-256 jeder Datei, vom Backup zurückgelesen). Ein
  konfigurierter Root, ein geplanter Job oder eine Liste dessen, was kopiert werden soll, ist kein
  Backup.
- `BACKUP` liegt auf einem anderen Volume als `PRIMARY`. Mehr Unabhängigkeit (anderer Ort, offline)
  wird nicht behauptet, solange sie nicht belegt ist.
- Restore ist prüfbar: Stichproben werden vom Backup an einen dritten Ort gelesen und neu gehasht.
  Der Bericht eines Sync-Clients ist kein Restore-Nachweis.
- Backup-Läufe kopieren und ergänzen; sie löschen nichts.
- `releases/` ist im Backup nicht vorgesehen, weil eine Freigabe aus `derived/` und `registry/`
  rekonstruierbar sein muss. Sollen eingefrorene Releases selbst gesichert werden, wird dieser
  Vertrag ergänzt.
- `restricted/` im Backup setzt voraus, dass der Datenträger verschlüsselt ist (offen, siehe
  Einrichtungsplan).

### 4.3 `EXCHANGE`

```text
<EXCHANGE>/                      = Ordner „MARES“ in Nextbox
├── seminars/
│   └── <Kohorte>/               z. B. WS2026-27, SS2027
│       ├── materials/           Vorlagen und Anleitungen; alle Teilnehmenden lesen
│       ├── submissions/
│       │   └── <Abgabe-Pseudonym>/   je erhebender Person bzw. Gruppe ein Ordner
│       └── feedback/
│           └── <Abgabe-Pseudonym>/
└── research_exchange/
```

- Ein neues Semester ist ein neuer Ordner `<Kohorte>`, kein neuer Code: die Kohorte ist ein Datum
  der Provenienz ([`data-contract.md`](data-contract.md) §3), keine Pipeline-Variante.
- **Abgaben sind getrennt berechtigt.** Jeder Ordner unter `submissions/` und `feedback/` wird in
  Nextbox einzeln freigegeben, nur für die jeweilige Person oder Gruppe; `submissions/` selbst wird
  nie als Ganzes geteilt. Die Zuordnung einer Abgabe ergibt sich aus dem Ordner, nicht aus
  Dateinamen.
- Nextbox ist Durchgangsstation. Abgaben werden von dort in `INTAKE/inbox` **kopiert**; erhalten
  ist eine Datei erst, wenn sie in `PRIMARY` verifiziert ist. Aus `EXCHANGE` wird nie analysiert,
  und kein Code liest es als Ersatz für `PRIMARY`.
- In `materials/` und `feedback/` gelangen nur Inhalte, die für die Empfänger bestimmt sind – nie
  `restricted/`, nie Daten anderer Abgaben.

### 4.4 `INTAKE` und `WORKSPACE`

```text
<INTAKE>/                        <WORKSPACE>/
├── inbox/        Eingang        ├── runs/     Arbeitsverzeichnisse einzelner Läufe
├── staging/      geprüft,       ├── cache/    wiederherstellbare Zwischenstände
│                 wartet auf     └── tmp/
│                 Preservation
├── quarantine/   beschädigt
│                 oder unklar
└── reports/      Intake- und Inventarberichte (können personenbezogene Dateinamen enthalten)
```

Beide liegen außerhalb jedes Git-Checkouts. `INTAKE` kann die einzige Kopie einer noch nicht
erhaltenen Datei enthalten und wird deshalb nie automatisch bereinigt.

## 5. Wechsel des Primärspeichers (K: → New_FS)

Der Umzug ist ein Wechsel des Werts von `MARES_PRIMARY_ROOT` nach einer verifizierten Kopie. Keine
Fall-ID, keine Asset-ID, kein Hash und keine gespeicherte Referenz ändert sich.

1. Inventar der Quelle (relativer Pfad, Größe, SHA-256) und Prüfung gegen die Manifeste.
2. Kein Schreiber arbeitet mehr auf der Quelle.
3. Kopie an den neuen Ort; Inventar des Ziels, vom Ziel zurückgelesen, ist gleich dem der Quelle.
4. `MARES_PRIMARY_ROOT` zeigt auf den neuen Ort; Stichproben werden über den normalen Lesepfad
   gelesen.
5. `BACKUP` wird **aus dem neuen Primärspeicher** neu erzeugt und verifiziert.
6. Der alte Ort bleibt unverändert, bis seine Freigabe ausdrücklich entschieden ist.

Keine Junctions, Symlinks oder Kompatibilitätspfade am alten Ort. Ein früherer Primärspeicher wird
nicht durch Umbenennen zum Backup.

## 6. Verhältnis zu den Korpusprojekten

MARES übernimmt die Prinzipien des gemeinsamen Storage-Vertrags `crosscorpus-storage/v1` von
CO.RA.PAN und CO.PRE.PAN (Rollen statt Orte, Fail-closed-Auflösung, „unerreichbar ist nicht leer“,
Backup nur als verifizierte Kopie auf anderem Volume, Identität unabhängig vom Root, Migration als
verifizierte Kopie). MARES ist **nicht** Vertragspartei: es pinnt das Vertragsbündel nicht,
implementiert dessen Konformitätsfälle nicht und kennt weder Holdings noch Spool, Distribution oder
Zielidentitätsmarker. Entsprechungen: `PRIMARY` ≙ `PRESERVATION`, `WORKSPACE` ≙ `RUNTIME`,
`BACKUP` ≙ `BACKUP`, `EXCHANGE` ≙ `EXCHANGE`; `INTAKE` ist ein lokaler Eingangsbereich ohne
Entsprechung dort.

Kein Root von MARES liegt in einem Root eines anderen Projekts oder umgekehrt.
