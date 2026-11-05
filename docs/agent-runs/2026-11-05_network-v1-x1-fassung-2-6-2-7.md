# Run-Bericht 2026-11-05 – `network_v1`: X1 Fassungen 2.6 und 2.7 (angedockte, rahmenlose Labels; Fläche und Label gemeinsam)

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §6.1. Vorlauf:
[`2026-11-05_network-v1-x1-fassung-2-5.md`](2026-11-05_network-v1-x1-fassung-2-5.md). Für den authentischen Fall MT nennt der Bericht
keine Orte und keine Länder.

## 1. Ziel

Ortslabels ruhiger und weniger kastenartig. Fläche und Label bilden ein gemeinsames Callout, das Label dockt direkt an. Ortsname fett,
Zahl kompakt, Einzelorte klein und grau; nur ein dezenter Halo bzw. eine weiche Hintergrundfläche, keine Rahmen. Vorab: Working Tree
sauber, `main` = `origin/main` (`ed495f3`).

## 2. Änderungen ([`experimental.py`](../../src/mares/network_v1/experimental.py))

- **Callout:** je Ort zuerst die Kontaktfläche neben dem Ortspunkt, dann das Label direkt am Flächenrand (`_place_label`; acht
  Richtungen, oben und unten auch seitlich versetzt; Abstand 0,03 bis 0,32 Zoll). Die eigene Linie Kasten → Ortspunkt entfällt; die
  feine Linie Ortspunkt → Fläche bleibt.
- **Stil:**
  - erste Zeile mit fettem Namen (`head`) und normalem Rest (`tail`, „· Kolumbien · 3“);
  - Einzelorte klein und grau;
  - weißer Halo (`patheffects`) und eine blasse, gerundete Fläche ohne Kontur;
  - „Zahl = Kontakte am Ort“ einmal in der Legende.
- **Kosten** (`_label_cost`):
  - Verdecken (Fläche, Ortspunkt, Linie, anderes Label) 150;
  - Mehrdeutigkeit 100, gemessen von der Labelmitte zum Flächenrand (`_reach`).

  Gemessen von der nächsten Labelecke stufte die Regel ein eindeutig über der eigenen Fläche stehendes Label als mehrdeutig ein.
- Linien der Kontaktflächen halten mehr Abstand zu fremden Ortspunkten.
- `version: "2.6"`.
- **Fassung 2.7**, auf Nachtrag der Projektleitung im selben Lauf: Fläche und Label werden gemeinsam platziert
  (`_place_callout`). Die Kandidaten für die Fläche (`_disc_candidates`) werden von nah nach fern geprüft. Genommen wird die
  nächstgelegene zulässige Position, an der das vollständige Label kollisionsfrei und eindeutig am Kreis Platz findet. Benachbarte
  Gruppen werden dafür auseinandergezogen; die Ortspunkte bleiben fest.
- Sichtprüfung auf Hinweis der Projektleitung: Das Label „Gießen und Umgebung“ (002) stand 0,18 Zoll über der eigenen Fläche, also
  nicht angedockt; darunter verlief die Linie von Frankfurt. Behoben auf drei Wegen:
  - Als angedockt zählt nur noch der engste Abstand (`LABEL_FITS`).
  - Ein nicht angedocktes Label kostet bei der gemeinsamen Suche zusätzlich (`LABEL_MISS`).
  - Eine Verbindungslinie über einem Label oder einer fremden Fläche ist ein harter Verstoß.

  Jetzt dockt das Label direkt unter der Gießener Fläche an. Die Frankfurter Fläche liegt nordwestlich; ihre Linie läuft frei
  zwischen den Flächen.

## 3. Ergebnisse (visuell geprüft, PNG)

- **002:**
  - Alle Labels docken an ihrer Fläche an.
  - In Deutschland steht „Marburg und Umgebung · 14“ unter der Marburger Fläche, „Gießen und Umgebung · 4“ über der Gießener,
    „Frankfurt am Main“ unter der eigenen.
  - Keine Linie wird verdeckt.
- **001:** Köln, Kassel, Frankfurt und Leipzig mit Label über bzw. unter der eigenen Fläche, Marburg rechts daneben, Gießen links.
- **MT:** Alle Labels sitzen direkt an der eigenen Fläche.

## 4. Tests und Regression

- X1: 24 Tests (2.7: zusätzlich „jedes Label findet vollständig am eigenen Kreis Platz“, auch in einer dichteren Variante).
  - Neu: Jedes Label dockt an der eigenen Fläche an (Abstand ≤ 0,35 Zoll, nie darauf), wird als deren Callout gelesen, überlappt kein
    anderes Label und verdeckt keine Linie.
  - Angepasst: Titelformat „· Zahl“, keine Rahmen, nur noch Verbindungslinien.
- Volle Suite: **597 bestanden**.
- Die 48 Standardgrafiken sind byteidentisch.

## 5. Status

| | X1 Fassung 2.7 |
|---|---|
| implementiert | ja |
| technisch getestet | ja |
| visuell geprüft (Agent, drei Fälle) | ja |
| fachlich bewertet / in den Standardsatz aufgenommen | nein (offen) |

## 6. Verbleibende Punkte

- In dichten Panels liegen Kontaktflächen weiterhin teils weit vom Ortspunkt (002: Frankfurt im Süden, 001: Köln, Kassel); die Linie
  ordnet sie zu.
- Die blasse Hintergrundfläche bleibt in hellen Kartenbereichen leicht sichtbar. Ohne sie wäre Schrift über Grenzlinien schlechter
  lesbar.
