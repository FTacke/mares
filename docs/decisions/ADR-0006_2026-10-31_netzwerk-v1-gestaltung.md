# ADR-0006 – `network_v1`: finale Erhebungsvorlage, gemeinsames Grafikdesign, einteiliges G3

**Datum:** 2026-10-31 · **Status:** in Kraft

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §2 und §5–§6. Ergänzt [`ADR-0005`](ADR-0005_2026-10-31_netzwerk-v0-v1.md);
ADR-0005 bleibt in Kraft, nur die dort beschriebene Gestaltung der Grafiken (§6 der damaligen Fassung) ist abgelöst.

## Kontext

Die erste Implementierung von `network_v1` (am selben Tag) folgte den Festlegungen eines Auftrags, weil die Erhebungsbögen nicht im
Repository lagen. Inzwischen liegt die finale Vorlage vor, und die Gestaltung der acht Grafiken wurde fachlich besprochen. Die erste
Fassung hatte je Grafik eigene Lösungen: Farben nach Wohnortbereich in G2, nach Beziehungstyp in G1, eine violette Skala in P4, Zellen mit
„k von n · %“, Spalten „nicht zuordenbar“, eine lange Fußzeile und ein zweiteiliges G3 (Gruppenkarte links, Ego-Gruppen-Strahlen rechts).

## Entscheidungen

1. **Die leere Vorlage `templates/network_v1/05_MARES_Netzwerk_Tabelle_v1.pdf` ist maßgeblich** (`INS-netzwerk-tabelle@v1`). Die Codelisten
   stehen nur im Code (`codes.py`) mit den Bezeichnungen der Vorlage; die Dokumentation verweist darauf.
2. **Übernommen aus der Vorlage:** Zwischenwerte der Nähe auch als Spanne (`1–2` = 1,5 …); der Block ABSCHLUSS als `metadata.closing`
   (geprüft gegen die Tabellen); erwartete Erläuterungen (Funktion 5, Kommunikation 6, `S`) als Hinweis. Die benannte andere Sprache steht
   auf dem Bogen im Kommentar, im Fallordner weiter in `other_languages` – eine bewusste Übertragungskonvention.
3. **Ein Designsystem für alle acht Grafiken** (`figures/base.py`): gleiche Seite (Titel, Untertitel, Kennzeichnung, Hauptdarstellung,
   Legende, höchstens zwei Hinweise, kurze Fußzeile), gleiche Typografie und Größen, zwei Matrixbausteine (Punktmatrix P1/P2/P5, Heatmap
   P3/P4) und **genau zwei Legendenlayouts** (`side`, `bottom`).
4. **Knotenfarbe = Beziehungstyp, überall** (Okabe-Ito-Palette, Grau für „Sonstige Beziehung“). Geografie und Gruppen sind nur helle
   Hintergründe; P3 und P4 teilen eine Blauskala.
5. **„Nicht zuordenbar“ ist keine Region:** keine Spalte, kein Band; ein Hinweis in den Matrizen, ein abgesetzter Kasten in G2.
6. **G2 bekommt geografische Untergruppen** (Ort bzw. Land) innerhalb der Bänder. Sie zeigen nur gemeinsame Geografie.
7. **G3 wird eine einzige Gruppenkarte.** Die rechte Strahlengrafik (Ego → Gruppen, Linienstärke = Zugehörigkeit) entfällt; die
   Zugehörigkeit geht in die **Linienstärke der Gruppenumrandung** und in die Beschriftung über. Eingebettete Gruppen bekommen statt einer
   gestrichelten eine engere durchgezogene Umrandung.
8. **Heatmap-Zellen zeigen nur die Anzahl**; 0 bleibt leer, Spalten mit n = 1 neutral.
9. **Fallkennzeichnung** aus den Metadaten (`TESTFALL 002* · SYNTHETISCH`, `FALL · MARES-003`), nie mit Namen.
10. **Kartografische G2-Variante nur als Experiment** (`pilots/network_v1_map/`), mit dem synthetischen Fall, ohne Geocoding-Dienst; die
    Bänderdarstellung bleibt Standard.

## Folgen

- Alle acht Grafiken beider Testfälle wurden neu erzeugt; die Dateinamen bleiben.
- Die Strahlengrafik von G3 zeigte die Zugehörigkeit getrennt von der Gruppenstruktur; jetzt stehen beide in einem Bild. Die Gefahr, eine
  kräftige Umrandung als dichte Vernetzung zu lesen, wird durch Legende und Hinweis adressiert, nicht beseitigt – Teil der fachlichen Abnahme.
- Wer eine neunte Grafik oder eine andere Farbbedeutung braucht, ändert zuerst `network-v1.md` und hält den Grund in einer neuen ADR fest.
