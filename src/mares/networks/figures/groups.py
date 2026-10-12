"""Figure B: groups and documented alter-alter ties.

Only documented ties are drawn: those derived from confirmed group outlines. Pairs without a statement
are *unknown* and are never drawn, and no tie is invented to connect groups.

Layout: every connected component of the documented ties is laid out on its own (a circle for a
clique, a seeded spring layout otherwise) and the components are placed side by side in a fixed
order, so distance *between* components carries no meaning. Contacts without any documented tie
sit in a separate box, not as if they were isolated in the network.
"""

from __future__ import annotations

import math
from itertools import combinations

import networkx as nx
import numpy as np
from matplotlib.patches import FancyBboxPatch, Polygon, Circle
from matplotlib.lines import Line2D
from matplotlib.patheffects import withStroke

from mares.core import ids

from ..analysis import AnalysisParams, SurveyStatus, geo_labels
from ..build import Network
from ..model import NetworkDataset
from .common import NODE_RADIUS, ContactView, contact_views, draw_legend, draw_node
from .style import (
    CANDIDATE_COLOR, FAINT, GEO_COLORS, GEO_ORDER, INK, MUTED, NEUTRAL_TIE, frame, group_color, new_figure, rc,
)

SEED = 20260925  # fixed: the layout is reproducible
_SPACING = 3.0  # horizontal gap between components
_LABEL_DIRECTIONS = ((0.0, 1.0), (-0.45, -1.0), (1.0, -0.15), (-1.0, 0.2), (0.8, 0.9), (-0.8, -0.8))


def _is_clique(graph: nx.Graph) -> bool:
    n = graph.number_of_nodes()
    return graph.number_of_edges() == n * (n - 1) // 2


def component_layout(graph: nx.Graph) -> dict[str, tuple[float, float]]:
    """Positions inside one component, centred on the origin, roughly unit scale per node."""
    nodes = sorted(graph.nodes, key=ids.contact_number)
    n = len(nodes)
    if n == 1:
        return {nodes[0]: (0.0, 0.0)}
    if n == 2:
        return {nodes[0]: (-0.8, 0.0), nodes[1]: (0.8, 0.0)}
    if _is_clique(graph):
        radius = max(0.9, 0.46 * n / math.pi * 1.9)
        return {c: (radius * math.cos(math.pi / 2 + 2 * math.pi * i / n), radius * math.sin(math.pi / 2 + 2 * math.pi * i / n)) for i, c in enumerate(nodes)}
    # Rebuild the graph in sorted order: the iteration order of a set of strings changes from process to
    # process (hash randomisation), and the layout would change with it.
    ordered = nx.Graph()
    ordered.add_nodes_from(nodes)
    ordered.add_edges_from(sorted(tuple(sorted(e, key=ids.contact_number)) for e in graph.edges))
    initial = {c: (math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i, c in enumerate(nodes)}
    raw = nx.spring_layout(ordered, pos=initial, seed=SEED, iterations=400, k=1.1 / math.sqrt(n), scale=0.62 * math.sqrt(n) + 0.8)
    xs = np.array([raw[c][0] for c in nodes])
    ys = np.array([raw[c][1] for c in nodes])
    return {c: (float(raw[c][0] - xs.mean()), float(raw[c][1] - ys.mean())) for c in nodes}


def _hull(points: list[tuple[float, float]], pad: float) -> np.ndarray:
    """A padded outline round a set of points: the convex hull, each corner rounded by a circle."""
    pts = np.array(points, dtype=float)
    if len(pts) == 1:
        angles = np.linspace(0, 2 * math.pi, 40, endpoint=False)
        return np.c_[pts[0, 0] + pad * np.cos(angles), pts[0, 1] + pad * np.sin(angles)]
    angles = np.linspace(0, 2 * math.pi, 36, endpoint=False)
    cloud = np.vstack([p + pad * np.c_[np.cos(angles), np.sin(angles)] for p in pts])
    return _convex_hull(cloud)


def _convex_hull(points: np.ndarray) -> np.ndarray:
    ordered = sorted(map(tuple, points.tolist()))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[tuple[float, float]] = []
    for p in ordered:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[tuple[float, float]] = []
    for p in reversed(ordered):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])


def group_network_figure(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams, *, network: Network):
    with rc():
        views = {v.contact_id: v for v in contact_views(dataset, params)}
        labels = geo_labels(params)
        graph = nx.Graph()
        graph.add_nodes_from(network.contact_ids)
        for tie in network.positive_ties:
            graph.add_edge(tie.a, tie.b, groups=tie.group_ids)
        group_ids = sorted(g for g, _ in network.confirmed_groups)
        members_of = dict(network.confirmed_groups)

        components = sorted(
            (c for c in nx.connected_components(graph) if len(c) > 1),
            key=lambda c: (-len(c), min(ids.contact_number(x) for x in c)),
        )
        singles = sorted((c for c in network.contact_ids if graph.degree(c) == 0), key=ids.contact_number)

        positions: dict[str, tuple[float, float]] = {}
        x_cursor = 0.0
        extents = []
        for comp in components:
            local = component_layout(graph.subgraph(comp))
            xs = [p[0] for p in local.values()]
            ys = [p[1] for p in local.values()]
            width = max(xs) - min(xs)
            x0 = x_cursor - min(xs) + 0.9
            for c, (x, y) in local.items():
                positions[c] = (x + x0, y)
            extents.append((x0 + min(xs) - 0.9, x0 + max(xs) + 0.9, min(ys) - 0.9, max(ys) + 0.9))
            x_cursor = x0 + max(xs) + _SPACING * 0.55

        total_width = max((e[1] for e in extents), default=4.0)
        y_low = min((e[2] for e in extents), default=-1.0)
        y_high = max((e[3] for e in extents), default=1.0)

        content_h = (y_high - y_low) + (3.2 if singles else 0.6)
        scale = 0.58  # inches per data unit
        fig_w = max(11.5, 4.2 + scale * (total_width + 1.2))
        fig_h = max(6.4, 2.3 + scale * content_h)
        fig = new_figure(fig_w, fig_h)
        note = (
            "Dargestellt sind ausschließlich dokumentierte Beziehungen: aus bestätigten Gruppenumrandungen abgeleitet (alle Personen innerhalb derselben Umrandung kennen sich). "
            "Nicht eingezeichnete Paare sind unbekannt,\nnicht „kennen sich nicht“; es wurden keine Verbindungen zwischen Gruppen ergänzt. "
            "Die Anordnung der Gruppen im Bild und die Abstände zwischen ihnen haben keine inhaltliche Bedeutung."
        )
        frame(fig, "Gruppen und dokumentierte Beziehungen zwischen Kontakten",
              f"{status.documented_ties} dokumentierte Beziehungen · {len(group_ids)} bestätigte Kontaktgruppen · Ego nicht eingezeichnet · Farbe der Punkte = Wohnort (wie Abbildung A)",
              status, note)

        axes_w = scale * (total_width + 1.2) / fig_w
        ax = fig.add_axes([0.02, 1.25 / fig_h, axes_w, 1 - 2.0 / fig_h - 0.2 / fig_h])
        ax.set_aspect("equal")
        ax.axis("off")

        # Group outlines: larger groups get more padding so nested groups stay visible.
        order = sorted(group_ids, key=lambda g: -len(members_of[g]))
        for rank, group_id in enumerate(order):
            pad = 0.40 + 0.075 * (len(order) - 1 - rank)
            outline = _hull([positions[c] for c in members_of[group_id]], pad)
            color = group_color(group_id, group_ids)
            ax.add_patch(Polygon(outline, closed=True, facecolor=color, alpha=0.13, edgecolor="none", zorder=1))
            ax.add_patch(Polygon(outline, closed=True, facecolor="none", edgecolor=color, linewidth=1.6, zorder=2))
            # Label at the outline's extreme point in a direction that differs per group of one
            # component, so the labels of nested or overlapping outlines do not collide.
            peers = [g for g in order if set(members_of[g]) & set(members_of[group_id])]
            direction = np.array(_LABEL_DIRECTIONS[peers.index(group_id) % len(_LABEL_DIRECTIONS)], dtype=float)
            anchor = outline[int(np.argmax(outline @ direction))]
            ax.text(anchor[0] + 0.14 * direction[0], anchor[1] + 0.14 * direction[1], group_id, ha="center", va="center",
                    fontsize=8.6, fontweight="bold", color=color, zorder=3,
                    path_effects=[withStroke(linewidth=2.6, foreground="white")])

        for tie in network.positive_ties:
            a, b = positions[tie.a], positions[tie.b]
            single = len(tie.group_ids) == 1
            color = group_color(tie.group_ids[0], group_ids) if single and tie.group_ids[0] in group_ids else NEUTRAL_TIE
            ax.add_line(Line2D([a[0], b[0]], [a[1], b[1]], color=color, linewidth=1.5 if single else 1.9, alpha=0.95, zorder=3, solid_capstyle="round"))

        candidates = {}
        for group_id, members in network.unconfirmed_groups:
            for c in members:
                candidates.setdefault(c, []).append(group_id)
        for contact_id, xy in positions.items():
            v = views[contact_id]
            draw_node(ax, xy, contact_id, GEO_COLORS[v.geo], flagged=v.flagged, z=6)
            if contact_id in candidates:
                ax.text(xy[0], xy[1] - 0.46, "·".join(candidates[contact_id]) + " ?", ha="center", va="center", fontsize=6.5, color=CANDIDATE_COLOR, zorder=7)

        # Contacts without any documented tie: a box of their own.
        bottom = y_low - 1.7
        if singles:
            box_w = max(2.4, 1.15 * len(singles) + 0.6)
            ax.add_patch(FancyBboxPatch((0.0, bottom - 0.95), box_w, 1.7, boxstyle="round,pad=0.0,rounding_size=0.25", facecolor="#F6F7F8", edgecolor="#8D969E", linewidth=1.0, linestyle=(0, (4, 3)), zorder=1))
            ax.text(0.0, bottom + 0.95, "Ohne dokumentierte Beziehung: Beziehungen unbekannt, nicht „keine“", fontsize=8, color=MUTED, va="bottom", ha="left")
            for i, c in enumerate(singles):
                v = views[c]
                draw_node(ax, (0.75 + 1.15 * i, bottom - 0.12), c, GEO_COLORS[v.geo], flagged=v.flagged, z=6)
            total_width = max(total_width, box_w)
        ax.set_xlim(-0.6, total_width + 0.6)
        ax.set_ylim((bottom - 1.2) if singles else y_low - 0.5, y_high + 0.6)

        legend_ax = fig.add_axes([0.02 + axes_w + 0.02, 1.25 / fig_h, 0.98 - (0.02 + axes_w + 0.02), 1 - 2.0 / fig_h - 0.2 / fig_h])
        geo_counts = {g: sum(1 for v in views.values() if v.geo is g) for g in GEO_ORDER}
        sections = [
            ("Wohnort des Kontakts", [("dot", GEO_COLORS[g], f"{labels[g]}  (n = {geo_counts[g]})") for g in GEO_ORDER if geo_counts[g]]),
        ]
        group_entries = []
        for g in group_ids:
            group_entries.append(("dot", group_color(g, group_ids), f"{g}: {len(members_of[g])} Kontakte"))
        sections.append(("Bestätigte Kontaktgruppen\n(Umrandung und Linien)", group_entries))
        sections.append(("Zeichen", [("flag", "#FFFFFF", "gestrichelter Rand: offene Prüfhinweise"), ("text", "", "dunkle Linie: Beziehung aus\nmehreren Gruppen")]))
        if network.unconfirmed_groups:
            sections.append(("Nicht bestätigt", [("text", "", "grau, „?“: Kandidatengruppe;\nerzeugt keine Beziehung")]))
        draw_legend(legend_ax, sections, line=0.047)
    return fig
