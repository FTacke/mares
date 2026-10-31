# Run-Bericht 2026-10-31 – `network_v1`: G1-Sektoren und kompakte G3-Beschriftung

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §5.3 und §6,
[`ADR-0008`](../decisions/ADR-0008_2026-10-31_netzwerk-v1-g1-sektoren-g3-beschriftung.md). Vorlauf am selben Tag:
[`2026-10-31_network-v1-g1-g3-feinschliff.md`](2026-10-31_network-v1-g1-g3-feinschliff.md). Ortsangaben beschreiben den
Projektarbeitsplatz.

## 1. Ziel und Ausgangslage

Abschließender Feinschliff von G1 (Kontakte gleichen Beziehungstyps räumlich zusammen) und G3 (kürzere Gruppenbeschriftungen, eng an
den Gruppen). G2 und P1–P5 sind gestalterisch abgenommen und sollten unverändert bleiben. Vorab: Working Tree sauber, `main` =
`origin/main` (`d1bc3fb`).

## 2. Änderungen

**G1** ([`networks.py`](../../src/mares/network_v1/figures/networks.py), `g1_sectors`, `g1_layout`): Winkelsektoren in fester Folge der
sechs Beziehungstypen (danach „keine Angabe“), Breite ∝ Zahl der Kontakte des Typs, fehlende Typen ohne Breite an ihrem Platz. Auf
jedem Ring liegen die Kontakte eines Typs verteilt über ihren Sektor; überlappende Knoten werden mit der kleinstmöglichen Verschiebung
unter Erhalt der Reihenfolge getrennt. Radius unverändert = erhobene Nähe. Keine Sektorlinien, keine Flächen. Neuer Hinweistext.

**G3:** Beschriftungsblock `C04 · <Name> (n)` / `○●○○○ 2`. Entfallen sind „Zugehörigkeit“, die verbalen Stufen und „Kontakte“, im
Darstellungsnamen außerdem Testdaten-Zusätze wie „(fiktive Bezeichnung)“. Überlange Namen werden in der Darstellung gekürzt. Fehlende
Werte zeigen das Kürzel (`KA`/`NS`/`NA`/`n. e.`), die Legende löst es auf. Die Legende erklärt die Skala einmal.

Die Platzierung ist neu:
- Die Kandidaten liegen rundum unmittelbar außerhalb der eigenen Umrandung, in fünf Abständen.
- Die Kosten zählen Knoten, Verbindungen, andere Labels, jede Umrandungslinie (mit kleinem Sicherheitsrand) und fremde
  Gruppenflächen. Flächen von Gruppen, die die eigene Gruppe umschließen, zählen nicht.
- Weitere Kosten: Abstand zur Gruppe und die Kreuzungen einer etwaigen Zuordnungslinie.
- Links und rechts der Karte bleiben 1,5 Zoll Rand (`G3_MARGIN_X`).
- Label- und Zuordnungsobjekte tragen eine `gid`, damit Tests die Platzierung prüfen können.

## 3. Visueller Befund (gerenderte PNGs, beide Fälle)

- **001 G1:** Familie oben links, Freund:innen unten, Bekannte rechts, A17 (professionell) oben rechts. Alle Kontakte liegen auf ihrem
  Nähering, alle IDs und Ringzahlen sind frei.
- **002 G1:** 32 Kontakte; die Typen bilden zusammenhängende Bereiche über alle Ringe; A22 ohne Nähe auf dem äußeren Bogen im
  Bekannten-Sektor. Keine Überlappungen.
- **001 G3:**
  - Alle sechs Labels sind kurz („C01 · Kreis 1 (6)“, Skala, Zahl) und stimmen mit `groups.csv` überein (1, 2, 3, 2, 4, 3).
  - C06 steht über seiner Umrandung, C05 links neben seiner.
  - C04 steht links neben dem Gruppenblock, mit kurzer Zuordnungslinie zur C04-Umrandung. Damit sind die drei Gruppen klar
    unterscheidbar.
  - Gruppen und Überschneidungen sind unverändert.
- **002 G3:** Alle Labels stehen an ihren Gruppen, auf keinen Knoten oder Linien. Werte stimmen (1, 2, 3, 3, 5).

## 4. Tests und Regression

- Volle Suite: **565 bestanden** (vorher 558).
- Neue oder angepasste Tests, G1:
  - Radius exakt = Nähe;
  - feste Sektorfolge auch bei fehlenden Typen;
  - Typen entlang jedes Rings nicht verschachtelt und im eigenen Sektor;
  - Layout unabhängig von der Zeilenreihenfolge;
  - keine Knotenüberlappung, Ringzahlen frei;
  - keine Sektorlinien oder -flächen.
- Neue oder angepasste Tests, G3:
  - Beschriftungstext ohne wiederholte Wörter;
  - Darstellungsname (Testzusatz, Kürzung, echter Klammerzusatz bleibt);
  - Labels nicht auf Knoten, Verbindungen oder anderen Labels, an der Umrandung oder mit kurzer Zuordnungslinie (< 1 Zoll), auch mit
    eingebetteter Gruppe;
  - fehlender Wert als `KA`.
- **G2 und P1–P5:** vor dem Run gehasht, nach `render-all` byteidentisch (12 PNG-Dateien).
- **`network_v0`:** in der vollen Suite enthalten, bestanden; kein v0-Code berührt.

## 5. Rendering

`render-all --root INTAKE --formats png,svg`: je 16 Dateien in `INTAKE:network_v1/pilots/<Fall>/graphics/`, gleiche Namen, keine
Zusatzversionen. Run-Records `RUN-20261031T180403Z-a4b1bf` (001) und `RUN-20261031T180406Z-83497e` (002). Die regulären G1/G3-Dateien
sind byteidentisch mit den geprüften Vorschauen. Diese lagen in einem eigenen Ordner unter `WORKSPACE:tmp/` und wurden nach Namen
gelöscht.

## 6. Status

| | G1 | G3 |
|---|---|---|
| implementiert | ja | ja |
| technisch getestet | ja | ja |
| visuell geprüft (Agent, beide Fälle) | ja | ja |
| wissenschaftlich abgenommen | nein | nein |

## 7. Verbleibende Punkte

- **G3 002:** Das Label von C02 hat keinen freien Platz direkt an der Umrandung (A06 und seine Verbindungen oberhalb, C03 unterhalb,
  Seitenrand links). Es steht darüber, angebunden mit einer etwa 0,7 Zoll langen senkrechten Zuordnungslinie.
- **G3 001:** Die Zuordnungslinie zu C04 kreuzt die Umrandungen von C05 und C06; unvermeidlich, weil C04 ganz in beiden liegt.
- **G3 allgemein:** Bei sehr vielen Gruppen ist die Platzierung nicht erprobt. Das Kraftlayout schließt eine lange Verbindung durch
  einen fremden Knoten weiterhin nicht grundsätzlich aus (siehe Vorlauf).
- **G1:** Bei vielen Kontakten eines Typs auf einem Ring kann der Sektor über seine Grenze hinaus geschoben werden; die Reihenfolge
  bleibt erhalten. In beiden Testfällen bleibt jeder Kontakt in oder direkt neben seinem Sektor.
- Ob die Sektoren als Gruppierung nach Beziehungstyp ohne zusätzliche Aussage gelesen werden, ist Teil der fachlichen Abnahme.
