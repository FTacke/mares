# ADR-0009 – `network_v1`: getrenntes Korpus `student_pilot` für studentische Peer-Piloten

**Datum:** 2026-11-04 · **Status:** in Kraft

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §2 und §7, Fallbaum in
[`storage-contract.md`](../architecture/storage-contract.md) §4.

## Kontext

Vier authentische Pilotfälle werden mit Studierenden als Peer-Befragten erhoben, um das Instrument `network_v1` methodisch zu erproben.
Die Befragten gehören nicht zur lateinamerikanischen Studienpopulation von MARES. Die Fälle sollen wie Studienfälle geprüft und mit den
acht Standardgrafiken dargestellt werden. Sie dürfen aber weder mit den Testfällen noch mit regulären Fällen vermischt werden und nie in
Auswertungen der Studie eingehen.

Bisher kannte der Fallbaum nur `network_v1/pilots/` (Pilot- und Testfälle) und `network_v1/cases/` (reguläre Erhebungen). Ein
Eigenschaftswert allein (`empirical_analysis_eligible: false`) hätte die Fälle zwar aus Übersichten herausgehalten, aber nicht als
eigene Gruppe kenntlich gemacht. Außerdem hätte er sich später versehentlich umsetzen lassen.

## Entscheidungen

1. **Eigener Ordner** `network_v1/student_pilot/<NNN_kurzname>/` im selben Fallbaum und mit demselben Datenmodell; kein neues Werkzeug.
   `NNN` zählt die Fälle des Korpus (nicht der Formularcode der erhebenden Person, der bei mehreren Studierenden gleich sein kann).
2. **Metadatenfeld `corpus: student_pilot`**, Pflicht in diesem Ordner und nur dort zulässig. Ordner und Metadaten müssen
   übereinstimmen, denn Identität und Auswertbarkeit folgen weiterhin aus den Metadaten, nicht aus Ordnernamen.
3. Fälle des Korpus sind `case_type: pilot`, `provenance: survey` und **nie** `empirical_analysis_eligible: true`.
   `case.is_empirical` schließt jeden Fall mit `corpus` zusätzlich aus.
4. **Kennzeichnung** über `display_code` (`FALL · STUDENT_PILOT MT`), ohne Testrahmung und ohne Klarnamen.
5. Die Übergabe eines Falls wird als Kopie in `INTAKE/inbox/<Lieferung>/` mit SHA-256 erhalten
   ([`intake-preservation.md`](../architecture/intake-preservation.md)). Die Übertragung in die Falltabellen ist (wie bei allen
   v1-Fällen) Handarbeit beziehungsweise ein einmaliger Schritt; ein Importer für das Übergabeformat ist nicht gebaut.

## Folgen

- `render-all` und `list` erfassen auch `student_pilot/`; `list --empirical` und `run.empirical_cases` nie.
- Die abweichende Wunschablage `student_pilot/MT/` außerhalb von `network_v1/` war mit dem Fallbaum und der Regel
  „`case_code` = Ordnername, drei Ziffern vorn“ nicht vereinbar. Der Fall heißt deshalb `001_mt`.
