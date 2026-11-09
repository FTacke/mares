# Run-Bericht 2026-11-08 – `network_v0`: Fall 002 mit Cliquenregel (Paket 1.1)

Journal eines Laufs, keine Spezifikation. Maßgeblich:
[`ADR-0025`](../decisions/ADR-0025_2026-11-08_netzwerk-v0-cliquenregel-als-studiendesign-fall-002.md),
[`network-module.md`](../architecture/network-module.md) §4, [`pilot-case-002.md`](../methodology/pilot-case-002.md). Der Bericht
nennt keine Personen, Namen, Orte oder Einzelwerte des Falls.

## 1. Ziel und Scope

Auf Rückfrage der Projektleitung wurde geprüft, ob die Gruppen von Fall 002 bestätigte Beziehungen enthalten. Klärung: Im
Studiendesign von v0 kennen sich alle Mitglieder einer Gruppe; überschneidende Gruppen verschmelzen nicht (Lesart A). Zwei
Gruppen, deren Umrandungen nahe beieinander liegen, sind getrennt. Daraufhin wurde Fall 002 auf die Cliquenregel umgestellt.

## 2. Untersuchung

- Netzwerkkarten von 002 und 001-2 erneut angesehen. 002 hat keine Verbindungslinien, nur Umrandungen.
- Folgen für 001-2: Unter Lesart A keine Änderung, die Cliquenregel gilt dort schon (41 Beziehungen). Die verworfene Lesart B
  hätte drei Beziehungen ergänzt.
- Folgen für 002: Lesart A ergibt 14 Beziehungen, Lesart B hätte 17 ergeben.

## 3. Daten (nur im geschützten Speicher)

- Neu sind **Paket 1.1** `INTAKE:inbox/MARES_002_Datenpaket_2026-11-08_v1.1/contents` und die **Kuratierung**
  `INTAKE:inbox/MARES_002_Kuratierung_2026-11-08/curation.json`.
- Inhalt:
  - `group_rule: all_members_know_each_other`;
  - Mitgliedschaften mit `derivable_edge = yes`;
  - Klärungen K01–K05 mit `all_pairs_know_each_other`;
  - neue Kantentabelle mit 14 Kanten;
  - ein neuer Prüfhinweis zur Überschneidung von drei Umrandungen.
- Paket 1.0 und Kuratierung vom 2026-11-07 sind unverändert. Der **Fallverweis** zeigt auf 1.1 und führt 1.0 in `history`.
- Ein Zwischenstand musste neu erzeugt werden, weil ein Prüfhinweis zuerst auf drei Gruppen zugleich verwies. Die zwei in
  diesem Lauf angelegten Ordner wurden dafür nach Namen entfernt und der Fallverweis aus der Sicherung zurückgesetzt.
- Prüfung: `PASSED_WITH_WARNINGS`, 0 Fehler, eine berechtigte Warnung (ein Wohnort, nur das Land ist bekannt), drei offene
  Datenfragen wie bisher.

## 4. Code und Dokumentation

- Kein Produktionscode geändert; die Ableitung verschmolz überschneidende Gruppen schon bisher nicht.
- Neuer synthetischer Test `test_overlapping_groups_do_not_merge`.
- Dokumentation:
  - `network-module.md` §4: Regeln 1, 2 und 7;
  - `pilot-case-002.md`: §2, §3, §4, §5 und §6;
  - neues ADR-0025;
  - Statuszeile von ADR-0024.

## 5. Prüfungen

- `render-case` für 002: `COMPLETED`, 18 Dateien.
  - Gegenüber Paket 1.0 haben sich nur G2 und G3 geändert, PNG und SVG.
  - G1, P1–P5 und X1 sind bytegleich.
- G2 und G3 visuell geprüft:
  - Clique der Familiengruppe;
  - drei Beziehungen des gemeinsamen Mitglieds;
  - Fernverbindungen gestrichelt;
  - die Legenden nennen wieder Verbindungslinien.
  - In G3 läuft eine Linie der Familiengruppe dicht an einem Knoten vorbei. Das ist das bestehende Layout und wurde nicht
    geändert.
- Tests: Gesamtsuite 505 bestanden (vorher 504, neu ist der Test zu überschneidenden Gruppen).

## 6. Status und offene Punkte

- Umgesetzt und gerendert; **nicht wissenschaftlich validiert**. Datenqualität `UNREVIEWED`, Freigabe offen.
- Die Beziehungen von 002 folgen allein aus der Cliquenregel. Die Karte enthält keine einzelne Verbindungslinie.
- Offene Datenfragen unverändert: Quellenprüfung durch eine Person, Bereichslesart eines Medieneintrags, Fall-ID und Provenienz,
  Eignung und Freigabe.
