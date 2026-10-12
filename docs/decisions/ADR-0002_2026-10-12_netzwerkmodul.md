# ADR-0002 – Netzwerkmodul: Kontaktzahl ohne Obergrenze, Paketformat, Abhängigkeiten

**Datum:** 2026-10-12 · **Status:** in Kraft

Diese Entscheidung begründet die Änderungen am Datenvertrag ([`data-contract.md`](../architecture/data-contract.md)
§2 und §5) und die Architektur des ersten Netzwerkmoduls
([`network-module.md`](../architecture/network-module.md)).

## Kontext

Der Datenvertrag ging von höchstens 15 Kontakten je Fall aus (`A01`–`A15`). Die studentische
Folgeerhebung des Pilotfalls `001-2` hat 22 Kontakte: Das Erhebungsblatt wurde auf einem zweiten
Bogen fortgesetzt und dort erneut ab `A01` nummeriert. Künftige Erhebungen und Seminarjahrgänge
können weitere Kontaktzahlen haben. Die Obergrenze ist eine Eigenschaft eines Instruments, nicht
der Software.

## Entscheidungen

1. **Keine Obergrenze der Kontaktzahl im Softwaremodell.** Kontakt-IDs sind `A` plus mindestens zwei
   Ziffern ohne führende Überzähligkeit (`A01`…`A99`, `A100`…). `ids.MAX_CONTACTS` entfällt. Die 15
   bleibt ein Merkmal des ursprünglichen Instruments, nicht eine Regel des Codes.
2. **Kanonische Kontakt-IDs sind fortlaufend und unabhängig von der Blattnummerierung.** Die
   Provenienz (`source_block`, `source_local_id`) bleibt erhalten; die kanonische ID ist der Rang in
   der Reihenfolge (Block, lokale Nummer).
3. **Quellkennung ≠ Fall-ID.** `001-2` ist die historische Quellkennung einer Erhebung. Das
   Netzwerkmodell führt `source_label` und eine *optionale* `canonical_case_id`; es ordnet nie zu,
   solange kein Register existiert. Der Fall wird später gegen das Register aufgelöst.
4. **Paketformat `mares-network-package/v0-draft`** (CSV, UTF-8 mit/ohne BOM, `;`, `|` für Mehrfachcodes,
   leer = nicht erhoben). Das Format ist ein Importvertrag des Moduls, nicht des Instruments; es wird
   bei der Festlegung der Instrument-Version überprüft.
5. **Beziehungen: ein Netzwerk, eine Wahrheit.** Kanten werden aus bestätigten Gruppenmitgliedschaften
   abgeleitet (Cliquenregel); die mitgelieferte Kantentabelle ist ein Kontrollbeleg, kein zweiter
   Datenweg. Abweichungen sind ein harter Fehler. Paare ohne Beleg sind „nicht erhoben“ und werden nie
   als `no` gelesen ([`data-contract.md`](../architecture/data-contract.md) §5).
6. **Keine vollständigkeitsabhängigen Kennzahlen.** Dichte, Kohäsion, Segregation und Zentralitäten
   werden nicht berechnet, solange die Alter-Alter-Erhebung unvollständig ist. Jede strukturelle
   Ausgabe trägt Erhebungs- und Vollständigkeitsstatus.
7. **Abhängigkeiten: NetworkX und Matplotlib, kein pandas.** Beide kommen mit dem Code, der sie
   benutzt. pandas entfällt bewusst: Der Import muss „leer“ von „null“ und von „nicht erhoben“
   strikt unterscheiden und Codes als Zeichenketten erhalten; pandas konvertiert beides implizit
   (NaN, Zahlentypen). Die Tabellenauswertung ist mit `csv` und `collections` überschaubar.
8. **Ausgaben nur nach `WORKSPACE/runs/<RUN-ID>/`.** `PRIMARY` ist nicht eingerichtet; Ergebnisse sind
   damit regenerierbare Arbeitsdaten, keine erhaltenen Ableitungen. Eingaben kommen nur aus `INTAKE`
   oder `PRIMARY`, nie aus `BACKUP` oder `EXCHANGE`.
9. **Keine Webanwendung, kein Datenbankserver, keine interaktive Oberfläche;** statische Grafiken
   (SVG, PNG, PDF) mit festen Seeds und ohne Zeitstempel in den Dateien.

## Folgen

- `tests/test_refs_and_ids.py` und das Beispiel unter `examples/synthetic/` folgen der geänderten
  ID-Regel.
- Die Methodikskizze („höchstens 15 Kontakte“) wird als Eigenschaft des ursprünglichen Instruments
  gekennzeichnet.
- Die Provenienz eines Falls (`TEACHING`, Kohorte, Erhebende, Instrument-Version) wird erst mit der
  Registrierung formal festgehalten; bis dahin trägt das Netzwerkmodell nur, was das Paket belegt.

## Offen

Kanonische Fall-ID und Verknüpfung von `001-2` mit der früheren Erhebung; Kohorte, Erhebende und
Instrument-Version des Pilotfalls; Format expliziter Alter-Alter-Angaben (Ja/Nein/Unbekannt) im
Paket; Auswahl strukturell zulässiger Kennzahlen bei vollständiger Erhebung.
