# Visualisierungskonventionen

**Status: verbindlich für die Grafiken des Netzwerkmoduls.** Gemeinsame Regeln, damit Abbildungen
verschiedener Fälle und Jahrgänge vergleichbar bleiben. Code:
[`src/mares/networks/figures/style.py`](../../src/mares/networks/figures/style.py) (Konventionen),
[`common.py`](../../src/mares/networks/figures/common.py) (Layout). Modul: [`network-module.md`](network-module.md).

Methodische Orientierung: Vacca et al. (2016), *A personal network approach to the study of immigrant structural
assimilation and transnationalism*. Übernommen wird die Grundidee, **Zusammensetzung des persönlichen Netzwerks
und Gruppenstruktur** zu zeigen. Nicht übernommen werden deren Kontaktzahl, Messinstrumente und quantitativen
Auswertungen.

## 1. Grundsätze

1. **Eine Variable, eine Farbe.** Dieselbe Größe hat in jeder Abbildung dieselbe Farbe und dasselbe Symbol; eine Farbe
   ändert nie ihre Bedeutung zwischen Abbildungen.
2. **Zeigen, was belegt ist.** Nicht dokumentierte Beziehungen sind unbekannt und werden nicht gezeichnet; es werden
   keine Verbindungen zwischen Gruppen ergänzt. Abstände und Anordnung im Bild tragen nur dort Bedeutung, wo die
   Legende es sagt.
3. **Jede Abbildung nennt ihren Status**: Fußzeile mit Quelle, Sitzung, Erhebungsart, Zahl der Kontakte und
   Datenqualität (`UNREVIEWED`); dazu der Hinweis auf die unvollständige Alter-Alter-Erhebung, wo Beziehungen gezeigt
   werden. Die studentische Herkunft bleibt in der Erhebungsart sichtbar.
4. **Nur IDs, Codes und Aggregate.** Keine Klarnamen, keine Freitexte, keine Review-Beschreibungen, keine Gruppennamen
   der Quelle. Wohnorte erscheinen als angegebener Ortsname; ungefähre Angaben werden nicht präzisiert.
5. **Reproduzierbar**: feste Seeds, kein Zufall, die mitgelieferte Schrift (DejaVu Sans), keine Zeitstempel oder
   Softwarekennungen in den Dateien. Gleiche Eingabe ergibt byteidentische Dateien (getestet).
6. **Kategorien beschreiben Orte und Praktiken, keine Menschengruppen.** Wohnland und Geburtsland werden nicht zu
   „Herkunftsgruppen“ zusammengefasst; keine ethnische oder nationale Lesart.

## 2. Farben und Symbole

| Größe | Kodierung | Quelle |
|---|---|---|
| Wohnort | Marburg (bzw. der Referenzort) = dunkelblau `#0072B2`; übriges Deutschland = hellblau `#56B4E9`; außerhalb Deutschlands = orange `#E69F00`; unbekannt = grau `#9A9A9A` | Okabe-Ito |
| Sprache | Spanisch `#882255`, Deutsch `#332288`, Englisch `#DDCC77`, Portugiesisch `#44AA99`, andere `#999933` | Paul Tol (muted), nach Codebuchcode |
| Sprachmodus | Modi 1–3 in der Farbe ihrer Sprache; Mischung dunkelgrau, situationsabhängig hellgrau, anderer Modus weiß mit gestricheltem Rand | wie Sprache |
| Kontaktgruppe | eigene Farbfolge, nur in Gruppenabbildungen: `#117A8B`, `#D55E00`, `#CC79A7`, `#7A5195`, `#8C6D31`, `#7BA600` (nach Gruppen-ID) | Okabe-Ito/Tol |
| Offene Prüfhinweise | **gestrichelter dunkler Rand** um den Kontakt, in allen Abbildungen | – |
| Kandidatengruppe (nicht bestätigt) | grau, mit „?“; erzeugt keine Linie | – |
| Beziehung aus mehreren Gruppen | dunkle Linie (`#3A444D`) | – |
| Ego | dunkler Kreis „EGO“ im Zentrum | – |

Beschriftungen wählen Schwarz oder Weiß nach Kontrast (WCAG-Luminanz). Alle Farben sind durch Beschriftung oder
Legende gedeckt, nie allein bedeutungstragend.

## 3. Die sechs Abbildungen

| Datei | Inhalt | Besonderheit |
|---|---|---|
| `fig_A_ego_naehe_wohnort` | Ego im Zentrum, fünf Nähezonen nach **Tabellenwert** 1–5, Kontakte als Punkte mit ID, Farbe = Wohnort | Radius nur aus dem Tabellenwert; Winkel/Reihenfolge innerhalb einer Zone rein darstellerisch (nach Wohnort, dann ID); leere Zone bleibt sichtbar; Kontakte ohne Wert in einem eigenen äußeren Band („?“), nie in einer Zone |
| `fig_B_gruppen_beziehungen` | Kontakte als Knoten, dokumentierte Beziehungen als Kanten, Gruppen als Umrandung | jede Komponente einzeln (Kreis bei Clique, sonst Spring-Layout mit festem Seed); Komponenten nebeneinander gesetzt, Abstände ohne Bedeutung; Kontakte ohne dokumentierte Beziehung in eigenem Kasten; Ego nicht eingezeichnet |
| `fig_C_geografisches_profil` | Kontakte nach Wohnort-Kategorie und Ort, Geburtsland laut Angabe; Matrix Wohnland × Geburtsland | Zählung von Kontakten; keine Herkunftsgruppen |
| `fig_D1_sprachprofil` | Matrix Kontakt × Sprache, Sprachmodus, Sprachrepertoires, Modus × Beziehungstyp | mehrere Sprachen bleiben mehrere; keine Hauptsprache |
| `fig_D2_ego_sprachmodus` | dasselbe Layout wie A, Farbe = Sprachmodus, Kürzel der Sprachen unter dem Punkt | ein Kontakt liegt in A und D2 am selben Ort; Kürzel in Codebuchreihenfolge = keine Rangfolge |
| `fig_E_deskriptive_uebersicht` | acht Balkendiagramme: Aufenthaltsorte, Beziehungstypen, Kontakthäufigkeit, Nähe, Sprachen, Sprachmodus, Medien, Funktionen | explorativ; leere Kategorien sichtbar; Mehrfachnennungen gekennzeichnet |

**Nähe:** Die fünf Zonen tragen die Bedeutung des Codebuchs (`closeness_1_5`: 1 überhaupt nicht nah … 5 sehr nah). Eine
abweichende Legende der Netzwerkkarte wird nicht auf eine vierstufige Skala umgerechnet.

## 4. Formate und Qualität

SVG (Text als Pfade, damit die Schrift nicht von der Maschine abhängt), PNG (200 dpi), PDF (eingebettete Schrift).
Die Größe richtet sich nach dem Inhalt; die Bildhöhe wächst mit der Zahl der Kontakte nur dort, wo das Layout es
verlangt. Jede Abbildung wurde nach dem Erzeugen angesehen; Beschriftungskollisionen wurden behoben, nicht
hingenommen. Die Tests prüfen Reproduzierbarkeit, fehlende Zeitstempel, Textinhalt (keine Notizen/Freitexte),
die Zahl der gezeichneten Kanten und die Zonenlage; die Lesbarkeit prüft eine Person.

## 5. Neue Abbildungen

Eine neue Abbildung benutzt die Paletten und Zeichen oben, trägt die Fußzeile (`frame`), bezieht Kontaktmerkmale über
`contact_views` und ergänzt diese Tabelle. Eine neue Variable bekommt eine Farbe, die zu keiner vorhandenen
Variablen gehört, und wird hier eingetragen.
