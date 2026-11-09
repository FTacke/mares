# Pilotfall 002

Fachdokumentation zum zweiten Datenpaket des Netzwerkmoduls. Sie enthält **keine Forschungsdaten und keine
personenbezogenen Einzelheiten**: keine Namen, keine Wohnorte, keine Einzelwerte von Kontakten, keine Angaben aus dem
Kontextbogen. Das Paket ist auch ohne Namen vertrauliches Forschungsmaterial und liegt außerhalb des Repositorys.
Technik: [`../architecture/network-module.md`](../architecture/network-module.md); Entscheidung:
[`ADR-0024`](../decisions/ADR-0024_2026-11-07_netzwerk-v0-gruppenregel-nur-zugehoerigkeit-und-fall-002.md).
Vergleichsfall: [`pilot-case-001-2.md`](pilot-case-001-2.md).

## 1. Was der Fall ist – und was nicht

| Frage | Stand |
|---|---|
| Kennung | `002` ist die Quellkennung, keine kanonische Fall-ID (kein Register). |
| Erhebung | Sitzung vom 2026-09-30, `network_v0`; Kontextbogen, Netzwerkerhebungssheet und Netzwerkkarte. Die interviewende Person ist im Paket vermerkt, nicht hier. |
| Datenherkunft | geprüfte Transkription der Projektleitung; die drei Original-PDFs liegen als eigene Lieferung in `INTAKE` und wurden mit ausdrücklicher, auf Fall 002 beschränkter Freigabe am 2026-11-07 gelesen und mit der Transkription abgeglichen. |
| Falltyp | `pilot`, `empirical_analysis_eligible: false`; vorläufiger inhaltlicher Falltyp laut Kontextbogen im Paket. |
| Datenqualität | `UNREVIEWED`. Der Abgleich mit den PDFs ist ein Lesevergleich durch einen Agenten, keine wissenschaftliche Quellenprüfung. |
| Freigabe | `NOT_DECIDED`. Eine erfolgreiche technische Verarbeitung begründet keine Eignung und keine Freigabe. |

## 2. Wie die Alter-Alter-Beziehungen dokumentiert sind

Die Netzwerkkarte zeigt **keine Verbindungslinien**, nur Gruppenumrandungen.

**Klärung der Projektleitung vom 2026-11-08:** Im Studiendesign von v0 kennen sich alle Personen, die als Teil einer Gruppe
definiert sind. Daraus folgt, wie bei 001-2:

- jede bestätigte Gruppe ist eine **Clique**; daraus entstehen 14 Beziehungen;
- **überschneidende Umrandungen verschmelzen nicht:** Das Mitglied, in dem sich drei Gruppen überschneiden, kennt alle
  Mitglieder seiner drei Gruppen; deren übrige Mitglieder kennen sich nur innerhalb ihrer eigenen Gruppe;
- Kontaktpaare ohne gemeinsame Gruppe sind **unbekannt**, keines gilt als „kennen sich nicht“.

In der Kuratierung steht `group_rule: all_members_know_each_other` ([`network-module.md`](../architecture/network-module.md)
§4, Regeln 1 und 2; [`ADR-0025`](../decisions/ADR-0025_2026-11-08_netzwerk-v0-cliquenregel-als-studiendesign-fall-002.md)).
Die Lesart „nur Zugehörigkeit“ (`membership_only`) des Pakets 1.0 vom 2026-11-07 ist damit ersetzt. Gleich benannte Gruppen
bleiben getrennt; maßgeblich sind die Gruppen-IDs. Zwei innere Umrandungen auf der Karte sind nicht als Cluster geführt und
wurden nicht als Gruppen übernommen; für die Beziehungen ist das ohne Folge, weil die ganze umgebende Gruppe eine Clique ist.

## 3. Umfang der Lieferung (Paketversion 1.1, 2026-11-08; ersetzt 1.0 vom 2026-11-07)

- 13 Kontakte `A01`–`A13`; zwei leere Zeilen des Bogens sind nicht übernommen.
- Fünf bestätigte Gruppen `C01`–`C05` mit 5, 2, 2, 2 und 2 Mitgliedern; ein Kontakt gehört drei Gruppen an, zwei Kontakte keiner.
- **14 Beziehungen**, alle aus der Cliquenregel; die Kantentabelle des Pakets ist der Beleg. Keine Linie der Karte
  liegt zugrunde. Paket 1.0 hatte keine Beziehungen.
- Zwei Beziehungscodes kommen vor; Mehrfachnennungen bei Medien, Sprachen und Funktionen sind vollständig übernommen.
- Nennquellen sind im Bogen nicht ausgefüllt und bleiben leer; nichts wurde aus anderen Attributen abgeleitet.
- Der **Kontextbogen** ist vollständig im Manifest des Pakets (`context_sheet`) übernommen: Herkunft und Migration,
  Marburg-Bezug (nicht Angekreuztes gilt nicht als verneint), Tätigkeit, Wohnsituation, Aufenthaltsperspektive mit ergänzender
  Notiz, Alltagssprachen, Sprachen nach Bereichen, eine rezeptive Mediennutzung (getrennt, nicht als Kommunikationsbereich
  gewertet), sprachliche Sicherheit mit Notiz, Zeitangaben (handschriftlich, keine Audio-Zeitmarken), vorläufiger Falltyp.
  Die Bemerkungen der interviewenden Person stehen dort ausdrücklich als **methodische Beobachtungen**, nicht als Aussagen der
  befragten Person.

## 4. Klärungen und Prüfhinweise

| Gegenstand | Kategorie | Behandlung |
|---|---|---|
| Zwischenwerte „3–4“ / „4–3“ bei der Nähe (vier Kontakte) und der Häufigkeit (ein Kontakt) | geklärt | Code `3.5`, im Codebuch des Pakets definiert; nicht gerundet; Originalschreibweise in `source_notation` |
| Mediennotation „1,(2)“ (zwei Kontakte) | geklärt | Code 2 = gelegentlich genutzt, bleibt in den Medien; das Paketformat kennt keine Nutzungsintensität, „gelegentlich“ steht als strukturierte Quellnotiz (`source_annotation`) und als Prüfhinweis |
| Medienbereich „2–6“ (ein Kontakt) | geklärt | inklusiver Bereich 2–6, wie bei 001-2 |
| Mediencode 8 mit Freitext | geklärt | Code und Freitext erhalten; kein Medium unterstellt |
| Funktion 11 mit Spezifikation (ein Kontakt) | geklärt | Code 11 („andere Funktion“), Spezifikation als Quellnotiz; keine neue Kategorie |
| Wohnland ohne Ort (ein Kontakt) | akzeptierte Unschärfe | nur das Land; kein Ort ergänzt |
| regionale Wohnortangabe (ein Kontakt) | akzeptierte Unschärfe | als Regionalangabe erkannt; keine Koordinate |
| Nennquellen nicht ausgefüllt | akzeptierte Unschärfe | leer |
| innere Kartenumrandungen in einer Gruppe | dokumentierte Mehrdeutigkeit | keine eigenen Gruppen; ohne Folge für die Beziehungen |
| drei sich überschneidende Umrandungen | geklärt (2026-11-08) | jede Gruppe eine Clique, keine Verschmelzung |
| Strich unter einem Funktionscode (ein Kontakt) | dokumentierte Mehrdeutigkeit | Code übernommen |
| Fall-ID, Provenienz, Quellenprüfung | **offen** | Registeraufgaben |

**Abgleich Transkription – PDFs:** Alle Werte stimmen überein. Unterschiede: die regionale Wohnortangabe ist im Original mit
Umlaut geschrieben (übernommen wie im Original); der Strich unter einem Funktionscode; die zwei inneren Umrandungen der Karte.

## 5. Methodische Einschränkungen

1. **Beziehungen nur aus der Cliquenregel.** Die Karte enthält keine einzelne Verbindungslinie. Alle 14 Beziehungen folgen aus
   der Gruppenzugehörigkeit; Paare ohne gemeinsame Gruppe sind unbekannt. Dichte oder Zentralität beschreiben deshalb nur die
   Gruppenstruktur, nicht ein vollständig erhobenes Netz.
2. **Nähe = Tabellenwert**, einschließlich der Zwischenstufe 3,5; die Kartenposition wird nicht verwendet.
3. **Nutzungsintensität von Medien** (regelmäßig/gelegentlich) zeigt keine Grafik; P3 zählt gelegentliche Nutzung wie regelmäßige.
4. **Funktion 11** erscheint in P5 als „andere Funktion“; ihre Spezifikation steht nur im Paket.
5. **Ungenaue Wohnorte** bleiben ungenau: X1 zeigt das Land ohne Ort als unscharfe Lage und nennt die Regionalangabe als nicht
   darstellbar.
6. Ein Einzelfall erlaubt keine Verallgemeinerung.

## 6. Standardgrafiken

`v0 render-case --case INTAKE:network_v0/pilots/002` erzeugt die neun Standardgrafiken (G1, G2, P1–P5, G3, X1) als PNG und SVG in
`INTAKE:network_v0/pilots/002/graphics/`. G2 und G3 zeigen die 14 Beziehungen der Cliquenregel. Stand 2026-11-08: alle neun mit
Paket 1.1 erzeugt, G2 und G3 visuell geprüft; **nicht wissenschaftlich abgenommen**.

## 7. Nächste fachliche Schritte

Wissenschaftliche Quellenprüfung durch eine Person; Bestätigung der vorläufigen Lesart des Medienbereichs; Registrierung des Falls
(Fall-ID, Provenienz); Entscheidung über Eignung und Freigabe.
