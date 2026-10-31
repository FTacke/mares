"""The network figures of network_v1: G1 (personal network), G2 (geographic network), G3 (group map).

Edges are always *confirmed* contact-contact connections (state ``1``). Denied (``0``) and unknown pairs are never drawn
as lines; a note gives the coverage, so an absent line is not read as 'no contact'. Group membership alone never creates
a line. Node colour = relation type, in all three figures.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, PathPatch, Polygon, Rectangle
from matplotlib.path import Path as MplPath
from matplotlib.transforms import Bbox

from .. import codes
from ..places import AREA_LABELS, AREA_ORDER, Area, norm
from .base import (
    AREA_TINTS, GROUP_COLORS, INK, LABEL_PT, LEGEND_PT, MUTED, NODE_PT, TIE, TIE_BETWEEN, Context, draw_nodes, force_layout,
    initial_circle, page, relation_entries, relation_fill, ring_segments, text_width,
)

EGO_FILL = "#1F2933"
NODE_R_IN = NODE_PT / 72 / 2  # node radius in inches


def _edges(ctx: Context) -> list[tuple[str, str]]:
    return ctx.derived.confirmed_edges


def _fills(ctx: Context, ids) -> dict[str, str | None]:
    return {cid: relation_fill(ctx.case, cid) for cid in ids}


def _tie(ax, path: MplPath, *, color: str, width: float, dashed: bool = False, zorder: int = 2) -> None:
    patch = PathPatch(path, fill=False, edgecolor=color, linewidth=width, linestyle=(0, (4, 2.5)) if dashed else "solid", zorder=zorder)
    patch.set_gid("tie")  # every confirmed tie is one artist with this id (counted by the tests)
    ax.add_patch(patch)


def _straight(p1, p2) -> MplPath:
    return MplPath([p1, p2], [MplPath.MOVETO, MplPath.LINETO])


# ---------------------------------------------------------------------------------------------------- G1 ---
MISSING_RADIUS = 4.75
EGO_CLEARANCE = 0.75  # ring units: no tie passes closer to Ego
LABEL_HALF_WIDTH = 0.42  # half the width kept free for the ring numbers at the top, in ring units
G1_SIZE = 8.4  # inches, square main area


def g1_layout(ctx: Context) -> dict[str, tuple[float, float]]:
    """Radius = recorded closeness (1 ... 4, half steps between); contacts without closeness on an outer arc.
    Only the angle is optimised (edges pull, contacts repel); the seed angles are fixed per contact ID."""
    radius = {}
    for c in ctx.case.contacts:
        value = codes.closeness_value(c.closeness)
        radius[c.id] = value if value is not None else MISSING_RADIUS
    nodes = ctx.case.contact_ids

    def project(n, p):
        angle = math.atan2(p[1], p[0])
        wedge = math.atan2(LABEL_HALF_WIDTH, radius[n])  # keep the ring numbers at the top free (wider on inner rings)
        low, high = math.pi / 2 - wedge, math.pi / 2 + wedge
        if low < angle < high:
            angle = low if angle < math.pi / 2 else high
        return np.array([math.cos(angle), math.sin(angle)]) * radius[n]

    return force_layout(nodes, _edges(ctx), start=initial_circle(nodes, 2.5), project=project, repulsion=0.06, spring=0.05,
                        iterations=600, min_distance=0.55)


def _bent(p1, p2) -> MplPath:
    """A tie between two contacts; one that would pass close to Ego bends away from the centre (perpendicular to the
    chord, on the side of its midpoint), so it is never mistaken for an ego line."""
    (x1, y1), (x2, y2) = p1, p2
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    length = math.hypot(x2 - x1, y2 - y1) or 1.0
    px, py = -(y2 - y1) / length, (x2 - x1) / length  # unit normal of the chord
    side = px * mx + py * my  # distance of the chord from Ego (signed)
    if side < 0:
        px, py, side = -px, -py, -side
    dx, dy = x2 - x1, y2 - y1
    t = min(max(-(x1 * dx + y1 * dy) / (dx * dx + dy * dy or 1.0), 0.0), 1.0)  # the point of the segment closest to Ego
    if math.hypot(x1 + t * dx, y1 + t * dy) >= EGO_CLEARANCE:
        return _straight(p1, p2)
    offset = 2 * (EGO_CLEARANCE - side)  # the apex of a quadratic curve lies halfway to its control point
    control = (mx + px * offset, my + py * offset)
    return MplPath([(x1, y1), control, (x2, y2)], [MplPath.MOVETO, MplPath.CURVE3, MplPath.CURVE3])


def g1(ctx: Context):
    sections = [
        ("Beziehungstyp", relation_entries(ctx.case)),
        ("Persönliche Nähe", [
            ("line", "1 sehr nah · 2 nah ·\n3 weniger nah · 4 außerhalb", {"color": "#9AA5B1", "linewidth": 1.0}),
            ("line", "Zwischenwerte 1,5 · 2,5 · 3,5", {"color": "#C3CAD1", "linewidth": 0.7, "linestyle": (0, (2, 3))}),
        ]),
        ("Verbindungen", [("line", "bestätigte Verbindung\nzwischen Kontakten", {"color": TIE, "linewidth": 1.0})]),
    ]
    notes = ["Abstand zu Ego = erhobene persönliche Nähe; die Lage auf dem Ring ist ein Layout ohne eigene Bedeutung.",
             "Fehlende Linie heißt nicht „kein Kontakt“ (nur bestätigte Verbindungen). " + ctx.coverage_line()]
    p = page(ctx, "G1 · Persönliches Beziehungsnetz", "Kontakte nach persönlicher Nähe und Beziehungstyp",
             main_w=G1_SIZE, main_h=G1_SIZE, legend="side", sections=sections, notes=notes)
    ax = p.main
    without = any(codes.closeness_value(c.closeness) is None for c in ctx.case.contacts)
    lim = (MISSING_RADIUS if without else max(codes.CLOSENESS_LEVELS)) + 0.45  # the outer arc only when it is needed
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    for value in codes.CLOSENESS_LEVELS:
        whole = value == int(value)
        ax.add_patch(Circle((0, 0), value, fill=False, edgecolor="#9AA5B1" if whole else "#C3CAD1",
                            linewidth=1.0 if whole else 0.7, linestyle="solid" if whole else (0, (2, 3)), zorder=0))
        if whole:
            ax.text(0, value, f"{int(value)}", fontsize=LABEL_PT - 1, color=MUTED, ha="center", va="center", zorder=1,
                    bbox={"boxstyle": "round,pad=0.12", "facecolor": "white", "edgecolor": "none"})
    positions = g1_layout(ctx)
    if any(codes.closeness_value(c.closeness) is None for c in ctx.case.contacts):
        ax.add_patch(Circle((0, 0), MISSING_RADIUS, fill=False, edgecolor="#C9CED3", linewidth=0.6, linestyle=(0, (1, 3))))
        ax.text(0, -MISSING_RADIUS - 0.22, "Nähe ohne Angabe", fontsize=LABEL_PT - 1.5, color=MUTED, ha="center", va="top", style="italic")
    for a, b in _edges(ctx):
        _tie(ax, _bent(positions[a], positions[b]), color=TIE, width=0.8)
    ax.add_patch(Circle((0, 0), 0.36, facecolor=EGO_FILL, edgecolor="white", zorder=5))
    ax.text(0, 0, "Ego", color="white", fontsize=LABEL_PT - 1, ha="center", va="center", fontweight="bold", zorder=6)
    draw_nodes(ax, positions, _fills(ctx, positions))
    return p.figure


# ---------------------------------------------------------------------------------------------------- G2 ---
G2_W = 13.0
STEP = 0.5  # inches between node centres inside a subgroup
ARC_STEP = 0.56  # inches between neighbours on the ellipse of a subgroup
BOX_PAD = 0.12  # subgroup area around its nodes
SUB_LABEL_H = 0.24  # room for a subgroup label above its area
BAND_GAP = 0.06
OUTSIDE_GAP_G2 = 0.3  # a little more room before 'außerhalb Europas' (a category step, never a distance)
UNRESOLVED_W = 1.15
HEADER_H_G2 = 0.62
BRACKET_H_G2 = 0.3
SHELF_GAP = 0.18
ISOLATED_LABEL_H = 0.3
SUBGROUP_AREAS = (Area.MITTELHESSEN, Area.GERMANY_OTHER, Area.EUROPE_OTHER, Area.OUTSIDE_EUROPE)


@dataclass
class Subgroup:
    """Contacts of one band with the same residence place (Mittelhessen, rest of Germany) or residence country (abroad).
    A geographic bundle only -- no social group and no connection. Connected contacts sit on an ellipse (no tie can run
    through a third node), contacts without a confirmed connection on a grid."""

    area: Area
    label: str | None  # None: no label (Marburg, unresolved)
    members: list[str]
    ring: bool = False
    cols: int = 1
    x: float = 0.0  # left edge of the node area (inches)
    top: float = 0.0  # top edge of the node area

    @property
    def radii(self) -> tuple[float, float]:
        k = len(self.members)
        if k <= 2:
            return ((k - 1) * STEP / 2, 0.0)
        r = max(k * ARC_STEP / (2 * math.pi), 0.32)
        return r * 1.3, r * 0.78

    @property
    def rows(self) -> int:
        return math.ceil(len(self.members) / self.cols)

    @property
    def width(self) -> float:
        inner = 2 * self.radii[0] if self.ring else (self.cols - 1) * STEP
        return inner + 2 * NODE_R_IN + 2 * BOX_PAD

    @property
    def height(self) -> float:
        inner = 2 * self.radii[1] if self.ring else (self.rows - 1) * STEP
        return inner + 2 * NODE_R_IN + 2 * BOX_PAD

    @property
    def footprint(self) -> tuple[float, float]:
        label_w = text_width(self.label_text, LABEL_PT - 1.5) + 0.1 if self.label else 0.0
        return max(self.width, label_w), self.height + (SUB_LABEL_H if self.label else 0.0)

    @property
    def label_text(self) -> str:
        if not self.label:
            return ""
        return self.label if len(self.members) == 1 else f"{self.label} · {len(self.members)}"

    def box(self) -> tuple[float, float, float, float]:
        return self.x, self.top - self.height, self.width, self.height


def subgroup_label(ctx: Context, cid: str) -> str | None:
    """The place (Mittelhessen, rest of Germany) or the country (abroad) as recorded; nothing is added."""
    c = ctx.case.contact(cid)
    area = ctx.derived.area(cid)
    if area in (Area.MITTELHESSEN, Area.GERMANY_OTHER):
        return c.residence_place.strip() or None
    if area in (Area.EUROPE_OTHER, Area.OUTSIDE_EUROPE):
        return c.residence_country.strip() or c.residence_country_iso3 or None
    return None


def subgroups(ctx: Context, ids: list[str], *, ring: bool = False) -> dict[Area, list[Subgroup]]:
    """Subgroups per band: same place or country (spelling variants of case and umlauts are one place). Largest first."""
    found: dict[Area, dict[str, Subgroup]] = defaultdict(dict)
    for cid in ids:
        area = ctx.derived.area(cid)
        label = subgroup_label(ctx, cid) if area in SUBGROUP_AREAS else None
        key = norm(label) if label else ""
        group = found[area].setdefault(key, Subgroup(area, label, [], ring))
        group.members.append(cid)
    result = {}
    for area, groups in found.items():
        ordered = sorted(groups.values(), key=lambda g: (-len(g.members), norm(g.label or "")))
        for g in ordered:
            g.cols = min(len(g.members), max(1, math.ceil(math.sqrt(len(g.members) * 1.6))))
        result[area] = ordered
    return result


def g2_bands(ctx: Context) -> dict[Area, tuple[float, float]]:
    """x-range per band in inches: the five areas, plus a narrow separate box for unresolved residences if needed. Width
    = room for the widest subgroup plus a share ∝ √(contacts) of the rest."""
    counts = defaultdict(int)
    for cid in ctx.case.contact_ids:
        counts[ctx.derived.area(cid)] += 1
    groups = subgroups(ctx, ctx.case.contact_ids)
    areas = list(AREA_ORDER)
    gaps = BAND_GAP * (len(areas) - 1) + OUTSIDE_GAP_G2
    width = G2_W
    if counts[Area.UNRESOLVED]:
        width -= UNRESOLVED_W + OUTSIDE_GAP_G2
    need = {a: max([g.footprint[0] for g in groups.get(a, [])] + [0.9]) + 0.2 for a in areas}
    extra = max(width - gaps - sum(need.values()), 0.0)
    weight = {a: math.sqrt(max(counts[a], 1)) for a in areas}
    total = sum(weight.values())
    bands, x = {}, 0.0
    for a in areas:
        if a is Area.OUTSIDE_EUROPE:
            x += OUTSIDE_GAP_G2 - BAND_GAP
        w = need[a] + extra * weight[a] / total
        bands[a] = (x, x + w)
        x += w + BAND_GAP
    if counts[Area.UNRESOLVED]:
        bands[Area.UNRESOLVED] = (G2_W - UNRESOLVED_W, G2_W)
    return bands


def _pack(groups: list[Subgroup], x0: float, x1: float) -> list[list[Subgroup]]:
    """Shelf packing: subgroups left to right, a new shelf when the band is full."""
    shelves: list[list[Subgroup]] = [[]]
    used = 0.0
    for g in groups:
        w = g.footprint[0]
        if shelves[-1] and used + w > (x1 - x0) - 0.1:
            shelves.append([])
            used = 0.0
        shelves[-1].append(g)
        used += w + 0.12
    return [s for s in shelves if s]


def _shelves_height(shelves: list[list[Subgroup]]) -> float:
    return sum(max(g.footprint[1] for g in s) for s in shelves) + SHELF_GAP * max(len(shelves) - 1, 0)


def _arrange(shelves: list[list[Subgroup]], x0: float, x1: float, top: float, height: float) -> None:
    """Shelves spread over the zone height, subgroups spread over the band width."""
    content = _shelves_height(shelves)
    y = top - max(height - content, 0) / 2
    for shelf in shelves:
        widths = [g.footprint[0] for g in shelf]
        free = (x1 - x0) - sum(widths)
        gap = free / (len(shelf) + 1)
        x = x0 + gap
        for g, w in zip(shelf, widths):
            label_h = SUB_LABEL_H if g.label else 0.0
            g.x = x + (w - g.width) / 2
            g.top = y - label_h
            x += w + gap
        y -= max(g.footprint[1] for g in shelf) + SHELF_GAP


def _ring_order(members: list[str], edges: set[tuple[str, str]]) -> list[str]:
    """Order on the ellipse: each next contact is the one with most ties to the previous one (then by ID), so
    connected contacts are neighbours and chords stay short. Deterministic."""
    rest = sorted(members)
    order = [rest.pop(0)]
    while rest:
        last = order[-1]
        nxt = max(rest, key=lambda c: (((min(c, last), max(c, last)) in edges), -rest.index(c)))
        order.append(nxt)
        rest.remove(nxt)
    return order


def _node_positions(g: Subgroup, edges: set[tuple[str, str]]) -> dict[str, tuple[float, float]]:
    cx = g.x + g.width / 2
    cy = g.top - g.height / 2
    if g.ring:
        rx, ry = g.radii
        k = len(g.members)
        if k <= 2:
            return {cid: (cx - rx + i * 2 * rx, cy) for i, cid in enumerate(sorted(g.members))}
        return {cid: (cx + rx * math.cos(math.pi / 2 + 2 * math.pi * i / k + math.pi / k),
                      cy + ry * math.sin(math.pi / 2 + 2 * math.pi * i / k + math.pi / k))
                for i, cid in enumerate(_ring_order(g.members, edges))}
    out = {}
    for i, cid in enumerate(g.members):
        r, c = divmod(i, g.cols)
        in_row = min(g.cols, len(g.members) - r * g.cols)
        offset = (g.cols - in_row) * STEP / 2  # a shorter last row is centred
        out[cid] = (g.x + BOX_PAD + NODE_R_IN + offset + c * STEP, g.top - BOX_PAD - NODE_R_IN - r * STEP)
    return out


@dataclass
class G2Layout:
    bands: dict[Area, tuple[float, float]]
    positions: dict[str, tuple[float, float]]
    subgroups: list[Subgroup] = field(default_factory=list)
    height: float = 0.0
    zone_top: float = 0.0  # top of the node zones
    isolated_top: float | None = None  # top of the zone of contacts without a confirmed connection


def g2_layout(ctx: Context) -> G2Layout:
    """Bands of the five areas; inside each band the contacts are bundled by place or country (subgroups). Contacts with
    a confirmed connection sit in the upper zone, the others in a lower zone. Inside a subgroup the nodes start on a
    grid and are moved by a small force layout (confined to the subgroup area), so ties stay readable. Deterministic."""
    bands = g2_bands(ctx)
    edges = _edges(ctx)
    linked = {c for e in edges for c in e}
    ids = ctx.case.contact_ids
    upper = subgroups(ctx, [c for c in ids if c in linked], ring=True)
    lower = subgroups(ctx, [c for c in ids if c not in linked])
    shelves_up = {a: _pack(upper.get(a, []), *bands[a]) for a in bands}
    shelves_low = {a: _pack(lower.get(a, []), *bands[a]) for a in bands}
    up_h = max([_shelves_height(s) for s in shelves_up.values()] + [2.6])
    low_h = max([_shelves_height(s) for s in shelves_low.values()] + [0.0])
    header = HEADER_H_G2 + BRACKET_H_G2
    height = header + up_h + (ISOLATED_LABEL_H + low_h + 0.12 if low_h else 0.0) + 0.1
    zone_top = height - header
    for a, (x0, x1) in bands.items():
        _arrange(shelves_up[a], x0, x1, zone_top, up_h)
    isolated_top = None
    if low_h:
        isolated_top = zone_top - up_h - 0.06
        for a, (x0, x1) in bands.items():
            _arrange(shelves_low[a], x0, x1, isolated_top - ISOLATED_LABEL_H, low_h)
    groups = [g for gs in list(upper.values()) + list(lower.values()) for g in gs]
    edge_set = set(edges)
    positions: dict[str, tuple[float, float]] = {}
    for g in groups:
        positions.update(_node_positions(g, edge_set))
    return G2Layout(bands, positions, groups, height, zone_top, isolated_top)


def g2(ctx: Context):
    layout = g2_layout(ctx)
    edges = _edges(ctx)
    area = {cid: ctx.derived.area(cid) for cid in ctx.case.contact_ids}
    within = sum(1 for a, b in edges if area[a] is area[b] and area[a] is not Area.UNRESOLVED)
    between = len(edges) - within
    sections = [
        ("Beziehungstyp", relation_entries(ctx.case)),
        ("Verbindungen", [
            ("line", f"im selben Bereich ({within})", {"color": TIE, "linewidth": 1.0}),
            ("line", f"zwischen Bereichen ({between})", {"color": TIE_BETWEEN, "linewidth": 0.8, "linestyle": (0, (4, 2.5))}),
        ]),
        (None, [("area", "gleicher Wohnort bzw. Wohnland", {"facecolor": "#FFFFFF", "edgecolor": "#B8C0C8", "linewidth": 0.7})]),
    ]
    notes = ["Wohnortbereiche sind Kategorien, keine Entfernungen; Flächen bündeln Kontakte mit gleichem Wohnort bzw. Wohnland.",
             "Linien zeigen bestätigte Verbindungen; fehlende Linien bedeuten nicht zwangsläufig keinen Kontakt. " + ctx.coverage_line()]
    p = page(ctx, "G2 · Geografisches Beziehungsnetz", "Kontakte nach Wohnortbereich und bestätigte Verbindungen zwischen ihnen",
             main_w=G2_W, main_h=layout.height, legend="bottom", sections=sections, notes=notes)
    ax = p.main
    counts = defaultdict(int)
    for a in area.values():
        counts[a] += 1
    zone_bottom = 0.05
    header_y = layout.zone_top + 0.08
    for a, (x0, x1) in layout.bands.items():
        if a is Area.UNRESOLVED:
            ax.add_patch(Rectangle((x0, zone_bottom), x1 - x0, layout.zone_top - zone_bottom, facecolor="#FFFFFF", edgecolor="#B8C0C8",
                                   linewidth=0.7, linestyle=(0, (3, 3)), zorder=0))
            ax.text((x0 + x1) / 2, header_y, f"Wohnort nicht\nzuordenbar\nn = {counts[a]}", ha="center", va="bottom",
                    fontsize=LABEL_PT - 1, color=MUTED, style="italic", linespacing=1.15)
            continue
        ax.add_patch(Rectangle((x0, zone_bottom), x1 - x0, layout.zone_top - zone_bottom, facecolor=AREA_TINTS[a], edgecolor="none", zorder=0))
        ax.text((x0 + x1) / 2, header_y, f"{AREA_LABELS[a]}\nn = {counts[a]}", ha="center", va="bottom", fontsize=LABEL_PT,
                color=INK, linespacing=1.2)
    m0, m1 = layout.bands[Area.MARBURG][0] + 0.1, layout.bands[Area.MITTELHESSEN][1] - 0.1
    yb = layout.height - BRACKET_H_G2 + 0.06
    ax.plot([m0, m0, m1, m1], [yb - 0.06, yb, yb, yb - 0.06], color=MUTED, linewidth=0.8)
    ax.text((m0 + m1) / 2, yb + 0.04, "Marburg und Mittelhessen", ha="center", va="bottom", fontsize=LABEL_PT - 0.5, color=MUTED)
    if layout.isolated_top is not None:
        y = layout.isolated_top
        ax.plot([0, G2_W], [y, y], color="#B8C0C8", linewidth=0.7, linestyle=(0, (3, 3)), zorder=1)
        ax.text(0.06, y - 0.05, "keine bestätigte Verbindung zu anderen Kontakten erfasst", fontsize=LABEL_PT - 1.5, color=MUTED,
                ha="left", va="top", style="italic", zorder=6)
    for g in layout.subgroups:
        bx, by, bw, bh = g.box()
        if g.label and len(g.members) > 1:
            ax.add_patch(FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0,rounding_size=0.12", facecolor="#FFFFFF", alpha=0.75,
                                        edgecolor="none", zorder=1))
            ax.add_patch(FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0,rounding_size=0.12", fill=False, edgecolor="#B8C0C8",
                                        linewidth=0.7, zorder=1))
        if g.label:
            ax.text(bx + bw / 2, g.top + 0.04, g.label_text, ha="center", va="bottom", fontsize=LABEL_PT - 1.5, color=INK, zorder=6)
    positions = layout.positions
    for a, b in edges:
        (x1, y1), (x2, y2) = positions[a], positions[b]
        if area[a] is area[b] and area[a] is not Area.UNRESOLVED:
            _tie(ax, _straight((x1, y1), (x2, y2)), color=TIE, width=0.9)
        else:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            control = (mx - 0.15 * (y2 - y1), my + 0.15 * (x2 - x1))  # a gentle arc keeps long ties apart
            curve = MplPath([(x1, y1), control, (x2, y2)], [MplPath.MOVETO, MplPath.CURVE3, MplPath.CURVE3])
            _tie(ax, curve, color=TIE_BETWEEN, width=0.7, dashed=True)
    draw_nodes(ax, positions, _fills(ctx, positions))
    return p.figure


# ---------------------------------------------------------------------------------------------------- G3 ---
def _group_order(ctx: Context) -> list[str]:
    """Groups on a circle, neighbours sharing members placed next to each other (greedy, deterministic)."""
    groups = [g.id for g in ctx.case.groups]
    if len(groups) <= 2:
        return groups
    members = {g: set(ctx.case.members(g)) for g in groups}
    order = [groups[0]]
    rest = groups[1:]
    while rest:
        last = order[-1]
        nxt = max(rest, key=lambda g: (len(members[g] & members[last]), -groups.index(g)))
        order.append(nxt)
        rest.remove(nxt)
    return order


def _hull(points: list[tuple[float, float]], pad: float) -> np.ndarray:
    """Convex hull of the points, each widened to a circle of radius ``pad`` (a rounded outline)."""
    samples = []
    for x, y in points:
        for k in range(32):
            t = 2 * math.pi * k / 32
            samples.append((x + pad * math.cos(t), y + pad * math.sin(t)))
    pts = sorted(set(samples))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])


HULL_PAD = 0.075
CLEARANCE = 0.035  # a non-member keeps this distance (layout units, about a node radius) from a foreign outline
NESTED_STEP = 0.022  # a group inside other groups gets a tighter outline, so every outline stays visible


def group_pads(ctx: Context) -> dict[str, float]:
    """Outline padding per group (layout units): tighter for each group that contains all its members (nested groups)."""
    members = {g.id: set(ctx.case.members(g.id)) for g in ctx.case.groups}
    pads = {}
    for g, ms in members.items():
        depth = sum(1 for h, hs in members.items() if h != g and ms and ms < hs)
        pads[g] = max(HULL_PAD - NESTED_STEP * depth, 0.03)
    return pads


def _fit(positions: dict[str, tuple[float, float]], margin: float = 0.1) -> dict[str, tuple[float, float]]:
    """Scale the layout into [margin, 1 - margin] on both axes, keeping its proportions."""
    xs = [p[0] for p in positions.values()]
    ys = [p[1] for p in positions.values()]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1e-6)
    scale = (1 - 2 * margin) / span
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    return {n: (0.5 + (x - cx) * scale, 0.5 + (y - cy) * scale) for n, (x, y) in positions.items()}


def g3_layout(ctx: Context) -> dict[str, tuple[float, float]]:
    """Members gather around an anchor of their group (several groups: between the anchors); contacts without a group
    keep to an outer ring, near the contacts they are connected with. Contacts that land inside the outline of a group
    they do not belong to are pushed out. Deterministic. Layout units: the unit square."""
    order = _group_order(ctx)
    k = max(len(order), 1)
    ring = 0.3 if k > 1 else 0.0
    anchors = {g: (0.5 + ring * math.cos(math.pi / 2 + 2 * math.pi * i / k), 0.5 + ring * math.sin(math.pi / 2 + 2 * math.pi * i / k))
               for i, g in enumerate(order)}
    nodes = ctx.case.contact_ids
    groups_of = {cid: ctx.case.groups_of(cid) for cid in nodes}
    start = {}
    for cid in nodes:
        gs = groups_of[cid]
        if gs:
            cx = sum(anchors[g][0] for g in gs) / len(gs)
            cy = sum(anchors[g][1] for g in gs) / len(gs)
            jx, jy = initial_circle([cid], 0.05)[cid]
            start[cid] = (cx + jx, cy + jy)
        else:
            jx, jy = initial_circle([cid], 0.55)[cid]
            start[cid] = (0.5 + jx, 0.5 + jy)
    outer = ring + 0.25

    def pulls(current):
        out = []
        for cid in nodes:
            gs = groups_of[cid]
            for g in gs:
                out.append((cid, anchors[g], 0.08 / len(gs)))
            if not gs:
                x, y = current[cid]
                d = math.hypot(x - 0.5, y - 0.5) or 1.0
                out.append((cid, (0.5 + (x - 0.5) / d * outer, 0.5 + (y - 0.5) / d * outer), 0.08))
        return out

    positions = force_layout(nodes, _edges(ctx), start=start, project=lambda _n, p: p, pulls=pulls, repulsion=0.00012,
                             spring=0.012, iterations=700, min_distance=0.065)
    pads = group_pads(ctx)
    for _ in range(80):
        moved = False
        for g in ctx.case.groups:
            members = ctx.case.members(g.id)
            if not members:
                continue
            hull = MplPath(_hull([positions[m] for m in members], pads[g.id] + CLEARANCE))
            centre = np.mean([positions[m] for m in members], axis=0)
            for cid in nodes:
                if cid in members:
                    continue
                p = np.array(positions[cid])
                if hull.contains_point(p):
                    direction = p - centre
                    norm_ = float(np.hypot(*direction)) or 1.0
                    p = p + direction / norm_ * 0.025
                    positions[cid] = (float(p[0]), float(p[1]))
                    moved = True
        if not moved:
            break
    return _fit(positions)


def intruders(ctx: Context, positions: dict[str, tuple[float, float]]) -> list[tuple[str, str]]:
    """(group, contact) pairs where a non-member lies inside a group outline -- a layout defect, checked by the tests."""
    found = []
    pads = group_pads(ctx)
    for g in ctx.case.groups:
        members = ctx.case.members(g.id)
        if not members:
            continue
        hull = MplPath(_hull([positions[m] for m in members], pads[g.id]))
        for cid in ctx.case.contact_ids:
            if cid not in members and hull.contains_point(positions[cid]):
                found.append((g.id, cid))
    return found


# Outline width = Ego's belonging to the group (1 = very strong ... 5 = not at all); even 5 stays visible.
BELONGING_WIDTH = {"1": 4.2, "2": 3.0, "3": 2.0, "4": 1.2, "5": 0.6}
G3_W, G3_H = 12.0, 8.6
G3_MARGIN = 0.8  # inches around the layout, room for group labels
MAX_STRETCH = 1.45  # the group map may be wider than high, but not distorted beyond this


def group_label_lines(ctx: Context, group) -> tuple[str, str]:
    members = ctx.case.members(group.id)
    name = group.label or "ohne Bezeichnung"
    first = f"{group.id} · {name} · {len(members)} Kontakt{'e' if len(members) != 1 else ''}"
    value = group.belonging.value
    if value:
        second = f"Zugehörigkeit: {value} · {codes.BELONGING[value]}"
    else:
        second = f"Zugehörigkeit: {codes.MISSING_LABELS.get(group.belonging.missing, 'keine Angabe')}"
    return first, second


def _overlap(a, b) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def place_labels(ctx: Context, positions: dict[str, tuple[float, float]], hulls: dict[str, np.ndarray],
                 bounds: tuple[float, float]) -> dict[str, tuple[float, float, str, tuple]]:
    """Label position per group (inches): above, below, right or left of its outline -- the first candidate that hits no
    node, no other label and stays on the page; otherwise the candidate with the fewest collisions."""
    nodes = [(x - NODE_R_IN - 0.03, y - NODE_R_IN - 0.03, x + NODE_R_IN + 0.03, y + NODE_R_IN + 0.03) for x, y in positions.values()]
    placed: list[tuple] = []
    result = {}
    for g in ctx.case.groups:
        if g.id not in hulls:
            continue
        first, second = group_label_lines(ctx, g)
        w = max(text_width(first, LEGEND_PT, bold=True), text_width(second, LEGEND_PT - 0.6)) + 0.08
        h = 0.36
        hull = hulls[g.id]
        xmin, ymin = hull.min(axis=0)
        xmax, ymax = hull.max(axis=0)
        cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
        candidates = []
        for lift in (0.03, 0.3, 0.6):
            for x0 in (cx - w / 2, xmin, xmax - w):  # centred, left-aligned, right-aligned
                candidates += [((x0, ymax + lift, x0 + w, ymax + lift + h), "top"), ((x0, ymin - lift - h, x0 + w, ymin - lift), "bottom")]
            candidates += [((xmax + lift, cy - h / 2, xmax + lift + w, cy + h / 2), "right"),
                           ((xmin - lift - w, cy - h / 2, xmin - lift, cy + h / 2), "left")]
        shifted = []
        for box, side in candidates:  # shift back onto the page instead of dropping the candidate
            dx = max(0.05 - box[0], 0.0) - max(box[2] - (bounds[0] - 0.05), 0.0)
            dy = max(0.05 - box[1], 0.0) - max(box[3] - (bounds[1] - 0.05), 0.0)
            shifted.append(((box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy), side))
        candidates = shifted
        outlines = [MplPath(np.vstack([hh, hh[:1]]), closed=True) for hh in hulls.values()]
        best, best_cost = None, None
        for box, side in candidates:
            inside = box[0] >= 0.05 and box[2] <= bounds[0] - 0.05 and box[1] >= 0.05 and box[3] <= bounds[1] - 0.05
            covered = sum(o.intersects_bbox(Bbox.from_extents(*box), filled=True) for o in outlines)
            cost = (sum(_overlap(box, n) for n in nodes) * 10 + sum(_overlap(box, b) for b in placed) * 10 + covered * 4
                    + (0 if inside else 50))
            if best_cost is None or cost < best_cost:
                best, best_cost = (box, side), cost
            if cost == 0:
                break
        box, side = best
        placed.append(box)
        result[g.id] = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2, side, box)
    return result


def g3_positions(ctx: Context) -> tuple[dict[str, tuple[float, float]], float]:
    """The layout in inches: its bounding box fills the main area (x stretched at most by MAX_STRETCH against y); the
    second value converts layout distances (outline padding) to inches."""
    unit = g3_layout(ctx)
    xs = [x for x, _ in unit.values()]
    ys = [y for _, y in unit.values()]
    w, h = max(max(xs) - min(xs), 1e-6), max(max(ys) - min(ys), 1e-6)
    sy = (G3_H - 2 * G3_MARGIN) / h
    sx = min((G3_W - 2 * G3_MARGIN) / w, sy * MAX_STRETCH)
    sy = min(sy, sx * MAX_STRETCH)
    ox = (G3_W - w * sx) / 2 - min(xs) * sx
    oy = (G3_H - h * sy) / 2 - min(ys) * sy
    return {cid: (ox + x * sx, oy + y * sy) for cid, (x, y) in unit.items()}, min(sx, sy)


def g3(ctx: Context):
    colors = {g.id: GROUP_COLORS[i % len(GROUP_COLORS)] for i, g in enumerate(ctx.case.groups)}
    belonging = [("area", f"{code} · {label}", {"facecolor": "#FFFFFF", "edgecolor": "#55606B", "linewidth": BELONGING_WIDTH[code]})
                 for code, label in codes.BELONGING.items()]
    multi = [ctx.case.groups_of(cid) for cid in ctx.case.contact_ids]
    sections = [
        ("Beziehungstyp", relation_entries(ctx.case)),
        ("Zugehörigkeit von Ego (Umrandung)", belonging),
        (None, [("line", "bestätigte Verbindung", {"color": TIE, "linewidth": 1.0})]
               + ([("ring", "Mitglied mehrerer Gruppen", [GROUP_COLORS[0], GROUP_COLORS[1]])] if any(len(m) > 1 for m in multi) else [])),
    ]
    notes = ["Umrandungsstärke = Egos Zugehörigkeit zur Gruppe, nicht ihre interne Vernetzung; gemeinsame Mitgliedschaft ist keine Verbindung.",
             "Kontakte außerhalb aller Umrandungen gehören keiner Gruppe an. " + ctx.coverage_line()]
    p = page(ctx, "G3 · Gruppenstruktur und Zugehörigkeit", "Von Ego benannte Gruppen, ihre Mitglieder und Egos Zugehörigkeit",
             main_w=G3_W, main_h=G3_H, legend="bottom", sections=sections, notes=notes)
    ax = p.main
    positions, span = g3_positions(ctx)
    pads = group_pads(ctx)
    hulls = {}
    for g in ctx.case.groups:
        members = ctx.case.members(g.id)
        if members:
            hulls[g.id] = _hull([positions[m] for m in members], pads[g.id] * span)
    # fill all first (pale), then outlines from the widest belonging to the thinnest, so thin outlines stay on top
    for g in ctx.case.groups:
        if g.id in hulls:
            ax.add_patch(Polygon(hulls[g.id], closed=True, facecolor=colors[g.id], alpha=0.07, edgecolor="none", zorder=0))
    order = sorted((g for g in ctx.case.groups if g.id in hulls), key=lambda g: -BELONGING_WIDTH.get(g.belonging.value or "", 0.8))
    for g in order:
        value = g.belonging.value
        style = {"linewidth": BELONGING_WIDTH[value]} if value else {"linewidth": 0.8, "linestyle": (0, (1, 2))}
        outline = Polygon(hulls[g.id], closed=True, fill=False, edgecolor=colors[g.id], alpha=0.9, zorder=1, joinstyle="round", **style)
        outline.set_gid(f"group-{g.id}")
        ax.add_patch(outline)
    for a, b in _edges(ctx):
        _tie(ax, _straight(positions[a], positions[b]), color=TIE, width=0.7)
    draw_nodes(ax, positions, _fills(ctx, positions))
    for cid, (x, y) in positions.items():
        gs = ctx.case.groups_of(cid)
        if len(gs) > 1:
            ring_segments(ax, (x, y), [colors[g] for g in gs], NODE_R_IN + 0.07)
    for gid, (x, y, side, box) in place_labels(ctx, positions, hulls, (G3_W, G3_H)).items():
        g = next(gr for gr in ctx.case.groups if gr.id == gid)
        first, second = group_label_lines(ctx, g)
        ax.add_patch(FancyBboxPatch((box[0], box[1]), box[2] - box[0], box[3] - box[1], boxstyle="round,pad=0.02,rounding_size=0.05",
                                    facecolor="#FFFFFF", alpha=0.72, edgecolor="none", zorder=6))
        ax.text(box[0] + 0.04, box[3] - 0.03, first, ha="left", va="top", fontsize=LEGEND_PT, fontweight="bold", color=colors[gid], zorder=7)
        ax.text(box[0] + 0.04, box[1] + 0.03, second, ha="left", va="bottom", fontsize=LEGEND_PT - 0.6, color=MUTED, zorder=7)
    return p.figure
