# ADR-0020 – `network_v1`: G3-Herkunft mit festen Länderfarben, Kürzeln im Knoten und lokalen Zonen

**Datum:** 2026-11-06 · **Status:** Entscheidungen 1–2 in Kraft; 3–5 ersetzt durch [`ADR-0021`](ADR-0021_2026-11-06_netzwerk-v1-g3-herkunft-zwei-ansichten.md). Ersetzt in
[`ADR-0019`](ADR-0019_2026-11-06_netzwerk-v1-experiment-g3-geburtsland.md) die Farbvergabe (Entscheidungen 3 und 4), die zweite
Beschriftungsvariante und die Gestaltung der Lokalansicht.

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §6.2.

## Kontext

Nach der ersten Fassung hat die Projektleitung drei Festlegungen getroffen:

1. das Geburtslandkürzel im Knoten als bevorzugte Form;
2. eine Farbe je Geburtsland, gleich in allen Fällen;
3. für die Lokalansicht schematische Zonen „Marburg“ und „Übriges Mittelhessen“ plus eine kleine Übersichtskarte.

Die bisherige Vergabe hing von der Zusammensetzung eines Falls ab (Ausweichen bei belegtem Platz, Grau ab dem zehnten Land), und die
Lokalansicht wirkte leer und ohne räumliche Orientierung.

## Entscheidungen

1. **Eine Beschriftungsform.** A-ID und darunter das Alpha-3-Kürzel. Die reine A-ID-Variante wird nicht mehr erzeugt.
2. **Feste Farbtabelle nach ISO-Code**, ohne fallweise Neuvergabe.
   - Die zehn voraussichtlich häufigen Länder und zehn weitere sind fest zugeordnet.
   - Jeder andere Code erhält deterministisch eine Ergänzungsfarbe, die keinem festen Land gehört.
   - Ähnliche Farben sind bei vielen Ländern unvermeidbar; das Kürzel im Knoten ist die zweite Kennzeichnung. Ein gemeinsames Grau für
     „weitere“ Länder entfällt.
3. **Zonen links/rechts statt oben/unten.** Abgewogen, nicht beide gerendert: links/rechts beeinträchtigt die Gruppenstruktur am
   wenigsten:
   - Die Seite ist quer, Gruppenlabels liegen bevorzugt über und unter den Umrissen.
   - Die Zeile der Kontakte ohne Gruppe und Verbindung am unteren Rand lässt sich an der Zonengrenze teilen; bei oben/unten läge sie
     nur in einer Zone.
   - Die Anker der Gruppen ordnen sich horizontal nach dem Mitgliederanteil. Eine gemischte Gruppe bleibt ein Umriss über die Grenze.
4. **Übersichtskarte ohne erfundene Grenze.** Die vorhandene Basiskarte enthält nur Staatsgrenzen. Gezeigt werden Deutschland mit dem
   Ausschnitt und im Ausschnitt Marburg und die Kreisstädte der fünf Landkreise, als feste Orientierungspunkte, keine Wohnorte.
5. **Kompakte Fläche.** Bei wenigen Kontakten wird die Netzwerkfläche kleiner, statt das Layout auf die volle Größe zu strecken.

## Folgen

- Die neun Standardgrafiken bleiben bytegleich. G3 erhielt nur optionale Parameter (Fläche, Zonen, freier Rand oben), die G3 selbst
  nicht nutzt.
- Neue Länder brauchen keine Codeänderung. Soll ein häufig auftretendes Land eine eigene feste Farbe erhalten, wird die Tabelle
  ergänzt, ohne dass sich die Farben anderer Länder ändern.
