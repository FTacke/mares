# ADR-0027 – X1: nur Kartenpanels mit Kontakten

**Datum:** 2026-11-09 · **Status:** in Kraft

Aktuelle Regeln: [`network-v1.md`](../architecture/network-v1.md) §6 und §6.1. Ändert eine Festlegung aus
[`ADR-0016`](ADR-0016_2026-11-05_netzwerk-v1-x1-kanonisch.md).

## Kontext

Bisher zeigte X1 immer die drei Panels Amerika, Europa und Deutschland, ein leeres im Standardausschnitt mit „n = 0“. Bei Fällen, deren
Kontakte alle in Deutschland leben, standen deshalb zwei leere Karten neben der einzigen mit Inhalt.

## Entscheidung

Die Projektleitung hat entschieden, dass ein Raum ohne Kontakte keine Karte bekommt. Das gilt übergreifend für v1 und v0, denn die
X1-Funktion ist gemeinsam. Die Reihenfolge der vorhandenen Panels bleibt gleich, Deutschland bleibt das größte. Ist kein einziger
Kontakt darstellbar, erscheint nur Deutschland im Standardausschnitt.

## Folgen

- Alle Fälle sind neu gerendert. Geändert haben sich nur die X1-Dateien von `student_pilot/002_ls` und `004_jz`, die vorher leere
  Panels zeigten.
- Bei den übrigen Fällen hatte jedes Panel Kontakte. Ihre Grafiken sind bytegleich: die v1-Testfälle, `001_mt`, `003_gh` und
  v0 001-2 und 002.
