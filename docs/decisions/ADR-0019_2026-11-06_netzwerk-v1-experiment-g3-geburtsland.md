# ADR-0019 – `network_v1`: Experiment G3 nach Geburtsland

**Datum:** 2026-11-06 · **Status:** in Kraft als Experiment (keine Kanonisierung; G3 bleibt unverändert)

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §2 und §6.2.

## Kontext

Die Projektleitung möchte explorativ prüfen, ob persönliche Kontaktgruppen aus Menschen verschiedener Geburtsländer bestehen und wie
diese untereinander verbunden sind. G3 färbt die Knoten nach Beziehungstyp. Das Geburtsland ist in Tabelle A erhoben
(`birth_country`, `birth_country_iso3`). Eine Kanonisierung ist ausdrücklich noch nicht beschlossen.

## Entscheidungen

1. **Kein zweites Layout.** Die Variante nutzt die G3-Implementierung selbst. G3 wurde dafür in Geometrie (`g3_geometry`) und Zeichnen
   (`draw_g3`) getrennt; Knotenfarbe, Knotenbeschriftung, Knotenradius und Gruppenlabel sind Parameter. G3 selbst bleibt bytegleich.
2. **Zwei Ansichten, zwei Beschriftungsvarianten, vier Dateien je Fall.** Die Lokalansicht verwendet die Wohnortbereiche Marburg (Stadt)
   und übriges Mittelhessen aus §3. Sie beschränkt Mitgliedschaften und Verbindungen auf diese Kontakte, behält Gruppen-IDs und
   Umrissfarben und nennt lokale und gesamte Mitgliederzahl, wo sie sich unterscheiden. Beide Beschriftungsvarianten bleiben
   nebeneinander bestehen, bis eine Entscheidung fällt.
3. **Farben nach Prüfung, nicht nach Augenmaß.** Weil die Knoten verstreut liegen, muss jedes Farbpaar unterscheidbar sein, nicht nur
   benachbarte Einträge. Gesucht wurde in gängigen farbfehlsichttauglichen Paletten (Okabe-Ito, Paul Tol und weitere). Die größte dort gefundene Auswahl, die
   das in allen Paaren auch unter Protan- und Deutan-Simulation schafft, hat neun Farben (OKLab-ΔE ≥ 8 simuliert, ≥ 15 normal). Mehr Länder werden nicht durch erzeugte Zwischenfarben bedient, sondern teilen ein Grau „weitere Geburtsländer“ und sind
   namentlich in der Legende genannt.
4. **Stabilität vor Häufigkeitsrang.** Der Farbplatz eines Landes ergibt sich aus seinem Code, nicht aus seinem Rang im Fall. Er weicht nur
   aus, wenn ein anderes Land des Falls denselben Platz belegt.
5. **Eigener Ort, eigener Befehl.** Die Dateien liegen unter `<Fall>/experimental/g3_geburtsland/` und entstehen nur mit
   `v1 experiment g3-geburtsland`. `render` und `render-all` erzeugen sie nicht. Der Run-Record enthält nur Zahlen, keine Länder.

## Folgen

- Die neun Standardgrafiken sind unverändert (bytegleich geprüft). `page()` hat einen optionalen Titel für Experimente außerhalb von
  `TITLES`.
- Bei einer Kanonisierung sind offen: die Variantenwahl, ein Grafikcode und Dateiname, die Aufnahme ins Register und ins Textinventar.
