# Experiment: kartografische Variante von G2

**Status: Experiment.** Keine Standardgrafik, nicht Teil von `render`/`render-all`, kein Bestandteil eines Fallordners.
Verbindlicher Standard bleibt die Bänderdarstellung G2 ([`network-v1.md`](../../docs/architecture/network-v1.md) §6).
Bewertung: [`docs/agent-runs/2026-10-31_network-v1-design-instrument.md`](../../docs/agent-runs/2026-10-31_network-v1-design-instrument.md) §5.

| Datei | Zweck |
|---|---|
| `g2_map.py` | zeichnet den vollständig synthetischen Testfall 002 auf einer groben Karte (Amerika, Europa, Ausschnitt Mittelhessen), in zwei Varianten: genauer Wohnort / nur Wohnland |

## Regeln

- Nur der synthetische Testfall 002 (`provenance: fully_synthetic`); andere Fälle werden abgelehnt.
- Koordinaten stammen aus einer kleinen festen Tabelle öffentlicher Ortskoordinaten der erfundenen Orte im Skript. Es wird kein
  Geocoding-Dienst benutzt; Wohnortangaben verlassen den Rechner nicht.
- Ist nur das Wohnland bekannt, steht der Kontakt am Länderpunkt der Basiskarte in einem gestrichelten Kreis – nie an einer
  erfundenen Stadt.

## Basiskarte

Natural Earth, Admin 0 Countries 1:50m (gemeinfrei), einmalig nach `WORKSPACE:cache/basemaps/` geladen:

```text
curl -o <WORKSPACE>\cache\basemaps\ne_50m_admin_0_countries.geojson ^
  https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson
```

Es ist eine Datei im regenerierbaren Cache, keine Abhängigkeit des Pakets.

## Aufruf

```text
.venv\Scripts\python pilots\network_v1_map\g2_map.py
```

Ausgabe: `WORKSPACE:runs/<RUN-ID>/` mit `002_test_synthetic_G2map_experiment_{exact,country}.{png,svg}` und `run_record.json`.
