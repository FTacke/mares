# ADR-0023 – `network_v0`: Standardgrafiken mit den Grafikfunktionen von v1; Fall 001-2 in Paketversion 1.2

**Datum:** 2026-11-07 · **Status:** in Kraft

Aktuelle Regeln: [`network-module.md`](../architecture/network-module.md) §7 und §7.1, [`network-v1.md`](../architecture/network-v1.md) §6,
Fall: [`pilot-case-001-2.md`](../methodology/pilot-case-001-2.md).

## Kontext

`network_v0` hatte eine eigene Grafikgeneration mit neunzehn Abbildungen in drei Ebenen und zwei Profilen. `network_v1` hat einen
abgenommenen Satz von Standardgrafiken. Die Projektleitung möchte für beide Versionen dieselben Grafiktypen und Gestaltungsprinzipien,
ohne die Erhebungsdefinitionen von v0 aufzugeben. Für Fall 001-2 liegen geprüfte Transkriptionen beider Erhebungsblätter und
verbindliche Klärungen vor, darunter eine abweichende Gruppenstruktur.

## Entscheidungen

1. **Eine Grafikimplementierung, zwei Versionsprofile.** Die Grafikfunktionen von v1 lesen Skalen, Kategorien, Farben, Bereichsnamen
   und die Versionskennung aus einem Profil (`base.Scheme`). v1 behält seine Werte unverändert; alle v1-Grafiken sind bytegleich
   geprüft. v0 bringt ein eigenes Profil (`network_v0.standard.V0Scheme`), dessen Wortlaute aus dem Codebuch des Pakets stammen.
2. **Keine Umcodierung.** Der v0-Datensatz wird mit seinen v0-Codes in die Fallstruktur der Grafikfunktionen übersetzt.
   - Nähe: Tabellenwert 1–5, 5 = sehr nah, nie die Kartenposition.
   - Häufigkeit: v0-Stufen.
   - Beziehung: mehrere v0-Codes je Kontakt als geteilter Knoten, keine Hauptbeziehung.
   - Elf Funktionen, acht Medien, Sprachen ohne Hauptsprache.
   - v0-Geografie mit „Region Marburg“.
   - Gruppen ohne Zugehörigkeitsskala, weil v0 sie nicht erhebt.

   Ein Codebuch mit anderen Bedeutungen der Beziehungscodes bricht ab, statt falsch zu färben.
3. **Neun Standardgrafiken für v0:** G1, G2, P1–P5, G3, X1, mit denselben Dateinamen wie v1. In v0 entfallen nominale Kategorien
   ohne Kontakt (P3/P4-Zeilen, P5-Spalten); Skalenstufen bleiben. Die Grafiken entstehen im Lauf (`figures/`) und für registrierte
   Fälle mit `v0 render-case` in `<Fall>/graphics/`. Die Version steht in Fußzeile und Fallkennzeichen.
4. **Alte v0-Grafiken entfallen.** Die neunzehn Abbildungen, ihre Module, die Optionen `--profiles`, `--language-view`,
   `--tie-highlight` und PDF als Standardformat sind entfernt. Frühere Läufe bleiben unverändert in `WORKSPACE/runs/`.
5. **Fall 001-2: Paketversion 1.2 statt Überschreiben.** 1.1 bleibt unverändert. 1.2 übernimmt die bestätigten Funktionen 2 und 5
   eines Kontakts und die vier verbindlichen Gruppen C01–C04 mit der Cliquenregel (Entscheidung der Projektleitung). Kanten, die nur
   aus einer ergänzenden Kartenumrandung folgten, entfallen. Eine neue Kuratierung übernimmt die bisherigen Einordnungen und
   ergänzt die Klärungen. Der Fallverweis zeigt auf 1.2; Pilotstatus, Eignung und Freigabe bleiben unverändert.

## Folgen

- Weitere v0-Fälle (zunächst 002) laufen über denselben Weg: Paket und Kuratierung nach `INTAKE`, Fallverweis
  `network_v0/pilots/<Fall>/data/case.json`, dann `v0 render-case`. Neuer Grafikcode ist dafür nicht nötig.
- X1 braucht für v0-Fälle Einträge im gemeinsamen Ortsverzeichnis; für 001-2 wurden sechs Städte von Hand ergänzt.
- Die Visualisierungskonventionen der alten v0-Grafiken sind historisch.
