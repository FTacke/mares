"""Figure E: descriptive overviews (exploratory, no inference).

Eight small bar charts of what was recorded: places of residence, relation types, contact frequency,
closeness, languages, language mode, media, functions. Bars count contacts; for multi-code fields a
contact is counted once per code, so the bars of such a panel can add up to more than n.
"""

from __future__ import annotations

from collections import Counter

from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from ..analysis import AnalysisParams, SurveyStatus, attribute_counts, residence_of
from ..model import NetworkDataset
from .style import BAR_COLOR, GEO_COLORS, INK, LANGUAGE_COLORS, MODE_COLORS, MUTED, FAINT, frame, new_figure, rc, wrap

_MAX_PLACES = 12


def _bars(ax, title: str, rows: list[tuple[str, int, str]], n: int, note: str = "") -> None:
    labels = [wrap(label, 38) for label, _, _ in rows]
    positions = list(range(len(rows)))
    ax.barh(positions, [count for _, count, _ in rows], color=[color for _, _, color in rows], height=0.66, edgecolor=["#6C757D" if c == "#FFFFFF" else "none" for _, _, c in rows])
    ax.set_yticks(positions, labels, fontsize=7.6, color=INK)
    ax.invert_yaxis()
    for p, (_, count, _) in zip(positions, rows):
        ax.text(count + max(n, 1) * 0.012, p, str(count), va="center", fontsize=8, color=INK)
    ax.set_xlim(0, max(n, max((c for _, c, _ in rows), default=0)) * 1.12 + 0.3)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
    ax.tick_params(axis="x", labelsize=7.2, colors=MUTED, length=2)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=FAINT, linewidth=0.5)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#AEB6BD")
    ax.set_title(title, loc="left", fontsize=9.8, fontweight="bold", color=INK, pad=17 if note else 8)
    if note:
        ax.text(0, 1.02, note, transform=ax.transAxes, fontsize=7.4, color=MUTED, va="bottom", ha="left")


def overview_figure(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams):
    with rc():
        n = len(dataset.contacts)
        panels = []

        places: Counter[tuple[str, object]] = Counter()
        for contact in dataset.contacts:
            residence = residence_of(contact, params)
            places[(residence.city or "Ort nicht erfasst", residence.category)] += 1
        place_rows = [(f"{city}", count, GEO_COLORS[category]) for (city, category), count in sorted(places.items(), key=lambda kv: (-kv[1], kv[0][0]))]
        if len(place_rows) > _MAX_PLACES:
            rest = place_rows[_MAX_PLACES - 1 :]
            place_rows = place_rows[: _MAX_PLACES - 1] + [(f"weitere Orte ({len(rest)})", sum(c for _, c, _ in rest), "#9A9A9A")]
        panels.append(("Aufenthaltsorte (Wohnort)", place_rows, "Farbe wie Abbildung A"))

        def coded(attribute: str, field: str, title: str, colors: dict[str, str] | None = None, note: str = "") -> None:
            rows, missing = attribute_counts(dataset, attribute, field)
            out = [(f"{code} · {meaning}", count, (colors or {}).get(code, BAR_COLOR)) for code, meaning, count in rows]
            if missing:
                out.append(("nicht erfasst", missing, "#C9CED3"))
            panels.append((title, out, note))

        multi = "Mehrfachnennungen: Summe kann n übersteigen"
        coded("relation", "relation", "Beziehungstypen", note=multi)
        coded("contact_frequency", "contact_frequency", "Kontakthäufigkeit")
        coded("closeness", "closeness_1_5", "Nähe (Tabellenwert 1–5)")
        coded("language", "language", "Verwendete Sprachen", LANGUAGE_COLORS, multi)
        coded("language_mode", "language_mode", "Typischer Sprachmodus", MODE_COLORS)
        coded("media", "media", "Kommunikationsmedien", note=multi)
        coded("function", "function", "Funktionen der Kontakte", note=multi)

        height = 15.2
        fig = new_figure(13.6, height)
        frame(
            fig,
            "Deskriptive Übersicht über die erfassten Kontaktmerkmale",
            f"Zahl der Kontakte je Ausprägung (n = {n}); explorativ-deskriptiv, keine inferenzstatistische Auswertung; leere Kategorien bleiben sichtbar",
            status,
            "Zählungen der Angaben der Quelle; „nicht erfasst“ = leeres Feld, nicht „trifft nicht zu“. Die Verteilungen sind kein Maß für Struktur oder Vollständigkeit des Netzwerks.",
        )
        grid = fig.add_gridspec(4, 2, left=0.21, right=0.985, top=1 - 1.45 / height, bottom=0.075, hspace=0.62, wspace=0.85)
        for index, (title, rows, note) in enumerate(panels):
            ax = fig.add_subplot(grid[index // 2, index % 2])
            _bars(ax, title, rows, n, note)
    return fig
