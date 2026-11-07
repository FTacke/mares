# Run-Bericht 2026-11-07 – `network_v0`: Fall 001-2 aktualisiert, Standardgrafiken mit den Grafikfunktionen von v1

Journal eines Laufs, keine Spezifikation. Maßgeblich:
[`ADR-0023`](../decisions/ADR-0023_2026-11-07_netzwerk-v0-standardgrafiken-und-fall-001-2.md),
[`network-module.md`](../architecture/network-module.md) §7.1, [`pilot-case-001-2.md`](../methodology/pilot-case-001-2.md). Der Bericht
nennt keine Personen, Namen, Orte oder Einzelwerte des Falls.

## 1. Ziel und Scope

1. Fall 001-2 mit der geprüften Transkription und den Klärungen der Projektleitung vom 2026-11-07 aktualisieren.
2. Die Grafiken von v1 für v0 nutzbar machen (G1, G2, P1–P5, G3, X1) und die bisherige v0-Grafikgeneration ersetzen.
3. Den Weg für weitere v0-Fälle wiederverwendbar halten.

Vorab: Working Tree sauber, `main` = `origin/main` (`7bba3e5`).

## 2. Daten (nur im geschützten Speicher)

- **Quell-PDFs** (Erhebungsblatt, Netzwerkkarte): lagen im Repository-Root (von Git ignoriert, nie vorgemerkt). Sie wurden nach
  `INTAKE:inbox/MARES_001-2_Quellen_2026-11-07` kopiert, mit SHA-256 geprüft und danach aus dem Root entfernt. Inhaltlich wurden sie
  nicht gelesen (AGENTS.md Regel 3); Grundlage ist die geprüfte Transkription der Projektleitung.
- **Abgleich** Transkription gegen Paket 1.1:
  - 22 Kontakte, IDs identisch (zweites Blatt bereits als A16–A22 geführt).
  - Unterschiede nur bei den Funktionscodes eines Kontakts (2 und 5 fehlten, waren offener Prüfpunkt) und in der Schreibweise
    einer Regionalangabe.
  - Das Geburtsland eines Kontakts blieb mehrdeutig, wie bisher.
  - Medienbereiche, Nähe, Häufigkeit, Sprachen, Sprachmodus, Beziehungscodes und Nennquellen stimmten überein.
- **Rückfragen an die Projektleitung** (im Lauf beantwortet):
  - Kanten: Cliquenregel für die vier Gruppen C01–C04.
  - Knotenfarbe bei mehreren Beziehungscodes: geteilter Knoten.
  - Ortsverzeichnis: Städte von Hand ergänzen.
- **Paketversion 1.2** neu neben 1.1 (unverändert):
  - Funktionen eines Kontakts ergänzt.
  - Gruppen C01–C04 (vorher sechs Gruppen; zwei waren ergänzende Umrandungen).
  - 41 Kanten nach Cliquenregel: drei neu, drei entfallen.
  - Klärungen K01–K04; neue Prüfpunkte R15–R17; Manifest mit Änderungsliste.
  - Neue Kuratierung 2026-11-07 übernimmt alle bisherigen Einordnungen und ergänzt die Klärungen (R02, R05, R13, R17 geklärt;
    R04, R07, R15, R16 dokumentierte Mehrdeutigkeit).
- **Prüfung von 1.2:** `PASSED`, 0 Fehler, 0 Warnungen, vier offene Datenfragen (Paarabdeckung, Fall-ID, Provenienz,
  Quellenprüfung; wie vorher).
- **Plausibilität:**
  - 22 eindeutige IDs;
  - Nähe 5/4/3/2 = 4/10/6/2;
  - Gruppen 7/5/6/2;
  - sechs Kontakte ohne Gruppe;
  - Mehrfachmitgliedschaften wie erwartet.
- **Fallverweis** `network_v0/pilots/001/data/case.json` auf 1.2 und die neue Kuratierung umgestellt, mit Hashes und Historie;
  `pilot`, `empirical_analysis_eligible: false` und Freigabe unverändert.
- **Ortsverzeichnis** `network_v1/reference/gazetteer.csv`: sechs Städte mit öffentlicher Stadtkoordinate ergänzt. Kein
  Geocoding-Dienst. Die Regionalangabe „Nähe Marburg“ bekam keine Koordinate.

## 3. Code

- `network_v1/figures/base.py`:
  - Versionsprofil `Scheme` mit dem v1-Verhalten als Standard, im Kontext als `scheme`.
  - Fußzeile mit Versionskennung.
  - Geteilte Knoten (Netz, Matrix, Legende).
  - Bereichsnamen und Klammertext aus dem Profil.
  - P5-Breite, optionales Weglassen leerer nominaler Kategorien.
- `networks.py`, `matrices.py`, `maps.py`: lesen Nähe, Sektoren, Ringe, Legenden, Häufigkeit, Medien, Sprachen, Funktionen und
  Beziehungsfarben aus dem Profil. G3 ohne Zugehörigkeit: einzeilige Labels, keine Skala.
- `network_v0/standard.py` (neu): v0-Profil aus dem Codebuch (mit Prüfung der Beziehungsbedeutungen), Übersetzung des v0-Datensatzes
  ohne Umcodierung, Rendern der neun Standardgrafiken.
- `network_v0/run.py`, `cli.py`, `report.py`: Die Grafikstufe erzeugt die neun Standardgrafiken; neuer Befehl `v0 render-case` liest
  den Fallverweis, prüft die Hashes und schreibt nach `<Fall>/graphics/`. Die alten Optionen und PDF als Standard sind entfallen.
- **Entfernt:** 15 alte v0-Grafikmodule (`figures/` außer `style.py`) und 5 Testdateien dazu. `test_network_v0_run.py` und
  `test_network_v0_geo_classification.py` wurden angepasst; neu ist `test_network_v0_standard.py` (10 Tests).

## 4. Prüfungen

- **v1 unverändert:** Nach jedem Eingriff in den gemeinsamen Grafikcode wurden die Standardgrafiken der Testfälle 001 und 002 neu
  gerendert und verglichen; alle 44 Dateien sind bytegleich.
- **v0 001-2:** `render-case` → `COMPLETED`, alle neun Grafiken gerendert (18 Dateien), keine übersprungen. Visuell geprüft:
  - G1: Ringe 5 innen bis 1 außen, Legendenhinweis zum Tabellenwert;
  - G2: v0-Bereiche, Ländernamen aus der Basiskarte;
  - P1/P2: v0-Skalen;
  - P3/P4: nur vorkommende Medien und Sprachen;
  - P5: nur vorkommende Funktionen;
  - G3: vier Gruppen, Mehrfachmitglieder mit Ringsegmenten;
  - X1: Städte auf drei Panels, die Regionalangabe als „nicht darstellbar“ genannt;
  - überall geteilter Knoten für den Kontakt mit zwei Beziehungscodes, keine Überlagerungen.
- **Tests:** 497 bestanden.

## 5. Status und offene Punkte

- Implementiert, getestet und gerendert; nicht wissenschaftlich validiert. Datenqualität `UNREVIEWED`.
- Gesamtsuite: 497 Tests bestanden (weniger als zuvor, weil die Tests der entfernten v0-Grafikmodule entfallen sind).
- **Offen (Daten):**
  - Paarabdeckung;
  - Abgleich der Transkription mit den Original-PDFs (nur mit ausdrücklicher Freigabe durch einen Agenten);
  - Sprachmodus 6 bei zwei Kontakten;
  - mehrdeutiges Geburtsland eines Kontakts;
  - Fall-ID und Provenienz.
- **Offen (Technik):**
  - Das Weglassen leerer Kategorien gilt nur für v0; v1 zeigt seine festen Kategorien weiter vollständig.
  - Neue v0-Fälle brauchen Ortsverzeichniseinträge für X1.
- **Nächster Schritt Fall 002:**
  1. Paket (`mares-network-package/v0-draft`) und Kuratierung nach `INTAKE:inbox/` legen.
  2. `v0 validate --package … --curation …` ausführen.
  3. Fallverweis `network_v0/pilots/002/data/case.json` mit Hashes anlegen.
  4. Fehlende Orte ins Ortsverzeichnis eintragen.
  5. `v0 render-case --case INTAKE:network_v0/pilots/002` ausführen.
