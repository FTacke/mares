# Run-Bericht 2026-11-05 – `network_v1`: X1 Fassung 2.1

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §6.1,
[`ADR-0012`](../decisions/ADR-0012_2026-11-05_netzwerk-v1-x1-fassung-2-1.md). Vorlauf am selben Tag:
[`2026-11-05_network-v1-x1-fassung-2.md`](2026-11-05_network-v1-x1-fassung-2.md). Für MT nennt der Bericht keine Orte.

## 1. Ziel

Drei gezielte Verbesserungen an X1:
1. Ortsgruppen nur nach geografischer Nähe (Bogotá und Medellín getrennt);
2. Kartenausschnitte nach den Kontakten;
3. kompaktere Ortskästen.

Alles Übrige bleibt. Vorab: Working Tree sauber, `main` = `origin/main` (`c48ad08`).

## 2. Änderungen

[`experimental.py`](../../src/mares/network_v1/experimental.py):
- Die Kartenregel der Ortsgruppen ist entfernt; es zählt nur die Luftlinie (höchstens 20 km).
- `_extent` ist neu: Umriss der Orte plus Rand je Region, Mindestgröße, Seitenverhältnis 0,65–1,5, Deutschland-Rahmen. Ohne Kontakte
  gilt der Standardausschnitt.
- Die Ortskästen sind kleiner und heller, die Flächen etwas enger.
- Die Fußnote nennt „Panels mit eigenem Maßstab“; das Laufprotokoll trägt `version: "2.1"`.

Außerdem: Tests (jetzt 13), `network-v1.md` §6.1, ADR-0012.

Ein Zwischenstand mit einer Deutschland-Mindestgröße von 7° × 5,5° zeigte bei MT (nur ein Ort in Deutschland) einen Ausschnitt ohne
erkennbaren Umriss. Die Mindestgröße ist deshalb auf 9° × 7,5° gesetzt.

## 3. Ergebnisse (visuell geprüft, PNG)

- **002:**
  - Bogotá (n = 3) und Medellín sind getrennt; Medellín weicht mit gepunkteter Linie aus.
  - Amerika reicht wegen Toronto von Kanada bis Ecuador; Europa ist auf Spanien und Südfrankreich fokussiert.
  - Deutschland zeigt Marburg und Umgebung (14) und Gießen und Umgebung (4) getrennt; Kassel und Frankfurt weichen aus.
- **MT:** Amerika zeigt den Raum um den einen Ort in Südamerika, Europa ist auf Italien fokussiert, Deutschland bleibt erkennbar. Alle
  Ortskästen stehen frei.
- **001:**
  - Amerika: Kolumbien bis Peru; Europa: Iberische Halbinsel.
  - Deutschland: Köln, Kassel, Marburg, Gießen, Frankfurt, Leipzig und Berlin unterscheidbar. Gießen und Frankfurt weichen neben die
    Marburg-Fläche aus.
- In allen drei Fällen gibt es keine Verbindungslinien zwischen Kontakten. IDs und Farben sind unverändert, die Ortspunkte stammen aus
  dem Ortsverzeichnis.

## 4. Tests und Regression

- X1: 13 Tests, neu bzw. angepasst:
  - Bogotá und Medellín getrennt;
  - jeder Ort im Ausschnitt seines Panels;
  - Deutschland im Rahmen und mindestens 9° breit;
  - Europa ohne Osteuropa bei nur westeuropäischen Kontakten, breiter mit östlichem Kontakt;
  - Amerika ohne Nordamerika bei nur südamerikanischen Kontakten;
  - leeres Panel mit Standardausschnitt.
- Volle Suite: **586 bestanden**.
- Die 48 Standardgrafiken sind vor und nach dem Lauf byteidentisch.

## 5. Status

| | X1 Fassung 2.1 |
|---|---|
| implementiert | ja |
| technisch getestet | ja |
| visuell geprüft (Agent, drei Fälle) | ja |
| fachlich bewertet / in den Standardsatz aufgenommen | nein (offen) |

## 6. Verbleibende Layoutprobleme

- Mittelhessen bleibt dicht: In 001 und 002 liegen die wahren Punkte ausgewichener Orte (hohle Ringe) in der Marburg-Fläche.
- Unterschiedliche Maßstäbe: Gleich große Symbole stehen in den Panels für unterschiedlich große Gebiete. Die Fußnote weist darauf hin.
- Unter den kleineren Panels bleibt durch die obere Bündigkeit etwas Leerraum. Bei sehr kleinen Ausschnitten, etwa MT Amerika, ist
  das Panel höher als nötig.
