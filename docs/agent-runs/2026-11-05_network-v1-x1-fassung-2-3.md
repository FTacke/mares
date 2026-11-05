# Run-Bericht 2026-11-05 – `network_v1`: X1 Fassung 2.3 (regionale Ortsgruppen)

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §6.1,
[`ADR-0014`](../decisions/ADR-0014_2026-11-05_netzwerk-v1-x1-regionale-ortsgruppen.md). Vorlauf:
[`2026-11-05_network-v1-x1-fassung-2-2.md`](2026-11-05_network-v1-x1-fassung-2-2.md). Für den authentischen Fall MT nennt der Bericht
keine Orte und keine Länder.

## 1. Ziel

Mittelhessen vereinfachen. Benachbarte Orte dürfen zusammengefasst werden, wenn das für den Kartenmaßstab sinnvoll und geografisch
plausibel ist, über eine zentral gepflegte Regel statt Einzelfallentscheidungen im Code. Vorab: Working Tree sauber,
`main` = `origin/main` (`cf9b5a8`).

## 2. Änderungen

- [`experimental.py`](../../src/mares/network_v1/experimental.py):
  - Ortsverzeichnis mit optionaler Spalte `group_with` statt `centre`; ein Verweis auf einen Ort, der nicht im Verzeichnis steht,
    ist ein Fehler.
  - `_group` ist neu: Zuordnung laut Verzeichnis, nur wenn der Zielort im Panel Kontakte hat, höchstens 40 km entfernt ist
    (`GROUP_MAX_KM`) und im Panel näher als etwa 15 mm liegt (`GROUP_MAP_IN`); eine Stufe.
  - Hohle Ringe für die wahren Punkte der weiteren Orte einer Gruppe.
  - Kürzere Fußnote; `version: "2.3"`.
- **Ortsverzeichnis** `INTAKE:network_v1/reference/gazetteer.csv` (außerhalb des Repositorys): `centre` durch `group_with` ersetzt.
  Fünf Zuordnungen mit Begründung in `basis`: Wehrda, Cölbe, Lahntal und Kirchhain zu Marburg, Wetzlar zu Gießen. Koordinaten
  unverändert.
- Tests: 18 X1-Tests. Doku: `network-v1.md` §6.1, ADR-0014.

## 3. Gruppierungsergebnisse (visuell geprüft, PNG)

- **002:**
  - „Marburg und Umgebung · n = 14“ (Marburg 10 · Cölbe · Kirchhain · Lahntal · Wehrda) und „Gießen und Umgebung · n = 4“
    (Gießen 3 · Wetzlar), zwei klar getrennte Schwerpunkte.
  - Kirchhain und Wetzlar ohne eigene Kästen.
  - Kassel, Frankfurt am Main und Berlin eigenständig; in Amerika Bogotá und Medellín getrennt.
- **001:** Marburg · n = 8 und Gießen jeweils für sich (der Fall hat keine Kontakte an zugeordneten Nachbarorten); Köln, Kassel,
  Frankfurt, Leipzig und Berlin eigenständig. Unverändert gegenüber Fassung 2.2.
- **MT:** keine Ortsgruppe; alle Orte stehen für sich. Unverändert gegenüber Fassung 2.2.
- Kein Kontakt verloren oder falsch zugeordnet: In 002 sind alle 31 verortbaren Kontakte dargestellt (A22 nicht zuordenbar); die
  Mitglieder der Marburger Gruppe entsprechen genau den Kontakten mit den fünf Wohnorten (Test).

## 4. Tests und Regression

- Neue bzw. angepasste X1-Tests:
  - Zuordnung laut Verzeichnis, Zahlen aus den Daten, kein Kontakt verloren;
  - ohne Zuordnung keine Gruppen;
  - Maßstab: bei kleiner Kartenschwelle keine Gruppen;
  - 40-km-Grenze (Kassel bleibt trotz Eintrag getrennt);
  - keine Ketten; keine Gruppe ohne Kontakte am Zielort;
  - unbekannter Verweis ist ein Fehler;
  - wahre Punkte der weiteren Orte sichtbar.
- Volle Suite: **591 bestanden**.
- Die 48 Standardgrafiken sind byteidentisch.

## 5. Status

| | X1 Fassung 2.3 |
|---|---|
| implementiert | ja |
| technisch getestet | ja |
| visuell geprüft (Agent, drei Fälle) | ja |
| fachlich bewertet / in den Standardsatz aufgenommen | nein (offen) |

## 6. Verbleibende Punkte

- In 002 weichen Kassel und Frankfurt weiterhin neben die Marburger Fläche aus. Ihre wahren Punkte liegen im Maßstab unter dieser
  Fläche.
- Die hohlen Ringe der weiteren Orte liegen bei sehr nahen Orten (Wehrda, Cölbe) fast auf dem Ortspunkt und sind dann kaum einzeln zu
  sehen.
- Die Zuordnung `group_with` ist eine fachliche Setzung im Verzeichnis und für neue Orte zu pflegen.
