# Run-Bericht 2026-10-31 – `network_v1`: finale Erhebungsvorlage, gemeinsames Grafikdesign, Regression, Git-Abschluss

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md),
[`ADR-0006`](../decisions/ADR-0006_2026-10-31_netzwerk-v1-gestaltung.md). Vorlauf am selben Tag:
[`2026-10-31_network-v0-v1-migration.md`](2026-10-31_network-v0-v1-migration.md). Ortsangaben beschreiben den Projektarbeitsplatz.

## 1. Git-Vorphase

**Bestand:** 69 Einträge in `git status` (≈ 110 Dateien, wenn man die unversionierten Ordner aufzählt), alle aus dem Vorlauf am selben
Tag: die Umbenennung `networks` → `network_v0` (bereits gestagt), der neue Einstieg, `network_v1` mit Tests und Beispiel, Dokumentation.
Dazu zwei Dateien, die nur Zeilenenden geändert hatten (Nebenwirkung eines `sed`-Aufrufs im Vorlauf, kein Inhalt) – zurückgesetzt. Kein
paralleler Prozess, keine Forschungsdaten, keine generierten Grafiken und keine temporären Dateien im Checkout; die PDF im Wurzelordner war
durch `*.pdf` ignoriert. Testbasis vorab: **509 bestanden**.

**Drei Commits** (lokal, mit expliziten Pfaden): `4d272ef` Umbenennung und Einstieg · `9283aaa` `network_v1` mit Tests und synthetischem
Fall 002 · `9bc09ea` Dokumentation, ADR-0005 und Run-Bericht. Fall 001 und alle Grafiken liegen nur in `INTAKE`, nicht im Repository.
Danach war der Working Tree sauber; keine Ausnahme.

## 2. Finale Erhebungsvorlage

- Ablage: [`templates/network_v1/05_MARES_Netzwerk_Tabelle_v1.pdf`](../../templates/network_v1/05_MARES_Netzwerk_Tabelle_v1.pdf)
  (verschoben, SHA-256 vor und nach dem Verschieben gleich `5052f949…57c9`); der Wurzelordner ist frei. Die Ausnahme `!/templates/**/*.pdf`
  in `.gitignore` deckt den Ort bereits ab. Die PDF ist leer (6 Seiten, keine Personendaten) und wurde seitenweise visuell gelesen.
- Abgleich mit dem Code, Ergebnis:

| Befund | Behoben |
|---|---|
| Zwischenwerte der Nähe stehen auf dem Bogen auch als Spanne (`1–2 / 1,5`); der Parser kannte nur `1,5` | `1–2`, `2–3`, `3–4` werden gelesen (Rohtext bleibt), andere Spannen sind Fehler |
| Block ABSCHLUSS (N Kontakte, N Gruppen, Kontaktnennung abgeschlossen/vorzeitig, Grund, Verbindungen geklärt) fehlte im Datenmodell | `metadata.closing`, geprüft gegen die Tabellen; für Pilot-/reguläre Fälle zu dokumentieren |
| Erläuterungspflichten („Sonstiges (erläutern)“, „S im Kommentar erläutern“) wurden nicht geprüft | Hinweis `comment_expected` (Funktion 5, Kommunikation 6, `S`) |
| Bezeichnungen wichen ab („professioneller/institutioneller Kontakt“, „sonstige Funktion“, Kleinschreibung) | Bezeichnungen der Vorlage in `codes.py`, auch in allen Grafiken |
| Benannte andere Sprache: auf dem Bogen im Kommentar, im Fallordner eigene Spalte | bewusst beibehalten (auswertbar), als Übertragungskonvention dokumentiert |
| Alle übrigen Codes (Typen 1–6, Häufigkeit 1–5, Funktionen 1–5/0 exklusiv, Formen 1–6, Sprachen 1–5, M/S/M;S, Sprachgebrauch leer bei einer Sprache, T/P/N/NS, Zugehörigkeit 1–5, 1/0/?, NS/KA/NA/leer) | stimmten überein |

Der Kontextbogen ist nicht Teil der Vorlage; seine Felder blieben unverändert.

## 3. Implementierung

Ein Designsystem in `figures/base.py` (vorher je Grafik eigene Lösungen): Seite mit Titel, Untertitel, Fallkennzeichnung, großer
Hauptdarstellung, Legende, höchstens zwei Hinweisen und kurzer Fußzeile; Typografie, Knoten-, Punkt- und Abstandsmaße als Konstanten, alles
in Zoll gezeichnet; die Beziehungstyp-Palette aus dem Auftrag; helle Bereichs- und Gruppenflächen; eine Blauskala für P3/P4; zwei
Legendenlayouts (`side`, `bottom`, Abschnitte umbrechen als Ganzes); Fallkennzeichnung aus den Metadaten (`TESTFALL 001* ·
FIKTIONALISIERT`, `TESTFALL 002* · SYNTHETISCH`, für echte Fälle `FALL · MARES-<Nr>`). Zwei Matrixbausteine statt fünf Einzelgrafiken.
Speichern wiederholt bis zu fünfmal, wenn Windows eine Datei kurz sperrt (trat beim Rendern in `INTAKE` zweimal auf, vermutlich
Vorschau/Miniaturansicht).

## 4. Standardgrafiken

| Grafik | Status | wichtigste Änderung |
|---|---|---|
| G1 | überarbeitet | neue Farben, größer, kompakte Seitenlegende, zwei kurze Hinweise; Linien werden nur gebogen, wenn ihre *Strecke* nahe an Ego vorbeiführt (vorher lief eine Familienkante sichtbar durch Ego); äußerer Bogen nur bei fehlender Nähe |
| G2 | überarbeitet | Knoten in Beziehungstypfarben; Untergruppen nach Ort bzw. Land mit hellen Flächen und Beschriftung, Einzelkontakte nur beschriftet; verbundene Kontakte einer Untergruppe auf einer Ellipse (kein Kraftlayout mehr, keine Linie durch fremde Knoten); Linien zwischen Bereichen dünn und hell; „nicht zuordenbar“ als abgesetzter Kasten |
| G3 | neu konzipiert | eine Gruppenkarte; Umrandungsstärke = Zugehörigkeit; Beschriftung mit Name, Größe, Zugehörigkeit; Knoten in Typfarben; eingebettete Gruppe durchgezogen; Beschriftungen werden gegen Knoten, andere Beschriftungen und fremde Umrandungen platziert |
| P1 | überarbeitet | Typfarben, keine Spalte „nicht zuordenbar“, Achse „Persönliche Nähe“, gemeinsamer Punktbaustein |
| P2 | überarbeitet | derselbe Baustein, Achse „Kontakthäufigkeit“ |
| P3 | überarbeitet | nur Anzahl je Zelle, 0 leer, n = 1 neutral, Zeilen ohne Codes in vier visuellen Abschnitten |
| P4 | überarbeitet | derselbe Baustein und dieselbe Blauskala; jede benannte Sprache eine Zeile (keine Obergrenze) |
| P5 | überarbeitet | Typfarben, Spalten ohne Codes, „Nichts davon“/„keine Angabe“ nur bei Vorkommen |

## 5. Kartografische G2-Variante (Experiment)

Skript [`pilots/network_v1_map/g2_map.py`](../../pilots/network_v1_map/README.md), nur für Fall 002; Ergebnis
`WORKSPACE:runs/RUN-20261031T142317Z-892640/` (`…_G2map_experiment_exact` und `…_country`, PNG/SVG). Drei Kartenfelder (Amerika, Europa,
Ausschnitt Mittelhessen) auf Natural Earth 1:50m (gemeinfrei, einmalig in `WORKSPACE:cache/basemaps/` geladen); Koordinaten aus einer
festen Tabelle öffentlicher Ortskoordinaten der erfundenen Orte, kein Geocoding-Dienst; Linien über die Feldgrenzen hinweg.

Bewertung (Sichtprüfung, keine fachliche Abnahme):
- **Informationsgewinn:** die transatlantische Struktur (Familie in Kolumbien – Schwester in Madrid – Netz in Marburg) ist sofort
  erkennbar, auch die Richtung der Bindungen. Für systematische Vergleiche zwischen Fällen ist G2 klarer (gleiche Bänder, gleiche Reihenfolge).
- **Lokale Dichte:** Marburg und die Nachbarorte (Cölbe, Lahntal, Wehrda) liegen im Ausschnitt auf wenigen Millimetern; die Knoten müssen
  per Kraftlayout von ihrem Ortspunkt weggeschoben werden (Leitlinie zum Punkt). Bei elf Marburger Kontakten ist das Feld voll und die
  lokalen Linien sind schwer zu verfolgen.
- **Nur Wohnland bekannt:** Kontakte stehen am Länderpunkt der Basiskarte im gestrichelten Kreis. Das vermeidet erfundene Städte, legt aber
  eine Lage nahe (USA-Punkt in Kansas, Kanada-Punkt im Norden), die nichts bedeutet; Kolumbien und Ecuador überlappen.
- **Aufwand und Robustheit:** ≈ 230 Zeilen, Basiskarte im Cache, Kartenausschnitte von Hand gesetzt; für echte Fälle wäre ein gepflegtes
  lokales Ortsverzeichnis nötig (Geocoding-Dienste sind ausgeschlossen). Nicht robust gegen beliebige Wohnorte.
- **Empfehlung:** kein Standard; allenfalls als ergänzende Illustration für einzelne, ausgewählte Fälle.

## 6. Testfälle

Beide Fälle neu installiert (002 aus dem Repository; 001 aus der v0-Lieferung neu gebaut, jetzt mit `closing`) und mit `render-all
--formats png,svg` neu gerendert: je 16 Dateien in `INTAKE:network_v1/pilots/<Fall>/graphics/`, alle mit gleichem Namen ersetzt, keine
fremden oder veralteten Dateien im Ordner. Beide tragen die Kennzeichnung oben rechts (rot) und `case_type: test`,
`empirical_analysis_eligible: false`. Fall 002 wurde ergänzt: Erläuterungen zu `S` (A12, A19), Nähe in Spannenschreibweise (A31 `2-3`),
eine zweite benannte Sprache (A29 Kichwa). Die zwischenzeitlichen Experimentläufe im `WORKSPACE` (eigene Ordner, Dateien einzeln
nach Namen) wurden gelöscht; die regulären Läufe blieben, auch zwei durch die Dateisperre abgebrochene.

## 7. Tests

- Vorher: volle Suite 509 bestanden.
- Neu: `tests/test_network_v1_design.py` (37 Tests: Codierschlüssel, Spannen, Abschlussblock, Erläuterungen, Palette, Legendenlayouts,
  Fallkennzeichnung, Fußzeile und Hinweise, Knotenfarben, G1-Ringe, G2-Untergruppen/Einzelbeschriftung/„nicht zuordenbar“/keine
  Überlappung, G3-Umrandungsstärke/Beschriftung/Linien, Matrizen ohne Spalte „nicht zuordenbar“, Punkte ohne Überlappung, Heatmap-Zellen,
  gemeinsame Blauskala, P3-Abschnitte, Mehrfachzählung, unbegrenzte Sprachen, „Nichts davon“ nur bei Vorkommen); zwei bestehende Tests an die
  Kennzeichnung bzw. an die Kantenzählung angepasst.
- Nachher: volle Suite **546 bestanden** (509 + 37 neue), Laufzeit ≈ 7 min.
- Visuell geprüft: alle acht Grafiken beider Fälle, mehrfach während der Arbeit und am Ende die Dateien in `INTAKE`.

## 8. Git

Zielbranch `main`, Remote `origin` (GitHub `FTacke/mares`). Vor dem Push stand `origin/main` auf `6ff6bb9`; lokal lagen neun Commits
darüber, ohne Abweichung (normaler Fast-forward-Push, kein Force). Vor dem Push wurde der gesamte Bereich `origin/main..HEAD` erneut geprüft:
keine Audio-, Excel-, Archiv- oder Datenbankdateien, als Binärdatei nur die leere Vorlage; Maschinenpfade nur in Run-Berichten; der
pseudonyme Fallcode des v0-Piloten nur in älteren Run-Berichten.

| Commit | Inhalt |
|---|---|
| `208b37e`, `7c03aec`, `894f11a` | Vorphase des Vorlaufs (Audio-Pilot, Speicher-Audit, v0-Netzwerkpipeline) |
| `4d272ef`, `9283aaa`, `9bc09ea` | Vorphase dieses Laufs: Umbenennung v0 + Einstieg, `network_v1`, Dokumentation |
| `924c695` | finale Vorlage nach `templates/`, Codierregeln abgeglichen, Fall 002 ergänzt |
| `7c15d4c` | Designsystem und überarbeitete acht Grafiken, Tests |
| `00586be` | Experiment kartografische G2 |
| (dieser Commit) | Dokumentation: `network-v1.md` §2/§5/§6, ADR-0006, Verweise, dieser Bericht |

Push-Ergebnis und Endstand stehen in der Abschlussnachricht des Laufs; sie werden hier nicht vorweggenommen.

## 9. Offene Punkte

1. G3 in Fall 002: die Beschriftung von C02 liegt teilweise auf der Umrandung von C01 (dichtes Gebiet, keine freie Position); halbtransparent,
   lesbar, aber nicht ideal.
2. G1 bei dicht vernetzten Fällen (001): viele Linien zwischen den Ringen bleiben unruhig; das Winkellayout ist unverändert.
3. Die Linienstärke in G3 kann als interne Vernetzung missverstanden werden; Legende und Hinweis sagen es, die fachliche Abnahme sollte es prüfen.
4. Kontextbogen ohne Vorlage; Excel-Import für v1 fehlt weiterhin; Gemeindeliste nicht amtlich (AGS) abgeglichen.

## Abschließendes Urteil

| Frage | Antwort |
|---|---|
| Implementierung abgeschlossen? | ja, im beschriebenen Umfang |
| Tests erfolgreich? | ja, 546 bestanden |
| Grafiken visuell geprüft? | ja, alle acht für beide Fälle (Lesbarkeit, nicht Wissenschaft) |
| Wissenschaftliche Abnahme erforderlich? | **ja** – Gestaltung und v0→v1-Lesart von 001 sind nicht fachlich validiert |
| Repository lokal sauber? | ja, nach dem letzten Commit (siehe §8) |
| Repository remote synchronisiert? | Push nach dem letzten Commit (siehe §8) |
