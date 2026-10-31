# Run-Bericht 2026-10-31 – `network_v1`: Feinschliff G1, G2, G3

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §5–§6,
[`ADR-0007`](../decisions/ADR-0007_2026-10-31_netzwerk-v1-g1-g3.md). Vorlauf am selben Tag:
[`2026-10-31_network-v1-design-instrument.md`](2026-10-31_network-v1-design-instrument.md). Ortsangaben beschreiben den
Projektarbeitsplatz.

## 1. Ziel und Ausgangslage

Gezielte Überarbeitung von G1, G2 und G3 nach der Sichtprüfung an Testfall 001; P1–P5 gelten als vorläufig abgenommen und sollten
unverändert bleiben. Vorab: Working Tree sauber, `main` = `origin/main` (`6afcec8`), keine fremden Änderungen.

## 2. Änderungen

**G1** ([`networks.py`](../../src/mares/network_v1/figures/networks.py)): keine Kontakt-Kontakt-Linien mehr; Legende nur Beziehungstyp und
Nähe; ein Hinweis zur Lesart (Abstand = Nähe, Lage auf dem Ring ohne Bedeutung); keine Paarabdeckung. Das Kraftlayout entfällt: die
Kontakte eines Nähewerts liegen gleichmäßig auf ihrem Ring (ID-Reihenfolge, Platz für die Ringzahl oben, Zwischenringe um eine
Viertelteilung gedreht). Radius = erhobener Wert, unverändert. Die Quellenangabe von G1 im Grafikregister nennt Tabelle C nicht mehr.

**G2:** Kein Band und kein Kasten mehr für „Wohnort nicht zuordenbar“; die fünf Bänder nutzen die volle Breite. Kontakte ohne bestätigte
Verbindung stehen nur im Hinweis („Wohnort nicht zuordenbar: A17.“). Mit bestätigter Verbindung: eine Zeile unter den Bändern ohne Fläche
und Rahmen, beschriftet „Wohnort nicht zuordenbar (keinem Bereich zugeordnet):“, Linien gestrichelt wie zwischen Bereichen, in der
Legende getrennt gezählt („ohne Bereich (n)“). In keinem Testfall hat der Kontakt mit unbekanntem Wohnort eine bestätigte Verbindung
(in 002 ist A18–A22 `?`); der Sonderfall wurde deshalb mit einer Kopie von 002 (A18–A22 auf `1`) im `WORKSPACE` gerendert und geprüft und
ist als Test abgesichert; die Falldaten blieben unverändert. Nebenbefund durch die breiteren Bänder: In 002 lagen drei Untergruppen auf
einer Linie (die Verbindung A17–A16 lief durch A13), in 001 entsprechend A03–A02 durch A01. Behoben durch Versatz jeder zweiten Untergruppe
in Reihen mit drei oder mehr Untergruppen (`STAGGER`), so groß, dass auch die Ortsbeschriftung unter der Linie der Nachbarn liegt.

**G3:** einheitliche Umrandung (`OUTLINE_W`); Zugehörigkeit als fünfstufige Punktskala in der Beschriftung (`base.ordinal_dots`, Legenden-
eintrag `scale`; kein drittes Legendenlayout). Fehlende Werte: kein Punkt gefüllt, die Art des Fehlens benannt. Layout: eingebettete Gruppen
ohne eigenen Ankerplatz (in 001 liegt C04 jetzt in der Schnittfläche von C05 und C06 statt quer dazu); Ringmarkierungen nur, wo die
Umrandungen eine Mehrfachmitgliedschaft nicht schon zeigen (in 001 entfallen die drei Ringe an A04–A06, in 002 bleiben A09 und A12);
Kontakte ohne Gruppe und ohne Verbindung in einer Zeile unten (001: A13, A17, A18; 002: A23, A24) statt verstreut am Rand, was Fläche für
die Karte gewinnt. Labelplatzierung: Kosten für Knoten, Linien, fremde und eigene Umrandungen und den Abstand zur Gruppe; ein Label, das
nicht an seiner Gruppe liegen kann, bekommt eine feine Linie in der Gruppenfarbe. Fußnote gekürzt, keine Umrandungslegende mehr.

## 3. Ergebnisse je Testfall (visuell geprüft, alle drei Grafiken, beide Fälle)

- **001:** G1 ruhig, alle 22 Kontakte auf ihrem Nähering, alle IDs lesbar, Ringzahlen frei. G2 fünf Bänder, A17 nur im Hinweis. G3: C04/C05/C06
  klar unterscheidbar (C04 innen, C05 unten, C06 oben rechts); C04-Label mit Zuordnungslinie, weil die eingebettete Gruppe keinen freien
  Rand hat; alle Skalen stimmen mit `groups.csv` überein (C01 1, C02 2, C03 3, C04 2, C05 4, C06 3).
- **002:** G1 32 Kontakte, A22 ohne Nähe auf dem äußeren Bogen. G2 ohne sechstes Band, A22 im Hinweis. G3: Überschneidungen C02/C03 (A12)
  und C02/C04 (A09) mit Ringen nachvollziehbar; Skalen stimmen (C01 1, C02 2, C03 3, C04 3, C05 5).

## 4. Tests und Regression

- Volle Suite: **558 bestanden** (vorher 546). Neu bzw. umgeschrieben: G1 ohne Linien und ohne Paartexte, gleichmäßige Verteilung ohne
  Überlappung; G2 ohne Band für unbekannte Wohnorte, Sonderfall mit bestätigter Verbindung (36 Linien, Zeile unter den Bändern), keine
  kurze Linie durch einen dritten Knoten; G3 einheitliche Umrandung, genau ein gefüllter Punkt je Gruppe, `ordinal_dots` für 1/3/5/ohne
  Wert, fehlende Zugehörigkeit (KA) benannt, isolierte Kontakte außerhalb des Layouts, Ringmarkierung bei eingebetteten Gruppen.
- **P1–P5:** vor dem Run gehasht, nach dem Run neu gerendert – alle zehn PNG-Dateien byteidentisch. Die gemeinsamen Bausteine wurden nur
  ergänzt (`ordinal_dots`, Legendeneintrag `scale`, `_swatch_width`), nicht verändert.
- **`network_v0`:** in der vollen Suite enthalten, unverändert bestanden; kein v0-Code berührt.

## 5. Rendering

`render-all --root INTAKE --formats png,svg`: je 16 Dateien in `INTAKE:network_v1/pilots/<Fall>/graphics/`, gleiche Namen, keine
Zusatzversionen. Reguläre Läufe `RUN-20261031T161816Z-34d71d` (001) und `RUN-20261031T161819Z-19d875` (002); zwei kurz davor erzeugte
reguläre Läufe (vor der letzten G2-Korrektur) bleiben als Record bestehen. Vergleichsausgaben lagen in einem eigenen Ordner unter
`WORKSPACE:tmp/` und wurden nach Namen gelöscht.

## 6. Status

| | G1 | G2 | G3 |
|---|---|---|---|
| implementiert | ja | ja | ja |
| technisch getestet | ja | ja | ja |
| visuell geprüft (Agent, beide Fälle) | ja | ja | ja |
| wissenschaftlich abgenommen | nein | nein | nein |

Die fachliche Endabnahme erfolgt durch den Projektverantwortlichen anhand der gerenderten Grafiken.

## 7. Offene Punkte

- **G3 002:** Das Label von C02 liegt auf zwei Verbindungslinien (A06–A10, A06–A08) und am Rand der eigenen Umrandung; ohne Verschieben
  der Knoten gibt es dort keinen freien Platz. Weiß hinterlegt, lesbar.
- **G3 allgemein:** Das Kraftlayout verhindert nicht, dass eine lange Verbindung durch einen fremden Knoten läuft (in der Sonderfall-Kopie:
  A26–A25 durch A27). In beiden echten Testfällen tritt es nicht auf.
- **G3 001:** Die Zuordnungslinie des C04-Labels kreuzt die Umrandungen von C05 und C06.
- **G2:** Der Versatz verlängert die obere Zone etwas; bei vielen Untergruppen in einem Band nicht geprüft.
- Ob die Punktskala ohne Erläuterung als einzelne Selbsteinschätzung gelesen wird, ist Teil der fachlichen Abnahme.
