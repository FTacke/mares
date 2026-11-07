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

**Klärung der Projektleitung vom 2026-11-07:** Die Originalkarte dokumentiert **nur Cluster, keine gesicherten
Beziehungen zwischen einzelnen Netzwerkpersonen**. Daraus folgt:

- Gruppen und Mehrfachmitgliedschaften werden übernommen;
- aus einer Gruppe folgt **keine** Beziehung, es werden keine Cliquen gebildet;
- alle Kontaktpaare sind **unbekannt**, keines gilt als „kennen sich nicht“.

Die für 001-2 getroffene Festlegung „alle Mitglieder einer Gruppe kennen sich“ gilt für 002 **nicht**. In der Kuratierung
steht deshalb `group_rule: membership_only` ([`network-module.md`](../architecture/network-module.md) §4, Regel 7). Gleich
benannte Gruppen bleiben getrennt; maßgeblich sind die Gruppen-IDs. Zwei innere Umrandungen auf der Karte sind nicht als
Cluster geführt und wurden nicht als Gruppen übernommen (Prüfhinweis).

## 3. Umfang der Lieferung (Paketversion 1.0, 2026-11-07)

- 13 Kontakte `A01`–`A13`; zwei leere Zeilen des Bogens sind nicht übernommen.
- Fünf bestätigte Gruppen `C01`–`C05` mit 5, 2, 2, 2 und 2 Mitgliedern; ein Kontakt gehört drei Gruppen an, zwei Kontakte keiner.
- **0 Beziehungen**; keine Kantentabelle im Paket.
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
| innere Kartenumrandungen in einer Gruppe | dokumentierte Mehrdeutigkeit | keine Gruppen, keine Beziehungen |
| Strich unter einem Funktionscode (ein Kontakt) | dokumentierte Mehrdeutigkeit | Code übernommen |
| Fall-ID, Provenienz, Quellenprüfung | **offen** | Registeraufgaben |

**Abgleich Transkription – PDFs:** Alle Werte stimmen überein. Unterschiede: die regionale Wohnortangabe ist im Original mit
Umlaut geschrieben (übernommen wie im Original); der Strich unter einem Funktionscode; die zwei inneren Umrandungen der Karte.

## 5. Methodische Einschränkungen

1. **Keine Beziehungen zwischen Kontakten erhoben.** Netzwerkstruktur, Dichte oder Zentralität sind nicht bestimmbar; die Gruppen
   beschreiben Zugehörigkeit, nicht Bekanntschaft.
2. **Nähe = Tabellenwert**, einschließlich der Zwischenstufe 3,5; die Kartenposition wird nicht verwendet.
3. **Nutzungsintensität von Medien** (regelmäßig/gelegentlich) zeigt keine Grafik; P3 zählt gelegentliche Nutzung wie regelmäßige.
4. **Funktion 11** erscheint in P5 als „andere Funktion“; ihre Spezifikation steht nur im Paket.
5. **Ungenaue Wohnorte** bleiben ungenau: X1 zeigt das Land ohne Ort als unscharfe Lage und nennt die Regionalangabe als nicht
   darstellbar.
6. Ein Einzelfall erlaubt keine Verallgemeinerung.

## 6. Standardgrafiken

`v0 render-case --case INTAKE:network_v0/pilots/002` erzeugt die neun Standardgrafiken (G1, G2, P1–P5, G3, X1) als PNG und SVG in
`INTAKE:network_v0/pilots/002/graphics/`. G2 und G3 zeigen keine Verbindungslinien, ihre Legenden nennen keine. Stand 2026-11-07:
alle neun erzeugt und visuell geprüft; **nicht wissenschaftlich abgenommen**.

## 7. Nächste fachliche Schritte

Wissenschaftliche Quellenprüfung durch eine Person; Bestätigung der vorläufigen Lesart des Medienbereichs; Registrierung des Falls
(Fall-ID, Provenienz); Entscheidung über Eignung und Freigabe.
