"""Figure B3 and its layout comparison: the personal network *including ego*.

Ego (one dark node) is tied to every contact; the contacts are tied to each other by the confirmed
alter-alter ties. Two kinds of line, kept visibly apart:

* ego-alter lines (thin, pale): membership of the contact in the personal network -- not a surveyed relation
  between persons, and not the subjective closeness (that is figure A);
* alter-alter lines (as in B1/B2): the confirmed, surveyed relations.

Because ego joins everybody, this graph is connected by construction. That is not a finding and no
structure measure is taken from it; measures rest on the alter-alter graph without ego (B1/B2).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace

from matplotlib.collections import LineCollection

from mares.core import ids

from ..analysis import AnalysisParams, SurveyStatus, geo_labels
from ..build import Network
from ..model import NetworkDataset
from . import ego_layouts, layouts
from .common import contact_views, draw_legend
from .network import (
    NODE_DIAMETER_PT, TIE_COLOR, TIE_WIDTH_PT, Structure, _elicitation_sentence, _frame_axes, _halo, _to_data, _to_pt,
    build_structure, draw_groups, place_labels,
)
from . import design
from .style import GEO_COLORS, GEO_ORDER, INK, MUTED, frame, group_color, new_figure, rc, rim_color, wrap

EGO_DIAMETER_PT = 22.0
EGO_LINE_COLOR = "#C5CCD3"
EGO_LINE_WIDTH_PT = 0.5


@dataclass(frozen=True)
class EgoStructure:
    """The alter-alter structure (as drawn in B1/B2 or re-laid-out together with ego) plus ego's place."""

    structure: Structure
    ego: tuple[float, float]
    variant: str

    @property
    def positions(self) -> dict[str, tuple[float, float]]:
        return {**self.structure.positions, ego_layouts.EGO: self.ego}


def build_ego_structure(network: Network, variant: str = ego_layouts.DEFAULT_EGO_VARIANT) -> EgoStructure:
    base = build_structure(network)  # the alter-alter layout of B1/B2
    graph = base.graph
    positions = ego_layouts.compute_ego_layout(graph, variant)
    ego = positions.pop(ego_layouts.EGO)
    structure = Structure(graph, positions, base.components, base.isolates, base.variant)
    return EgoStructure(structure, ego, variant)


@dataclass(frozen=True)
class DrawStyle:
    """How draw_ego_structure draws. The defaults are the working (analysis) look of B3; the clean profile and the
    perspectives change sizes and the emphasis of lines and nodes, never the positions."""

    node_pt: float = NODE_DIAMETER_PT
    ego_pt: float = EGO_DIAMETER_PT
    ego_label_pt: float = 6.6
    font_pt: float = 7.6
    tie_color: str = TIE_COLOR
    tie_width: float = TIE_WIDTH_PT
    tie_alpha: float = 0.9
    ego_line_color: str = EGO_LINE_COLOR
    ego_line_width: float = EGO_LINE_WIDTH_PT
    # per-contact overrides (contact id -> value); a contact not listed keeps the default
    ego_line_colors: tuple = ()  # ((id, colour), ...)
    ego_line_widths: tuple = ()  # ((id, width), ...)
    rim_colors: tuple = ()  # ((id, colour), ...) a node's rim
    rim_widths: tuple = ()
    rings: tuple = ()  # (id, ...) contacts that get a second, hollow ring around the node
    tie_overrides: tuple = ()  # (((a, b), colour, width, zorder), ...) ties drawn separately


def draw_ego_structure(ax, es: EgoStructure, colors: dict[str, str], *, label: bool = True, node_pt: float | None = None,
                       style: DrawStyle | None = None):
    """Ego lines, alter-alter ties, contacts, ego, ids. Returns the label boxes (in points)."""
    style = style or DrawStyle()
    if node_pt is not None:
        style = replace(style, node_pt=node_pt)
    positions = es.structure.positions
    everything = es.positions
    _frame_axes(ax, everything, margin=0.16)
    nodes = sorted(positions, key=ids.contact_number)
    line_colors = dict(style.ego_line_colors)
    line_widths = dict(style.ego_line_widths)
    ego_segments = [(es.ego, positions[c]) for c in nodes]
    if ego_segments:
        ax.add_collection(LineCollection(ego_segments, colors=[line_colors.get(c, style.ego_line_color) for c in nodes],
                                         linewidths=[line_widths.get(c, style.ego_line_width) for c in nodes], zorder=1.6, capstyle="round"))
    edges = [tuple(e) for e in es.structure.graph.edges]
    special = {tuple(pair): (colour, width, z) for pair, colour, width, z in style.tie_overrides}
    plain = [e for e in edges if tuple(e) not in special and tuple(reversed(e)) not in special]
    segments = [(positions[a], positions[b]) for a, b in plain]
    if segments:
        ax.add_collection(LineCollection(segments, colors=style.tie_color, linewidths=style.tie_width, alpha=style.tie_alpha, zorder=2, capstyle="round"))
    for pair, (colour, width, z) in special.items():
        a, b = pair
        ax.add_collection(LineCollection([(positions[a], positions[b])], colors=colour, linewidths=width, alpha=style.tie_alpha, zorder=z, capstyle="round"))
    rims, rim_widths = dict(style.rim_colors), dict(style.rim_widths)
    ax.scatter([positions[c][0] for c in nodes], [positions[c][1] for c in nodes], s=style.node_pt**2, c=[colors[c] for c in nodes],
               edgecolors=[rims.get(c, rim_color(colors[c])) for c in nodes], linewidths=[rim_widths.get(c, 0.8) for c in nodes], zorder=4)
    ringed = [c for c in nodes if c in set(style.rings)]
    if ringed:
        ax.scatter([positions[c][0] for c in ringed], [positions[c][1] for c in ringed], s=(style.node_pt + 6.0) ** 2, facecolors="none",
                   edgecolors=INK, linewidths=1.1, zorder=3.9)
    ax.scatter([es.ego[0]], [es.ego[1]], s=style.ego_pt**2, c=INK, edgecolors="white", linewidths=1.2, zorder=5)
    ax.text(es.ego[0], es.ego[1], "EGO", ha="center", va="center", fontsize=style.ego_label_pt, fontweight="bold", color="white", zorder=6)
    boxes: list[tuple[float, float, float, float]] = []
    if label:
        pts = {c: _to_pt(ax, positions[c]) for c in nodes}
        ego_pt = _to_pt(ax, es.ego)
        soft = tuple((ego_pt, pts[c]) for c in nodes)
        placed = place_labels(pts, edges, ego_pt, obstacles=((ego_pt[0], ego_pt[1], style.ego_pt / 2),), soft_segments=soft,
                              font_pt=style.font_pt, node_pt=style.node_pt + (6.0 if ringed else 0.0))
        for cx, cy, text in placed.values():
            data = _to_data(ax, (cx, cy))
            w, h = 0.62 * style.font_pt * len(text) + 2, style.font_pt * 1.15
            boxes.append((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
            ax.text(data[0], data[1], text, ha="center", va="center", fontsize=style.font_pt, color=INK, zorder=7, path_effects=[_halo()])
    return boxes


def _legend(es: EgoStructure, views, labels, network: Network, with_groups: bool):
    geo_counts = Counter(v.geo for v in views)
    n = len(es.structure.positions)
    ties = es.structure.graph.number_of_edges()
    sections = [
        ("Ego", [("dot", INK, "Ego (befragte Person)")]),
        ("Kontakte nach Wohnort", [("dot", GEO_COLORS[g], f"{labels[g]}  (n = {geo_counts[g]})") for g in GEO_ORDER if geo_counts[g]]),
        ("Linien", [
            ("line", EGO_LINE_COLOR, wrap(f"Ego – Kontakt: Zugehörigkeit zum persönlichen Netzwerk (n = {n})", 34)),
            ("line", TIE_COLOR, wrap(f"Kontakt – Kontakt: erhobene, bestätigte Beziehung (n = {ties})", 34)),
        ]),
    ]
    if with_groups:
        members_of = dict(network.confirmed_groups)
        ordered = sorted(members_of)
        sections.append((
            "Erhobene Kontaktgruppen\n(Fläche hinter dem Netz)",
            [("swatch", group_color(g, ordered), f"{g}: {len(members_of[g])} Kontakte") for g in ordered]
            + [("text", "", "Überlappung = gemeinsame Mitglieder")],
        ))
    return sections


def fit_height(positions: dict[str, tuple[float, float]], margin: float, axes_width_in: float, low: float, high: float) -> float:
    """Height in inches of an equal-aspect axes of the given width that fits the positions, kept inside [low, high]."""
    xs, ys = [p[0] for p in positions.values()], [p[1] for p in positions.values()]
    dx, dy = (max(xs) - min(xs)) + 2 * margin, (max(ys) - min(ys)) + 2 * margin
    return min(high, max(low, axes_width_in * dy / dx))


def ego_network_figure(
    dataset: NetworkDataset,
    status: SurveyStatus,
    params: AnalysisParams,
    *,
    network: Network,
    show_groups: bool = True,
    variant: str = ego_layouts.DEFAULT_EGO_VARIANT,
    structure: EgoStructure | None = None,
    profile: str = "clean",
):
    """B3: ego, all contacts, the ego-contact lines and the confirmed contact-contact ties.

    The surveyed groups appear as very soft areas (``show_groups``), enough to see the overlap of nested groups
    without competing with the two kinds of line. ``profile``: ``clean`` (reduced text, large drawing; the standard)
    or ``analysis`` (the working version with the fuller notes). The positions are the same.
    """
    design.check_profile(profile)
    if profile == "analysis":
        return _ego_network_analysis(dataset, status, params, network=network, show_groups=show_groups, variant=variant, structure=structure)
    with rc():
        es = structure or build_ego_structure(network, variant)
        views = contact_views(dataset, params)
        labels = geo_labels(params)
        colors = {v.contact_id: GEO_COLORS[v.geo] for v in views}
        width = 13.0
        axes_h = fit_height(es.positions, 0.16, width * 0.96, 5.6, 7.4)
        height = axes_h + 2.25
        fig = new_figure(width, height)
        counts = Counter(v.geo for v in views)
        entries = [("dot", GEO_COLORS[g], design.zone_name(g, params)) for g in GEO_ORDER if counts[g]]
        entries += [("line", design.EGO_LINE, "Ego – Kontakt"), ("line", design.TIE_NORMAL, "Beziehung zwischen Kontakten")]
        if show_groups and network.confirmed_groups:
            entries.append(("area", "#6C7A89", "Kontaktgruppe"))
        hint = "Der Abstand zu Ego zeigt keine Nähe. " + ("Paare ohne Linie: verneint." if status.completeness == "complete" else "Paare ohne Linie: unbekannt.")
        top, bottom = design.clean_frame(fig, "Persönliches Beziehungsnetz", None, hint, status)
        top = design.legend_strip(fig, entries, top=top)
        ax = fig.add_axes([0.02, bottom, 0.96, top - bottom])
        draw_style = DrawStyle(
            node_pt=design.NODE_DIAMETER_PT, ego_pt=design.EGO_DIAMETER_PT, ego_label_pt=design.EGO_LABEL_PT, font_pt=design.ID_PT,
            tie_color=design.TIE_NORMAL, tie_width=design.TIE_WIDTH_PT, ego_line_color=design.EGO_LINE, ego_line_width=design.EGO_LINE_WIDTH_PT,
        )
        _frame_axes(ax, es.positions, margin=0.16)
        boxes = draw_ego_structure(ax, es, colors, style=draw_style)
        if show_groups:
            ego_pt = _to_pt(ax, es.ego)
            draw_groups(ax, es.structure, network, boxes, fill_alpha=design.GROUP_FILL_ALPHA, line_alpha=design.GROUP_LINE_ALPHA,
                        extra_obstacles=((ego_pt[0], ego_pt[1], design.EGO_DIAMETER_PT / 2),), tag_pt=design.GROUP_TAG_PT, node_pt=design.NODE_DIAMETER_PT)
    return fig


def _ego_network_analysis(
    dataset: NetworkDataset,
    status: SurveyStatus,
    params: AnalysisParams,
    *,
    network: Network,
    show_groups: bool,
    variant: str,
    structure: EgoStructure | None,
):
    with rc():
        es = structure or build_ego_structure(network, variant)
        views = contact_views(dataset, params)
        labels = geo_labels(params)
        colors = {v.contact_id: GEO_COLORS[v.geo] for v in views}
        fig = new_figure(12.6, 8.6)
        ax = fig.add_axes([0.02, 0.125, 0.71, 0.765])
        _frame_axes(ax, es.positions, margin=0.16)
        boxes = draw_ego_structure(ax, es, colors)  # fixes the label boxes in points
        remarks: list[str] = []
        if show_groups:
            ego_pt = _to_pt(ax, es.ego)
            remarks = draw_groups(ax, es.structure, network, boxes, fill_alpha=0.07, line_alpha=0.4,
                                  extra_obstacles=((ego_pt[0], ego_pt[1], EGO_DIAMETER_PT / 2),))
        legend_ax = fig.add_axes([0.745, 0.14, 0.245, 0.75])
        draw_legend(legend_ax, _legend(es, views, labels, network, show_groups), line=0.05)
        n, ties = len(es.structure.positions), es.structure.graph.number_of_edges()
        note = (
            f"{_elicitation_sentence(status)} Ego ist mit allen Kontakten verbunden: die hellen Linien zeigen die Zugehörigkeit zum persönlichen Netzwerk, "
            f"nicht erhobene Beziehungen. {status.short_note()}\n"
            f"Die Position ergibt sich aus den Kontakt–Kontakt-Beziehungen ({ego_layouts.EGO_VARIANT_LABELS[es.variant]}, fester Seed). Der Abstand zu Ego misst keine Nähe "
            "(subjektive Nähe: Abbildung A); der Abstand zwischen getrennten Gruppen ist keine soziale oder geografische Distanz.\n"
            "Weil Ego alle Kontakte verbindet, ist dieses Netz zwangsläufig zusammenhängend – das ist kein Befund; Strukturmaße beruhen auf dem Netz ohne Ego (B1, B2)."
            + ("\nHinweis zur Darstellung: " + "; ".join(remarks) + "." if remarks else "")
        )
        frame(
            fig,
            "Persönliches Netzwerk einschließlich Ego" + (" – mit erhobenen Kontaktgruppen" if show_groups else ""),
            f"Ego und {n} Kontakte · {n} Ego–Kontakt-Linien · {ties} bestätigte Kontakt–Kontakt-Beziehungen",
            status,
            note,
        )
    return fig


def ego_layout_comparison_figure(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams, *, network: Network):
    """The same personal network under every ego layout variant, with readability measures (a working figure)."""
    with rc():
        views = contact_views(dataset, params)
        colors = {v.contact_id: GEO_COLORS[v.geo] for v in views}
        edges = [t.pair for t in network.positive_ties]
        base = build_structure(network)
        fig = new_figure(16.5, 7.4)
        frame(
            fig,
            "Layoutvergleich B3: Ego im Netzwerk der Kontakte",
            "Arbeitsabbildung zur Wahl des Layouts von B3; alle Varianten nutzen nur die erhobenen Beziehungen, jeder Lauf mit festem Seed",
            status,
            "Kreuzungen: alle Linienpaare, die sich schneiden (Linien mit gemeinsamem Knoten ausgenommen). „Struktur wie B2“: Korrelation der Abstände zwischen den "
            "Kontakten mit dem Layout ohne Ego (1 = identisch). Die Kennzahlen vergleichen Layouts und sagen nichts über die Daten.",
        )
        for index, variant in enumerate(ego_layouts.EGO_VARIANTS):
            es = build_ego_structure(network, variant)
            measures = ego_layouts.measure_ego(es.positions, edges, base.positions)
            left = 0.015 + index * 0.328
            ax = fig.add_axes([left, 0.13, 0.31, 0.63])
            draw_ego_structure(ax, es, colors, node_pt=9.5)
            fig.text(left + 0.005, 0.885, ego_layouts.EGO_VARIANT_LABELS[variant], fontsize=10.5, fontweight="bold", color=INK, ha="left", va="bottom")
            fig.text(left + 0.005, 0.87, wrap(measures.summary(), 78), fontsize=7.4, color=MUTED, ha="left", va="top", linespacing=1.3)
    return fig
