# Run-Bericht 2026-11-06 – `network_v1`: G4 und G5 kanonisiert, experimentelle Altbestände entfernt

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §6 und §6.2,
[`ADR-0022`](../decisions/ADR-0022_2026-11-06_netzwerk-v1-g4-g5-kanonisch.md), Texte:
[`network-v1-visualization-text-inventory.md`](../architecture/network-v1-visualization-text-inventory.md). Vorlauf:
[`2026-11-06_network-v1-g3-herkunft-zwei-ansichten.md`](2026-11-06_network-v1-g3-herkunft-zwei-ansichten.md). Für den authentischen
Fall MT nennt der Bericht keine Inhalte.

## 1. Ziel und Scope

- Die beiden abgenommenen Geburtslandansichten werden zur zehnten und elften Standardgrafik.
- Letzte redaktionelle Korrektur: ein einziger Hinweis in der Lokalansicht.
- Alle Fälle werden regulär gerendert.
- Überholte Experimentausgaben und -pfade werden entfernt.

Vorab: Working Tree sauber, `main` = `origin/main` (`7546e7b`). Vorhandene Fälle laut `v1 list`: `pilots/001_test_v0_fictionalized`,
`pilots/002_test_synthetic`, `student_pilot/001_mt`; keine weiteren.

## 2. Änderungen

**Code:**
- `figures/base.py`: `TITLES` um G4 und G5 ergänzt; der Titel-Parameter von `page()` (nur für Experimente) entfällt.
- `figures/birth_country.py`:
  - Funktionen `g4`, `g5`;
  - Skip-Prüfungen `g4_missing`, `g5_missing`;
  - `g5_details` (was G5 auslässt);
  - `local_note` mit dem einen Hinweis „Lokaler Ausschnitt: n von N Kontakten (Marburg und Mittelhessen).“
- `figures/__init__.py`: G4 `gruppen_geburtsland` und G5 `lokale_gruppen_geburtsland` im Register; ein optionales Feld `details`
  je Grafik, das `render` in den Registereintrag schreibt.
- `run.py`: `details` auch im Run-Record.
- Entfernt: `experiments.py` und der CLI-Befehl `v1 experiment`. Wortlaute „nine“ in Docstrings und CLI-Hilfe auf „eleven“.

**Tests:**
- `test_network_v1_birth_country.py` auf G4/G5 umgestellt (20 Tests). Neu geprüft werden:
  - der eine Hinweis;
  - die Registerdetails;
  - die Skip-Gründe;
  - 22 Dateien in `graphics/` und kein `experimental/`;
  - dass der Experimentbefehl fehlt.
- Zählungen in `test_network_v1_figures.py` und `test_network_v1_x1.py` von 9/18 auf 11/22.

**Dokumentation:**
- `network-v1.md`: Status, Ablauf, Fallordner, §5.7, §6 (Tabelle, Registerfolge), neuer §6.2, §8.
- Textinventar um G4 und G5 ergänzt (Knoten, Legende, Hinweis, Skip-Gründe, Registerdetails).
- `storage-contract.md`, `network-versions.md`, README.
- ADR-0022; Statusvermerk in ADR-0021.

## 3. Bereinigung im geschützten Speicher

- Inventar vorab: Je Fall enthielt `experimental/` nur Bilddateien:
  - eine frühere X1-Ausgabe (2);
  - X1 Fassung 1 (2);
  - die Experimentkopien von G3 nach Geburtsland (4).

  Kein Code und kein Test liest diese Pfade.
- Nach dem erfolgreichen regulären Lauf entfernt: 24 Dateien einzeln mit exaktem Namen, danach 9 leere Ordner. Jeder Fall
  enthält jetzt nur `data/` und `graphics/`.
- Erhalten: das Pilotskript `pilots/network_v1_map/` (eigenes, nicht abschließend bewertetes Experiment), alle Daten, Metadaten,
  ADRs und Run-Berichte.

## 4. Tests und Prüfungen

- **Gesamtsuite:** siehe §5.
- **Regulärer Lauf** `render-all --root INTAKE --formats png,svg`: drei Fälle `COMPLETED`, je 11 Grafiken gerendert, keine übersprungen,
  je 22 Dateien in `graphics/`.
- **Bisherige neun Grafiken:** alle 54 Dateien bytegleich zum Stand vor den G3-Geburtsland-Läufen.
- **Visuell:** G4 und G5 aller drei Fälle anhand der PNGs geprüft.
  - G4 entspricht der abgenommenen Fassung.
  - G5 zeigt nur noch den einen Hinweis; bei wenigen Gruppen (001, MT) kompakt nebeneinander, bei 002 mit erkennbaren
    Überschneidungen.
  - Keine Überlagerungen.

## 5. Status und offene Punkte

- Implementiert, getestet und gerendert; nicht wissenschaftlich validiert.
- Gesamtsuite: 630 Tests bestanden.
- Die Zeilenangaben im Textinventar beziehen sich auf den Stand der redaktionellen Vereinheitlichung. Für G4/G5 sind Funktionen
  angegeben, keine Zeilen.
- Ein Fall ohne Gruppen oder ohne lokale Kontakte ist nur in Tests (synthetisch) durchlaufen; unter den vorhandenen Fällen gibt es keinen.
