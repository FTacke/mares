# Methodik

Ort für die methodischen Grundlagen von MARES: Erhebungsdesign, Aufbau der Instrumente, Definition
der Netzwerkkennzahlen, Transkriptions- und Pseudonymisierungskonventionen. Methodische Dokumente
begründen, *was* erhoben und berechnet wird; die technischen Verträge unter
[`../architecture/`](../architecture/overview.md) regeln, wie damit umgegangen wird.

Bisher festgehaltene Eckpunkte (aus dem Projektauftrag, noch ohne eigenes Dokument):

- egozentrierte Netzwerke mit strukturierten Kontaktattributen und Alter-Alter-Beziehungen; das
  ursprüngliche Instrument sieht bis zu 15 Kontakte je befragter Person vor, Folgeerhebungen können mehr
  haben (Pilotfall: 22) – die Software setzt keine Obergrenze
  ([ADR-0002](../decisions/ADR-0002_2026-10-12_netzwerkmodul.md));
- bei Beziehungen wird zwischen „kennen sich nicht“, „unbekannt“ und „nicht erhoben“ unterschieden;
- Netzwerkgrafiken orientieren sich methodisch an Vacca et al. (2016);
- Vergleiche nach geografischen, sozialen und sprachlichen Merkmalen;
- Audiointerviews und narrative Episoden werden transkribiert und für die Forschung
  pseudonymisiert beziehungsweise anonymisiert.

Erster Fall: [`pilot-case-001-2.md`](pilot-case-001-2.md). Offen und hier zu dokumentieren, sobald entschieden: Namensgenerator und Attributkatalog des
Netzwerk-Sheets, Auswahl und Definition der Kennzahlen, Transkriptionskonventionen.
