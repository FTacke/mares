# ADR-0003 – Erhebungsmethode, Paarabdeckung, Prüfkategorien und kraftbasierte Netzwerkdarstellung

**Datum:** 2026-10-12 · **Status:** in Kraft

Ergänzt [`ADR-0002`](ADR-0002_2026-10-12_netzwerkmodul.md); die aktuellen Regeln stehen in
[`network-module.md`](../architecture/network-module.md) und
[`visualization-conventions.md`](../architecture/visualization-conventions.md).

## Kontext

Der erste Netzwerkbericht beschrieb die Beziehungen des Pilotfalls `001-2` als „aus Gruppenumrandungen
abgeleitet“ und die Alter-Alter-Erhebung pauschal als unvollständig. Die Projektleitung hat das berichtigt:
**Der Explorator hat die Beziehungen zwischen den Netzwerkpersonen im Interview erfragt; die eingezeichneten
Gruppenumrandungen fassen diese erhobenen Beziehungen zusammen. Alle Personen innerhalb derselben bestätigten
Gruppe kennen sich.** Außerdem sollten Prüfhinweise, die Datenprüfung mit Netzwerkeigenschaften vermischten
(gestrichelte Knotenränder), aus den wissenschaftlichen Grafiken verschwinden, und die Gruppendarstellung wirkte
wie eine Nachbildung des Erhebungsbogens statt wie ein Netzwerk.

## Entscheidungen

1. **Drei Dinge werden getrennt geführt:** die **Erhebungsmethode** der Alter-Alter-Beziehungen (was der
   Explorator getan hat), ihre **Dokumentationsform** (wie es aufgeschrieben wurde: Gruppenumrandungen) und die
   **Paarabdeckung** (ob *jedes* Paar erfasst wurde). Die Cliquenregel ist die Rekonstruktion der Paarliste aus der
   Dokumentationsform; sie ist für bestätigte Gruppen zulässig, weil die Erhebung es deckt.
2. **Eine fehlende Kante ist nur dann verneint, wenn die Paarabdeckung bestätigt ist.** Das Paket und die Aussage der
   Projektleitung belegen die 41 bestätigten Beziehungen, nicht, dass alle 231 Paare erfragt wurden; deshalb bleiben
   Paare ohne Angabe **unbekannt**. Der Zustand „Paarabdeckung vollständig“ ist im Modell vorgesehen
   (`TieBasis.COVERAGE`, `pair_coverage: complete`): dann werden fehlende Paare `no` und strukturelle Kennzahlen
   berechnet, ausdrücklich als explorative Beschreibung eines Einzelfalls. Eine belegte Kante wird in keinem
   Zustand entfernt.
3. **Nachträgliche Klarstellungen sind eine eigene, datierte, gehashte Datei (Kuratierung),** nicht eine Änderung
   der Originallieferung ([`intake-preservation.md`](../architecture/intake-preservation.md) §3). Sie trägt die
   Erhebungsmethode, die Paarabdeckung und die Kategorie jedes Prüfhinweises mit Urheber (`project_lead`
   oder `agent_proposal`) und Begründung. Ein Lauf liest sie neben dem Paket und hält ihren Hash im Run-Record fest.
   Ohne Kuratierung gilt „Methode nicht angegeben“ und jeder Hinweis nach der empfohlenen Aktion des Pakets.
4. **Prüfhinweise haben vier Kategorien:** offene, entscheidungsrelevante Datenfrage · dokumentierte Mehrdeutigkeit
   der Quelle · akzeptierte Unschärfe der Erhebung · geklärt/abgeschlossen. Nur die erste zählt als offene Datenfrage.
   Die Software entscheidet keinen Hinweis; die Kategorie kommt aus der Kuratierung. Was eine Person nicht
   entschieden hat, bleibt offen.
5. **Zustände der Quelle bleiben erhalten, die Auswertung hat eigene Kategorien.** Ein mehrdeutiges Geburtsland
   (zwei Länder genannt) behält den Rohwert und ist weder ein gewähltes Land noch zwei Länder noch „fehlt“ (Status
   `mehrdeutig`). Eine regionale Wohnortangabe („Nähe X“) ist eine Region (`Region X`), nicht die Stadt, und kein
   erfundener Wohnort. Ein Sprachmodus wird nie umcodiert.
6. **Prüfmarkierungen gehören nicht in wissenschaftliche Abbildungen.** Die Datenqualität steht im Prüf- und
   Reviewbericht und als Statuszeile im Fuß der Abbildungen (`Datenqualität: UNREVIEWED`).
7. **Die Netzwerkabbildung ist ein kraftbasiertes Layout (nach Vacca et al. 2016, Abb. 2):** Knoten und Beziehungen
   bestimmen die Position; keine Ringe, keine Gruppenrahmen als Layout. Gewählt ist die Stress-Majorisierung (SMACOF,
   mehrere deterministische Starts) nach einem dokumentierten Vergleich mit Spring (Fruchterman–Reingold) und
   ForceAtlas2 (Abbildung `fig_B0_layoutvergleich` mit Lesbarkeitsmaßen). Kein scipy: alles mit NumPy. B1 zeigt das
   Netz, B2 dasselbe Netz mit den erhobenen Gruppen als weiche Flächen. Gruppen sind erhobene Gruppen, keine
   „Communities“ eines Algorithmus.

## Folgen

- Neue Eingabe `--curation ROOT:rel` (nur `INTAKE`/`PRIMARY`); neue Ausgabe `review/review_register.csv`.
- Das Statusfeld `alter_alter` (partiell, aus Clique abgeleitet) entfällt zugunsten von `elicitation`,
  `documentation`, `pair_coverage`.
- Aus der Ausgabe der ersten Fassung (`fig_B_gruppen_beziehungen`) werden `fig_B1_…`, `fig_B2_…` und `fig_B0_…`.
- Die zwei Kuratierungsentscheidungen, die ein Agent nur vorschlagen konnte (er hatte die Originalbögen nicht), sind
  als `agent_proposal` gekennzeichnet und warten auf Bestätigung.

## Offen

Ob jedes der 231 Paare des Pilotfalls erfragt wurde (Bestätigung durch Explorator/Projektleitung); die Lesart der
handschriftlichen Ergänzungen am Originalbogen; ein Vergleich der erhobenen Gruppen mit algorithmisch bestimmten
Communities (nicht Teil dieser Entscheidung).
