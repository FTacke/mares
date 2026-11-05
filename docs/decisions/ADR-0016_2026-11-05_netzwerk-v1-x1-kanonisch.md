# ADR-0016 – `network_v1`: X1 wird neunte Standardgrafik

**Datum:** 2026-11-05 · **Status:** in Kraft (ersetzt den Experimentstatus aus
[`ADR-0010`](ADR-0010_2026-11-05_netzwerk-v1-experimentelle-grafik-x1.md); die Gestaltungsentscheidungen aus ADR-0010 bis
[`ADR-0015`](ADR-0015_2026-11-05_netzwerk-v1-x1-ortspunkt-frei.md) gelten weiter, soweit §6.1 sie übernimmt)

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §6 und §6.1. Sichtbare Texte:
[`network-v1-visualization-text-inventory.md`](../architecture/network-v1-visualization-text-inventory.md).

## Kontext

Die Karte X1 „Geografische Verteilung des persönlichen Netzwerks“ wurde als experimentelle Zusatzgrafik in den Fassungen 1 bis 2.8
an drei Fällen entwickelt und gestalterisch abgenommen. Bis dahin entstand sie nur über einen eigenen Befehl und lag unter
`<Fall>/experimental/`, getrennt von den acht Standardgrafiken. X1 braucht als einzige Grafik Quellen außerhalb des Fallordners: das
Ortsverzeichnis im Root des Falls und die Basiskarte im `WORKSPACE`.

## Entscheidungen

1. **X1 ist die neunte Standardgrafik.** Sie steht im Grafikregister (`figures/__init__.py`), entsteht bei jedem `render` und
   `render-all` und liegt als `<Fallcode>_X1_geografische_verteilung.png|svg` in `<Fall>/graphics/` neben den übrigen. Der Code `X1`
   bleibt (keine Umbenennung in `G4`); er steht in Dateinamen, Register und Dokumentation, nicht im sichtbaren Titel.
2. **Eine Implementierung.** Der bisherige Code zieht von `experimental.py` nach `figures/maps.py`; der Befehl `experimental-x1` und
   der eigene Ausgabeort entfallen. Layout, Ortsgruppen und Platzierungsregeln bleiben unverändert (Fassung 2.8).
3. **Kartenquellen als expliziter Zustand.** Der Fallauf liest Ortsverzeichnis und Basiskarte vor dem Anlegen des Run-Ordners und
   vermerkt beide mit Hash im Run-Record (`map_sources`). Fehlt eine der beiden Dateien, wird X1 mit diesem Grund übersprungen
   (`skipped`), nie aus einer anderen Quelle gezeichnet. Eine fehlerhafte Datei stoppt den Lauf.
4. **Redaktionell reduziert.** Titel ohne Code, kein Untertitel, Legende nur mit Beziehungstypen und Ortspunkt (bedingt: weiterer Ort
   einer Ortsgruppe, nur Wohnland bekannt), Zahlen als `n = x`, als Hinweise nur „Wohnort nicht darstellbar: …“ (bei Bedarf) und
   „Kartengrundlage: Natural Earth.“, Fußzeile „MARES · network_v1 · {n} Kontakte“ ohne Gruppenzahl und ohne Datenqualität.
   Methodische Erläuterungen (Verschiebung, Zusammenfassung, Maßstäbe) stehen in der Dokumentation, nicht in der Grafik.
5. **Datenstatus gehört nicht in X1.** Datenqualität und Prüfstatus stehen in den Fallmetadaten und Run-Records. X1 zeigt sie auch bei
   authentischen Fällen nicht. Die Fußzeile von G1–G3 und P1–P5 bleibt vorerst unverändert; ihre Texte werden auf Grundlage des
   Textinventars gesondert geprüft.

## Folgen

- Ein vollständiger Grafiksatz umfasst neun Grafiken je Format. Tests und Pipeline-Prüfungen erwarten neun Dateien; ohne Kartenquellen
  sind es acht, und der Grund steht im Run-Record.
- Ältere Ausgaben unter `<Fall>/experimental/` bleiben als Entwicklungsstände liegen; die Pipeline liest und schreibt dort nichts mehr.
  Ob sie gelöscht werden, entscheidet eine Person.
- Die Fassungsnummer erscheint nicht mehr in der Grafik; die Entwicklungsgeschichte steht in ADR-0010 bis ADR-0015 und den
  Run-Berichten.
