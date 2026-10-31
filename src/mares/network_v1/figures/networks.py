"""The network figures of network_v1: G1 (personal network), G2 (geographic network), G3 (group map).

G1 shows closeness and relation type only, without ties. In G2 and G3, edges are always *confirmed* contact-contact connections (state ``1``). Denied (``0``) and unknown pairs are never drawn
as lines; a note gives the coverage, so an absent line is not read as 'no contact'. Group membership alone never creates
a line. Node colour = relation type, in all three figures.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, PathPatch, Polygon, Rectangle
from matplotlib.path import Path as MplPath
from matplotlib.transforms import Bbox

from .. import codes
from ..codes import Missing
from ..places import AREA_LABELS, AREA_ORDER, Area, norm
from .base import (
    AREA_TINTS, GROUP_COLORS, INK, LABEL_PT, LEGEND_PT, MUTED, NODE_PT, TIE, TIE_BETWEEN, Context, draw_nodes, force_layout,
    initial_circle, ordinal_dots, page, relation_entries, relation_fill, ring_segments, scale_width, text_width,
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
LABEL_HALF_WIDTH = 0.42  # half the width kept free for the ring numbers at the top, in ring units
G1_SIZE = 8.4  # inches, square main area
SECTOR_ORDER = tuple(codes.RELATION_TYPE) + ("",)  # the six relation types, then 'keine Angabe' -- in every case
SECTOR_GAP = 0.6  # free share between two neighbouring sectors, in contacts
NODE_GAP_IN = 0.08  # free space between two nodes on one ring (inches)


def relation_code(ctx: Context, cid: str) -> str:
    cell = ctx.case.contact(cid).relation_type
    return cell.value if cell.recorded and cell.value in codes.RELATION_TYPE else ""


def g1_sectors(ctx: Context) -> dict[str, tuple[float, float]]:
    """Angular sector per relation type as a share (0 ... 1) of the circle, in the fixed order of SECTOR_ORDER,
    counter-clockwise from the ring numbers at the top. Width ∝ number of contacts; absent types get no width but keep
    their place in the order."""
    counts = {code: 0 for code in SECTOR_ORDER}
    for cid in ctx.case.contact_ids:
        counts[relation_code(ctx, cid)] += 1
    present = [code for code in SECTOR_ORDER if counts[code]]
    total = sum(counts.values()) + SECTOR_GAP * len(present)
    sectors, f = {}, 0.0
    for code in SECTOR_ORDER:
        w = counts[code] / total if total else 0.0
        if counts[code]:
            f += SECTOR_GAP / 2 / total
        sectors[code] = (f, f + w)
        f += w + (SECTOR_GAP / 2 / total if counts[code] else 0.0)
    return sectors


def _spread(wanted: list[float], gap: float, lo: float, hi: float) -> list[float]:
    """Positions closest to ``wanted`` (sorted) with at least ``gap`` between neighbours, inside [lo, hi]
    (pool adjacent violators on wanted[i] - i·gap). Order is kept."""
    n = len(wanted)
    gap = min(gap, (hi - lo) / max(n - 1, 1))
    shifted = [w - i * gap for i, w in enumerate(wanted)]
    blocks: list[list[float]] = []  # [mean, count]
    for v in shifted:
        blocks.append([v, 1])
        while len(blocks) > 1 and blocks[-2][0] > blocks[-1][0]:
            m2, c2 = blocks.pop()
            m1, c1 = blocks.pop()
            blocks.append([(m1 * c1 + m2 * c2) / (c1 + c2), c1 + c2])
    flat = [m for m, c in blocks for _ in range(c)]
    top = hi - (n - 1) * gap
    return [min(max(v, lo), top) + i * gap for i, v in enumerate(flat)]


def g1_layout(ctx: Context) -> dict[str, tuple[float, float]]:
    """Radius = recorded closeness (1 ... 4, half steps between); contacts without closeness on an outer arc. The angle
    groups the contacts by relation type: each type has a fixed sector (:func:`g1_sectors`); on each ring the contacts of
    a type are spread over their sector (in ID order) and then pushed apart just enough that no two nodes overlap; the
    ring numbers at the top stay free. Only the angle is layout; no contact is ever moved to another radius.
    Deterministic."""
    radius = {}
    for c in ctx.case.contacts:
        value = codes.closeness_value(c.closeness)
        radius[c.id] = value if value is not None else MISSING_RADIUS
    sectors = g1_sectors(ctx)
    lim = (MISSING_RADIUS if MISSING_RADIUS in radius.values() else max(codes.CLOSENESS_LEVELS)) + 0.45
    node = (2 * NODE_R_IN + NODE_GAP_IN) * 2 * lim / G1_SIZE  # node diameter plus gap, in ring units
    by_ring: dict[float, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for cid in ctx.case.contact_ids:
        by_ring[radius[cid]][relation_code(ctx, cid)].append(cid)
    positions = {}
    for r, by_type in by_ring.items():
        wedge = math.atan2(LABEL_HALF_WIDTH, r)  # wider on inner rings
        start, span = math.pi / 2 + wedge, 2 * math.pi - 2 * wedge
        ids, wanted = [], []
        for code in SECTOR_ORDER:
            f0, f1 = sectors[code]
            members = sorted(by_type.get(code, []))
            for i, cid in enumerate(members):
                ids.append(cid)
                wanted.append(start + span * (f0 + (f1 - f0) * (i + 0.5) / len(members)))
        gap = 2 * math.asin(min(node / (2 * r), 1.0))
        for cid, angle in zip(ids, _spread(wanted, gap, start + gap / 2, start + span - gap / 2)):
            positions[cid] = (r * math.cos(angle), r * math.sin(angle))
    return {cid: positions[cid] for cid in ctx.case.contact_ids}


def g1(ctx: Context):
    """Closeness and relation type only. Contact-contact ties are shown in G2 and G3, not here."""
    sections = [
        ("Beziehungstyp", relation_entries(ctx.case)),
        ("Persönliche Nähe", [
            ("line", "1 sehr nah · 2 nah ·\n3 weniger nah · 4 außerhalb",{"color": "#9AA5B1", "linewidth": 1.0}),
            ("line", "Zwischenwerte 1,5 · 2,5 · 3,5", {"color": "#C3CAD1", "linewidth": 0.7, "linestyle": (0, (2, 3))}),
        ]),
    ]
    notes = ["Abstand zu Ego = persönliche Nähe; Winkelbereiche ordnen die Kontakte nach Beziehungstyp. "
             "Die genaue Position innerhalb eines Sektors hat keine zusätzliche inhaltliche Bedeutung."]
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
    if without:
        ax.add_patch(Circle((0, 0), MISSING_RADIUS, fill=False, edgecolor="#C9CED3", linewidth=0.6, linestyle=(0, (1, 3))))
        ax.text(0, -MISSING_RADIUS - 0.22, "Nähe ohne Angabe", fontsize=LABEL_PT - 1.5, color=MUTED, ha="center", va="top", style="italic")
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
UNPLACED_H = 0.5  # the line below the bands for contacts with unresolved residence and confirmed ties
HEADER_H_G2 = 0.62
BRACKET_H_G2 = 0.3
SHELF_GAP = 0.18
STAGGER = 0.52  # in a shelf of three or more subgroups every second one sits lower, so no tie runs through a third node
# (and the lower label stays below the ties between its neighbours)
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
    """x-range per band in inches, the five areas only ('nicht zuordenbar' is never a band). Width = room for the widest
    subgroup plus a share ∝ √(contacts) of the rest."""
    counts = defaultdict(int)
    for cid in ctx.case.contact_ids:
        counts[ctx.derived.area(cid)] += 1
    groups = subgroups(ctx, ctx.case.contact_ids)
    areas = list(AREA_ORDER)
    gaps = BAND_GAP * (len(areas) - 1) + OUTSIDE_GAP_G2
    width = G2_W
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


def _stagger(shelf: list[Subgroup]) -> float:
    return STAGGER if len(shelf) >= 3 else 0.0


def _shelf_height(shelf: list[Subgroup]) -> float:
    return max(g.footprint[1] for g in shelf) + _stagger(shelf)


def _shelves_height(shelves: list[list[Subgroup]]) -> float:
    return sum(_shelf_height(s) for s in shelves) + SHELF_GAP * max(len(shelves) - 1, 0)


def _arrange(shelves: list[list[Subgroup]], x0: float, x1: float, top: float, height: float) -> None:
    """Shelves spread over the zone height, subgroups spread over the band width."""
    content = _shelves_height(shelves)
    y = top - max(height - content, 0) / 2
    for shelf in shelves:
        widths = [g.footprint[0] for g in shelf]
        free = (x1 - x0) - sum(widths)
        gap = free / (len(shelf) + 1)
        x = x0 + gap
        for i, (g, w) in enumerate(zip(shelf, widths)):
            label_h = SUB_LABEL_H if g.label else 0.0
            g.x = x + (w - g.width) / 2
            g.top = y - label_h - (_stagger(shelf) if i % 2 else 0.0)
            x += w + gap
        y -= _shelf_height(shelf) + SHELF_GAP


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
    zone_bottom: float = 0.05  # bottom of the bands; below it only the line of unplaced contacts
    unplaced: list[str] = field(default_factory=list)  # unresolved residence, with confirmed ties: drawn below the bands
    not_shown: list[str] = field(default_factory=list)  # unresolved residence, no confirmed tie: named in a note only


def g2_layout(ctx: Context) -> G2Layout:
    """Bands of the five areas; inside each band the contacts are bundled by place or country (subgroups). Contacts with
    a confirmed connection sit in the upper zone (on an ellipse per subgroup), the others in a lower zone (on a grid).
    Contacts whose residence cannot be assigned get no band: with confirmed ties they sit on a separate line below the
    bands (so no tie is lost), without ties they are only named in a note. Deterministic."""
    bands = g2_bands(ctx)
    edges = _edges(ctx)
    linked = {c for e in edges for c in e}
    unresolved = ctx.unresolved()
    unplaced = [c for c in unresolved if c in linked]
    ids = [c for c in ctx.case.contact_ids if c not in unresolved]
    upper = subgroups(ctx, [c for c in ids if c in linked], ring=True)
    lower = subgroups(ctx, [c for c in ids if c not in linked])
    shelves_up = {a: _pack(upper.get(a, []), *bands[a]) for a in bands}
    shelves_low = {a: _pack(lower.get(a, []), *bands[a]) for a in bands}
    up_h = max([_shelves_height(s) for s in shelves_up.values()] + [2.6])
    low_h = max([_shelves_height(s) for s in shelves_low.values()] + [0.0])
    header = HEADER_H_G2 + BRACKET_H_G2
    zone_bottom = 0.05 + (UNPLACED_H if unplaced else 0.0)
    height = header + up_h + (ISOLATED_LABEL_H + low_h + 0.12 if low_h else 0.0) + 0.05 + zone_bottom
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
    x0 = text_width(UNPLACED_LABEL, LABEL_PT - 1.5) + 0.35
    for i, cid in enumerate(unplaced):
        positions[cid] = (x0 + i * STEP, UNPLACED_H / 2)
    return G2Layout(bands, positions, groups, height, zone_top, isolated_top, zone_bottom, unplaced,
                    [c for c in unresolved if c not in linked])


UNPLACED_LABEL = "Wohnort nicht zuordenbar (keinem Bereich zugeordnet):"


def g2(ctx: Context):
    layout = g2_layout(ctx)
    edges = _edges(ctx)
    area = {cid: ctx.derived.area(cid) for cid in ctx.case.contact_ids}
    within = sum(1 for a, b in edges if area[a] is area[b] and area[a] is not Area.UNRESOLVED)
    unassigned = sum(1 for a, b in edges if Area.UNRESOLVED in (area[a], area[b]))
    between = len(edges) - within - unassigned
    other = f" · ohne Bereich ({unassigned})" if unassigned else ""
    sections = [
        ("Beziehungstyp", relation_entries(ctx.case)),
        ("Verbindungen", [
            ("line", f"im selben Bereich ({within})", {"color": TIE, "linewidth": 1.0}),
            ("line", f"zwischen Bereichen ({between}){other}", {"color": TIE_BETWEEN, "linewidth": 0.8, "linestyle": (0, (4, 2.5))}),
        ]),
        (None, [("area", "gleicher Wohnort bzw. Wohnland", {"facecolor": "#FFFFFF", "edgecolor": "#B8C0C8", "linewidth": 0.7})]),
    ]
    hidden = f" Wohnort nicht zuordenbar: {', '.join(layout.not_shown)}." if layout.not_shown else ""
    notes = ["Wohnortbereiche sind Kategorien, keine Entfernungen; Flächen bündeln Kontakte mit gleichem Wohnort bzw. Wohnland." + hidden,
             "Linien zeigen bestätigte Verbindungen; fehlende Linien bedeuten nicht zwangsläufig keinen Kontakt. " + ctx.coverage_line()]
    p = page(ctx, "G2 · Geografisches Beziehungsnetz", "Kontakte nach Wohnortbereich und bestätigte Verbindungen zwischen ihnen",
             main_w=G2_W, main_h=layout.height, legend="bottom", sections=sections, notes=notes)
    ax = p.main
    counts = defaultdict(int)
    for a in area.values():
        counts[a] += 1
    zone_bottom = layout.zone_bottom
    header_y = layout.zone_top + 0.08
    for a, (x0, x1) in layout.bands.items():
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
    if layout.unplaced:  # no background, no frame: these contacts are outside the geography, not a sixth area
        ax.text(0.06, UNPLACED_H / 2, UNPLACED_LABEL, fontsize=LABEL_PT - 1.5, color=MUTED, ha="left", va="center", style="italic")
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
def nested_groups(ctx: Context) -> set[str]:
    """Groups whose members all belong to another (larger) group as well -- they sit inside it."""
    members = {g.id: set(ctx.case.members(g.id)) for g in ctx.case.groups}
    return {g for g, ms in members.items() if ms and any(h != g and ms < hs for h, hs in members.items())}


def _group_order(ctx: Context) -> list[str]:
    """Groups on a circle, neighbours sharing members placed next to each other (greedy, deterministic). A nested group
    gets no place of its own: its members lie where the groups around it overlap."""
    inner = nested_groups(ctx)
    groups = [g.id for g in ctx.case.groups if g.id not in inner]
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


def loose_contacts(ctx: Context) -> list[str]:
    """Contacts in no group and without a confirmed tie: they carry no structure and are set apart in one row."""
    linked = {c for e in _edges(ctx) for c in e}
    return [cid for cid in ctx.case.contact_ids if not ctx.case.groups_of(cid) and cid not in linked]


def g3_layout(ctx: Context) -> dict[str, tuple[float, float]]:
    """Members gather around an anchor of their group (several groups: between the anchors; a nested group has no
    anchor of its own); contacts without a group but with ties keep to an outer ring, near the contacts they are
    connected with. Contacts that land inside the outline of a group they do not belong to are pushed out. Contacts
    without group and tie are not part of this layout (:func:`loose_contacts`). Deterministic. Layout units: the unit
    square."""
    order = _group_order(ctx)
    k = max(len(order), 1)
    ring = 0.3 if k > 1 else 0.0
    anchors = {g: (0.5 + ring * math.cos(math.pi / 2 + 2 * math.pi * i / k), 0.5 + ring * math.sin(math.pi / 2 + 2 * math.pi * i / k))
               for i, g in enumerate(order)}
    loose = set(loose_contacts(ctx))
    nodes = [cid for cid in ctx.case.contact_ids if cid not in loose]
    groups_of = {cid: [g for g in ctx.case.groups_of(cid) if g in anchors] for cid in nodes}
    for cid in nodes:  # a contact only in nested groups follows the groups around them
        if not groups_of[cid] and ctx.case.groups_of(cid):
            inner = set(ctx.case.groups_of(cid))
            groups_of[cid] = [g for g in anchors if any(set(ctx.case.members(i)) <= set(ctx.case.members(g)) for i in inner)]
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
        for cid in positions:
            if cid not in members and hull.contains_point(positions[cid]):
                found.append((g.id, cid))
    return found


OUTLINE_W = 1.8  # one outline width for every group: the width carries no meaning
G3_W, G3_H = 12.0, 8.6
G3_MARGIN = 0.8  # inches above and below the layout, room for group labels
G3_MARGIN_X = 1.5  # inches left and right: a label block beside a group at the edge still fits on the page
LOOSE_H = 0.5  # the row of contacts without group and tie, at the bottom of the main area
MAX_STRETCH = 1.45  # the group map may be wider than high, but not distorted beyond this
LABEL_H = 0.38
LOOSE_LABEL = "keiner Gruppe zugeordnet, keine bestätigte Verbindung:"
NAME_MAX = 34  # characters of a group name shown in its label; longer names are shortened in the figure only
# explanatory suffixes of test data, e.g. 'Kreis 1 (fiktive Bezeichnung)': the case badge already says so
TEST_SUFFIX = re.compile(r"\s*\((?:fiktiv\w*|synthetisch\w*)(?:\s+\w+)?\)\s*$", re.IGNORECASE)
MISSING_SHORT = {Missing.UNKNOWN: "NS", Missing.NO_ANSWER: "KA", Missing.NOT_APPLICABLE: "NA", Missing.NOT_COLLECTED: "n. e."}


def belonging_text(group) -> str:
    """The recorded answer as its number, or the short code of the missing answer -- never a guessed value."""
    value = group.belonging.value
    if value:
        return value
    return MISSING_SHORT.get(group.belonging.missing, "–")


def display_name(label: str) -> str:
    """The group name as shown: without a test-data suffix, shortened if very long. The data are not changed."""
    name = TEST_SUFFIX.sub("", label or "").strip() or "ohne Bezeichnung"
    return name if len(name) <= NAME_MAX else name[: NAME_MAX - 1].rstrip() + "…"


def group_label_lines(ctx: Context, group) -> tuple[str, str]:
    """First line of a group label ('C04 · name (3)'), and the text after the belonging dots."""
    return f"{group.id} · {display_name(group.label)} ({len(ctx.case.members(group.id))})", belonging_text(group)


def _label_width(ctx: Context, group) -> float:
    first, second = group_label_lines(ctx, group)
    line2 = scale_width() + 0.08 + text_width(second, LEGEND_PT - 0.6, bold=True)
    return max(text_width(first, LEGEND_PT, bold=True), line2) + 0.1


def _overlap(a, b) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _box_point(box, x: float, y: float) -> tuple[float, float]:
    """The point of a box closest to (x, y)."""
    return min(max(x, box[0]), box[2]), min(max(y, box[1]), box[3])


def label_gap(box, hull: np.ndarray) -> tuple[float, tuple[float, float], tuple[float, float]]:
    """Distance between a label box and a group outline, with the two closest points (box, outline)."""
    best = None
    for x, y in hull:
        bx, by = _box_point(box, x, y)
        d = math.hypot(x - bx, y - by)
        if best is None or d < best[0]:
            best = (d, (bx, by), (float(x), float(y)))
    return best


LEADER_GAP = 0.12  # a label further than this from its outline gets a fine leader line


def _containers(ctx: Context) -> dict[str, set[str]]:
    """Per group, the other groups that contain all its members (a label of the inner group may lie on their areas)."""
    members = {g.id: set(ctx.case.members(g.id)) for g in ctx.case.groups}
    return {g: {h for h, hs in members.items() if h != g and ms and ms <= hs} for g, ms in members.items()}


LABEL_DIRECTIONS = 32  # candidate directions around an outline
LABEL_GAPS = (0.08, 0.2, 0.36, 0.6, 0.9)  # inches between outline and label block (the far ones need a leader line)
LABEL_CLEAR = 0.05  # margin around a label block in the collision test (its white background reaches a little further)


def label_candidates(hull: np.ndarray, w: float, h: float) -> list[tuple[tuple[float, float, float, float], int]]:
    """Label boxes (x0, y0, x1, y1) right outside an outline: in each of LABEL_DIRECTIONS directions the box is moved
    out from the centre until it clears the outline's supporting line, plus boxes flush above and below the outline,
    slid along it. Second value: rank of the gap (0 = closest)."""
    c = hull.mean(axis=0)
    xmin, ymin = hull.min(axis=0)
    xmax, ymax = hull.max(axis=0)
    out = []
    for rank, gap in enumerate(LABEL_GAPS):
        for k in range(LABEL_DIRECTIONS):
            t = 2 * math.pi * k / LABEL_DIRECTIONS
            ux, uy = math.cos(t), math.sin(t)
            support = float(np.max(hull @ np.array([ux, uy]))) - (c[0] * ux + c[1] * uy)
            d = support + gap + w / 2 * abs(ux) + h / 2 * abs(uy)
            x, y = c[0] + ux * d, c[1] + uy * d
            out.append(((x - w / 2, y - h / 2, x + w / 2, y + h / 2), rank))
        for f in (0.0, 0.25, 0.5, 0.75, 1.0):
            x0 = xmin - w / 2 + f * (xmax - xmin)
            out += [((x0, ymax + gap, x0 + w, ymax + gap + h), rank), ((x0, ymin - gap - h, x0 + w, ymin - gap), rank)]
    return out


def place_labels(ctx: Context, positions: dict[str, tuple[float, float]], hulls: dict[str, np.ndarray],
                 bounds: tuple[float, float], floor: float = 0.05) -> dict[str, tuple[float, float, str, tuple]]:
    """Label block (name line and belonging scale) per group, in inches, right at its outline: the candidate with no
    node, no tie, no other label, no foreign outline and no foreign group area under it and the smallest distance to its
    outline; otherwise the one with the fewest such collisions. A nested group's label may lie on the areas of the
    groups around it (not on their outlines). Larger groups are placed first."""
    nodes = [(x - NODE_R_IN - 0.03, y - NODE_R_IN - 0.03, x + NODE_R_IN + 0.03, y + NODE_R_IN + 0.03) for x, y in positions.values()]
    ties = [_straight(positions[a], positions[b]) for a, b in _edges(ctx) if a in positions and b in positions]
    outlines = {gid: MplPath(np.vstack([hh, hh[:1]]), closed=True) for gid, hh in hulls.items()}
    containers = _containers(ctx)
    placed: list[tuple] = []
    result = {}
    groups = sorted((g for g in ctx.case.groups if g.id in hulls), key=lambda g: -len(ctx.case.members(g.id)))
    for g in groups:
        w, h = _label_width(ctx, g), LABEL_H
        hull = hulls[g.id]
        best, best_cost = None, None
        for box, rank in label_candidates(hull, w, h):
            dx = max(0.05 - box[0], 0.0) - max(box[2] - (bounds[0] - 0.05), 0.0)  # shifted back onto the page
            dy = max(floor - box[1], 0.0) - max(box[3] - (bounds[1] - 0.05), 0.0)
            box = (box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy)
            bbox = Bbox.from_extents(box[0] - LABEL_CLEAR, box[1] - LABEL_CLEAR, box[2] + LABEL_CLEAR, box[3] + LABEL_CLEAR)
            lines = sum(o.intersects_bbox(bbox, filled=False) for gid, o in outlines.items())  # any outline, own included
            areas = sum(o.intersects_bbox(bbox, filled=True) for gid, o in outlines.items()
                        if gid != g.id and gid not in containers[g.id])
            crossed = sum(t.intersects_bbox(bbox, filled=False) for t in ties)
            gap, near_box, near_hull = label_gap(box, hull)
            leader = 0
            if gap > LEADER_GAP:  # the leader line should not cross other outlines either
                segment = _straight(near_box, near_hull)
                leader = sum(segment.intersects_path(o, filled=False) for gid, o in outlines.items() if gid != g.id)
            cost = (sum(_overlap(box, n) for n in nodes) * 30 + sum(_overlap(box, b) for b in placed) * 30 + lines * 8
                    + areas * 6 + crossed * 6 + leader * 2 + gap * 10 + rank * 0.2)
            if best_cost is None or cost < best_cost:
                best, best_cost = box, cost
        placed.append(best)
        result[g.id] = ((best[0] + best[2]) / 2, (best[1] + best[3]) / 2, "", best)
    return result


def g3_positions(ctx: Context) -> tuple[dict[str, tuple[float, float]], float]:
    """The layout in inches: its bounding box fills the main area above the row of loose contacts (x stretched at most
    by MAX_STRETCH against y); the second value converts layout distances (outline padding) to inches."""
    unit = g3_layout(ctx)
    floor = LOOSE_H if loose_contacts(ctx) else 0.0
    xs = [x for x, _ in unit.values()]
    ys = [y for _, y in unit.values()]
    w, h = max(max(xs) - min(xs), 1e-6), max(max(ys) - min(ys), 1e-6)
    sy = (G3_H - floor - 2 * G3_MARGIN) / h
    sx = min((G3_W - 2 * G3_MARGIN_X) / w, sy * MAX_STRETCH)
    sy = min(sy, sx * MAX_STRETCH)
    ox = (G3_W - w * sx) / 2 - min(xs) * sx
    oy = floor + (G3_H - floor - h * sy) / 2 - min(ys) * sy
    return {cid: (ox + x * sx, oy + y * sy) for cid, (x, y) in unit.items()}, min(sx, sy)


def membership_marked(ctx: Context) -> list[str]:
    """Contacts of several groups that get ring segments: only where the outlines alone do not show it, i.e. not when
    one of the contact's groups lies inside all its other groups (a nested group already shows the overlap)."""
    members = {g.id: set(ctx.case.members(g.id)) for g in ctx.case.groups}
    marked = []
    for cid in ctx.case.contact_ids:
        gs = ctx.case.groups_of(cid)
        if len(gs) < 2:
            continue
        if any(all(members[i] < members[o] for o in gs if o != i) for i in gs):
            continue
        marked.append(cid)
    return marked


def g3(ctx: Context):
    colors = {g.id: GROUP_COLORS[i % len(GROUP_COLORS)] for i, g in enumerate(ctx.case.groups)}
    marked = membership_marked(ctx)
    scale = [("scale", "1 = sehr stark bis 5 = überhaupt nicht; der markierte Punkt zeigt den erhobenen Wert", "2")]
    missing = sorted({g.belonging.missing for g in ctx.case.groups if not g.belonging.value}, key=list(MISSING_SHORT).index)
    if missing:
        named = ", ".join(f"{MISSING_SHORT[m]} = {codes.MISSING_LABELS[m].split(' (')[0]}" for m in missing)
        scale.append(("scale", f"kein Wert ({named}): kein Punkt markiert", None))
    sections = [
        ("Beziehungstyp", relation_entries(ctx.case)),
        ("Zugehörigkeit zu einer Gruppe", scale),
        (None, [("line", "bestätigte Verbindung", {"color": TIE, "linewidth": 1.0})]
               + ([("ring", "Mitglied mehrerer Gruppen", [GROUP_COLORS[0], GROUP_COLORS[1]])] if marked else [])),
    ]
    notes = ["Gruppen umfassen die von Ego zugeordneten Kontakte; gemeinsame Mitgliedschaft ist keine Verbindung.",
             ctx.coverage_line()]
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
    for g in ctx.case.groups:  # fill all first (pale), then the outlines
        if g.id in hulls:
            ax.add_patch(Polygon(hulls[g.id], closed=True, facecolor=colors[g.id], alpha=0.07, edgecolor="none", zorder=0))
    for g in ctx.case.groups:
        if g.id in hulls:
            outline = Polygon(hulls[g.id], closed=True, fill=False, edgecolor=colors[g.id], alpha=0.9, zorder=1, joinstyle="round",
                              linewidth=OUTLINE_W)
            outline.set_gid(f"group-{g.id}")
            ax.add_patch(outline)
    for a, b in _edges(ctx):
        _tie(ax, _straight(positions[a], positions[b]), color=TIE, width=0.7)
    loose = loose_contacts(ctx)
    floor = LOOSE_H if loose else 0.05
    if loose:
        x0 = text_width(LOOSE_LABEL, LABEL_PT - 1.5) + 0.35
        ax.text(0.06, LOOSE_H / 2, LOOSE_LABEL, fontsize=LABEL_PT - 1.5, color=MUTED, ha="left", va="center", style="italic")
        for i, cid in enumerate(loose):
            positions[cid] = (x0 + i * 0.5, LOOSE_H / 2)
    draw_nodes(ax, positions, _fills(ctx, positions))
    for cid in marked:
        ring_segments(ax, positions[cid], [colors[g] for g in ctx.case.groups_of(cid)], NODE_R_IN + 0.07)
    labelled = {cid: xy for cid, xy in positions.items() if cid not in loose}
    for gid, (_x, _y, _side, box) in place_labels(ctx, labelled, hulls, (G3_W, G3_H), floor).items():
        g = next(gr for gr in ctx.case.groups if gr.id == gid)
        first, second = group_label_lines(ctx, g)
        gap, near_box, near_hull = label_gap(box, hulls[gid])
        if gap > LEADER_GAP:  # assigns a label that cannot sit right at its outline (nested or crowded groups)
            ax.plot([near_box[0], near_hull[0]], [near_box[1], near_hull[1]], color=colors[gid], linewidth=0.8, zorder=5,
                    gid=f"leader-{gid}")
            ax.add_patch(Circle(near_hull, 0.03, facecolor=colors[gid], edgecolor="none", zorder=5))
        ax.add_patch(FancyBboxPatch((box[0], box[1]), box[2] - box[0], box[3] - box[1], boxstyle="round,pad=0.02,rounding_size=0.05",
                                    facecolor="#FFFFFF", alpha=0.85, edgecolor="none", zorder=6, gid=f"label-{gid}"))
        ax.text(box[0] + 0.05, box[3] - 0.03, first, ha="left", va="top", fontsize=LEGEND_PT, fontweight="bold", color=colors[gid], zorder=7)
        y = box[1] + 0.1
        x = box[0] + 0.05
        x += ordinal_dots(ax, x, y, g.belonging.value) + 0.08
        ax.text(x, y, second, ha="left", va="center", fontsize=LEGEND_PT - 0.6, color=INK if g.belonging.value else MUTED,
                fontweight="bold" if g.belonging.value else "normal", style="normal" if g.belonging.value else "italic", zorder=7)
    return p.figure
