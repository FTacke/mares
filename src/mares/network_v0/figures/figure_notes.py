"""What each figure asks and how far it can be read -- kept out of the figures themselves.

A clean figure carries a short title, at most one context line, a compact legend and one short hint. The longer
explanations (the research question, the visual codings, the limits of interpretation) live here and are written to
``figures/figures_index.json`` of every run, next to the files. The sources of truth for the rules are
``docs/architecture/visualization-conventions.md`` and ``network-module.md``.
"""

from __future__ import annotations

# stem -> note. ``base``: what places a contact (the three spatial meanings stay apart).
NOTES: dict[str, dict[str, object]] = {
    "fig_A_ego_naehe_wohnort": {
        "title": "Egozentriertes Netzwerk: Nähe und Wohnort der Kontakte",
        "base": "Nähe-Layout: der Radius ist der erhobene Tabellenwert der subjektiven Nähe (1–5)",
        "question": "Wie nah erlebt Ego seine Kontakte, und wo wohnen sie?",
        "encodings": ["Radius: Tabellenwert der Nähe", "Farbe: Wohnort-Kategorie", "Winkel: nur Lesbarkeit"],
        "limits": ["Winkel und Reihenfolge innerhalb einer Zone tragen keine Information", "Nähe wird nie aus der Kartenposition rekonstruiert"],
    },
    "fig_B1_netzwerkstruktur": {
        "title": "Netzwerkstruktur der erhobenen Beziehungen zwischen den Kontakten",
        "base": "Struktur-Layout: die Position folgt den bestätigten Kontakt–Kontakt-Beziehungen (Stress-Majorisierung)",
        "question": "Wie hängen die Kontakte durch die erhobenen Beziehungen zusammen?",
        "encodings": ["Position: Beziehungsstruktur", "Farbe: Wohnort-Kategorie", "Linie: bestätigte Beziehung"],
        "limits": ["Abstände zwischen getrennten Teilnetzen haben keine Bedeutung", "nicht eingezeichnete Paare sind unbekannt, nicht verneint (solange die Paarabdeckung nicht belegt ist)"],
    },
    "fig_B2_netzwerkstruktur_gruppen": {
        "title": "Netzwerkstruktur mit erhobenen Kontaktgruppen",
        "base": "Struktur-Layout wie B1",
        "question": "Wie verhalten sich die erhobenen Kontaktgruppen zur Struktur der Beziehungen?",
        "encodings": ["Fläche: erhobene Kontaktgruppe", "Überlappung: gemeinsame Mitglieder"],
        "limits": ["Gruppen sind erhobene Gruppen, keine algorithmisch gefundenen Communities"],
    },
    "fig_B3_ego_netzwerk": {
        "title": "Persönliches Beziehungsnetz",
        "base": "Struktur-Layout wie B2, Ego ergänzt (Kontaktpositionen unverändert)",
        "question": "Wie sieht das persönliche Netzwerk einschließlich Ego mit seinen Teilgruppen aus?",
        "encodings": ["dunkler Knoten: Ego", "Farbe: Wohnort-Kategorie", "helle Linie: Ego–Kontakt (Zugehörigkeit)", "dunklere Linie: erhobene Beziehung zwischen Kontakten", "weiche Fläche: erhobene Kontaktgruppe"],
        "limits": ["der Abstand zu Ego ist kein Nähemaß (Nähe: Abbildung A)", "Ego verbindet alle Kontakte, der Graph ist daher zwangsläufig zusammenhängend – kein Befund", "Strukturmaße beruhen auf dem Netz ohne Ego"],
    },
    "fig_G1_geografische_zonen": {
        "title": "Geografische Einordnung der Kontakte relativ zu Ego",
        "base": "Geografie-Layout: die Zone ist die Wohnort-Kategorie",
        "question": "Wie verteilen sich die Kontakte über die geografischen Stufen?",
        "encodings": ["Ring: Wohnort-Kategorie", "Farbe: Wohnort-Kategorie"],
        "limits": ["keine Karte, keine Kilometer; Ringbreiten folgen der Kontaktzahl", "Winkel: nur Lesbarkeit"],
    },
    "fig_G2a_geografische_baender": {
        "title": "Geografische Verflechtung (Bänder)",
        "base": "Geografie-Layout: Bänder = Wohnort-Kategorien von links (nah) nach rechts (fern); die Breite folgt der Kontaktzahl, die Höhe der Reihenfolge der sozialen Struktur",
        "question": "Wie sind lokale, überregionale und transkontinentale Beziehungen im persönlichen Netzwerk verflochten – welche bestätigten Beziehungen verlaufen innerhalb, welche zwischen geografischen Bereichen?",
        "encodings": ["Band: Wohnort-Kategorie (fünf Stufen)", "Linie: bestätigte Beziehung zwischen zwei Kontakten", "dunkle Linie: zwischen Bereichen", "helle Linie: innerhalb eines Bereichs", "Knotenfarbe: Wohnort-Kategorie"],
        "limits": ["Ego ist nicht Teil des Graphen und trägt keine Linien", "Bänder sind Kategorien, keine Entfernungen; die Höhe im Band zeigt keine Nähe", "räumliche Trennung der Bänder ist keine soziale Trennung", "keine Aussage über Integration oder Segregation", "Paare ohne Linie sind unbekannt, solange die Paarabdeckung nicht belegt ist"],
        "options": ["tie_highlight: between | within | none"],
        "decision": "Prototyp; Variante G2-A. Die Wahl des Standardlayouts liegt beim Projektleiter.",
    },
    "fig_G2b_geografisches_kraftlayout": {
        "title": "Geografische Verflechtung (Kraftlayout)",
        "base": "Geografisch eingeschränktes Kraftlayout: Ego im Zentrum als Bezugspunkt; die Wohnort-Kategorie bestimmt die radiale Zone (der Radius eines Kontakts bleibt in einem schmalen Fenster seiner Zone), die bestätigten Beziehungen ziehen verbundene Kontakte zusammen, alle Kontakte stoßen sich ab",
        "question": "Wie sind lokale, überregionale und transkontinentale Beziehungen im persönlichen Netzwerk verflochten – welche sozialen Teilnetze erstrecken sich über mehrere geografische Räume?",
        "encodings": ["Zone (konzentrische Ellipse): Wohnort-Kategorie (fünf Stufen)", "Linie: bestätigte Beziehung zwischen zwei Kontakten", "dunkle Linie: zwischen Zonen", "helle Linie: innerhalb einer Zone", "Knotenfarbe: Wohnort-Kategorie"],
        "limits": ["Radialer Abstand bedeutet Wohnort-Kategorie, nicht Kilometer, nicht subjektive Nähe und nicht graphentheoretische Distanz", "die Abstände zwischen den Zonen sind eine grafische Konvention; die horizontale Streckung (Faktor 1,3) ist reine Seitenformat-Konvention", "Winkel und Abstände innerhalb einer Zone tragen keine eigene Bedeutung", "Ego ist nicht Teil des Graphen und trägt keine Linien", "keine Aussage über Integration oder Segregation", "Paare ohne Linie sind unbekannt, solange die Paarabdeckung nicht belegt ist"],
        "options": ["tie_highlight: between | within | none"],
        "decision": "Prototyp; Variante G2-B, aktueller Kandidat nach Sichtprüfung (Gruppenkompaktheit). Die Wahl des Standardlayouts liegt beim Projektleiter.",
    },
    "fig_G2_1_vergleich_a_b": {
        "title": "Variantenvergleich G2-A / G2-B",
        "base": "Arbeitsabbildung: beide G2-Varianten mit Lesbarkeitsmaßen",
        "question": "Welche geografische Anordnung zeigt die Verflechtung am besten?",
        "encodings": ["Kreuzungen", "Knotenabstand relativ zur mittleren Beziehungslänge", "Gruppenkompaktheit (kleiner = erhobene Gruppen bleiben zusammen)"],
        "limits": ["die Kennzahlen vergleichen Darstellungen und sagen nichts über die Daten"],
    },
    "fig_G2_geografisches_beziehungsnetz": {
        "title": "Kontakte und Beziehungen nach Wohnort (frühere Fassung mit Ego-Linien)",
        "base": "Geografie-Layout: Bänder gleicher Breite; Ego links mit hellen Zugehörigkeitslinien",
        "question": "Verlaufen die erhobenen Beziehungen innerhalb oder zwischen den geografischen Bereichen?",
        "encodings": ["Band: Wohnort-Kategorie", "Linienstärke/-farbe: Beziehung innerhalb / zwischen Bereichen", "helle Linie: Ego–Kontakt"],
        "limits": ["Bänder sind Kategorien, keine Entfernungen; die Höhe im Band zeigt keine Nähe"],
        "decision": "Frühere Fassung, nur zur Nachvollziehbarkeit erhalten; ersetzt durch G2-A und G2-B (ohne Ego-Linien).",
    },
    "fig_P1_distanz_und_naehe": {
        "title": "Räumliche Einordnung und subjektive Nähe",
        "base": "Matrix: Spalten = Wohnort-Kategorie, Zeilen = erhobene Nähe (Tabellenwert)",
        "question": "Wie verhalten sich die geografische Einordnung der Kontakte und ihre subjektiv erlebte Nähe zu Ego zueinander?",
        "encodings": ["Chip: ein Kontakt (ID)", "Spalte: Wohnort-Kategorie", "Zeile: Nähe (Tabellenwert 1–5)", "Zeile „nicht erfasst“: kein Nähewert"],
        "limits": ["Kategorien, keine Kilometerskala", "Nähe wird nicht geschätzt; fehlende Angaben stehen in eigener Zeile", "zeigt Konstellationen, keine Ursachen"],
    },
    "fig_P2_sprachliche_praktiken": {
        "title": "Sprachliche Praktiken in sozialen Teilgruppen",
        "base": "Struktur-Layout wie B2/B3; die Position ändert sich mit der Sprachansicht nicht",
        "question": "Wie verteilen sich sprachliche Praktiken über die sozialen Teilgruppen des persönlichen Netzwerks?",
        "encodings": ["Knotenfarbe: Sprachmodus (Standardansicht) oder Verwendung einer Sprache", "Ring: mehrere genannte Sprachen", "Ego–Kontakt-Linie in Sprachfarbe: Sprache wird mit diesem Kontakt genannt", "weiche Fläche: erhobene Kontaktgruppe"],
        "limits": ["die Sprache gehört zur Kommunikation zwischen Ego und Kontakt, nicht zwischen den Kontakten", "genannte Sprachen und typischer Sprachmodus sind getrennte Angaben", "mehrere Sprachen bleiben mehrere, keine Hauptsprache wird abgeleitet"],
        "options": ["language_view: mode | mode:<code> | lang:<code> | multilingual"],
    },
    "fig_P3_einbettung_und_kommunikation": {
        "title": "Wohnort, Kontakthäufigkeit und Kommunikationsmedien",
        "base": "Matrix: Spalten = Wohnort-Kategorie, Zeilen = Kontakthäufigkeit insgesamt",
        "question": "Welche Rolle spielen Kontakthäufigkeit und Kommunikationsmedien in lokalen und räumlich entfernten Beziehungen?",
        "encodings": ["Chip: ein Kontakt (ID)", "Symbole auf dem Chip: genannte Medien (persönlich ●, Telefon ▲, digital ■)", "Zeile: Kontakthäufigkeit der Beziehung insgesamt"],
        "limits": ["Medien sind Mehrfachangaben; persönliche und digitale Kommunikation können zugleich vorkommen", "die Kontakthäufigkeit gilt nicht je Medium", "ein genanntes digitales Medium heißt nicht, dass die Beziehung überwiegend digital geführt wird", "keine Kausalaussage über Medien und Nähe"],
    },
    "fig_B0_layoutvergleich": {"title": "Layoutvergleich B0", "base": "Arbeitsabbildung", "question": "Welches kraftbasierte Layout eignet sich für B1/B2?", "encodings": ["Kreuzungen, Knotenabstand"], "limits": ["die Kennzahlen vergleichen Layouts und sagen nichts über die Daten"]},
    "fig_B3_0_layoutvergleich": {"title": "Layoutvergleich B3", "base": "Arbeitsabbildung", "question": "Wie wird Ego in das Struktur-Layout gesetzt?", "encodings": ["Kreuzungen, gestreifte Kontakte"], "limits": ["die Kennzahlen vergleichen Layouts und sagen nichts über die Daten"]},
    "fig_G2_0_variantenvergleich": {"title": "Variantenvergleich G2 (Ringe / Bänder)", "base": "Arbeitsabbildung", "question": "Ringe oder Bänder für die geografische Gliederung?", "encodings": ["Kreuzungen, Knotenabstand"], "limits": ["die Kennzahlen vergleichen Darstellungen und sagen nichts über die Daten"]},
    "fig_C_geografisches_profil": {"title": "Geografisches Netzwerkprofil", "base": "Tabelle", "question": "Wo wohnen die Kontakte, wo sind sie geboren (laut Angabe)?", "encodings": ["Chip: Kontakt", "Spalte: Wohnort-Kategorie"], "limits": ["Wohn- und Geburtsland bilden keine Herkunftsgruppen"]},
    "fig_D1_sprachprofil": {"title": "Sprachliches Netzwerkprofil", "base": "Matrix", "question": "Welche Sprachen und Sprachmodi gibt es je Kontakt?", "encodings": ["Punkt: Sprache genannt", "Modus: typischer Sprachmodus"], "limits": ["keine Hauptsprache"]},
    "fig_D2_ego_sprachmodus": {"title": "Egozentriertes Netzwerk: Sprachmodus", "base": "Nähe-Layout wie A", "question": "Wie verteilen sich Sprachmodi über die Nähezonen?", "encodings": ["Farbe: Sprachmodus"], "limits": ["der Radius ist die Nähe, nicht der Sprachmodus"]},
    "fig_E_deskriptive_uebersicht": {"title": "Deskriptive Übersicht", "base": "Balkendiagramme", "question": "Wie sind die erhobenen Merkmale verteilt?", "encodings": ["Balken: Zahl der Kontakte"], "limits": ["explorativ, keine Inferenz"]},
}


def note_for(stem: str) -> dict[str, object]:
    return NOTES.get(stem, {"title": stem})
