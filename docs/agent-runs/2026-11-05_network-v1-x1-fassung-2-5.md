# Run-Bericht 2026-11-05 – `network_v1`: X1 Fassung 2.5 (Ortspunkt immer frei, Kontakte daneben)

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §6.1,
[`ADR-0015`](../decisions/ADR-0015_2026-11-05_netzwerk-v1-x1-ortspunkt-frei.md). Vorlauf:
[`2026-11-05_network-v1-x1-fassung-2-4.md`](2026-11-05_network-v1-x1-fassung-2-4.md). Für den authentischen Fall MT nennt der Bericht
keine Orte und keine Länder.

## 1. Ziel

Ortspunkt und Ortsname immer sichtbar; Kontaktflächen grundsätzlich neben dem Ortspunkt, mit feiner Linie angebunden. Vorrang:
Sichtbarkeit von Punkt und Name, dann Trennung der Ortsgruppen, dann kompakte Lage. Vorab: Working Tree sauber,
`main` = `origin/main` (`3f8d633`).

## 2. Änderungen ([`experimental.py`](../../src/mares/network_v1/experimental.py))

- Die Ringe sitzen um den Mittelpunkt der Kontaktfläche, nicht mehr um den Ortspunkt. Die Leader-Lücke im Ring entfällt.
- `_place_panel` geht je Panel Ort für Ort vor, größte zuerst:
  - `_place_disc`: Kontaktfläche daneben (16 Richtungen, wachsender Abstand); nicht auf Ortspunkten, Kästen oder Linien, nicht über
    anderen Flächen.
  - Danach eine Nachbesserungsrunde: Jeder Kasten wird mit allen anderen Elementen als Hindernis neu gewählt.
- Kastenwahl in `_box_cost`: Alles, was einen Namen, Punkt, eine Fläche oder Linie verdecken würde, kostet 100. Neue
  Kastenvarianten: oberhalb und unterhalb auch seitlich versetzt.
- Zeichnung: Verbindungslinie Ortspunkt → Fläche (`connector`) und Kastenlinie (`leader`) über allen Flächen; Ortspunkt darüber.
  Gepunktete Ausweichlinien entfallen.
- `version: "2.5"`.

Unterwegs verworfen:
- Kästen vor allen Flächen zu setzen. Das schob die große Marburger Fläche weit nach Süden.
- Die eigenen Gruppenorte bei der Linienprüfung mitzuzählen. Dadurch war rund um Marburg und Gießen fast jede Richtung blockiert.

## 3. Ergebnisse (visuell geprüft, PNG)

- **002, Deutschland:**
  - Alle Ortspunkte sind frei.
  - Die Kästen von Marburg und Umgebung, Gießen und Umgebung und Frankfurt am Main stehen rechts untereinander, je mit eigener
    kurzer Linie.
  - Die Marburger Fläche liegt nordwestlich ihres Punktes, die Gießener westlich; Kassel und Berlin stehen klar daneben.
- **002, Amerika:** Bogotá und Medellín sind getrennt; ihre Flächen sind auseinandergezogen und angebunden.
- **001:** Alle Punkte und Namen sind frei. Köln und Kassel weichen mit längeren Linien nach Norden aus, weil die Marburger Fläche
  die Mitte belegt.
- **MT:** Jede Fläche liegt direkt neben ihrem Ortspunkt, jeder Kasten direkt am Punkt.

## 4. Tests und Regression

- X1 jetzt 22 Tests. Neu:
  - Ortspunkte und Namen frei (zwei Ortsverteilungen);
  - Flächen neben dem Punkt, überlappungsfrei, Punkt unverändert;
  - keine Linie unter Flächen oder Kästen, keine kreuzenden Linien;
  - Linien über allen Flächen.
- Volle Suite: **595 bestanden**.
- Die 48 Standardgrafiken sind byteidentisch.

## 5. Status

| | X1 Fassung 2.5 |
|---|---|
| implementiert | ja |
| technisch getestet | ja |
| visuell geprüft (Agent, drei Fälle) | ja |
| fachlich bewertet / in den Standardsatz aufgenommen | nein (offen) |

## 6. Verbleibende Punkte

- In dichten Panels rücken Kontaktflächen deutlich vom Ortspunkt ab (001: Köln, Kassel). Sie stehen dann über einer anderen Gegend
  der Karte; die Linie zeigt die Zugehörigkeit.
- Ein Kasten mit langer Linie kann näher an einem fremden Ortspunkt liegen (002: Marburg neben Kassel); die freie Linie ordnet ihn zu.
- Die Platzierung ist eine Heuristik mit Gewichten. Bei sehr vielen Orten in einem Panel ist sie nicht erprobt.
