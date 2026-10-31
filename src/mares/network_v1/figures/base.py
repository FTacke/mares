"""Building blocks of the eight network_v1 figures: case context, palettes, frame, layouts, point and count matrices.

Rendering primitives (bundled font, deterministic files, contrast helpers) come from the v0 style module; they are
version-neutral. Palettes: one variable keeps one colour in every figure -- residence area (blues = Marburg and
Mittelhessen, pale blue = rest of Germany, oranges = abroad) and relation type (own hues). Every figure carries a small
case line (case code, contacts, groups, data status) and, for a test case, a visible test marker.
"""

from __future__ import annotations

import math
import zlib
from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch, Rectangle

from mares.network_v0.figures.style import INK, MUTED, FAINT, label_color, new_figure, rim_color  # noqa: F401  (re-exported)

from .. import codes
from ..case import Case
from ..derive import Derived
from ..places import AREA_LABELS, AREA_ORDER, Area

TITLE_PT, TEXT_PT, ID_PT, SMALL_PT = 15.0, 9.5, 7.6, 7.6
TEST_RED = "#B03A2E"

AREA_COLORS = {
    Area.MARBURG: "#0072B2",
    Area.MITTELHESSEN: "#56B4E9",
    Area.GERMANY_OTHER: "#C3DAEC",
    Area.EUROPE_OTHER: "#F3D49A",
    Area.OUTSIDE_EUROPE: "#E69F00",
    Area.UNRESOLVED: "#FFFFFF",
}
RELATION_COLORS = {
    "1": "#D55E00",  # Familie
    "2": "#CC79A7",  # Partner:in
    "3": "#009E73",  # Freund:in
    "4": "#F0E442",  # Bekannte:r
    "5": "#6C7A89",  # professionell/institutionell
    "6": "#A6761D",  # sonstige
}
MISSING_FILL = "#FFFFFF"  # no statement: white with a dotted rim, never the colour of a category
TIE_WITHIN = "#7D8892"
TIE_BETWEEN = "#1F2933"
GROUP_COLORS = ("#117A8B", "#D55E00", "#7A5195", "#8C6D31", "#2E7D32", "#C2185B", "#455A64", "#EF6C00")


@dataclass(frozen=True)
class Context:
    """What a figure needs about the case."""

    case: Case
    derived: Derived

    @property
    def code(self) -> str:
        return self.case.code

    @property
    def is_test(self) -> bool:
        return self.case.metadata.get("case_type") == "test"

    def areas_present(self) -> list[Area]:
        """The five display areas, plus 'nicht zuordenbar' only when a contact needs it."""
        areas = list(AREA_ORDER)
        if any(r.area is Area.UNRESOLVED for r in self.derived.residence.values()):
            areas.append(Area.UNRESOLVED)
        return areas

    def status_text(self) -> str:
        m = self.case.metadata
        provenance = {
            "fully_synthetic": "vollständig synthetisch",
            "v0_derived_fictionalized": "aus network_v0 abgeleitet, fiktionalisiert",
            "survey": "Erhebung",
        }.get(m.get("provenance"), str(m.get("provenance")))
        if self.is_test:
            return f"Testfall · {provenance} · nicht empirisch auswertbar"
        return f"{ {'pilot': 'Pilotfall', 'regular': 'Erhebung'}.get(m.get('case_type'), '') } · Datenqualität {m.get('data_quality', 'nicht angegeben')}".strip()

    def case_line(self) -> str:
        n_groups = len(self.case.groups)
        groups = f" · {n_groups} Gruppen" if n_groups else ""
        return f"MARES · network_v1 · Fall {self.code} · {len(self.case.contacts)} Kontakte{groups} · {self.status_text()}"

    def coverage_line(self) -> str:
        cov = self.derived.coverage
        if not cov.pairs:
            return ""
        share = 100 * (cov.confirmed + cov.denied) / cov.pairs
        return (f"Kontaktpaare: {cov.pairs} · bestätigt {cov.confirmed} · verneint {cov.denied} · unbekannt {cov.unknown} "
                f"(geklärt: {share:.0f} %)".replace(".", ","))


def frame(figure: Figure, ctx: Context, title: str, subtitle: str, note: str = "") -> None:
    """Title block, the small case line and -- for a test case -- the test marker."""
    h = figure.get_figheight()
    figure.text(0.03, 1 - 0.22 / h, title, fontsize=TITLE_PT, fontweight="bold", color=INK, ha="left", va="top")
    if subtitle:
        figure.text(0.03, 1 - 0.56 / h, subtitle, fontsize=TEXT_PT, color=MUTED, ha="left", va="top")
    if note:
        figure.text(0.03, 0.22 / h + 0.03, note, fontsize=SMALL_PT, color=INK, ha="left", va="bottom", linespacing=1.35)
    figure.text(0.03, 0.12 / h, ctx.case_line(), fontsize=SMALL_PT, color=MUTED, ha="left", va="bottom")
    if ctx.is_test:
        figure.text(0.97, 1 - 0.22 / h, "TESTFALL · FIKTIVE DATEN", fontsize=TEXT_PT, fontweight="bold", color="#FFFFFF",
                    ha="right", va="top", bbox={"boxstyle": "round,pad=0.35", "facecolor": TEST_RED, "edgecolor": "none"})


def file_name(case_code: str, figure_code: str, name: str, ext: str) -> str:
    """``<case>_<figure>_<name>.<ext>`` -- ASCII letters, digits and underscores only."""
    stem = f"{case_code}_{figure_code}_{name}"
    if not all(ch.isascii() and (ch.isalnum() or ch == "_") for ch in stem):
        raise ValueError(f"file name {stem!r} must contain ASCII letters, digits and underscores only")
    return f"{stem}.{ext}"


# ----------------------------------------------------------------------------------------- nodes and legends ---
def node_style(fill: str | None) -> dict:
    if fill is None or fill == MISSING_FILL:
        return {"facecolor": MISSING_FILL, "edgecolor": "#5B6770", "linestyle": (0, (1.2, 1.2)), "linewidth": 0.9}
    return {"facecolor": fill, "edgecolor": rim_color(fill), "linewidth": 0.8}


def legend_box(ax, entries: Sequence[tuple[str, str | None]], title: str, *, x: float, y: float, kind: str = "dot", columns: int = 1,
               col_width: float = 0.5, line_gap: float = 0.055) -> float:
    """A compact legend in axes-fraction coordinates; returns the y below it."""
    ax.text(x, y, title, transform=ax.transAxes, fontsize=TEXT_PT, fontweight="bold", color=INK, ha="left", va="top")
    y -= line_gap * 1.15
    rows = math.ceil(len(entries) / columns)
    for i, (label, color) in enumerate(entries):
        cx = x + (i // rows) * col_width
        cy = y - (i % rows) * line_gap
        style = node_style(color)
        ax.scatter([cx + 0.012], [cy - 0.012], s=70, transform=ax.transAxes, clip_on=False, zorder=5, **_scatter(style))
        ax.text(cx + 0.035, cy - 0.012, label, transform=ax.transAxes, fontsize=TEXT_PT - 0.5, color=INK, ha="left", va="center")
    return y - rows * line_gap


def _scatter(style: dict) -> dict:
    return {"c": [style["facecolor"]], "edgecolors": [style["edgecolor"]], "linewidths": style["linewidth"],
            "linestyle": style.get("linestyle", "solid")}


def draw_nodes(ax, positions: dict[str, tuple[float, float]], fills: dict[str, str | None], *, size: float = 150, labels: bool = True,
               label_offset: tuple[float, float] = (0, 0), zorder: int = 4) -> None:
    for cid, (x, y) in positions.items():
        style = node_style(fills.get(cid))
        ax.scatter([x], [y], s=size, zorder=zorder, **_scatter(style))
        if labels:
            fill = style["facecolor"]
            ax.text(x + label_offset[0], y + label_offset[1], cid, fontsize=ID_PT - 1.4, color=label_color(fill),
                    ha="center", va="center", zorder=zorder + 1, fontweight="bold")


# ----------------------------------------------------------------------------------------------- layouts ---
def _seed_angle(key: str) -> float:
    return (zlib.crc32(key.encode()) % 3600) / 3600 * 2 * math.pi


def force_layout(
    nodes: Sequence[str],
    edges: Sequence[tuple[str, str]],
    *,
    start: dict[str, tuple[float, float]],
    project: Callable[[str, np.ndarray], np.ndarray],
    pulls: Sequence[tuple[str, tuple[float, float], float]] | Callable[[dict[str, np.ndarray]], Sequence[tuple[str, np.ndarray, float]]] = (),
    repulsion: float = 0.004,
    spring: float = 0.08,
    iterations: int = 500,
    min_distance: float = 0.06,
) -> dict[str, tuple[float, float]]:
    """A small deterministic force layout with a constraint: after every step each node is projected back into its
    allowed region (a ring, a band ...). Edges pull, all nodes repel, ``pulls`` add attractions to points (fixed or
    recomputed each step). Same input, same output."""
    if not nodes:
        return {}
    index = {n: i for i, n in enumerate(nodes)}
    pos = np.array([start[n] for n in nodes], dtype=float)
    pos = np.array([project(n, pos[index[n]]) for n in nodes])
    edge_idx = [(index[a], index[b]) for a, b in edges if a in index and b in index]
    for step in range(iterations):
        temperature = 0.06 * (1 - step / iterations) + 0.004
        delta = pos[:, None, :] - pos[None, :, :]
        dist = np.sqrt((delta ** 2).sum(-1)) + 1e-9
        np.fill_diagonal(dist, np.inf)
        force = (delta / dist[..., None] * (repulsion / dist ** 2)[..., None]).sum(1)
        overlap = np.where(dist < min_distance, min_distance - dist, 0.0)
        if overlap.any():
            force += (delta / dist[..., None] * (overlap * 2.0)[..., None]).sum(1)
        for i, j in edge_idx:
            d = pos[j] - pos[i]
            force[i] += spring * d
            force[j] -= spring * d
        current = {n: pos[index[n]] for n in nodes}
        for n, target, weight in (pulls(current) if callable(pulls) else pulls):
            if n in index:
                force[index[n]] += weight * (np.asarray(target) - pos[index[n]])
        length = np.sqrt((force ** 2).sum(-1))[:, None] + 1e-9
        pos = pos + force / length * np.minimum(length, temperature)
        pos = np.array([project(n, pos[index[n]]) for n in nodes])
    return {n: (float(pos[index[n]][0]), float(pos[index[n]][1])) for n in nodes}


def initial_circle(nodes: Sequence[str], radius: float = 1.0, center: tuple[float, float] = (0.0, 0.0)) -> dict[str, tuple[float, float]]:
    return {n: (center[0] + radius * math.cos(_seed_angle(n)), center[1] + radius * math.sin(_seed_angle(n))) for n in nodes}


def crossings(positions: dict[str, tuple[float, float]], edges: Sequence[tuple[str, str]]) -> int:
    """Number of crossing edge pairs (a technical layout measure, never a finding)."""
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])

    count = 0
    segs = [(positions[a], positions[b], {a, b}) for a, b in edges]
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            (p1, p2, s1), (p3, p4, s2) = segs[i], segs[j]
            if s1 & s2:
                continue
            if (ccw(p1, p3, p4) > 0) != (ccw(p2, p3, p4) > 0) and (ccw(p1, p2, p3) > 0) != (ccw(p1, p2, p4) > 0):
                count += 1
    return count


# ------------------------------------------------------------------------------------------ point matrix ---
@dataclass(frozen=True)
class Item:
    contact_id: str
    column: object
    row: object
    color: str | None


def point_matrix(
    ax,
    columns: Sequence[tuple[object, str]],
    rows: Sequence[tuple[object, str]],
    items: Sequence[Item],
    *,
    column_gaps: Sequence[int] = (),
    row_gaps: Sequence[int] = (),
    per_line: int = 4,
    column_counts: dict[object, int] | None = None,
    column_header_colors: dict[object, str] | None = None,
) -> None:
    """Categories on both axes; every contact is a labelled point in its cell (several per cell side by side).
    ``*_gaps``: indices before which a visual gap separates a block (e.g. 'keine Angabe')."""
    col_x, x = {}, 0.0
    for i, (key, _) in enumerate(columns):
        if i in column_gaps:
            x += 0.35
        col_x[key] = x
        x += 1.0
    row_y, y = {}, 0.0
    for i, (key, _) in enumerate(rows):
        if i in row_gaps:
            y += 0.45
        row_y[key] = y
        y += 1.0
    width, height = x, y
    ax.set_xlim(-0.05, width + 0.05)
    ax.set_ylim(height + 0.05, -0.95)
    ax.axis("off")
    for key, label in columns:
        x0 = col_x[key]
        ax.add_patch(Rectangle((x0 + 0.02, 0), 0.96, height, facecolor="#F6F7F9", edgecolor="none", zorder=0))
        header = label + (f"\nn = {column_counts.get(key, 0)}" if column_counts is not None else "")
        color = (column_header_colors or {}).get(key)
        if color:
            ax.add_patch(Rectangle((x0 + 0.06, -0.18), 0.88, 0.08, facecolor=color, edgecolor=rim_color(color), linewidth=0.6, zorder=1))
        ax.text(x0 + 0.5, -0.24, header, ha="center", va="bottom", fontsize=TEXT_PT - 0.8, color=INK, linespacing=1.2)
    for key, label in rows:
        y0 = row_y[key]
        ax.plot([-0.05, width + 0.05], [y0, y0], color=FAINT, linewidth=0.5, zorder=0)
        ax.text(-0.09, y0 + 0.5, label, ha="right", va="center", fontsize=TEXT_PT - 0.8, color=INK)
    cells: dict[tuple[object, object], list[Item]] = {}
    for item in items:
        cells.setdefault((item.column, item.row), []).append(item)
    for (ck, rk), group in cells.items():
        group = sorted(group, key=lambda it: it.contact_id)
        lines = math.ceil(len(group) / per_line)
        for k, item in enumerate(group):
            line, slot = divmod(k, per_line)
            cx = col_x[ck] + 0.1 + slot * (0.88 / per_line)
            cy = row_y[rk] + 0.5 + (line - (lines - 1) / 2) * min(0.28, 0.9 / max(lines, 1))
            style = node_style(item.color)
            ax.scatter([cx + 0.03], [cy], s=34, zorder=3, **_scatter(style))
            ax.text(cx + 0.07, cy, item.contact_id, fontsize=ID_PT - 0.6, color=INK, ha="left", va="center", zorder=4)


def count_matrix(
    ax,
    columns: Sequence[tuple[object, str]],
    rows: Sequence[tuple[object, str]],
    counts: dict[tuple[object, object], int],
    bases: dict[object, int],
    *,
    missing: dict[object, int],
    column_gaps: Sequence[int] = (),
    column_header_colors: dict[object, str] | None = None,
    shade: str = "#2B6A99",
) -> None:
    """Rows x columns of 'k of n' with the share as shading; n = contacts of the column with a recorded answer.
    A last row shows contacts of the column without an answer (never counted as 'no')."""
    col_x, x = {}, 0.0
    for i, (key, _) in enumerate(columns):
        if i in column_gaps:
            x += 0.3
        col_x[key] = x
        x += 1.0
    n_rows = len(rows) + 1
    ax.set_xlim(-0.05, x + 0.05)
    ax.set_ylim(n_rows + 0.55, -1.4)
    ax.axis("off")
    rgb = np.array([int(shade[i : i + 2], 16) / 255 for i in (1, 3, 5)])
    for key, label in columns:
        x0 = col_x[key]
        color = (column_header_colors or {}).get(key)
        if color:
            ax.add_patch(Rectangle((x0 + 0.06, -0.2), 0.88, 0.09, facecolor=color, edgecolor=rim_color(color), linewidth=0.6))
        ax.text(x0 + 0.5, -0.27, f"{label}\nn = {bases.get(key, 0)}", ha="center", va="bottom", fontsize=TEXT_PT - 0.8, color=INK, linespacing=1.2)
    for r, (rkey, rlabel) in enumerate(rows):
        ax.text(-0.09, r + 0.5, rlabel, ha="right", va="center", fontsize=TEXT_PT - 0.8, color=INK)
        for ckey, _ in columns:
            n = bases.get(ckey, 0)
            k = counts.get((ckey, rkey), 0)
            share = k / n if n else 0.0
            fill = tuple(1 - share * (1 - rgb)) if n else (1, 1, 1)
            ax.add_patch(Rectangle((col_x[ckey] + 0.03, r + 0.04), 0.94, 0.92, facecolor=fill, edgecolor="#E3E6EA", linewidth=0.6))
            if n:
                text_color = "#FFFFFF" if share > 0.55 else INK
                ax.text(col_x[ckey] + 0.5, r + 0.42, f"{k}", ha="center", va="center", fontsize=TEXT_PT + 1, fontweight="bold", color=text_color)
                ax.text(col_x[ckey] + 0.5, r + 0.74, f"von {n} · {100 * share:.0f} %", ha="center", va="center", fontsize=SMALL_PT - 0.4, color=text_color)
            else:
                ax.text(col_x[ckey] + 0.5, r + 0.5, "–", ha="center", va="center", fontsize=TEXT_PT, color=MUTED)
    r = len(rows) + 0.25
    ax.text(-0.09, r + 0.4, "ohne Angabe", ha="right", va="center", fontsize=TEXT_PT - 0.8, color=MUTED, style="italic")
    for ckey, _ in columns:
        ax.add_patch(FancyBboxPatch((col_x[ckey] + 0.08, r + 0.12), 0.84, 0.56, boxstyle="round,pad=0.0,rounding_size=0.08",
                                    facecolor="#FFFFFF", edgecolor="#B5BEC7", linestyle=(0, (2, 2)), linewidth=0.7))
        ax.text(col_x[ckey] + 0.5, r + 0.4, str(missing.get(ckey, 0)), ha="center", va="center", fontsize=TEXT_PT - 0.5, color=MUTED)


def area_columns(ctx: Context) -> list[tuple[Area, str]]:
    return [(a, AREA_LABELS[a].replace("übriges ", "übriges\n").replace("außerhalb ", "außerhalb\n").replace(" (Stadt)", "\n(Stadt)").replace("nicht ", "nicht\n")) for a in ctx.areas_present()]


def area_bracket(ax, columns: Sequence[tuple[Area, str]], *, y: float, gap_after: Sequence[int] = ()) -> None:
    """A bracket over Marburg and übriges Mittelhessen: together they are the primary category 1."""
    keys = [k for k, _ in columns]
    if Area.MARBURG in keys and Area.MITTELHESSEN in keys:
        x0, x1 = keys.index(Area.MARBURG) + 0.08, keys.index(Area.MITTELHESSEN) + 0.92
        ax.plot([x0, x0, x1, x1], [y + 0.06, y, y, y + 0.06], color=MUTED, linewidth=0.8, clip_on=False)
        ax.text((x0 + x1) / 2, y - 0.04, "Marburg und Mittelhessen", ha="center", va="bottom", fontsize=SMALL_PT, color=MUTED, clip_on=False)


def closeness_rows(include_missing: bool) -> list[tuple[object, str]]:
    rows: list[tuple[object, str]] = [(v, f"{codes.closeness_label(v)}" + (f"  {codes.CLOSENESS[v]}" if v == int(v) else "")) for v in codes.CLOSENESS_LEVELS]
    if include_missing:
        rows.append(("missing", "keine Angabe"))
    return rows
