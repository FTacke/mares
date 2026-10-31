# Erhebungsinstrumente

Hier liegen die Erhebungsinstrumente als **leere, versionierte Vorlagen**: das standardisierte
Excel-Sheet für die Netzwerkerhebung, später Leitfäden und Kontextfragebögen.

- Jede eingesetzte Fassung hat eine Instrument-Version (`INS-<slug>@v<N>`,
  [Datenvertrag](../docs/architecture/data-contract.md) §2). Eine geänderte Vorlage ist eine neue
  Version; eine eingesetzte Version wird nicht mehr verändert, weil erhobene Daten auf sie
  verweisen.
- Hier liegen nur leere Vorlagen. Ein ausgefülltes Sheet ist ein Forschungsdatum und gehört nicht
  ins Repository.

## Vorlagen

| Datei | Instrument-Version | Inhalt |
|---|---|---|
| [`network_v1/05_MARES_Netzwerk_Tabelle_v1.pdf`](network_v1/05_MARES_Netzwerk_Tabelle_v1.pdf) | `INS-netzwerk-tabelle@v1` | Netzwerkerhebung `network_v1`: Tabellen A (Kontakte und Beziehungen), B (Kommunikation und Sprachgebrauch), Erweiterungsblätter A+ und B+, C (Gruppen und Verbindungen, Abschluss) und Codierschlüssel; zweisprachig Deutsch/Spanisch, leer |

Datenmodell und Codierregeln dazu: [`docs/architecture/network-v1.md`](../docs/architecture/network-v1.md). Der Kontextbogen liegt noch
nicht als Vorlage vor.
