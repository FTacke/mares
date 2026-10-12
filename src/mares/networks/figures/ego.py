"""Figures A and D2: the ego-centred view.

Ego in the centre, concentric zones for the **table** value of closeness (never the position on
the hand-drawn map). The same layout serves two encodings -- geography (A) and language mode (D2) --
so that a contact sits at the same place in both figures.
"""

from __future__ import annotations

from collections import Counter

from matplotlib.patches import Circle
from matplotlib.patheffects import withStroke

from ..analysis import AnalysisParams, SurveyStatus, geo_labels
from ..model import NetworkDataset
from .common import EGO_RADIUS, NODE_RADIUS, ContactView, EgoLayout, contact_views, draw_legend, draw_node, ego_layout
from .style import GEO_COLORS, GEO_ORDER, INK, LANGUAGE_SHORT, MODE_COLORS, MUTED, frame, new_figure, rc

_SCALE_TITLE = "Nähezonen (Tabellenwert „closeness“, 1–5)\ninnen = nah, außen = weniger nah"
_POSITION_NOTE = (
    "Radius = Tabellenwert der Nähe (1–5), nicht die Position auf der handgezeichneten Netzwerkkarte; die Kartenlegende wurde nicht umgerechnet. "
    "Winkel und Reihenfolge innerhalb einer Zone\nsind rein darstellerisch (nach Wohnort, dann ID) und tragen keine Information."
)


def _zones(dataset: NetworkDataset) -> list[str]:
    """Closeness codes from closest (highest value) to farthest, as the codebook defines them."""
    return sorted(dataset.codebook.codes("closeness_1_5"), key=lambda code: -int(code) if code.isdigit() else 0)


def _draw_zones(ax, layout: EgoLayout) -> None:
    n = len(layout.zone_codes)
    for index in range(n - 1, -1, -1):  # outermost first so inner discs lie on top
        inner, outer = layout.band_bounds[index]
        tint = 0.972 - 0.017 * (n - index)
        ax.add_patch(
            Circle((0, 0), outer, facecolor=(tint, tint + 0.004, tint + 0.012), edgecolor="#AEB6BD", linewidth=0.9, zorder=1 + 0.1 * (n - index))
        )
    for index, code in enumerate(layout.zone_codes):
        inner, outer = layout.band_bounds[index]
        mid = (inner + outer) / 2
        ax.scatter([0], [mid], s=260, c="white", edgecolors="#8D969E", linewidths=1.0, zorder=3)
        ax.text(0, mid, code, ha="center", va="center", fontsize=9.5, fontweight="bold", color=INK, zorder=4)
    if layout.unrecorded_band:
        inner, outer = layout.unrecorded_band
        ax.add_patch(Circle((0, 0), outer, facecolor="none", edgecolor="#8D969E", linewidth=0.9, linestyle=(0, (4, 3)), zorder=1.0))
        ax.scatter([0], [(inner + outer) / 2], s=260, c="white", edgecolors="#8D969E", linewidths=1.0, zorder=3)
        ax.text(0, (inner + outer) / 2, "?", ha="center", va="center", fontsize=10, fontweight="bold", color=MUTED, zorder=4)
    ax.add_patch(Circle((0, 0), EGO_RADIUS, facecolor=INK, edgecolor="white", linewidth=1.5, zorder=6))
    ax.text(0, 0, "EGO", ha="center", va="center", fontsize=8.5, fontweight="bold", color="white", zorder=7)


def _zone_legend(dataset: NetworkDataset, layout: EgoLayout, views: list[ContactView]):
    counts = Counter(v.closeness for v in views)
    entries = []
    for code in layout.zone_codes:
        meaning = dataset.codebook.meaning("closeness_1_5", code)
        n = counts.get(code, 0)
        entries.append(("ring", "#FFFFFF", f"{code} · {meaning}  (n = {n})" if n else f"{code} · {meaning}\n     (keine Kontakte)"))
    if layout.unrecorded_band:
        entries.append(("ring", "#FFFFFF", f"? · Nähe nicht erfasst  (n = {sum(1 for v in views if v.closeness not in layout.zone_codes)})"))
    return (_SCALE_TITLE, entries)


def _canvas(title: str, subtitle: str, status: SurveyStatus, note: str, layout: EgoLayout):
    fig = new_figure(13.2, 9.6)
    frame(fig, title, subtitle, status, note)
    ax = fig.add_axes([0.02, 0.12, 0.62, 0.77])
    limit = layout.outer_radius + 0.45
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_aspect("equal")
    ax.axis("off")
    legend = fig.add_axes([0.68, 0.12, 0.30, 0.76])
    return fig, ax, legend


def proximity_figure(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams):
    """Figure A: ego-centred network, colour = geographic category of the residence."""
    with rc():
        views = contact_views(dataset, params)
        labels = geo_labels(params)
        layout = ego_layout(views, _zones(dataset))
        note = _POSITION_NOTE + "\nKategorien beschreiben den Wohnort, nicht die Person; ungefähre oder mehrdeutige Angaben sind nicht präzisiert."
        fig, ax, legend = _canvas(
            "Egozentriertes Netzwerk: Nähe und Wohnort der Kontakte",
            "Jeder Punkt ist ein Kontakt (ID); Farbe = geografische Einordnung des Wohnorts; Beziehungen zwischen Kontakten sind hier nicht dargestellt",
            status,
            note,
            layout,
        )
        _draw_zones(ax, layout)
        for view in views:
            draw_node(ax, layout.positions[view.contact_id], view.contact_id, GEO_COLORS[view.geo], flagged=view.flagged)
        geo_counts = Counter(v.geo for v in views)
        sections = [
            _zone_legend(dataset, layout, views),
            ("Wohnort des Kontakts", [("dot", GEO_COLORS[g], f"{labels[g]}  (n = {geo_counts[g]})") for g in GEO_ORDER if geo_counts[g] or g is not GEO_ORDER[-1]]),
            ("Zeichen", [("flag", "#FFFFFF", "gestrichelter Rand: offene Prüfhinweise\n(siehe Prüfbericht)")]),
        ]
        draw_legend(legend, sections)
    return fig


def language_mode_figure(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams):
    """Figure D2: the same layout, colour = typical language mode (the respondent's own coding).

    Beneath each contact, the languages named for that contact -- listed in codebook order, which
    is not a ranking. No dominant language is derived from several languages.
    """
    with rc():
        views = contact_views(dataset, params)
        labels = geo_labels(params)
        layout = ego_layout(views, _zones(dataset))
        fig, ax, legend = _canvas(
            "Egozentriertes Netzwerk: Sprachmodus der Kontakte",
            "Farbe = typischer Sprachmodus laut Tabelle; Kürzel unter dem Punkt = alle genannten Sprachen (Reihenfolge des Codebuchs, keine Rangfolge)",
            status,
            _POSITION_NOTE + "\nDer Sprachmodus ist die codierte Angabe der Erhebung; er wird nicht aus den Sprachen berechnet. Mehrsprachige Kontakte bleiben mehrsprachig.",
            layout,
        )
        _draw_zones(ax, layout)
        for view in views:
            x, y = layout.positions[view.contact_id]
            fill = MODE_COLORS.get(view.language_mode or "", "#FFFFFF")
            draw_node(ax, (x, y), view.contact_id, fill, flagged=view.flagged)
            if fill == "#FFFFFF":  # a white disc needs a visible rim
                ax.add_patch(Circle((x, y), NODE_RADIUS, facecolor="none", edgecolor="#6C757D", linewidth=0.9, linestyle=(0, (1.2, 1.2)), zorder=5.5))
            tag = " ".join(LANGUAGE_SHORT.get(code, code) for code in view.languages) or "–"
            ax.text(x, y - 0.43, tag, ha="center", va="center", fontsize=6.8, color=INK, zorder=6,
                    path_effects=[withStroke(linewidth=2.4, foreground="#F1F3F5")])
        mode_counts = Counter(v.language_mode for v in views)
        mode_entries = [
            ("dot", MODE_COLORS.get(code, "#FFFFFF"), f"{dataset.codebook.meaning('language_mode', code)}  (n = {mode_counts.get(code, 0)})")
            for code in dataset.codebook.codes("language_mode")
        ]
        if mode_counts.get(None):
            mode_entries.append(("dot", "#FFFFFF", f"nicht erfasst  (n = {mode_counts[None]})"))
        abbreviations = "\n".join(f"{LANGUAGE_SHORT.get(c, c)} = {dataset.codebook.meaning('language', c)}" for c in dataset.codebook.codes("language"))
        draw_legend(
            legend,
            [
                _zone_legend(dataset, layout, views),
                ("Typischer Sprachmodus", mode_entries),
                ("Sprachkürzel", [("text", "", abbreviations)]),
                ("Zeichen", [("flag", "#FFFFFF", "gestrichelter Rand: offene Prüfhinweise")]),
            ],
            line=0.040,
        )
    return fig
