# Visualisierungskonventionen

**Status: verbindlich für die Grafiken des Netzwerkmoduls.** Gemeinsame Regeln, damit Abbildungen
verschiedener Fälle und Jahrgänge vergleichbar bleiben. Code:
[`src/mares/networks/figures/style.py`](../../src/mares/networks/figures/style.py) (Konventionen),
[`common.py`](../../src/mares/networks/figures/common.py) (Ring-Layout),
[`layouts.py`](../../src/mares/networks/figures/layouts.py) und [`network.py`](../../src/mares/networks/figures/network.py)
(Netzwerkfiguren), [`ego_layouts.py`](../../src/mares/networks/figures/ego_layouts.py) und [`ego_network.py`](../../src/mares/networks/figures/ego_network.py) (Ego im Netzwerk, B3),
[`geo_zones.py`](../../src/mares/networks/figures/geo_zones.py) (geografische Zonen G1/G2),
[`design.py`](../../src/mares/networks/figures/design.py) (Designsystem, §3.4) und
[`perspectives.py`](../../src/mares/networks/figures/perspectives.py) (analytische Perspektiven P1–P3, §3.5),
[`geo_network.py`](../../src/mares/networks/figures/geo_network.py) (geografische Beziehungsnetze G2-A/G2-B, §3.7) und
[`registry.py`](../../src/mares/networks/figures/registry.py) (Abbildungsregister und Gliederung, §3.8). Geografische Klassifikation:
[`geographic-classification.md`](geographic-classification.md). Modul: [`network-module.md`](network-module.md).

Methodische Orientierung: Vacca et al. (2016), *A personal network approach to the study of immigrant structural
assimilation and transnationalism*, Abb. 2: das Netzwerk ohne Ego als kraftbasierter Graph, kleine Knoten, dünne
Linien, getrennte Teilnetze frei positioniert. Übernommen wird das Darstellungsprinzip – **Zusammensetzung des
Netzwerks und Struktur der Beziehungen aus den Beziehungen selbst**. Nicht übernommen werden deren Kategorien,
Kontaktzahl, Messinstrumente und Ergebnisse; maßgeblich sind die in MARES erhobenen Kategorien.

## 1. Grundsätze

1. **Eine Variable, eine Farbe.** Dieselbe Größe hat in jeder Abbildung dieselbe Farbe und dasselbe Symbol; eine Farbe
   ändert nie ihre Bedeutung zwischen Abbildungen.
2. **Zeigen, was belegt ist.** Nicht dokumentierte Beziehungen sind unbekannt und werden nicht gezeichnet; es werden
   keine Verbindungen zwischen Teilnetzen ergänzt, kein Layoutverfahren fügt eine Linie hinzu. Abstände und Anordnung
   haben nur dort Bedeutung, wo die Legende es sagt.
3. **Jede Abbildung nennt ihren Status.** Profil `clean`: die Kurzkennung `MARES · 001-2 · vorläufig` (Fall und: Daten nicht geprüft). Profil `analysis`: Fußzeile mit Quelle, Sitzung,
   Erhebungsart, Zahl der Kontakte und Datenqualität (`UNREVIEWED`); bei Beziehungen dazu, wie sie erhoben wurden und dass für die übrigen Paare keine Angabe vorliegt. Der **vollständige** Status
   (Quelle, Sitzung, Erhebungsart einschließlich studentischer Herkunft, Paarabdeckung, Datenqualität) steht je Lauf in `figures/figures_index.json`. Eine Freigabe wird durch eine Abbildung nie behauptet.
4. **Keine Prüfmarkierungen an Kontakten.** Gestrichelte Ränder oder Symbole für Datenprüfhinweise vermischen Datenprüfung
   mit Netzwerkeigenschaften und stehen in keiner Abbildung. Die Datenqualität steht im Prüf- und Reviewbericht und in
   der Statuszeile.
5. **Nur IDs, Codes und Aggregate.** Keine Klarnamen, keine Freitexte, keine Review-Beschreibungen, keine Gruppennamen
   der Quelle, keine Rohwerte mehrdeutiger Angaben. Wohnorte erscheinen als angegebener Ortsname; regionale Angaben als
   „Region X“.
6. **Reproduzierbar**: feste Seeds, sortierte Reihenfolgen, die mitgelieferte Schrift (DejaVu Sans), keine Zeitstempel oder
   Softwarekennungen in den Dateien. Gleiche Eingabe ergibt byteidentische Dateien, auch zwischen Prozessen (getestet).
7. **Kategorien beschreiben Orte und Praktiken, keine Menschengruppen.** Wohnland und Geburtsland werden nicht zu
   „Herkunftsgruppen“ zusammengefasst; ein mehrdeutiges Geburtsland ist `mehrdeutig` und wird nie einem Land zugeschlagen.
8. **Gruppen sind erhobene Gruppen.** Sie heißen nie „Communities“ und werden nicht von einem Algorithmus entdeckt.

## 2. Farben und Symbole

| Größe | Kodierung | Quelle |
|---|---|---|
| Wohnort (fünf Stufen) | Marburg (bzw. der Referenzort) dunkelblau `#0072B2`; Region Marburg mittelblau `#56B4E9`; übriges Deutschland hellblau `#C3DAEC` mit dünnem Rand; **übriges Europa hellorange `#F3D49A` mit dünnem Rand**; **außerhalb Europas orange `#E69F00`**; nicht zuordenbar grau `#9A9A9A` | Okabe-Ito; Blautöne = Deutschland (abgestuft nach Nähe zum Referenzort), Orangetöne = Ausland (hell = Europa) |
| Sprache | Spanisch `#882255`, Deutsch `#332288`, Englisch `#DDCC77`, Portugiesisch `#44AA99`, andere `#999933` | Paul Tol (muted), nach Codebuchcode |
| Sprachmodus | Modi 1–3 in der Farbe ihrer Sprache; Mischung dunkelgrau, situationsabhängig hellgrau, anderer Modus weiß mit gestricheltem Rand (**Wert**, kein Prüfhinweis) | wie Sprache |
| Erhobene Kontaktgruppe | eigene Farbfolge, nur in Gruppenabbildungen: `#117A8B`, `#D55E00`, `#CC79A7`, `#7A5195`, `#8C6D31`, `#7BA600` (nach Gruppen-ID) | Okabe-Ito/Tol |
| Bestätigte Beziehung | dünne Linie (0,75 pt) in `#7D8892` | – |
| Ego (Ringfiguren, B3) | dunkler Kreis „EGO“ (in den Ringen im Zentrum, in B3 größer als ein Kontakt); **keine** geografische Kategorie | – |
| Ego–Kontakt-Linie (B3, G2, P2) | sehr dünne, helle Linie (0,55 pt) in `#CAD1D8`, unter allen anderen Linien (Profil `clean`; `analysis` bei B3 wie zuvor `#C5CCD3`) | – |
| Hervorgehobene / zurückgenommene Beziehung (G2) | hervorgehoben `#1F2933`, 1,8 pt; zurückgenommen `#AEB8C2`, 0,7 pt | Designsystem (§3.4) |
| Kontakt außerhalb einer Hervorhebung (P1–P3) | helles Grau `#E6E9ED` mit grauem Rand | Designsystem (§3.4) |
| Keine Angabe (P2) | weiß mit grauem Rand – nie die Farbe einer Kategorie | Designsystem (§3.4) |

Beschriftungen wählen Schwarz oder Weiß nach Kontrast (WCAG-Luminanz), helle Füllungen bekommen einen dünnen dunklen
Rand. Alle Farben sind durch Beschriftung oder Legende gedeckt, nie allein bedeutungstragend.

## 3. Die Abbildungen

| Datei | Inhalt | Besonderheit |
|---|---|---|
| `fig_A_ego_naehe_wohnort` | Ego im Zentrum, fünf Nähezonen nach **Tabellenwert** 1–5, Kontakte als Punkte mit ID, Farbe = Wohnort | Radius nur aus dem Tabellenwert, nie aus der Kartenposition; Winkel/Reihenfolge innerhalb einer Zone rein darstellerisch; leere Zone bleibt sichtbar; Kontakte ohne Wert in einem eigenen äußeren Band („?“), nie in einer Zone |
| `fig_B1_netzwerkstruktur` | Kontakte als kleine Knoten, bestätigte Beziehungen als dünne Linien, Position aus einem kraftbasierten Layout, Ego nicht eingezeichnet | Knotenfarbe = Wohnort; IDs neben den Knoten (Kollisionsvermeidung); getrennte Teilnetze und Kontakte ohne bestätigte Beziehung stehen frei; Statuszeile nennt Teilnetze und Kontakte ohne Beziehung |
| `fig_B2_netzwerkstruktur_gruppen` | dasselbe Netzwerk **mit identischen Positionen**, dazu die erhobenen Kontaktgruppen als weiche Flächen | Fläche je Gruppe, größere Gruppen mit mehr Polster, sodass verschachtelte und überlappende Gruppen als Überlappung erkennbar bleiben; Gruppenkürzel an der Fläche, frei von ID-Beschriftungen; die Abbildung nennt Kontakte, die im Layout in einer fremden Gruppenfläche liegen |
| `fig_B0_layoutvergleich` | dasselbe Netzwerk in drei Layoutverfahren mit Lesbarkeitsmaßen | Arbeitsabbildung; dokumentiert die Wahl des Layouts |
| `fig_B3_ego_netzwerk` | (Referenz des Designsystems, Profile `clean` und `analysis`, §3.4) Ego als dunkler Knoten, alle Kontakte, je eine helle Ego–Kontakt-Linie, dazu die bestätigten Kontakt–Kontakt-Beziehungen wie in B1/B2; erhobene Gruppen als sehr weiche Flächen | **Kontakte an denselben Positionen wie in B1/B2**, Ego ergänzt (§3.2); zwei Linienarten (hell, dünn = Zugehörigkeit zum Netz; dunkler = erhobene Beziehung), getrennte Legendeneinträge; keine Kennzahl und keine Kante wird aus Ego abgeleitet |
| `fig_B3_0_layoutvergleich` | dasselbe persönliche Netzwerk in drei Ego-Layouts mit Lesbarkeitsmaßen | Arbeitsabbildung; dokumentiert die Wahl des B3-Layouts |
| `fig_G1_geografische_zonen` | Ego im Zentrum, fünf konzentrische Zonen nach Wohnortkategorie (Marburg, Region Marburg, übriges Deutschland, übriges Europa, außerhalb Europas), Kontakte als Punkte mit ID in der Farbe ihrer Kategorie | keine Karte, kein Kilometermaß: die Zone ist die Kategorie; Ringbreiten folgen der Kontaktzahl; Winkel gleichmäßig, nur nach Wohnort und ID sortiert; leere Zone bleibt sichtbar, „unbekannt“ nur bei Bedarf als fünftes, gestricheltes Band; Orte je Zone in der Legende |
| `fig_G2b_geografisches_kraftlayout` | **G2-B (Kandidat, `core`)**: Ego als Bezugspunkt im Zentrum (ohne Linien), fünf radiale Zonen (konzentrische Ellipsen), Kontakte im kraftbasierten Layout der bestätigten Beziehungen, Radius an die Zone gebunden; Beziehungen zwischen den Zonen dunkel, innerhalb hell (§3.7) | radialer Abstand = Wohnort-Kategorie, nicht Kilometer, Nähe oder graphentheoretische Distanz; Abstände zwischen den Zonen sind Konvention; keine Gruppenflächen |
| `fig_G2a_geografische_baender` | **G2-A (`supplementary`)**: fünf Bänder von links (nah) nach rechts (fern), Breite folgt der Kontaktzahl, Höhe der Reihenfolge der sozialen Struktur; keine Ego-Linien (§3.7) | Bänder sind Kategorien; die Höhe im Band zeigt keine Nähe |
| `fig_G2_0_variantenvergleich` | frühere Varianten G2a (Ringe) und G2b (gleich breite Bänder, mit Ego-Linien) nebeneinander mit Lesbarkeitsmaßen | `diagnostic`; dokumentiert die frühere Wahl |
| `fig_G2_1_vergleich_a_b` | G2-A und G2-B nebeneinander mit Lesbarkeitsmaßen (Kreuzungen, Knotenabstand, Gruppenkompaktheit) | `diagnostic`; dokumentiert die Wahl des Kandidaten |
| `fig_G2_geografisches_beziehungsnetz` | frühere G2-Fassung (gleich breite Bänder, **mit** Ego-Linien) | `diagnostic`, nur zur Nachvollziehbarkeit erhalten |
| `fig_P1_distanz_und_naehe` | Matrix: Spalten = Wohnort-Kategorie, Zeilen = erhobene Nähe (Tabellenwert 5 … 1), ein Chip je Kontakt in der Farbe seiner Kategorie (§3.5) | keine Kilometerskala, keine geschätzte Nähe; Kontakte ohne Wert in der Zeile „nicht erfasst“; leere Zeilen und Spalten bleiben sichtbar |
| `fig_P2_sprachliche_praktiken` | Struktur-Layout von B2/B3 (Positionen unverändert), erhobene Gruppen als weiche Flächen, Sprachansicht (`--language-view`) färbt Kontakte und Ego–Kontakt-Linien (§3.5) | Sprache gehört zur Beziehung Ego–Kontakt, nicht zwischen Kontakten; Sprachmodus und genannte Sprachen getrennt; Mehrsprachigkeit bleibt (Ring bzw. eigene Ansicht); keine Angabe = weiß |
| `fig_P3_einbettung_und_kommunikation` | Matrix: Spalten = Wohnort-Kategorie, Zeilen = Kontakthäufigkeit (insgesamt), Symbole auf dem Chip = genannte Medien ● persönlich, ▲ Telefon, ■ digital (§3.5) | Medien sind Mehrfachangaben; die Häufigkeit gilt nicht je Medium; keine Kausalaussage |
| `fig_C_geografisches_profil` | Kontakte nach Wohnort-Kategorie und Ort, Geburtsland laut Angabe; Matrix Wohnland × Geburtsland | Region Marburg unter Marburg; „mehrdeutig“ als eigene Spalte; Zählung von Kontakten |
| `fig_D1_sprachprofil` | Matrix Kontakt × Sprache, Sprachmodus, Sprachrepertoires, Modus × Beziehungstyp | mehrere Sprachen bleiben mehrere; keine Hauptsprache; Modus 5/6 bleiben erhoben |
| `fig_D2_ego_sprachmodus` | dasselbe Layout wie A, Farbe = Sprachmodus, Kürzel der Sprachen unter dem Punkt | ein Kontakt liegt in A und D2 am selben Ort; Kürzel in Codebuchreihenfolge = keine Rangfolge |
| `fig_E_deskriptive_uebersicht` | acht Balkendiagramme: Aufenthaltsorte, Beziehungstypen, Kontakthäufigkeit, Nähe, Sprachen, Sprachmodus, Medien, Funktionen | explorativ; leere Kategorien sichtbar; Mehrfachnennungen gekennzeichnet |

**Nähe:** Die fünf Zonen tragen die Bedeutung des Codebuchs (`closeness_1_5`: 1 überhaupt nicht nah … 5 sehr nah). Eine
abweichende Legende der Netzwerkkarte wird nicht auf eine vierstufige Skala umgerechnet.

### 3.1 Das kraftbasierte Layout (B0–B2)

Die Position eines Knotens ergibt sich **allein aus den bestätigten Beziehungen**: keine Ringe, keine vorgegebenen
Gruppenkoordinaten, keine Gruppenrahmen als Layout. Drei Verfahren werden verglichen (alle nur mit NumPy,
deterministisch, fester Seed):

| Verfahren | Wirkung auf unverbundene Teilnetze |
|---|---|
| Spring (Fruchterman–Reingold) | Teilnetze stoßen sich ab und wandern an den Rand; sie werden zusammengedrückt |
| **Stress-Majorisierung** (SMACOF, ≈ Kamada–Kawai; mehrere deterministische Starts, der niedrigste Stress gewinnt) | unverbundene Paare erhalten den Abstand *Durchmesser + 1*: Teilnetze bleiben groß und in einem Bild, ohne Verbindung zu behaupten |
| ForceAtlas2 (mit Schwerkraft) | kompakter, empfindlich gegenüber Parametern |

Gewählt ist die **Stress-Majorisierung**: längste Beziehungslinien relativ zum Bild, keine sich berührenden Knoten,
Kreuzungen auf ähnlichem Niveau wie die anderen Verfahren, stabil. Kreuzungen bleiben bei überlappenden Cliquen unvermeidlich (eine Clique aus sechs Kontakten kreuzt sich in jeder Geradlinien-Zeichnung). Das Bild wird auf
die Hauptachse gedreht und normiert; der Abstand zwischen getrennten Teilnetzen hat keine Bedeutung, und das steht in
der Abbildung.

### 3.2 Ego im Netzwerk (B3)

B3 ergänzt **eine** Perspektive: Ego und alle Kontakte mit ihren erhobenen Beziehungen in einem Graphen. Die vier Abbildungen
beantworten verschiedene Fragen und ersetzen einander nicht: **A** subjektive Nähe zu Ego (Tabellenwert), **B1** Struktur
der Kontakt–Kontakt-Beziehungen, **B2** dieselbe Struktur mit den erhobenen Gruppen, **B3** das persönliche Netzwerk einschließlich Ego.

**Layout.** Drei Varianten wurden verglichen (`fig_B3_0_layoutvergleich`; alle deterministisch, nur NumPy):

| Variante | Idee | Befund am Pilotfall |
|---|---|---|
| **A · Kontakte wie in B2, Ego ergänzt** (gewählt) | die Kontakte behalten die Positionen von B1/B2; Ego wird nahe dem Schwerpunkt dort gesetzt, wo seine Linien die wenigsten Beziehungen kreuzen und keinen Kontakt streifen (festes Raster, deterministisch) | Struktur wie B2 = 1,00; 60 Kreuzungen (27 durch Ego-Linien); 0 gestreifte Kontakte; Ego nah an der Mitte |
| B · gemeinsames gewichtetes Layout | Stress-Majorisierung aller Knoten; Ego–Kontakt-Strecken länger (2,0) und mit 0,2 gewichtet | Struktur wie B2 = 0,89; 62 Kreuzungen; 1 gestreifter Kontakt; Ego genau in der Mitte, Gruppen rücken zusammen |
| Referenz · Ego als gewöhnlicher Knoten | alle Strecken gleich | Struktur wie B2 = 0,80; 71 Kreuzungen; 2 gestreifte Kontakte; die Gruppen werden zusammengezogen – der erwartete Nachteil |

Gewählt ist **A**: Die Kontakt–Kontakt-Struktur bleibt identisch zu B1/B2 (Vergleichbarkeit der Abbildungen, kein neuer Eindruck von
Gruppenzusammenhalt), die Überlappung der verschachtelten Gruppen bleibt erkennbar, es gibt die wenigsten Kreuzungen und keine
Ego-Linie läuft durch einen Kontakt. Ego liegt nicht zwanghaft im Mittelpunkt, aber klar im Zentrum zwischen den Teilnetzen. Die
Gruppenflächen werden in B3 sehr weich (Füllung 7 %) gezeichnet; sie stören die Linien nicht. Bei sehr dichten Netzen ist
`show_groups=False` die Rückfallebene.

**Interpretation.** B3 zeigt zwei Dimensionen: die *Zugehörigkeit zum persönlichen Netzwerk* (Ego–Kontakt) und die *erhobenen Beziehungen*
(Kontakt–Kontakt). Die dritte, die *subjektive Nähe*, zeigt nur Abbildung A. Folgerungen, die B3 ausschließt und die in der Abbildung stehen:
(1) die Entfernung eines Kontakts zu Ego im Bild ist **kein Maß der Nähe**; (2) der Abstand zwischen getrennten Gruppen ist keine soziale oder
geografische Distanz; (3) weil Ego alle Kontakte verbindet, ist der Graph **zwangsläufig zusammenhängend** – das ist kein Befund über die
Vernetzung der Kontakte; (4) Strukturmaße, falls sie berechnet werden dürfen, beruhen auf dem Netz **ohne** Ego (B1/B2).

### 3.3 Geografische Zonen (G1, G2)

Die Abbildungen G1/G2 ergänzen eine **dritte Dimension**: die *räumliche Einordnung des Wohnorts relativ zu Ego*. Sie unterscheidet sich von
subjektiver Nähe (A), von der Struktur der Kontakt–Kontakt-Beziehungen (B1–B3) und vom Wohnort-Profil als Tabelle (C). **Fünf Stufen** (Regeln:
[`geographic-classification.md`](geographic-classification.md)): `Marburg` bei exakt genanntem Ort; `Region Marburg` für regionale Angaben wie „Nähe Marburg“; `übriges Deutschland`;
`übriges Europa`; `außerhalb Europas` – dazu ein Band „nicht zuordenbar“ nur, wenn ein Wohnort keinem Land zugeordnet werden kann. **Die Lage im Bild ist die Kategorie** – nicht die Entfernung in
Kilometern, nicht die Nähe zu Ego, nicht ein Netzwerk-Layout; das steht in jeder dieser Abbildungen.

**Frühere Wahl von G2 (überholt durch §3.7, hier zur Nachvollziehbarkeit).** Verglichen wurden G2a (Kontakte in den Ringen von G1, Linien dazwischen) und G2b (vier Bänder). Gewählt ist **G2b**:

| | G2a · Ringe | G2b · Bänder (gewählt) |
|---|---|---|
| Kreuzungen (Pilotfall) | 37 | 30 |
| Knotenabstand relativ zur Beziehungslänge | 0,49 | 0,98 |
| Eindruck | die Linien einer Gruppe bündeln sich in einem Ringabschnitt; Beschriftungen und Linien konkurrieren | klare Staffelung von Marburg bis außerhalb; Beziehungen zwischen Zonen sind gut verfolgbare, waagerechte Linien, Beziehungen innerhalb einer Zone senkrechte |

Die Bänder zeigen zugleich, ob Beziehungen **innerhalb** oder **zwischen** den Zonen verlaufen, ohne etwas zu erfinden: Beide Linienarten sind genau die bestätigten
Beziehungen, aufgeteilt nach den Zonen ihrer zwei Kontakte. Die Ego–Kontakt-Linien (hell, dünn) sind wie in B3 Zugehörigkeitslinien und bleiben
unter den Beziehungen. Erhobene Gruppen werden in G1/G2 **nicht** gezeichnet: Flächen über Ringen oder Bändern würden Kontakte anderer Zonen umschließen und Mitgliedschaft
vortäuschen; B2 und B3 zeigen die Gruppen. Weitere Kodierungen (Symbole nach Beziehungstyp, Geburtsland am Knoten) wurden verworfen, um die Zonen nicht zu überladen;
Geburtsland steht in C.

### 3.4 Das Designsystem (`design.py`)

Ein einheitliches Erscheinungsbild für die Abbildungen B3, G2-A/G2-B und P1–P3; die älteren Abbildungen (A, B1, B2, G1, C, D1, D2, E) tragen es **nur im Rahmen**: kurzer Titel, ein Hinweis,
Kurzkennung, Legenden ohne Fallzahlen, Klammerbemerkungen und Ortslisten (`design.frame_for`, `design.lean_sections`); im Profil `analysis` behalten sie ihren früheren Wortlaut. Grundgedanke: **eine Abbildung beantwortet eine Frage; alles andere steht in der Dokumentation und in `figures/figures_index.json`.**

**Profile.** `clean` (Standard, in `figures/<tier>/`) für Präsentation und Veröffentlichung; `analysis` (in `figures/analysis/<tier>/`) für die Arbeit. Nur `diagnostic`-Abbildungen haben ein einziges Aussehen. Beide zeigen
dieselben Daten im selben Layout; `analysis` ergänzt die längeren Erläuterungen, Fallzahlen (`n =`) und die ausführlichere Statuszeile.

| Baustein | `clean` | `analysis` |
|---|---|---|
| Titel | kurz und sachlich (z. B. „Persönliches Beziehungsnetz“), 16 pt fett | gleich (B3, G2: die ausführlichen Titel der bisherigen Abbildungen) |
| Untertitel | höchstens einer, knapp, grau (oder keiner), 10 pt | gleich |
| Legende | ein kompakter Streifen unter dem Titel (Punkt, Ring, Linie, Fläche, Zeichen), nur Einträge, die vorkommen; was direkt beschriftet ist (Zonen, Bänder), steht nicht noch einmal in der Legende | ergänzt Fallzahlen |
| Hinweis | **ein** kurzer Absatz am Fuß mit der wichtigsten Lesegrenze | zusätzlich die längere Notiz (Kodierung, Grenzen) |
| Herkunftszeile | `MARES · 001-2 · vorläufig` | ausführlich („Quelle …“, Sitzung, Erhebungsart, n, UNREVIEWED) |
| Zonen/Bänder | direkt beschriftet, kurze Namen (ohne „ungefähre Angabe“) | wie `clean`, mit Fallzahl |

**Zentrale Parameter** (Konstanten in `design.py`; kein Wert ist in den Abbildungen verstreut): **vier Schriftgrößen** – Titel 16 pt, Text 10 pt (Untertitel, Beschriftungen, Legende, Hinweis),
Kontakt-IDs 9 pt, klein 8 pt (Herkunftszeile, Notizen des Profils `analysis`) –, nur Regular und Bold; Knoten 12,5 pt, Ego 26 pt, Linienbreiten (Beziehung 0,8, hervorgehoben 1,8, zurückgenommen 0,7,
Ego–Kontakt 0,55 pt), Farben für Hervorhebung (`#1F2933`, `#AEB8C2`, `#CAD1D8`) und zurückgenommene Kontakte (`#E6E9ED`), Deckkraft der Gruppenflächen.
Die Paletten der Variablen (Wohnort, Sprache, Gruppen) bleiben in `style.py`.

**Schrift.** Gewünscht war *Source Sans 3*; sie ist auf dem Arbeitsplatz nicht vorhanden und wird **nicht** ins Repository aufgenommen. Es gilt
DejaVu Sans (liegt Matplotlib bei, überall identisch, byte-reproduzierbar), nur Regular und Bold. Eine spätere Schrift ändert nur diese Festlegung
in `style.py`; sie muss dann auf jedem Rechner verfügbar sein oder mitgeliefert werden.

**Hervorhebung.** Jede Hervorhebung (Beziehungsart in G2, Sprache/Modus in P2, Kontakt-IDs in P1/P3) ändert nur Farbe, Stärke und Reihenfolge der
Zeichnung: **keine** Position, kein Kontakt und keine Beziehung wird verändert, ergänzt oder ausgeblendet; was zurücktritt, bleibt sichtbar.

**Bausteine für spätere Auswertungen.** Basislayout (B2/B3-Struktur, G2-Bänder, Matrix) + Attributdarstellung (Farbe, Ring, Symbol) + analytische
Hervorhebung (Menge von Kontakt-IDs, Sprache, Beziehungsart). Kontakt-IDs sind stabil (`A01` …), und die Hervorhebungsmenge `highlight` in P1/P3 adressiert
Kontakte über sie. Ein Modell für narrative Verknüpfungen gibt es **nicht**.

**Verallgemeinerung.** Keine Zahl von Kontakten, Gruppen oder Zonen ist festgelegt; überlappende Gruppen, fehlende Merkmale und unvollständige
Alter-Alter-Angaben werden dargestellt wie in B2/B3. Der lokale Bezugsort ist `AnalysisParams.local_places` (`--local-place`), nicht „Marburg“.

### 3.5 Analytische Perspektiven P1–P3 (`perspectives.py`)

Jede Perspektive stellt **eine** Frage an jedes persönliche Netzwerk. Sie sind Sichten auf die erhobenen Merkmale, keine Ergebnisse und keine Tests.

| | P1 · Räumliche Einordnung und subjektive Nähe | P2 · Sprachliche Praktiken in sozialen Teilgruppen | P3 · Wohnort, Kontakthäufigkeit und Kommunikationsmedien |
|---|---|---|---|
| Frage | Wie verhalten sich die geografische Einordnung der Kontakte und ihre erlebte Nähe zu Ego zueinander? | Wie verteilen sich sprachliche Praktiken über die sozialen Teilgruppen des persönlichen Netzwerks? | Welche Rolle spielen Kontakthäufigkeit und Medien in lokalen und räumlich entfernten Beziehungen? |
| Basislayout | Matrix (Wohnort-Kategorie × Nähe) | Struktur-Layout B2/B3, Positionen konstant | Matrix (Wohnort-Kategorie × Kontakthäufigkeit) |
| Attribut | Farbe = Wohnort-Kategorie | Knoten = Sprachmodus oder Sprachverwendung; Ring = mehrere Sprachen; Ego–Kontakt-Linie in Sprachfarbe | Farbe = Wohnort-Kategorie; Symbole = Medien |
| Hervorhebung | Menge von Kontakt-IDs | `--language-view`: `mode`, `mode:<code>`, `lang:<code>` (z. B. Spanisch), `multilingual` | Menge von Kontakt-IDs |
| Gesucht | räumlich entfernte, aber sehr nahe Kontakte; lokal wohnende, eher periphere Kontakte | ob Gruppen sprachlich einheitlich oder gemischt sind; wo Spanisch genannt wird | transnationale Kontakte mit häufiger Kommunikation; lokal wohnende, digital erreichte Kontakte |

**Kodierung und Lesegrenzen.**
- **P1.** Spalten sind Kategorien, **keine Kilometer**; die Zeilen sind die erhobenen Tabellenwerte 5 … 1 (Codebuch `closeness_1_5`). Ein Kontakt ohne Wert steht
  in einer eigenen Zeile „nicht erfasst“, seine Nähe wird nie geschätzt. Leere Zeilen und Spalten bleiben sichtbar. Die Matrix wurde einem weiteren konzentrischen
  Netzwerkbild vorgezogen: Wohnort-Kategorie und Nähe sind zwei Ordinalmerkmale; ein Ringbild könnte nur eines als Abstand kodieren und die Kategorie als Distanz lesen lassen.
- **P2.** Die Sprache ist ein Merkmal der Beziehung *Ego–Kontakt*, nicht der Beziehung zwischen Kontakten – deshalb färbt die Ansicht Kontakte und Ego–Kontakt-Linien, nie
  die Kontakt–Kontakt-Linien. Der **Sprachmodus** (typischer Gebrauch, ein Wert) und die **genannten Sprachen** (Mehrfachangabe) sind getrennte Angaben: weder wird der Modus aus
  den Sprachen noch eine Hauptsprache aus mehreren Sprachen abgeleitet. In der Standardansicht (`mode`) ist die Füllung der Modus, ein Ring markiert mehrere genannte Sprachen. Kontakte ohne Angabe sind weiß
  mit grauem Rand (nicht „andere Sprache“). Die Positionen sind in allen Ansichten identisch zu B3.
- **P3.** Hauptaussage ist die Beziehung von Wohnort-Kategorie und Kontakthäufigkeit; Medien sind die zweite, leisere Ebene. Medien sind **Mehrfachangaben**; persönliche und digitale
  Kommunikation können zugleich vorkommen. Die Zuordnung der Codebuchcodes zu den Klassen persönlich / Telefon / digital steht in `perspectives.MEDIA_CLASSES` (instrumentenabhängig, dort zu ändern); nicht zugeordnete Codes
  („anderes Medium“) werden nicht markiert. Die Kontakthäufigkeit gilt für die Beziehung insgesamt, **nicht je Medium**; ein genanntes digitales Medium heißt nicht, dass die Beziehung überwiegend digital geführt wird.
  Ein Kontakt ohne Medienangabe trägt „–“.

**Interpretationsgrenzen (alle drei).** Konstellationen sichtbar machen, keine Ursachen behaupten; keine Inferenz aus einem einzelnen Fall; Kategorien sind Selbstangaben und Ortsklassen, keine Messwerte.

### 3.6 Wissenschaftliche und gestalterische Entscheidungen

*Wissenschaftlich* (ändern, was gezeigt oder behauptet wird; Änderung nur zusammen mit dieser Dokumentation): Wohnort als Kategorie statt Kilometer; Nähe nur als erhobener Tabellenwert; Matrix statt Ringbild für P1/P3;
Sprachmodus und genannte Sprachen getrennt; Sprache als Merkmal der Ego–Kontakt-Beziehung; Mehrfachangaben bleiben mehrfach; fehlende Angaben sichtbar und eigene Kategorie; Hervorhebung ändert nie Relationen; Medienklassen.

*Gestalterisch* (ändern, wie es gezeigt wird; ohne Folgen für die Aussage): Schrift, Größen, Legendenstreifen, kurze Titel, Linienstärken und -farben der Hervorhebung, Standardhervorhebung „zwischen Bereichen“ in G2,
Chipgröße und -anordnung, Seitenverhältnis.

### 3.7 Geografische Beziehungsnetze G2-A und G2-B

**Frage.** Wie sind lokale, überregionale und transkontinentale Beziehungen im persönlichen Netzwerk miteinander verflochten – welche sozialen Teilgruppen erstrecken sich über mehrere geografische Räume,
welche bestätigten Beziehungen verlaufen innerhalb, welche zwischen den Bereichen, und welche bestehen trotz räumlicher Trennung? Gemeinsam: dieselben fünf Stufen, genau die bestätigten
Kontakt–Kontakt-Beziehungen (der Pilotfall hat 41), **keine Ego–Kontakt-Linien** (Ego gehört nicht zum Graphen), Beziehungen **zwischen** den Bereichen dunkel und kräftig, **innerhalb** hell
(`--tie-highlight between|within|none`), Knotenfarbe = Wohnort-Kategorie.

| | G2-A · Bänder | G2-B · geografisch eingeschränktes Kraftlayout |
|---|---|---|
| Anordnung | fünf Bänder von links (nah) nach rechts (fern); **Breite folgt der Kontaktzahl** (ein Kontakt: schmales Band), Spalten bei vielen Kontakten; Höhe folgt der Reihenfolge der sozialen Struktur | Ego als Bezugspunkt im Zentrum; fünf radiale Zonen (konzentrische Ellipsen, dezente gepunktete Linien, sehr leichte Tönung jeder zweiten Zone, Zonennamen direkt in einer Lücke bei 12 Uhr); Kontakte per Kraftlayout |
| Verfahren | feste Regeln, deterministisch | Anziehung entlang der bestätigten Beziehungen (Ruhelänge: Abstand der Zonen bzw. Mindestabstand), Abstoßung aller Kontakte, Radius auf ein Fenster (30 % des Zonenabstands) um die Zonenmitte beschränkt; drei feste Starts (Kreisordnung der Beziehungsstruktur, gespiegelt, Winkel von B1/B2), der mit dem besten Wert (Abweichung + Überlappung + Kreuzungen) gewinnt; NumPy |
| Gruppen | nicht gezeichnet; sozial zusammengehörige Kontakte stehen auf ähnlicher Höhe | nicht gezeichnet; die Teilnetze erkennt man an der Knotenstruktur und an den Linien über die Zonengrenzen |
| Grenzen | Bänder sind Kategorien; die Höhe im Band zeigt keine Nähe | radialer Abstand = Wohnort-Kategorie, **nicht** Kilometer, subjektive Nähe oder graphentheoretische Distanz; Zonenabstände und die horizontale Streckung (1,3, nur Seitenformat) sind Konventionen |

**Vergleich am Pilotfall** (`fig_G2_1_vergleich_a_b`; 22 Kontakte, 41 Beziehungen, davon 11 zwischen den Bereichen):

| Maß | G2-A | G2-B |
|---|---:|---:|
| Kreuzungen | 24 | 30 |
| Knotenabstand (relativ zur mittleren Beziehungslänge) | 0,45 | 0,46 |
| Gruppenkompaktheit (kleiner = erhobene Gruppen bleiben zusammen) | 0,39 | 0,25 |

**Sichtprüfung.** G2-A ist ruhig und gut lesbar; die ID-Beschriftungen sind klar, die Verflechtung zwischen Deutschland und außerhalb Europas ist als Bündel waagerechter Linien erkennbar, aber die
Gruppen sind nur an der Höhe zu erkennen, und die Darstellung bleibt schematisch. G2-B zeigt die Teilnetze als zusammenhängende Gruppen mit ihren zonenübergreifenden Linien – das Teilnetz über Deutschland und außerhalb
Europas bleibt als Einheit erkennbar, die Marburger Gruppe bleibt kompakt; sie lässt allerdings mehr Fläche leer und hat etwas mehr Kreuzungen. **G2-B ist der Kandidat (`core`); G2-A bleibt `supplementary`.
Das endgültige Standardlayout bestimmt der Projektleiter.** Gruppenflächen werden in beiden nicht gezeichnet (sie würden Kontakte anderer Zonen umschließen und Mitgliedschaft vortäuschen; B2 und B3 zeigen sie).

**Interpretation.** Die Abbildungen zeigen Konstellationen, keine Erklärung ihrer Entstehung; die geografische Einordnung ist kein Maß sozialer Integration oder Segregation; die räumliche Trennung der Zonen
ist keine soziale Trennung; Paare ohne Linie sind unbekannt, solange die Paarabdeckung nicht belegt ist.

### 3.8 Gliederung des Abbildungsrepertoires

Die Gliederung betrifft das Abbildungsregister (`figures/figures_index.json`, Code `figures/registry.py`) und die Ausgabeordner `figures/<tier>/` (und `figures/analysis/<tier>/`); Funktionen und Daten bleiben unverändert und reproduzierbar.

| Tier | Abbildungen | Zweck |
|---|---|---|
| `core` | B3 persönliches Netzwerk und Gruppen · G2 geografische Verflechtung (Kandidat G2-B) · P1 geografische Einordnung und Nähe · P2 sprachliche Praktiken in Teilgruppen | das visuelle Fallporträt |
| `supplementary` | A Nähe und Wohnort · B1, B2 Struktur ohne/mit Gruppen · G1 geografische Zonen · G2-A Bänder · P3 Wohnort, Häufigkeit, Medien · C Wohnort und Geburtsland · D1 Sprachprofil · D2 Sprachmodus nach Nähe · E Übersicht | ergänzende analytische Ansichten und deskriptive Übersichten |
| `diagnostic` | B0, B3-0 Layoutvergleiche · G2-0, G2-1 Variantenvergleiche · frühere G2-Fassung mit Ego-Linien | technische Entwicklungs- und Prüfabbildungen |

## 4. Formate und Qualität

SVG (Text als Pfade, damit die Schrift nicht von der Maschine abhängt), PNG (200 dpi), PDF (eingebettete Schrift). Die
Größe richtet sich nach dem Inhalt. Jede Abbildung wird nach dem Erzeugen angesehen; Beschriftungskollisionen werden
behoben, nicht hingenommen. Die Tests prüfen Reproduzierbarkeit (auch zwischen Prozessen), fehlende Zeitstempel,
Textinhalt (keine Notizen, Freitexte, Prüfmarkierungen), die Zahl der gezeichneten Linien (= bestätigte Beziehungen),
gleiche Positionen in B1 und B2, Unabhängigkeit des Layouts von Attributen und Gruppen, Kollisionsfreiheit der
ID-Beschriftungen und die Zonenlage. Für das Designsystem außerdem: `clean` ist knapper als `analysis` bei gleichen Daten, Hervorhebung ändert weder Positionen noch Beziehungen,
jeder Kontakt steht in genau einer Matrixzelle, fehlende Werte stehen in „nicht erfasst“, die Sprachansicht ändert keine Position, der Bezugsort ist konfigurierbar, beliebige Kontaktzahlen werden gezeichnet,
Dateien sind auch zwischen Prozessen byteidentisch, und kein Freitext gelangt in die Bilder. Für G2: fünf Stufen, genau die bestätigten Beziehungen, keine Ego-Linien, der Radius jedes Kontakts bleibt im
Fenster seiner Zone, der Sektor der Zonennamen bleibt frei, Gruppenkompaktheit, ungewöhnliche Verteilungen (nur lokal, nur transkontinental, sehr ungleich, fehlende Wohnorte), 1 bis 100 Kontakte, Unabhängigkeit vom Hash-Seed;
für die Gliederung: jede Abbildung in genau einem Tier, ein Kandidat, Register mit Frage und Grenzen, beide Profile reproduzierbar. Die Lesbarkeit prüft eine Person (Sichtprüfung der echten Abbildungen im Arbeitsbereich).

## 5. Neue Abbildungen

Eine neue Abbildung benutzt die Paletten und Zeichen oben, trägt die Fußzeile (`frame`), bezieht Kontaktmerkmale über
`contact_views` und ergänzt diese Tabelle. Eine neue Variable bekommt eine Farbe, die zu keiner vorhandenen
Variablen gehört, und wird hier eingetragen.
