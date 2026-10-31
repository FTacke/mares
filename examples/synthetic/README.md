# Synthetische Beispieldaten

Alles in diesem Ordner ist **erfunden**. Es gibt keine reale Person, kein reales Interview und
keinen realen Erhebungsbogen hinter diesen Dateien. Tests und Dokumentation benutzen ausschließlich
solche Daten; echte Forschungsdaten gehören nie ins Repository (`AGENTS.md`).

- Synthetische Fälle tragen das reservierte Jahr `0000` (`MARES-0000-001`), das nie einen echten
  Fall bezeichnet.
- Die Spalten der Beispieltabellen sind **illustrativ**. Das verbindliche Format legt erst das
  Erhebungsinstrument fest (`templates/`, `docs/architecture/modules.md`).

## `network-package-0000/`

Ein vollständiges, erfundenes Netzwerkpaket im Importformat (`mares-network-package/v0-draft`, siehe
[`network-module.md`](../../docs/architecture/network-module.md)): 12 Kontakte auf zwei Erhebungsblättern (die lokale
Nummerierung beginnt auf Blatt 2 neu), vier Gruppen (zwei überlappende bestätigte, eine unbestätigte, eine Paargruppe),
neun abgeleitete Beziehungen, Review-Einträge, Prüfsummen. Quellkennung `0000-1`, `"synthetic": true`. Es wird von
den Tests benutzt und lässt sich zum Ausprobieren in einen `INTAKE`-Ordner kopieren. Erzeugt mit
`tests/network_fixtures.py`; die Tests prüfen, dass es gültig bleibt.

## `network-curation-0000/`

Eine erfundene Kuratierungsdatei (`mares-network-curation/v0-draft`) zum Beispielpaket: Erhebungsmethode der Alter-Alter-Beziehungen,
Paarabdeckung und die Kategorie jedes Prüfhinweises. Aufruf: `--curation INTAKE:inbox/<Ordner>/curation.json`. Die Datei ändert das
Paket nicht; sie wird beim Lauf neben ihm gelesen und mit ihrem Hash im Run-Record festgehalten.

## `MARES-0000-001/`

| Datei | Inhalt |
|---|---|
| `case.json` | Fall mit Provenienz und den unabhängigen Statusdimensionen |
| `contacts.csv` | fünf Kontakte `A01`–`A05` mit Beispielattributen |
| `ties.csv` | Alter-Alter-Beziehungen: `yes`, `no`, `unknown`; ein leerer Wert heißt *fehlt* (nicht erhoben) |
