# ADR-0024 – `network_v0`: Gruppenregel „nur Zugehörigkeit“, Zwischenwerte im Codebuch; Fall 002

**Datum:** 2026-11-07 · **Status:** in Kraft

Aktuelle Regeln: [`network-module.md`](../architecture/network-module.md) §3, §3.1, §4 (Regel 7), §7.1.
Fall: [`pilot-case-002.md`](../methodology/pilot-case-002.md). Vorgänger: [`ADR-0023`](ADR-0023_2026-11-07_netzwerk-v0-standardgrafiken-und-fall-001-2.md).

## Kontext

`network_v0` leitete aus jeder bestätigten Gruppe eine Clique ab. Für 001-2 ist das durch die Projektleitung gedeckt. Für Fall 002
hat die Projektleitung geklärt, dass die Karte nur Cluster dokumentiert und keine Beziehungen zwischen Kontakten. Außerdem enthält 002
Zwischenwerte („3–4“, „4–3“ = 3,5) bei Nähe und Häufigkeit; Code-Parser und v0-Profil kannten nur ganze Stufen.

## Entscheidungen

1. **Gruppenregel `membership_only`** in der Kuratierung (`survey.group_rule`). Bestätigte Gruppen und Mitgliedschaften bleiben,
   die Cliquenregel entfällt (`build_network(…, clique_rule=False)`). Mitgliedschaften tragen `derivable_edge = no`, Klärungen die
   Regel `membership_only`; der Validator prüft beides gegen die Kuratierung. Ohne Angabe bleibt die Cliquenregel Standard; 001-2 ist
   unverändert.
2. **Zwischenwerte sind Codes des Paketcodebuchs.** Der Parser liest Dezimalcodes (`3.5`); gültig sind sie nur, wenn das Codebuch des
   Pakets sie definiert. Das v0-Profil nimmt die Stufen von Nähe und Häufigkeit aus dem Codebuch (absteigend). Ein Zwischenwert
   bekommt in G1 einen gestrichelten Ring ohne Zahl und in P1/P2/P5 eine eigene Zeile. Es wird nie gerundet; die
   Originalschreibweise steht im Paket.
3. **Legenden erklären nur Gezeichnetes.** Gibt es keine einzige Beziehung, nennen G2 und G3 keine Verbindungslinie. Für Fälle mit
   Beziehungen (v1, 001-2) ändert sich nichts; die Grafiken sind bytegleich geprüft.
4. **Fall 002** als Paket 1.0 mit Kuratierung und Fallverweis `network_v0/pilots/002/data/case.json` (Pilot, nicht geeignet,
   Freigabe offen). Der Kontextbogen steht im Manifest (`context_sheet`); Originalnotation und Quellnotizen stehen in zusätzlichen
   Spalten von `contacts.csv`, die der Leser ignoriert. Es gibt kein zweites Fallformat.

## Folgen

- Nutzungsintensitäten von Medien („gelegentlich“) und Spezifikationen offener Codes bleiben Quellnotizen. Das Paketformat und die
  Grafiken bilden sie nicht ab; eine Erweiterung wäre eine eigene Entscheidung.
- Weitere Fälle wählen ihre Gruppenregel ausdrücklich in der Kuratierung.
