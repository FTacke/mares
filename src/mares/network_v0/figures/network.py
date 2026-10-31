"""Figures B1, B2 and the layout comparison: the network structure of the confirmed alter-alter ties.

Following the principle of Vacca et al. (2016, fig. 2): contacts as small nodes, ties as thin lines, positions
from a force-directed layout, ego not drawn, separate components free to settle apart. The nodes are the
22 (or n) contacts; the lines are exactly the confirmed ties; the position of a node follows from the
ties alone. Nothing here adds a line.

* **B1** -- nodes and ties only; node colour = residence category.
* **B2** -- the same picture with the *surveyed contact groups* as soft areas behind it. The groups are
  what was recorded on the network map, not communities found by an algorithm. Overlapping groups show
  as overlapping areas.

The layout is identical in both (one computation); they differ only in what is drawn on top.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

import networkx as nx
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.patches import Polygon

from mares.core import ids

from ..analysis import AnalysisParams, SurveyStatus, geo_labels
from ..build import Network
from ..model import NetworkDataset
from . import design, layouts
from .common import contact_views, draw_legend
from .style import (
    GEO_COLORS, GEO_ORDER, GROUP_COLORS, INK, MUTED, frame, group_color, label_color, new_figure, rc, rim_color,
)

NODE_DIAMETER_PT = 11.0
LABEL_FONT_PT = 7.6
TIE_COLOR = "#7D8892"
TIE_WIDTH_PT = 0.75
_DIRECTIONS = tuple((math.cos(math.radians(a)), math.sin(math.radians(a))) for a in (90, 45, 135, 0, 180, -45, -135, -90))
_GROUP_LABEL_DIRECTIONS = ((0.0, 1.0), (-0.45, -1.0), (1.0, -0.2), (-1.0, 0.25), (0.8, 0.9), (-0.8, -0.8))


@dataclass(frozen=True)
class Structure:
    """What the figures draw: the graph, its positions, its components."""

    graph: nx.Graph
    positions: dict[str, tuple[float, float]]
    components: tuple[tuple[str, ...], ...]  # with at least two contacts
    isolates: tuple[str, ...]
    variant: str


def build_structure(network: Network, variant: str = layouts.DEFAULT_VARIANT) -> Structure:
    edges = [t.pair for t in network.positive_ties]
    graph = layouts.ordered_graph(network.contact_ids, edges)
    positions = layouts.compute_layout(graph, variant)
    components = sorted(
        (tuple(sorted(c, key=ids.contact_number)) for c in nx.connected_components(graph) if len(c) > 1),
        key=lambda c: (-len(c), ids.contact_number(c[0])),
    )
    isolates = tuple(sorted((c for c in graph.nodes if graph.degree(c) == 0), key=ids.contact_number))
    return Structure(graph, positions, tuple(components), isolates, variant)


# ---------------------------------------------------------------- geometry helpers --------------

def _convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[tuple[float, float]] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[tuple[float, float]] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def padded_outline(points: list[tuple[float, float]], pad: float) -> np.ndarray:
    """The convex hull of ``points`` grown by ``pad`` with rounded corners (a circle round each point)."""
    angles = np.linspace(0, 2 * math.pi, 48, endpoint=False)
    ring = np.c_[np.cos(angles), np.sin(angles)] * pad
    cloud = [(p[0] + dx, p[1] + dy) for p in points for dx, dy in ring]
    return np.array(_convex_hull(cloud))


def inside(point: tuple[float, float], polygon: np.ndarray) -> bool:
    x, y = point
    hit = False
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def _segment_hits_box(a, b, box) -> bool:
    (x0, y0, x1, y1) = box
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if p == 0:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t0 > t1:
                return False
    return True


def _boxes_overlap(a, b) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def place_labels(
    points_pt: dict[str, tuple[float, float]],
    edges,
    centre: tuple[float, float],
    obstacles: tuple[tuple[float, float, float], ...] = (),
    soft_segments: tuple = (),
    *,
    font_pt: float = LABEL_FONT_PT,
    node_pt: float = NODE_DIAMETER_PT,
) -> dict[str, tuple[float, float, str]]:
    """Label positions (in points) for node ids, greedily, avoiding other nodes, labels and ties.

    Eight candidate positions around each node; the cheapest wins, ties go to the first in a fixed order,
    nodes are handled in a fixed order: the result is deterministic. ``obstacles`` are further discs
    ``(x, y, radius)`` to keep clear of (for example the ego node); ``soft_segments`` are lines a label
    should avoid but may cross at a lower price (the many ego lines).
    """
    radius = node_pt / 2
    degree = Counter()
    for a, b in edges:
        degree[a] += 1
        degree[b] += 1
    order = sorted(points_pt, key=lambda c: (-degree[c], ids.contact_number(c)))
    placed: dict[str, tuple[float, float, float, float]] = {}
    result: dict[str, tuple[float, float, str]] = {}
    segments = [(points_pt[a], points_pt[b]) for a, b in edges]
    for contact in order:
        x, y = points_pt[contact]
        w = 0.62 * font_pt * len(contact) + 2
        h = font_pt * 1.15
        away = (x - centre[0], y - centre[1])
        norm = math.hypot(*away) or 1.0
        best = None
        for rank, (dx, dy) in enumerate(_DIRECTIONS):
            cx = x + dx * (radius + 1.5 + w / 2)
            cy = y + dy * (radius + 1.5 + h / 2)
            box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
            cost = 0.0
            for other, (ox, oy) in points_pt.items():
                if other == contact:
                    continue
                nx_, ny_ = max(box[0], min(ox, box[2])), max(box[1], min(oy, box[3]))
                if math.hypot(ox - nx_, oy - ny_) < radius + 0.5:
                    cost += 12
            for other_box in placed.values():
                if _boxes_overlap(box, other_box):
                    cost += 12
            for ox, oy, orad in obstacles:
                nx_, ny_ = max(box[0], min(ox, box[2])), max(box[1], min(oy, box[3]))
                if math.hypot(ox - nx_, oy - ny_) < orad + 1.0:
                    cost += 12
            cost += 1.4 * sum(1 for s in segments if _segment_hits_box(s[0], s[1], box))
            cost += 0.25 * sum(1 for s in soft_segments if _segment_hits_box(s[0], s[1], box))
            cost -= 0.35 * (dx * away[0] + dy * away[1]) / norm  # prefer outward
            cost += 0.01 * rank
            if best is None or cost < best[0]:
                best = (cost, box, cx, cy)
        placed[contact] = best[1]
        result[contact] = (best[2], best[3], contact)
    return result


# ---------------------------------------------------------------- drawing ----------------------

def _frame_axes(ax, positions: dict[str, tuple[float, float]], margin: float = 0.14) -> None:
    xs = [p[0] for p in positions.values()] or [0.0]
    ys = [p[1] for p in positions.values()] or [0.0]
    ax.set_xlim(min(xs) - margin, max(xs) + margin)
    ax.set_ylim(min(ys) - margin, max(ys) + margin)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.apply_aspect()


def _to_pt(ax, xy) -> tuple[float, float]:
    """Data coordinates -> points on the figure (the figure is saved at its own size)."""
    return tuple(v * 0.72 for v in ax.transData.transform(xy))


def _to_data(ax, pt) -> tuple[float, float]:
    return tuple(ax.transData.inverted().transform((pt[0] / 0.72, pt[1] / 0.72)))


def draw_structure(ax, structure: Structure, colors: dict[str, str], *, label: bool = True, node_pt: float = NODE_DIAMETER_PT) -> list[tuple[float, float, float, float]]:
    """Ties, then nodes, then ids. ``colors`` maps a contact id to its fill. Returns the boxes (in points)
    taken by the id labels, so that further text can keep clear of them."""
    positions = structure.positions
    _frame_axes(ax, positions)
    edges = [tuple(e) for e in structure.graph.edges]
    segments = [(positions[a], positions[b]) for a, b in edges]
    if segments:
        ax.add_collection(LineCollection(segments, colors=TIE_COLOR, linewidths=TIE_WIDTH_PT, alpha=0.85, zorder=2, capstyle="round"))
    nodes = sorted(positions, key=ids.contact_number)
    ax.scatter([positions[c][0] for c in nodes], [positions[c][1] for c in nodes], s=node_pt**2, c=[colors[c] for c in nodes],
               edgecolors=[rim_color(colors[c]) for c in nodes], linewidths=0.8, zorder=4)
    boxes: list[tuple[float, float, float, float]] = []
    if label:
        pts = {c: _to_pt(ax, positions[c]) for c in nodes}
        centre = (sum(p[0] for p in pts.values()) / len(pts), sum(p[1] for p in pts.values()) / len(pts)) if pts else (0.0, 0.0)
        for cx, cy, text in place_labels(pts, edges, centre).values():
            data = _to_data(ax, (cx, cy))
            w = 0.62 * LABEL_FONT_PT * len(text) + 2
            h = LABEL_FONT_PT * 1.15
            boxes.append((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
            ax.text(data[0], data[1], text, ha="center", va="center", fontsize=LABEL_FONT_PT, color=INK, zorder=6,
                    path_effects=[_halo()])
    return boxes


def _halo():
    from matplotlib.patheffects import withStroke

    return withStroke(linewidth=2.0, foreground="white")


def _resample(outline: np.ndarray, count: int) -> list[tuple[float, float]]:
    """Points spread evenly along a closed outline."""
    closed = np.vstack([outline, outline[:1]])
    lengths = np.r_[0.0, np.cumsum(np.hypot(*np.diff(closed, axis=0).T))]
    targets = np.linspace(0, lengths[-1], count, endpoint=False)
    return [(float(np.interp(s, lengths, closed[:, 0])), float(np.interp(s, lengths, closed[:, 1]))) for s in targets]


def draw_groups(ax, structure: Structure, network: Network, avoid: list[tuple[float, float, float, float]], *,
                fill_alpha: float = 0.11, line_alpha: float = 0.55, extra_obstacles: tuple[tuple[float, float, float], ...] = (),
                tag_pt: float = 8.0, node_pt: float = NODE_DIAMETER_PT, pad_scale: float = 1.0) -> list[str]:
    """Soft areas for the surveyed groups, each with a small tag clear of node ids and other tags.

    Returns remarks about non-members that lie inside an area.
    """
    members_of = dict(network.confirmed_groups)
    group_ids = sorted(members_of)
    order = sorted(group_ids, key=lambda g: -len(members_of[g]))  # larger groups get more padding: nested groups stay visible
    pt = (ax.transData.inverted().transform((72 / 0.72, 0))[0] - ax.transData.inverted().transform((0, 0))[0]) / 72  # data units per pt
    centres = {c: _to_pt(ax, xy) for c, xy in structure.positions.items()}
    taken = list(avoid)
    remarks: list[str] = []
    outlines: dict[str, np.ndarray] = {}
    for rank, group_id in enumerate(order):
        pad = (10.0 + 3.5 * (len(order) - 1 - rank)) * pt * 0.8 * pad_scale
        members = [c for c in members_of[group_id] if c in structure.positions]
        outline = padded_outline([structure.positions[c] for c in members], pad)
        outlines[group_id] = outline
        color = group_color(group_id, group_ids)
        ax.add_patch(Polygon(outline, closed=True, facecolor=color, alpha=fill_alpha, edgecolor="none", zorder=1))
        ax.add_patch(Polygon(outline, closed=True, facecolor="none", edgecolor=color, alpha=line_alpha, linewidth=0.8, zorder=1.2))
        for contact, point in structure.positions.items():
            if contact not in members and inside(point, outline):
                remarks.append(f"{contact} liegt im Layout innerhalb der Fläche von {group_id}, ohne dazuzugehören")
    for group_id in group_ids:  # fixed order
        outline = outlines[group_id]
        color = group_color(group_id, group_ids)
        centre = np.mean([centres[c] for c in members_of[group_id] if c in centres], axis=0)
        w, h = 0.62 * tag_pt * len(group_id) + 2, tag_pt * 1.15
        best = None
        for rank, sample in enumerate(_resample(outline, 48)):
            sp = _to_pt(ax, sample)
            away = np.array(sp) - centre
            away = away / (np.hypot(*away) or 1.0)
            cx, cy = sp[0] + away[0] * (w / 2 + 2.5), sp[1] + away[1] * (h / 2 + 2.5)
            box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
            cost = 12.0 * sum(1 for other in taken if _boxes_overlap(box, other))
            for other, (ox, oy) in centres.items():
                nx_, ny_ = max(box[0], min(ox, box[2])), max(box[1], min(oy, box[3]))
                if math.hypot(ox - nx_, oy - ny_) < node_pt / 2 + 1:
                    cost += 12.0
            for ox, oy, orad in extra_obstacles:
                nx_, ny_ = max(box[0], min(ox, box[2])), max(box[1], min(oy, box[3]))
                if math.hypot(ox - nx_, oy - ny_) < orad + 1:
                    cost += 12.0
            cost += 0.002 * rank  # ties: the first sample, a fixed start
            if best is None or cost < best[0]:
                best = (cost, box, cx, cy)
        taken.append(best[1])
        data = _to_data(ax, (best[2], best[3]))
        ax.text(data[0], data[1], group_id, ha="center", va="center", fontsize=tag_pt, fontweight="bold", color=color, zorder=3,
                path_effects=[_halo()])
    return remarks


def _legend_sections(structure: Structure, views, labels, network: Network, with_groups: bool):
    geo_counts = Counter(v.geo for v in views)
    sections = [("Wohnort des Kontakts", [("dot", GEO_COLORS[g], f"{labels[g]}  (n = {geo_counts[g]})") for g in GEO_ORDER if geo_counts[g]])]
    ties = structure.graph.number_of_edges()
    sections.append(("Beziehungen", [("line", TIE_COLOR, f"bestätigte Beziehung  (n = {ties})")]))
    if with_groups:
        members_of = dict(network.confirmed_groups)
        ordered = sorted(members_of)
        sections.append((
            "Erhobene Kontaktgruppen\n(Fläche hinter dem Netz)",
            [("swatch", group_color(g, ordered), f"{g}: {len(members_of[g])} Kontakte") for g in ordered]
            + [("text", "", "Überlappung = gemeinsame Mitglieder")],
        ))
    return sections


def _elicitation_sentence(status: SurveyStatus) -> str:
    if status.elicitation == "asked_per_pair":
        return "Die Beziehungen wurden im Interview erfragt und in der Netzwerkkarte als Gruppen dokumentiert."
    return "Dargestellt sind die aus bestätigten Gruppen abgeleiteten Beziehungen (Cliquenregel)."


def network_structure_figure(
    dataset: NetworkDataset,
    status: SurveyStatus,
    params: AnalysisParams,
    *,
    network: Network,
    show_groups: bool = False,
    variant: str = layouts.DEFAULT_VARIANT,
    structure: Structure | None = None,
    profile: str = "clean",
):
    """B1 (``show_groups=False``) or B2 (``True``). Pass ``structure`` to give both the identical layout."""
    with rc():
        structure = structure or build_structure(network, variant)
        views = contact_views(dataset, params)
        labels = geo_labels(params)
        colors = {v.contact_id: GEO_COLORS[v.geo] for v in views}
        width, height = 12.6, 8.4
        fig = new_figure(width, height)
        components = len(structure.components)
        isolates = len(structure.isolates)
        remarks: list[str] = []
        ax = fig.add_axes([0.02, 0.115, 0.71, 0.775])
        # the axes must have their final size before groups and labels are placed in physical units
        _frame_axes(ax, structure.positions)
        boxes = draw_structure(ax, structure, colors)
        if show_groups:
            remarks = draw_groups(ax, structure, network, boxes)
        legend_ax = fig.add_axes([0.75, 0.14, 0.24, 0.74])
        draw_legend(legend_ax, design.lean_sections(_legend_sections(structure, views, labels, network, show_groups), profile), line=0.05)
        none_word = "ohne bestätigte Beziehung" if status.completeness != "complete" else "ohne Beziehung"
        note = (
            f"{_elicitation_sentence(status)} Ego ist nicht eingezeichnet. {status.short_note()}\n"
            f"Die Position der Kontakte ergibt sich allein aus den Beziehungen ({layouts.VARIANT_LABELS[structure.variant]}, fester Seed); "
            "Nähe im Bild bedeutet Verbundenheit durch Beziehungen, nicht Nähe zu Ego. Der Abstand getrennter Teilnetze hat keine Bedeutung."
            + ("\nHinweis zur Darstellung: " + "; ".join(remarks) + "." if remarks else "")
        )
        design.frame_for(
            profile,
            fig,
            "Netzwerkstruktur der erhobenen Beziehungen zwischen den Kontakten" + (" – mit erhobenen Kontaktgruppen" if show_groups else ""),
            f"{len(structure.positions)} Kontakte · {structure.graph.number_of_edges()} bestätigte Beziehungen · {components} Teilnetze · {isolates} Kontakte {none_word}",
            status,
            note,
            short_title="Beziehungen und Kontaktgruppen" if show_groups else "Beziehungen zwischen Kontakten",
            hint="Die Position folgt den Beziehungen, nicht der Nähe zu Ego. Paare ohne Linie: unbekannt.",
        )
    return fig


def layout_comparison_figure(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams, *, network: Network):
    """The same network under every layout variant, with readability measures. Not a result: a working figure
    that documents why a layout was chosen."""
    with rc():
        views = contact_views(dataset, params)
        colors = {v.contact_id: GEO_COLORS[v.geo] for v in views}
        fig = new_figure(16.5, 6.6)
        edges = [t.pair for t in network.positive_ties]
        frame(
            fig,
            "Layoutvergleich: dasselbe Netzwerk, drei kraftbasierte Verfahren",
            "Arbeitsabbildung zur Wahl des Layouts; alle Verfahren nutzen nur die Beziehungen, jeder Lauf mit festem Seed",
            status,
            "Kreuzungen = Zahl der Linienpaare, die sich schneiden (Linien mit gemeinsamem Kontakt ausgenommen); Knotenabstand relativ zur mittleren Beziehungslänge. "
            "Die Kennzahlen vergleichen Layouts und sagen nichts über die Daten. Gewählt für B1 und B2: Stress-Majorisierung – längste Beziehungslinien (Teilnetze nicht zusammengedrückt), keine sich berührenden Knoten, deterministisch.",
        )
        for index, variant in enumerate(layouts.VARIANTS):
            structure = build_structure(network, variant)
            measures = layouts.measure(structure.positions, edges)
            left = 0.015 + index * 0.328
            ax = fig.add_axes([left, 0.13, 0.31, 0.68])
            draw_structure(ax, structure, colors, node_pt=10.0)
            fig.text(left + 0.005, 0.86, layouts.VARIANT_LABELS[variant], fontsize=10.5, fontweight="bold", color=INK, ha="left", va="bottom")
            fig.text(left + 0.005, 0.835, measures.summary(), fontsize=7.6, color=MUTED, ha="left", va="top")
    return fig
