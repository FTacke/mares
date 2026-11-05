# Run-Bericht 2026-11-05 – `network_v1`: X1 Fassung 2.2 (Zentren und Länder)

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §6.1,
[`ADR-0013`](../decisions/ADR-0013_2026-11-05_netzwerk-v1-x1-zentren-und-laender.md). Vorlauf am selben Tag:
[`2026-11-05_network-v1-x1-fassung-2-1.md`](2026-11-05_network-v1-x1-fassung-2-1.md). Für den authentischen Fall MT nennt der Bericht
keine Orte und keine Länder, nur Strukturangaben.

## 1. Ziel

Zwei Ergänzungen der Projektleitung:
- das Land im Ortskasten außerhalb Deutschlands;
- „und Umgebung“ nur, wenn Orte nahe liegen **und** eine gemeinsame Ortsgruppe sachlich plausibel ist (eigenständige Zentren bleiben
  getrennt), ohne fallbezogene Ausnahmen im Code.

Vorab: Working Tree sauber, `main` = `origin/main` (`7e84683`).

## 2. Änderungen

- [`experimental.py`](../../src/mares/network_v1/experimental.py):
  - Land im Ortskasten außerhalb Deutschlands (aus der erhobenen Wohnland-Angabe, sonst aus der Basiskarte);
  - Ortsverzeichnis mit optionaler Spalte `centre`;
  - Gruppierung neu: Nicht-Zentren kommen zum nächstgelegenen Zentrum innerhalb von 20 km, Zentren nie zusammen, keine Ketten,
    unbekannt = Zentrum;
  - kürzere Fußnote; `version: "2.2"`.
- **Ortsverzeichnis** `INTAKE:network_v1/reference/gazetteer.csv` (außerhalb des Repositorys):
  - Spalte `centre` ergänzt, Begründung in `basis`;
  - drei Orte ohne Zentrumsstatus (ein Stadtteil, zwei Umlandgemeinden), 22 Zentren;
  - Koordinaten unverändert.
- Tests: 17 X1-Tests (vorher 13). Doku: `network-v1.md` §6.1, ADR-0013.
- **Korrektur von Inhalten aus MT in versionierten Dokumenten:** Zwei bereits gepushte Run-Berichte nannten ein Land bzw. eine
  benannte Sprache aus dem Fall MT. Beides ist durch neutrale Formulierungen ersetzt (Regel 4 in AGENTS.md); die früheren Fassungen
  bleiben in der Git-Historie, die nicht umgeschrieben wird. Ein Beispiel aus MT im neuen Code und in der neuen Doku ist durch Beispiele
  aus dem synthetischen Fall 002 ersetzt.

## 3. Ergebnisse (visuell geprüft, PNG)

- **002:**
  - „Marburg und Umgebung · n = 13“ (Marburg 10 · Cölbe · Lahntal · Wehrda).
  - Gießen (3), Wetzlar, Kirchhain, Kassel, Frankfurt und Berlin stehen für sich; mehrere weichen mit gepunkteter Linie zur wahren
    Lage aus.
  - Amerika mit Land im Kasten: „Bogotá · Kolumbien · n = 3“, „Medellín · Kolumbien“, „Quito · Ecuador“, „Miami · USA“,
    „Toronto · Kanada“.
- **MT:** Alle Ortskästen außerhalb Deutschlands tragen das Land, der Kasten in Deutschland nur den Ort; keine Ortsgruppe nötig, keine
  Kollisionen.
- **001:** Gruppierung unverändert (keine Umlandorte im Fall), Länder in Amerika und Europa ergänzt.
- In allen drei Fällen keine Verbindungslinien. Die Ortspunkte sind unverändert, die erhobenen Wohnorte nicht verändert.

## 4. Tests und Regression

- Neue X1-Tests:
  - nur Nicht-Zentren kommen zum Zentrum, Zentren bleiben getrennt (auch Gießen–Wetzlar, 13 km);
  - ohne Spalte `centre` keine Gruppen;
  - ein Umlandort kommt zum nächsten Zentrum, keine Ketten;
  - ungültiger `centre`-Wert ist ein Fehler;
  - Land im Kasten außerhalb Deutschlands, nicht in Deutschland, nicht doppelt bei „nur Land bekannt“.
- Volle Suite: **590 bestanden**.
- Die 48 Standardgrafiken sind byteidentisch.

## 5. Status

| | X1 Fassung 2.2 |
|---|---|
| implementiert | ja |
| technisch getestet | ja |
| visuell geprüft (Agent, drei Fälle) | ja |
| fachlich bewertet / in den Standardsatz aufgenommen | nein (offen) |

## 6. Verbleibende Punkte

- Mittelhessen in 002: Die eigenständigen Zentren führen dazu, dass mehr Symbole ausweichen (Wetzlar, Kirchhain, Frankfurt). Die Lage
  bleibt über die gepunkteten Linien nachvollziehbar, das Bild ist aber dichter.
- Der Zentrumsstatus ist eine von Hand gepflegte Einstufung (zentralörtliche Gliederung bzw. eigenständige Stadt). Neue Orte brauchen
  eine Einstufung; ohne sie bleiben sie getrennt.
