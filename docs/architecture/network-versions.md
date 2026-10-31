# Netzwerkdaten: `network_v0` und `network_v1`

**Status: verbindlich (2026-10-31).** Begründung: [`ADR-0005`](../decisions/ADR-0005_2026-10-31_netzwerk-v0-v1.md).

MARES kennt zwei Netzwerkpipelines. Sie gehören zu zwei Erhebungsdesigns und werden **nie vermischt**: v0-Daten werden
nicht nach v1 umcodiert, v1 liest keine v0-Pakete, und die Fälle der einen Version zählen nicht als Fälle der anderen.

| | `network_v0` | `network_v1` |
|---|---|---|
| Erhebung | früheres Design: Erhebungsbögen + handgezeichnete Netzwerkkarte | eigenständige Netzwerkerhebung: Kontextbogen, Tabellen A, B, C |
| Datenformat | Paket `mares-network-package/v0-draft` (+ Kuratierung `mares-network-curation/v0-draft`) | Fallordner `mares-network-case/v1` |
| Nähe | Tabellenwert 1–5, **5 = sehr nah** | erfragter Wert 1–4 mit Zwischenwerten, **1 = sehr nah** |
| Kontakthäufigkeit | 1 = selten … 5 = täglich | 1 = (fast) täglich … 5 = wenige Male im Jahr |
| Alter-Alter | Gruppenumrandungen (Cliquenregel), Paarabdeckung nicht belegt | Tabelle C: Gruppen mit Status T/P/N/NS, Einzelpaare 1/0/? |
| Geografie | Marburg · Region Marburg · übriges Deutschland · übriges Europa · außerhalb Europas | Marburg (Stadt) · übriges Mittelhessen · übriges Deutschland · übriges Europa · außerhalb Europas |
| Code | [`src/mares/network_v0/`](../../src/mares/network_v0/__init__.py) | [`src/mares/network_v1/`](../../src/mares/network_v1/__init__.py) |
| Vertrag | [`network-module.md`](network-module.md), [`visualization-conventions.md`](visualization-conventions.md) | [`network-v1.md`](network-v1.md) |
| Ausgaben | `WORKSPACE/runs/<RUN-ID>/` (19 Abbildungen, Berichte) | acht Standardgrafiken in `<Fall>/graphics/`, Berichte in `WORKSPACE/runs/<RUN-ID>/` |
| Tests | `tests/test_network_v0_*.py` | `tests/test_network_v1_*.py` |

## 1. Ein Bedienweg

```text
.venv\Scripts\python -m mares.networks <v0-Schritt> --package ROOT:rel ...     (v0, wie bisher)
.venv\Scripts\python -m mares.networks v0 <v0-Schritt> --package ROOT:rel ...  (v0, ausdrücklich)
.venv\Scripts\python -m mares.networks v1 <Befehl> ...                         (v1, network-v1.md §8)
```

`mares.networks` ist nur noch der gemeinsame Einstieg ([`cli.py`](../../src/mares/networks/cli.py)); er verteilt an
`mares.network_v0` oder `mares.network_v1`. `python -m mares.network_v0` funktioniert ebenfalls.

## 2. Fallbaum

```text
<ROOT>/
├── network_v0/
│   └── pilots/
│       └── 001/                     Verweis auf das v0-Paket (data/case.json), keine Kopie
└── network_v1/
    ├── pilots/                      Testfälle und spätere v1-Piloterhebungen
    │   ├── 001_test_v0_fictionalized/
    │   │   ├── data/                metadata.json, Tabellen (network-v1.md §2)
    │   │   └── graphics/            nur die fertigen Standardgrafiken
    │   └── 002_test_synthetic/
    └── cases/                       nur reguläre Erhebungen; zunächst leer
```

- **Wo:** Der Baum enthält (künftig) Forschungsdaten und liegt deshalb **nie im Repository** (AGENTS.md Regel 1),
  sondern in einem Storage-Root: übergangsweise in `INTAKE`, nach Einrichtung von `PRIMARY` dort
  (die genaue Stelle im `PRIMARY`-Layout wird bei dessen Einrichtung festgelegt; [`storage-contract.md`](storage-contract.md) §4.4). Weil jeder Fall nur als
  logische Referenz (`INTAKE:network_v1/pilots/<Fall>`) angesprochen wird, ist der Umzug ein Wechsel des Rootnamens.
- **v0-Fälle** bleiben, wo ihre Lieferung liegt (`INTAKE:inbox/…`); `network_v0/pilots/<Fall>/data/case.json` verweist mit
  Referenz und SHA-256 auf Paket und Kuratierung. Weitere zwei bis drei v0-Pilotfälle erhalten denselben Eintrag. Die v0-Grafiken
  entstehen weiterhin in den Läufen unter `WORKSPACE/runs/` (unverändert); ein `graphics/`-Ordner für v0 ist vorgesehen, aber noch nicht
  befüllt (offen, siehe Run-Bericht 2026-10-31).
- **Test oder empirisch** entscheidet nie der Ordnername, sondern `metadata.json` (`case_type`, `provenance`,
  `empirical_analysis_eligible`; [`network-v1.md`](network-v1.md) §7).

## 3. Was bei der Migration geschah (2026-10-31)

- Code `src/mares/networks/` → `src/mares/network_v0/` (Git-Umbenennung, Inhalt unverändert); Tests
  `tests/test_networks_*.py` → `tests/test_network_v0_*.py`. Kein v0-Datum, kein v0-Lauf und kein Format wurde verändert.
- Neu: `src/mares/networks/` als gemeinsamer Einstieg; `src/mares/network_v1/`.
- Frühere Run-Berichte verweisen auf die alten Pfade; sie sind historische Journale und bleiben unverändert.
- v1 nutzt versionsneutrale Bausteine aus v0 (ISO-Ländertabellen und UN-Geoschema in `network_v0.geo`, Renderprimitive in
  `network_v0.figures.style`, Laufhelfer in `network_v0.run`), statt sie zu kopieren.

## 4. Testfall 001: Lesart der v0-Codes

`001_test_v0_fictionalized` übernimmt die **Struktur** des v0-Pilotfalls `001-2` (Kontakt-IDs, Gruppen, bestätigte
Mitgliedschaften) und deutet die v0-Codes nach ihrer im Codebuch des Pakets dokumentierten Bedeutung um. Der Aufbau prüft vorher, dass
das Codebuch genau diese Bedeutungen hat, und schreibt sonst nichts. Code: [`testcases.py`](../../src/mares/network_v1/testcases.py).

| v0 | → v1 | Art |
|---|---|---|
| Nähe 5 / 4 / 3 / 2 / 1 | 1 / 2 / 3 / 3,5 / 4 | Interpretation (andere Länge und Richtung der Skala) |
| Häufigkeit 5 / 4 / 3 / 2 / 1 | 1 / 2 / 3 / 4 / 5 | Richtungsumkehr, gleiche Stufen |
| Beziehung (mehrere Codes) | eine Hauptbeziehung nach Vorrang Partner:in > Familie > Freundschaft > professionell > bekannt; Arbeit, Studium, Nachbarschaft/Verein → Bekannte:r; andere → sonstige | Interpretation |
| Funktionen 1, 2, 10 / 3 / 4, 7 / 5 / 6, 8, 9, 11 | 1 / 2 / 3 / 4 / 5 | Interpretation |
| Medien persönlich, Chat, Sprachnachricht, Telefon, Video / soziale Medien, E-Mail, anderes | 1, 5, 4, 3, 2 / 6 | Interpretation |
| Sprachen 1–5 | 1–5 | übernommen |
| Sprachmodus 1–3 / 4 / 5 / 6 | Sprache / M / S / leer | Interpretation; Modus 6 hat keine Entsprechung |
| bestätigte Gruppe / zu prüfende Gruppe | T / NS (nur bestätigte Mitgliedschaften) | Interpretation (Cliquenregel von v0) |
| Bezeichnungen, Orte, Länder, Gruppennamen, Zugehörigkeit, Kontextbogen | erfunden | fiktiv |

Wohnorte werden nicht übernommen: der v0-Bereich (und innerhalb Deutschlands die Mittelhessen-Liste) bestimmt den Bereich, der Ort selbst wird
erfunden; eine regionale Angabe bleibt eine regionale Angabe („Nähe Marburg“, in v1 nicht zuordenbar). Jedes Feld trägt seine Herkunft
in `metadata.json` (`field_origins`: `v0_taken`, `v0_interpreted`, `fictional`).
