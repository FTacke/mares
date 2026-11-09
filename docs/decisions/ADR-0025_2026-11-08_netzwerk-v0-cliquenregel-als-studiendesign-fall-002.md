# ADR-0025 – `network_v0`: Cliquenregel als Studiendesign, überschneidende Gruppen verschmelzen nicht; Fall 002 Paket 1.1

**Datum:** 2026-11-08 · **Status:** in Kraft

Aktuelle Regeln: [`network-module.md`](../architecture/network-module.md) §4 (Regeln 1, 2 und 7).
Fall: [`pilot-case-002.md`](../methodology/pilot-case-002.md). Ersetzt für Fall 002 Entscheidung 1 und 4 von
[`ADR-0024`](ADR-0024_2026-11-07_netzwerk-v0-gruppenregel-nur-zugehoerigkeit-und-fall-002.md).

## Kontext

Paket 1.0 von Fall 002 führte die Gruppen mit der Regel `membership_only`. Die Karte enthält keine Verbindungslinien,
daher hatte der Fall null Beziehungen. Die Projektleitung hat am 2026-11-08 klargestellt: Im Studiendesign von v0 kennen sich
alle Personen, die als Teil einer Gruppe definiert sind. Offen war, was gilt, wenn sich Umrandungen überschneiden.

## Entscheidungen

1. **Die Cliquenregel ist das Studiendesign von v0.** Jede bestätigte Gruppe ist eine Clique. Das gilt für 001-2 schon und jetzt
   auch für 002.
2. **Überschneidende Gruppen verschmelzen nicht.** Ein gemeinsames Mitglied kennt alle Mitglieder jeder seiner Gruppen.
   Mitglieder verschiedener Gruppen ohne gemeinsame Gruppe bleiben unbekannt. Das ist die bestehende Ableitung
   (`build_network`); der Code bleibt unverändert. Eine Lesart, nach der überschneidende Gruppen zu einer Clique verschmelzen,
   wurde verworfen. Sie hätte in 001-2 drei und in 002 drei weitere Beziehungen ergeben.
3. **Fall 002 Paket 1.1** mit Kuratierung vom 2026-11-08 (`group_rule: all_members_know_each_other`) und 14 Beziehungen in der
   Kantentabelle. Paket 1.0 und seine Kuratierung bleiben unverändert in `INTAKE` und stehen in der Historie des Fallverweises.
4. **`membership_only` bleibt im Code** als ausdrückliche Ausnahme für Erhebungen, die Bekanntschaft innerhalb von Gruppen
   nicht festhalten. Derzeit benutzt sie kein Fall.

## Folgen

- Fall 002: In G2 und G3 erscheinen die Beziehungen. G1, P1–P5 und X1 sind gegenüber Paket 1.0 bytegleich.
- 001-2 und v1 sind unverändert.
