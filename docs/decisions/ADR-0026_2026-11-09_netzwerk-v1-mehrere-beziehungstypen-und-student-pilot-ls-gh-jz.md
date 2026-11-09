# ADR-0026 – `network_v1`: mehrere eingetragene Beziehungstypen; student_pilot LS, GH, JZ

**Datum:** 2026-11-09 · **Status:** in Kraft

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §2.1 und §7. Korpus: [`ADR-0009`](ADR-0009_2026-11-04_netzwerk-v1-korpus-student-pilot.md).

## Kontext

Drei weitere studentische Peer-Pilotfälle wurden mit den v1-Bögen erhoben. In einem Fall hat die befragte Person für einen Kontakt
zwei Beziehungstypen eingetragen. Die Projektleitung hat entschieden, dass beide erhalten bleiben, obwohl der Bogen nur die
Hauptbeziehung vorsieht. Bisher war ein zweiter Code in `relation_type` ein Fehler. Damit wäre der Fall nicht verarbeitbar gewesen,
außer man hätte einen Code gestrichen.

## Entscheidungen

1. **`relation_type` liest mehrere Codes.** Ein einzelner Code bleibt der Normalfall. Mehrere Codes sind eine Warnung
   (`relation_type_several`), kein Fehler. Doppelte oder ungültige Codes bleiben Fehler.
2. **Darstellung wie in v0:** ein geteilter Knoten in den Farben der Typen und eine Legendenzeile „mehrere Beziehungstypen“. In G1
   steht die Kombination in einem eigenen Sektor direkt nach dem Sektor ihres ersten Typs.
3. **Regression:** Fälle mit einem Code je Kontakt sind unverändert. Die 66 Grafikdateien der v1-Testfälle und von `001_mt` sind
   bytegleich geprüft.
4. **Fälle `002_ls`, `003_gh`, `004_jz`.** Die Nummer zählt den Korpus. Bei LS ist es zugleich der Interviewcode der Bögen, die Kürzel
   stammen aus den Dateinamen. Grundlage sind die Tabellen der Bögen, nicht die Netzwerkkarten. Der Einwilligungsstatus steht in
   `survey.consent`. Bei LS hat die Projektleitung die Einwilligung bestätigt; das ist keine Prüfung des Dokuments durch den Agenten.

## Folgen

- Eine Auswertung nach „Hauptbeziehung“ muss Kontakte mit mehreren Typen ausdrücklich behandeln.
