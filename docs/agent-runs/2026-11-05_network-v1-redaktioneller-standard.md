# Run-Bericht 2026-11-05 – `network_v1`: redaktionelle Vereinheitlichung der neun Standardgrafiken

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §5.2 und §5.7,
[`ADR-0018`](../decisions/ADR-0018_2026-11-05_netzwerk-v1-redaktioneller-standard.md), Texte:
[`network-v1-visualization-text-inventory.md`](../architecture/network-v1-visualization-text-inventory.md). Vorlauf:
[`2026-11-05_network-v1-x1-kanonisch-und-legenden.md`](2026-11-05_network-v1-x1-kanonisch-und-legenden.md). Für den authentischen Fall MT
nennt der Bericht keine Inhalte.

## 1. Ziel

Auftrag: die sichtbaren Texte der neun Standardgrafiken nach den freigegebenen Festlegungen der Projektleitung bereinigen, die X1-Form auf
alle übertragen und alle Fallgrafiken neu erzeugen; Daten, Berechnungen und Layouts unverändert lassen.

Vorab: Working Tree sauber, `main` = `origin/main` (`f1941e6`). Das Textinventar war die Ausgangsbasis und stimmte mit dem Code überein.

## 2. Änderungen

**Gemeinsam (`figures/base.py`):**
- `TITLES` ist die eine Titeltabelle, die auch das Register verwendet; `page(ctx, code, …)` setzt nur noch den Titel, ohne Untertitel und
  mit einheitlich niedrigem Kopf. Der Parameter für einen eigenen Untertitel und der für eine eigene Fußzeile entfallen.
- `footer_line` ergibt für alle neun Grafiken `MARES · network_v1 · {n} Kontakte`.
- `MISSING_LABEL` (`keine Angabe`), `BRACKET_LABEL` (`Marburg und Mittelhessen`) und `relation_section` (Beziehungstyp-Legende) sind
  jeweils an einer Stelle definiert; `Context.unresolved_note(ids)` liefert `Wohnort nicht zuordenbar: …` für P1–P4 und G2.
  `Context.coverage_line` entfällt.
- `HEAT_LEGEND` mit vier Einträgen für P3 und P4.

**Je Grafik:**
- G1: Nähe-Legende kompakt; kein Hinweis; Bogen fehlender Nähe heißt `keine Angabe`.
- G2: Legende `innerhalb eines Bereichs` / `zwischen Bereichen` ohne Zahlen; `gleicher Wohnort / gleiches Wohnland`; nur noch der Hinweis
  zum Wohnort; die Zeile ohne Bereich heißt `Wohnort nicht zuordenbar:`.
- G3: Skala `Zugehörigkeit: 1 sehr stark – 5 überhaupt nicht`, die fehlenden Kurzcodes nur bei Vorkommen, keine Hinweise.
- P1, P2: keine methodischen Hinweise.
- P3, P4: gemeinsame Heatmap-Legende mit Bezugsgröße; P4-Hinweis kompakt; „ohne Angabe“ wird `keine Angabe`.
- P5: Hinweis `Mehrfachnennungen möglich.`
- X1: nur auf die zentralen Komponenten umgestellt.

**Dokumentation:**
- `network-v1.md`: §2.4 (Abdeckung im Prüfbericht statt in der Grafik), §5.1, §5.2 und §5.5; neu §5.7 mit den redaktionellen Regeln
  und allen methodischen Lesarten, die nicht mehr in den Grafiken stehen; Wortlaute in §6.
- Das Textinventar ist auf den neuen Stand neu gefasst.
- ADR-0018.

## 3. Entscheidungen im Lauf

- **G1-Zeile „Zwischenwerte“ bleibt immer.** Der Auftrag erlaubte das Weglassen ohne Zwischenwerte im Fall, wenn es die Lesbarkeit
  verbessert. Weil G1 die gestrichelten Ringe immer zeichnet, stünden sie dann unerklärt da. Ein erster Stand ließ die Zeile bedingt
  weg (bei MT sichtbar), das wurde zurückgenommen.
- **G2-Legende „zwischen Bereichen · ohne Bereich“** bleibt als bedingter Zusatz. Verbindungen zu Kontakten ohne Bereich tragen
  dieselbe Strichart; ohne Zusatz wären sie falsch beschrieben.
- **G1-Bogen `keine Angabe`** folgt der einheitlichen Terminologie; die radiale Lage zeigt, dass es um die Nähe geht.
- **P4** nennt „Mehrfachnennungen möglich“ in Legende und Hinweis, wie vereinbart.
- **Platz:** Der Kopf ist um 0,33 Zoll niedriger, Hinweise entfallen. Die Diagramme behalten ihre Maße in Zoll; die Seiten werden
  entsprechend kürzer, die Diagramme nehmen also einen größeren Anteil der Seite ein. Eine Vergrößerung der Diagramme selbst hätte Layouts
  verändert und war nicht vorgesehen.

## 4. Tests und Prüfungen

- **Tests:** angepasst bzw. neu für Titel ohne Code und ohne Untertitel (alle neun), eine Fußzeile, reduzierte Texte von G1, G2, G3, P1,
  P2, P5, die Heatmap-Legende von P3/P4, bedingte Hinweise, `keine Angabe` statt „ohne Angabe“, Abdeckung nur in den Daten, die
  G1-Zwischenwerte; der Vergleich des Hauptbereichs mit voller Legende nutzt jetzt die eine gemeinsame Komponente.
- **Gesamtsuite:** 610 Tests bestanden.
- **Hauptbereich unverändert:** Für alle drei Fälle und alle neun Grafiken wurden Knoten (Lage und Farbe), Texte, Linien und Flächen
  des Hauptbereichs zwischen dem vorigen Commit und dem neuen Stand verglichen. Einzige Abweichung ist die beabsichtigte: in G1 von 002
  heißt der Bogen fehlender Nähe `keine Angabe` statt „Nähe ohne Angabe“.
- **X1:** in allen drei Fällen PNG und SVG bytegleich zum Stand vor dem Lauf.
- **Rendering:** `render-all --root INTAKE --formats png,svg` verarbeitete die drei vorhandenen Fälle (`001_test_v0_fictionalized`,
  `002_test_synthetic`, `student_pilot/001_mt`) mit Status `COMPLETED`; je Fall 18 Dateien in `graphics/`.
- **Visuell:** alle 27 Grafiken geprüft. Keine Überlagerungen, keine abgeschnittenen Texte, Legenden verständlich, Fallkennzeichen
  korrekt; Fälle mit 22 und 32 Kontakten und mit vier bzw. fünf Beziehungstypen.

## 5. Status und offene Punkte

- Implementiert, getestet und gerendert; nicht wissenschaftlich validiert.
- Gesamtsuite: 610 Tests bestanden.
- Offen bleibt, ob die Diagramme selbst größer werden sollen. Der frei gewordene Platz verkürzt bisher nur die Seite.
- Die G1-Legende „1 sehr nah · 2 nah · 3 weniger nah · 4 außerhalb der Kreise“ steht wegen der Breite der Seitenlegende dreizeilig.
