# Run-Bericht 2026-11-04 – `network_v1`: erster studentischer Peer-Pilotfall (MT) im Korpus `student_pilot`

Journal eines Laufs, keine Spezifikation. Maßgeblich: [`network-v1.md`](../architecture/network-v1.md) §2 und §7,
[`ADR-0009`](../decisions/ADR-0009_2026-11-04_netzwerk-v1-korpus-student-pilot.md). Ortsangaben beschreiben den Projektarbeitsplatz. Der
Bericht enthält keine Inhalte der Forschungsdaten (Orte, Alter, Gruppenbezeichnungen), nur Zählungen, A-IDs und pseudonyme Kürzel.

## 1. Ziel und Ausgangslage

Den authentischen studentischen Peer-Pilotfall MT (erhebende Person LS) als ersten Fall des getrennten Korpus `student_pilot` in die
bestehende `network_v1`-Pipeline übernehmen und die acht Standardgrafiken erzeugen. Grundlage war eine strukturierte Übergabe der
Projektleitung (`MARES-student-pilot-transcription-v1`, JSON). Sie lag unversioniert im Repository-Root und wurde nach dem Intake
auf Anweisung dort gelöscht. Die Verarbeitung der Inhalte durch den Agenten war ausdrücklich beauftragt. Vorab: Working Tree sauber bis
auf diese Datei, `main` = `origin/main` (`d32cd82`).

## 2. Ablage (logische Referenzen)

| Was | Wo |
|---|---|
| Original der Übergabe, byteidentisch, mit `SHA256SUMS.txt` | `INTAKE:inbox/MARES_student_pilot_MT_2026-11-01/` |
| Falltabellen | `INTAKE:network_v1/student_pilot/001_mt/data/` |
| acht Standardgrafiken (PNG + SVG, 16 Dateien) | `INTAKE:network_v1/student_pilot/001_mt/graphics/` |
| Prüfbericht, Ableitungen, Run-Record | `WORKSPACE:runs/RUN-20261104T163125Z-af28e6/` |

Die gewünschte Ablage `mares_storage/student_pilot/MT/` war nicht mit der Konfiguration vereinbar. Die Pipeline adressiert Fälle nur
im Baum `network_v1/`, und `case_code` muss mit drei Ziffern beginnen und dem Ordnernamen entsprechen. `PRIMARY` ist auf dem
Arbeitsplatz nicht konfiguriert, Fälle liegen daher übergangsweise in `INTAKE`.

## 3. Änderungen im Repository (Code, Tests, Doku – keine Falldaten)

- `run.KINDS` um `student_pilot` erweitert; Metadatenfeld `corpus` (`case.CORPORA`).
- Validator: Ordner und `corpus` müssen übereinstimmen; im Korpus nur `case_type: pilot` und nie `empirical_analysis_eligible: true`.
- `case.is_empirical` schließt Fälle mit `corpus` aus.
- Tests mit synthetischer Kopie von Fall 002 (Jahr `0000`): gültiger Korpusfall, fünf Fehlvarianten der Metadaten, Korpusfall unter
  `pilots/`, Verarbeitung im eigenen Ordner, Ausschluss aus dem empirischen Filter auch bei gesetztem Flag.
- Doku: `network-v1.md` §2/§7/§8, `storage-contract.md` §4, ADR-0009.

## 4. Übertragung (einmaliges Skript außerhalb des Repositorys)

- Tabelle A und B: Werte wie übergeben, Ländercodes ISO-3166-alpha-2 deterministisch auf alpha-3 und die Ländernamen der Übergabe
  übertragen. Spalte `label` leer, weil Vornamen und Rollen Dritter nicht übergeben wurden (Datenminimierung). Code 5 als Italienisch in
  `other_languages`. Sprachgebrauch nur bei mehreren Sprachen (A08–A10 `M;S`, A13–A15 `S`). Keine überwiegende Sprache und keine
  Erläuterung ergänzt.
- Tabelle C: fünf Gruppen, alle `T`. Die Gruppenpaare leitet die Pipeline aus `T` ab und sind nicht doppelt eingetragen. Dazu kommen
  die drei bestätigten Zusatzverbindungen A04–A16/A17/A18 (Quelle „weitere Verbindungen“) und die 187 übrigen Paare als `0` (Quelle
  „Abschluss: vollständig geklärt“). Die `0` gilt nur, weil dieser Fall ausdrücklich als vollständig geklärt markiert und von der
  Projektleitung bestätigt ist (`closing.connections: complete`).
- Kontextbogen: nur gesetzte Kreuze und Angaben. Ein nicht angekreuztes Feld zum Marburg-Bezug ist im Kommentar vermerkt, nicht ergänzt.
  Fehlende Sicherheitsangabe Portugiesisch nicht übertragen.
- Metadaten: `corpus: student_pilot`, `case_type: pilot`, `provenance: survey`, `empirical_analysis_eligible: false`,
  `display_code: STUDENT_PILOT MT`, `data_quality: UNREVIEWED`. Der `survey`-Block enthält Design, Instrument, Datum, Herkunft,
  Kürzel MT/LS und Formularcode. Die Transkriptionsentscheidungen der Übergabe stehen als `limitations`. Abschlusszahlen und Abschluss
  der Kontaktnennung sind nicht übertragen, weil die Übergabe sie nicht als Bogenwerte enthält.

## 5. Prüfung und Ergebnis

- Validierung `PASSED_WITH_WARNINGS`: 0 Fehler, 1 Warnung (Person/Rolle fehlt bei allen 22 Kontakten, erwartet), 6 Hinweise
  (`S` ohne Erläuterung bei A08–A10, A13–A15, wie in der Übergabe vermerkt).
- Abgleich mit den Erwartungen der Übergabe, alle gleich: **22 Kontakte, 5 Gruppen** (7/4/3/5/2 Mitglieder), ungruppiert A10,
  Beziehungstypen, Kontakthäufigkeiten, Wohnländer.
- **231 Paare: 44 bestätigt, 187 verneint, 0 ungeklärt**, 0 Widersprüche. Wohnortbereiche 8 / 0 / 0 / 11 / 3, keiner nicht zuordenbar.
- Rendering `COMPLETED`, **8 von 8 Grafiken** (G1–G3, P1–P5), Kennzeichnung `FALL · STUDENT_PILOT MT`, keine Testrahmung, Fußzeile
  mit Datenqualität.

## 6. Tests

Volle Suite: **573 bestanden** (vorher 565). `network_v0` und die Testfälle 001/002 sind unberührt.

## 7. Status

| | |
|---|---|
| implementiert (Korpus, Prüfregeln) | ja |
| technisch getestet | ja |
| Fall übertragen, geprüft, gerendert | ja |
| visuell geprüft (Agent, acht Grafiken) | ja |
| fachlich qualitätsgeprüft (`data_quality`) | nein (`UNREVIEWED`) |
| wissenschaftlich abgenommen | nein |

## 8. Offene Punkte

- **G2:** Die drei gestrichelten Verbindungen von A22 zu A19–A21 (zwischen zwei Bereichen) laufen unter dem Knoten A18 hindurch und
  können wie Verbindungen von A18 wirken. G2 ist gestalterisch abgenommen; nicht geändert, zur Entscheidung vorgelegt.
- Das Übertragungsskript ist nicht versioniert (kein Importer gewünscht). Für die drei weiteren Fälle mit demselben Übergabeformat wäre
  ein kleiner, getesteter Umsetzer im Repository zu erwägen.
- Die Originalscans (PDF) waren nicht Teil dieses Laufs; der Agent hat sie weder gelesen noch abgelegt.
