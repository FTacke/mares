# ADR-0014 – `network_v1`: X1 Fassung 2.3 (regionale Ortsgruppen über eine gepflegte Zuordnung)

**Datum:** 2026-11-05 · **Status:** in Kraft (Experiment; ersetzt in
[`ADR-0013`](ADR-0013_2026-11-05_netzwerk-v1-x1-zentren-und-laender.md) die Entscheidungen 1 und 2, Entscheidung 3 bleibt)

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §6.1.

## Kontext

Fassung 2.2 hielt eigenständige Zentren immer getrennt. Im Kartenmaßstab der Deutschlandkarte war Mittelhessen damit zu kleinteilig:
Kirchhain und Wetzlar standen mit eigenen Kästen und Ausweichlinien neben Marburg und Gießen. Gewünscht sind wenige, geografisch
plausible Schwerpunkte, ohne Sonderlogik für einzelne Orte im Code und ohne weit entfernte Städte zusammenzufassen.

## Entscheidungen

1. **Zentral gepflegte Zuordnung** statt Zentrumsstatus: Die Spalte `group_with` im Ortsverzeichnis nennt den Ort, mit dem ein Ort
   regional dargestellt wird (Stadtteil, Umlandgemeinde oder Nachbarstadt eines größeren Ortes), mit Begründung in `basis`. Leer heißt
   eigenständig. Die Spalte `centre` entfällt.
2. **Maßstabsabhängig und begrenzt:** Die Zuordnung greift nur unter drei Bedingungen:
   - der Zielort hat im selben Panel Kontakte;
   - er liegt höchstens 40 km Luftlinie entfernt;
   - beide Punkte liegen im Panel weniger als etwa 15 mm auseinander.

   Es gibt nur eine Stufe und keine Ketten. Auf einer Karte mit größerem Maßstab bleiben die Orte getrennt.
3. **Kenntlich gemacht:** Der Kasten listet die Einzelorte mit Zahl. Die Kontakte stehen nach Ort sortiert im Ring. Die wahren Punkte
   der weiteren Orte bleiben als kleine hohle Ringe sichtbar. So entsteht nicht der Eindruck, alle wohnten in derselben Stadt.
4. Die erhobenen Wohnorte und die Koordinaten im Verzeichnis bleiben unverändert; die Gruppierung betrifft nur die Darstellung.

## Folgen

- Testfall 002: „Marburg und Umgebung“ (mit Cölbe, Kirchhain, Lahntal, Wehrda) und „Gießen und Umgebung“ (mit Wetzlar); Kassel,
  Frankfurt, Berlin, Bogotá und Medellín stehen für sich.
- Neue Orte brauchen gegebenenfalls einen `group_with`-Eintrag; ohne ihn bleiben sie eigenständig.
- Die Zuordnung ist eine fachliche Setzung im Verzeichnis und gehört bei neuen Fällen zur Prüfung.
