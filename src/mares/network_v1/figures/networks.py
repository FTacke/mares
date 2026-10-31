"""The network figures of network_v1: G1 (personal network), G2 (geographic network), G3 (groups and belonging).

Edges are always *confirmed* contact-contact connections (state ``1``). Denied (``0``) and unknown pairs are never drawn
as lines; the case line and the note give the coverage, so an absent line is not read as 'no contact'. Group
membership alone never creates a line.
"""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, PathPatch, Polygon, Rectangle, Wedge
from matplotlib.path import Path as MplPath

from .. import codes
from ..places import AREA_LABELS, Area
from .base import (
    AREA_COLORS, GROUP_COLORS, ID_PT, INK, MISSING_FILL, MUTED, RELATION_COLORS, SMALL_PT, TEXT_PT, TIE_BETWEEN, TIE_WITHIN,
    Context, draw_nodes, force_layout, frame, initial_circle, legend_box, new_figure, rim_color,
)

EGO_FILL = "#1F2933"


def _relation_fill(ctx: Context, cid: str) -> str | None:
    cell = ctx.case.contact(cid).relation_type
    return RELATION_COLORS.get(cell.value) if cell.recorded else None


def _area_fill(ctx: Context, cid: str) -> str | None:
    area = ctx.derived.area(cid)
    return None if area is Area.UNRESOLVED else AREA_COLORS[area]


def _edges(ctx: Context) -> list[tuple[str, str]]:
    return ctx.derived.confirmed_edges


# ---------------------------------------------------------------------------------------------------- G1 ---
MISSING_RADIUS = 4.75
LABEL_HALF_WIDTH = 0.33  # half the width kept free for the ring numbers at the top, in ring units


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
    """A tie between two contacts; one that would pass close to Ego bends away from the centre, so it is never
    mistaken for an ego line."""
    (x1, y1), (x2, y2) = p1, p2
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dist = math.hypot(mx, my)
    push = max(0.0, 1.25 - dist)
    if push == 0.0:
        control = (mx, my)
    else:
        if dist > 0.05:
            ux, uy = mx / dist, my / dist
        else:
            length = math.hypot(x2 - x1, y2 - y1) or 1.0
            ux, uy = -(y2 - y1) / length, (x2 - x1) / length
        control = (mx + ux * push * 1.6, my + uy * push * 1.6)
    return MplPath([(x1, y1), control, (x2, y2)], [MplPath.MOVETO, MplPath.CURVE3, MplPath.CURVE3])


def g1(ctx: Context):
    figure = new_figure(11.0, 9.6)
    ax = figure.add_axes((0.02, 0.07, 0.66, 0.82))
    ax.set_aspect("equal")
    ax.axis("off")
    lim = MISSING_RADIUS + 0.55
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    for value in codes.CLOSENESS_LEVELS:
        whole = value == int(value)
        ax.add_patch(Circle((0, 0), value, fill=False, edgecolor="#9AA5B1" if whole else "#D5DAE0",
                            linewidth=1.0 if whole else 0.6, linestyle="solid" if whole else (0, (2, 3)), zorder=0))
        if whole:
            ax.text(0, value, f"{int(value)}", fontsize=SMALL_PT + 0.5, color=MUTED, ha="center", va="center", zorder=1,
                    bbox={"boxstyle": "round,pad=0.12", "facecolor": "white", "edgecolor": "none"})
    positions = g1_layout(ctx)
    if any(codes.closeness_value(c.closeness) is None for c in ctx.case.contacts):
        ax.add_patch(Circle((0, 0), MISSING_RADIUS, fill=False, edgecolor="#C9CED3", linewidth=0.6, linestyle=(0, (1, 3))))
        ax.text(0, -MISSING_RADIUS - 0.2, "Nähe ohne Angabe", fontsize=SMALL_PT, color=MUTED, ha="center", va="top", style="italic")
    for a, b in _edges(ctx):
        ax.add_patch(PathPatch(_bent(positions[a], positions[b]), fill=False, edgecolor=TIE_WITHIN, linewidth=0.8, alpha=0.85, zorder=2))
    ax.add_patch(Circle((0, 0), 0.36, facecolor=EGO_FILL, edgecolor="white", zorder=5))
    ax.text(0, 0, "Ego", color="white", fontsize=TEXT_PT - 1, ha="center", va="center", fontweight="bold", zorder=6)
    draw_nodes(ax, positions, {cid: _relation_fill(ctx, cid) for cid in positions}, size=330)

    side = figure.add_axes((0.69, 0.07, 0.29, 0.82))
    side.axis("off")
    entries = [(f"{code} · {label}".replace("professioneller/institutioneller Kontakt", "professionell / institutionell"), RELATION_COLORS[code])
               for code, label in codes.RELATION_TYPE.items()]
    if any(_relation_fill(ctx, c) is None for c in ctx.case.contact_ids):
        entries.append(("keine Angabe", MISSING_FILL))
    y = legend_box(side, entries, "Beziehungstyp (Tabelle A)", x=0.0, y=0.98, line_gap=0.038)
    y = legend_box(side, [], "Ringe = persönliche Nähe (Tabelle A)", x=0.0, y=y - 0.02, line_gap=0.038)
    for value in (1, 2, 3, 4):
        side.text(0.0, y + 0.01, f"{value} · {codes.CLOSENESS[float(value)]}", transform=side.transAxes, fontsize=TEXT_PT - 0.5, color=INK, va="center")
        y -= 0.034
    side.text(0.0, y + 0.01, "gestrichelt: Zwischenwerte 1,5 · 2,5 · 3,5", transform=side.transAxes, fontsize=TEXT_PT - 0.5, color=MUTED, va="center")
    y -= 0.04
    side.add_line(Line2D([0.0, 0.07], [y - 0.03, y - 0.03], transform=side.transAxes, color=TIE_WITHIN, linewidth=1.2))
    side.text(0.1, y - 0.03, "bestätigte Verbindung\nzwischen Kontakten", transform=side.transAxes, fontsize=TEXT_PT - 0.5, va="center")
    side.text(0.0, y - 0.13, (
        "Abstand zu Ego = erhobene Nähe, nie aus\nder Kartenposition abgeleitet.\n\n"
        "Die Lage auf dem Kreis ist ein reproduzier-\nbares Layout ohne Bedeutung.\n\n"
        "Unbekannte und verneinte Paare werden\nnicht gezeichnet; fehlende Linie heißt\nnicht „kein Kontakt“.\n\n"
        "Ego ist mit allen Kontakten verbunden\n(nicht gezeichnet).\n\n" + ctx.coverage_line().replace(" · ", "\n", 1)
    ), transform=side.transAxes, fontsize=SMALL_PT + 0.3, color=INK, va="top", linespacing=1.35)
    frame(figure, ctx, "G1 · Persönliches Beziehungsnetz", "Kontakte nach erhobener persönlicher Nähe und Beziehungstyp")
    return figure


# ---------------------------------------------------------------------------------------------------- G2 ---
def g2_bands(ctx: Context) -> dict[Area, tuple[float, float]]:
    """Band per area: width follows the number of contacts (at least room for two)."""
    counts = defaultdict(int)
    for r in ctx.derived.residence.values():
        counts[r.area] += 1
    areas = ctx.areas_present()
    widths = {a: math.sqrt(max(counts[a], 2)) for a in areas}
    total = sum(widths.values())
    bands, x = {}, 0.0
    for a in areas:
        w = widths[a] / total
        bands[a] = (x, x + w)
        x += w
    return bands


ISOLATED_Y = 0.07  # contacts without a confirmed connection: a row of their own at the bottom of their band


def g2_layout(ctx: Context) -> dict[str, tuple[float, float]]:
    """Connected contacts: a force layout confined to their band (x) and to the upper part (y). Contacts without a
    confirmed connection: evenly spaced in a row at the bottom of their band, so they are neither hidden nor stuck at a
    border."""
    bands = g2_bands(ctx)
    nodes = ctx.case.contact_ids
    area = {cid: ctx.derived.area(cid) for cid in nodes}
    edges = _edges(ctx)
    linked = {c for e in edges for c in e}
    pad = 0.03
    positions: dict[str, tuple[float, float]] = {}
    for a, (x0, x1) in bands.items():
        alone = [c for c in nodes if area[c] is a and c not in linked]
        for i, cid in enumerate(alone):
            positions[cid] = (x0 + (x1 - x0) * (i + 1) / (len(alone) + 1), ISOLATED_Y)
    connected = [c for c in nodes if c in linked]

    def project(n, p):
        x0, x1 = bands[area[n]]
        return np.array([min(max(p[0], x0 + pad), x1 - pad), min(max(p[1], 0.24), 0.94)])

    start = {}
    for n in connected:
        x0, x1 = bands[area[n]]
        cx, cy = initial_circle([n], 0.3)[n]
        start[n] = ((x0 + x1) / 2 + cx * (x1 - x0), 0.58 + cy)
    centre = [(n, ((bands[area[n]][0] + bands[area[n]][1]) / 2, 0.58), 0.012) for n in connected]
    positions.update(force_layout(connected, edges, start=start, project=project, pulls=centre, repulsion=0.00006, spring=0.04,
                                  iterations=700, min_distance=0.06))
    return positions


def g2(ctx: Context):
    figure = new_figure(12.5, 8.2)
    ax = figure.add_axes((0.03, 0.17, 0.94, 0.68))
    ax.axis("off")
    ax.set_xlim(-0.005, 1.005)
    ax.set_ylim(-0.02, 1.1)
    bands = g2_bands(ctx)
    counts = defaultdict(int)
    for r in ctx.derived.residence.values():
        counts[r.area] += 1
    for i, (area, (x0, x1)) in enumerate(bands.items()):
        color = AREA_COLORS[area]
        ax.add_patch(Rectangle((x0 + 0.002, 0), x1 - x0 - 0.004, 1.0, facecolor=color if area is not Area.UNRESOLVED else "#F4F5F7",
                               alpha=0.16 if area is not Area.UNRESOLVED else 1.0, edgecolor="none", zorder=0))
        ax.add_patch(Rectangle((x0 + 0.002, 1.005), x1 - x0 - 0.004, 0.018, facecolor=color, edgecolor=rim_color(color), linewidth=0.5))
        ax.text((x0 + x1) / 2, 1.035, f"{AREA_LABELS[area]}\nn = {counts[area]}", ha="center", va="bottom", fontsize=TEXT_PT - 0.6, color=INK, linespacing=1.15)
    positions = g2_layout(ctx)
    area = {cid: ctx.derived.area(cid) for cid in positions}
    within = between = 0
    for a, b in _edges(ctx):
        (x1, y1), (x2, y2) = positions[a], positions[b]
        if area[a] is area[b]:
            within += 1
            ax.plot([x1, x2], [y1, y2], color=TIE_WITHIN, linewidth=0.9, zorder=2)
        else:
            between += 1
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            control = (mx - 0.18 * (y2 - y1), my + 0.18 * (x2 - x1))  # a gentle arc keeps long ties apart
            curve = MplPath([(x1, y1), control, (x2, y2)], [MplPath.MOVETO, MplPath.CURVE3, MplPath.CURVE3])
            ax.add_patch(PathPatch(curve, fill=False, edgecolor=TIE_BETWEEN, linewidth=1.1, linestyle=(0, (4, 2)), zorder=2))
    draw_nodes(ax, positions, {cid: _area_fill(ctx, cid) for cid in positions}, size=290)
    if any(abs(y - ISOLATED_Y) < 1e-9 for _, y in positions.values()):
        ax.plot([0, 1], [0.15, 0.15], color="#C9CED3", linewidth=0.7, linestyle=(0, (3, 3)), zorder=1)
        ax.text(0.004, 0.158, "ohne bestätigte Verbindung zu anderen Kontakten", fontsize=SMALL_PT, color=MUTED, ha="left", va="bottom", style="italic")
    legend = [
        Line2D([], [], color=TIE_WITHIN, linewidth=1.2, label=f"bestätigte Verbindung im selben Bereich ({within})"),
        Line2D([], [], color=TIE_BETWEEN, linewidth=1.2, linestyle=(0, (4, 2)), label=f"bestätigte Verbindung über Bereiche hinweg ({between})"),
    ]
    ax.legend(handles=legend, loc="upper left", bbox_to_anchor=(0.0, -0.01), ncol=2, frameon=False, fontsize=TEXT_PT - 0.5)
    note = ("Bereiche sind Kategorien des Wohnorts, keine Entfernungen; Breite folgt der Kontaktzahl. Die Lage innerhalb eines Bereichs "
            "ist ein reproduzierbares Layout\nund bedeutet keine persönliche Nähe. Ego ist nicht eingezeichnet. "
            "Unbekannte und verneinte Paare erscheinen nicht als Linie. " + ctx.coverage_line())
    frame(figure, ctx, "G2 · Geografisches Beziehungsnetz", "Kontakte nach Wohnortbereich und bestätigte Verbindungen zwischen ihnen", note)
    return figure


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
        for k in range(24):
            t = 2 * math.pi * k / 24
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
NESTED_STEP = 0.022  # a group inside other groups gets a tighter outline, so every outline stays visible


def group_pads(ctx: Context) -> dict[str, float]:
    """Outline padding per group: tighter for each group that contains all its members (nested groups)."""
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
    they do not belong to are pushed out. Deterministic."""
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
                             spring=0.012, iterations=700, min_distance=0.06)
    pads = group_pads(ctx)
    for _ in range(40):
        moved = False
        for g in ctx.case.groups:
            members = ctx.case.members(g.id)
            if not members:
                continue
            hull = MplPath(_hull([positions[m] for m in members], pads[g.id]))
            centre = np.mean([positions[m] for m in members], axis=0)
            for cid in nodes:
                if cid in members:
                    continue
                p = np.array(positions[cid])
                if hull.contains_point(p, radius=-0.03):
                    direction = p - centre
                    norm = float(np.hypot(*direction)) or 1.0
                    p = p + direction / norm * 0.025
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


def g3(ctx: Context):
    figure = new_figure(14.5, 9.0)
    ax = figure.add_axes((0.01, 0.14, 0.56, 0.74))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    positions = g3_layout(ctx)
    colors = {g.id: GROUP_COLORS[i % len(GROUP_COLORS)] for i, g in enumerate(ctx.case.groups)}
    pads = group_pads(ctx)
    for g in ctx.case.groups:
        members = ctx.case.members(g.id)
        if not members:
            continue
        hull = _hull([positions[m] for m in members], pads[g.id])
        ax.add_patch(Polygon(hull, closed=True, facecolor=colors[g.id], alpha=0.10, edgecolor="none", zorder=0))
        ax.add_patch(Polygon(hull, closed=True, fill=False, edgecolor=colors[g.id], linewidth=1.4, alpha=0.8, zorder=1,
                             linestyle=(0, (5, 2)) if pads[g.id] < HULL_PAD else "solid"))
        nested = pads[g.id] < HULL_PAD  # label of a nested group below its outline, clear of the enclosing ones
        anchor = hull[np.argmin(hull[:, 1])] if nested else hull[np.argmax(hull[:, 1])]
        ax.text(anchor[0], anchor[1] + (-0.006 if nested else 0.006), f"{g.id} ({len(members)})", va="top" if nested else "bottom", color=colors[g.id], fontsize=TEXT_PT - 0.5, fontweight="bold",
                ha="center", zorder=6, bbox={"boxstyle": "round,pad=0.15", "facecolor": "white", "edgecolor": "none", "alpha": 0.85})
    for a, b in _edges(ctx):
        (x1, y1), (x2, y2) = positions[a], positions[b]
        ax.plot([x1, x2], [y1, y2], color=TIE_WITHIN, linewidth=0.8, zorder=2)
    fills = {cid: ("#E6E9ED" if ctx.case.groups_of(cid) else MISSING_FILL) for cid in positions}
    draw_nodes(ax, positions, fills, size=240)
    for cid in positions:  # several memberships: one ring segment per group around the node
        gs = ctx.case.groups_of(cid)
        if len(gs) < 2:
            continue
        x, y = positions[cid]
        for i, g in enumerate(gs):
            ax.add_patch(Wedge((x, y), 0.026, 90 + 360 * i / len(gs), 90 + 360 * (i + 1) / len(gs), width=0.007,
                               facecolor=colors[g], edgecolor="none", zorder=5))

    # ------------------------------------------------------------------ belonging panel (ego and groups) -----
    side = figure.add_axes((0.6, 0.14, 0.39, 0.74))
    side.axis("off")
    side.set_xlim(0, 1)
    side.set_ylim(0, 1)
    side.text(0.0, 1.0, "Zugehörigkeit von Ego zu den Gruppen", fontsize=TEXT_PT + 0.5, fontweight="bold", color=INK, va="top")
    side.text(0.0, 0.955, "Linienstärke = erhobene Zugehörigkeit (1 = sehr stark … 5 = überhaupt nicht).\n"
              "Sie beschreibt Ego und Gruppe, keine Beziehung zwischen Kontakten.\nZahl im Kreis = Mitglieder.",
              fontsize=SMALL_PT, color=MUTED, va="top", linespacing=1.3)
    n = len(ctx.case.groups)
    ego = (0.06, 0.45)
    side.scatter([ego[0]], [ego[1]], s=1100, c=[EGO_FILL], edgecolors="white", zorder=4)
    side.text(*ego, "Ego", color="white", fontsize=TEXT_PT - 1, ha="center", va="center", fontweight="bold", zorder=5)
    width_of = {"1": 7.0, "2": 5.0, "3": 3.2, "4": 1.8, "5": 0.7}
    gx = 0.36
    for i, g in enumerate(ctx.case.groups):
        y = 0.8 - (0.7 * i / (n - 1) if n > 1 else 0.35)
        members = ctx.case.members(g.id)
        value = g.belonging.value
        if value:
            side.plot([ego[0], gx], [ego[1], y], color=colors[g.id], linewidth=width_of[value], solid_capstyle="butt", zorder=2)
            label = f"{value} · {codes.BELONGING[value]}"
        else:
            side.plot([ego[0], gx], [ego[1], y], color="#9AA5B1", linewidth=0.8, linestyle=(0, (1, 2)), zorder=2)
            label = codes.MISSING_LABELS.get(g.belonging.missing, "keine Angabe")
        side.scatter([gx], [y], s=260 + 40 * len(members), c=[colors[g.id]], edgecolors="white", zorder=3)
        side.text(gx, y, str(len(members)), color="white", fontsize=SMALL_PT + 0.4, ha="center", va="center", fontweight="bold", zorder=4)
        side.text(gx + 0.06, y + 0.012, f"{g.id} · {g.label or 'ohne Bezeichnung'}", fontsize=TEXT_PT - 0.8, color=INK, va="bottom")
        side.text(gx + 0.06, y - 0.004, f"Zugehörigkeit {label}\nStatus {g.status.value or '–'} · {len(members)} Mitglieder",
                  fontsize=SMALL_PT - 0.2, color=MUTED, va="top", linespacing=1.25)
    note = ("Gruppenkarte (links): Umrandung = von Ego benannte Gruppe (Zahl = Mitglieder); farbiger Ring = Mitglied mehrerer Gruppen; gestrichelte Umrandung = Gruppe, die ganz in anderen liegt; "
            "gestrichelter Knoten = keiner Gruppe zugeordnet.\n"
            "Linien = bestätigte Verbindungen. Status T: alle verbunden · P: teilweise · N: keine Verbindungen · NS: unbekannt – bei P und NS "
            "gelten nur einzeln bestätigte Paare.\n"
            "Gemeinsame Mitgliedschaft allein ist keine Verbindung; die Lage der Knoten ist ein reproduzierbares Layout. " + ctx.coverage_line())
    frame(figure, ctx, "G3 · Gruppenstruktur und Zugehörigkeit", "Von Ego benannte Gruppen als konkrete Konstellationen und Egos Zugehörigkeit zu ihnen", note)
    return figure
