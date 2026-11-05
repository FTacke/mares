# Run-Bericht 2026-11-05 – `network_v1`: X1 Fassung 2.4 (eindeutige Zuordnung der Ortskästen)

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §6.1. Vorlauf:
[`2026-11-05_network-v1-x1-fassung-2-3.md`](2026-11-05_network-v1-x1-fassung-2-3.md). Für den authentischen Fall MT nennt der Bericht
keine Orte und keine Länder.

## 1. Ziel

Ortskästen und Ortsanker sollen auf einen Blick eindeutig zusammengehören. Leader-Linien dürfen nicht unter Flächen oder anderen
Elementen verschwinden. Marburg und Umgebung und Gießen und Umgebung sollen klar getrennt beschriftet sein. Vorab: Working Tree
sauber, `main` = `origin/main` (`09be17e`).

## 2. Änderungen ([`experimental.py`](../../src/mares/network_v1/experimental.py))

- **Zeichenreihenfolge:** Leader-Linien über allen Flächen und Ausweichlinien; Ortspunkt und hohle Ringe darüber; Knoten oben.
- **Platzierung der Kästen:** hohe Kosten, wenn
  - die Linie eine fremde Fläche, einen anderen Kasten oder eine andere Linie kreuzt;
  - der Kasten eine andere Linie verdeckt;
  - der Kasten näher am Rand einer fremden Fläche liegt als an der eigenen.

  Ein erster Ansatz verglich Abstände zu den Ortspunkten statt zu den Flächenrändern. Er ließ den Bogotá-Kasten in 002 neben Quito
  stehen; der Test hat das aufgedeckt.
- **Zweizeiliger Titel** (Ort / Land und Zahl) als zusätzlicher Kandidat, wenn ein einzeiliger Kasten nicht passt.
- **Mindest-Seitenverhältnis** der Panels 0,8 statt 0,65, damit schmale Panels Platz für Kästen haben.
- `version: "2.4"`.

## 3. Ergebnisse (visuell geprüft, PNG)

- **002:**
  - Deutschland: Kasten „Marburg und Umgebung“ rechts, „Gießen und Umgebung“ unten rechts. Beide Linien sind frei und enden sichtbar
    am Ortspunkt.
  - Amerika: „Bogotá / Kolumbien · n = 3“ zweizeilig nordöstlich der eigenen Gruppe, Quito darunter, Medellín darüber.
- **001:** Alle Kästen liegen an ihrer Gruppe, keine Linie wird gekreuzt.
- **MT:** unverändert klar; alle Kästen liegen an ihrer Gruppe.

## 4. Tests und Regression

- Neue X1-Tests:
  - keine Linie unter einer fremden Fläche oder einem fremden Kasten, keine Linienkreuzung;
  - jeder Kasten näher an der eigenen Gruppe als an jeder anderen;
  - Leader-Linien über allen Flächen, Ortspunkt darüber.
- X1 insgesamt 20 Tests. Volle Suite: **593 bestanden**.
- Die 48 Standardgrafiken sind byteidentisch.

## 5. Status

| | X1 Fassung 2.4 |
|---|---|
| implementiert | ja |
| technisch getestet | ja |
| visuell geprüft (Agent, drei Fälle) | ja |
| fachlich bewertet / in den Standardsatz aufgenommen | nein (offen) |

## 6. Verbleibende Punkte

- Im Deutschland-Panel von 002 liegen die Kästen von Gießen und Frankfurt untereinander. Sie sind getrennt und je über eine kurze Linie
  angebunden, stehen aber nah beieinander.
- Ein zweizeiliger Kasten ist etwas höher; er wird nur gewählt, wenn er besser liegt.
