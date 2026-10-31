"""Design system of the eight network_v1 figures -- one place for everything they share.

* **Palettes.** Colour of a contact = its relation type, in every figure (G1, G2, G3, P1, P2, P5): six fixed colours from
  the Okabe-Ito family, neutral grey for 'Sonstige Beziehung'. Geographic areas and groups are pale backgrounds only, so
  they never compete with the nodes. P3 and P4 share one quiet blue scale for shares.
* **Typography and sizes** in points and inches, so every figure uses the same title, labels, node and dot sizes.
* **The page** (:func:`page`): title and subtitle, case badge top right, the main area (most of the page), one of the
  two legend layouts (``side`` or ``bottom``), at most two short notes and a one-line footer.
* **Two matrix blocks**: :func:`point_matrix` (P1, P2, P5) and :func:`heat_matrix` (P3, P4).

Rendering primitives (bundled font, deterministic files, contrast helpers) come from the v0 style module; they are
version-neutral. Main areas and legends are drawn in inch coordinates, so sizes do not depend on the page size.
"""

from __future__ import annotations

import math
import zlib
from dataclasses import dataclass, field
from typing import Callable, Sequence

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle, Wedge
from matplotlib.textpath import TextPath

from mares.network_v0.figures.style import FONT, INK, MUTED, FAINT, label_color, new_figure  # noqa: F401  (re-exported)

from .. import codes
from ..case import Case
from ..derive import Derived
from ..places import AREA_LABELS, AREA_ORDER, Area

# ------------------------------------------------------------------------------------------------ typography ---
TITLE_PT = 16.0
SUBTITLE_PT = 10.5
LABEL_PT = 9.5  # category labels, column headers
ID_PT = 7.6  # contact IDs next to matrix dots
NODE_ID_PT = 7.0  # contact IDs inside network nodes
LEGEND_PT = 8.8
NOTE_PT = 8.0
FOOT_PT = 7.5
BADGE_PT = 9.0

# --------------------------------------------------------------------------------------------- page (inches) ---
MARGIN_X = 0.4
HEADER_H = 0.95
FOOTER_H = 0.32
NOTE_LINE_H = 0.19
GAP = 0.14
SIDE_W = 2.6
LEGEND_ROW_H = 0.26

# ---------------------------------------------------------------------------------------------------- colours ---
RELATION_COLORS = {
    "1": "#D55E00",  # Familie
    "2": "#CC79A7",  # Partner:in
    "3": "#009E73",  # Freund:in
    "4": "#56B4E9",  # Bekannte:r
    "5": "#0072B2",  # Professionell / institutionell
    "6": "#6B7280",  # Sonstige Beziehung
}
NODE_RIM = "#4B5563"  # a fine neutral rim keeps light nodes visible on pale backgrounds
MISSING_FILL = "#FFFFFF"  # no relation type: white with a dotted rim, never the colour of a category
TIE = "#8A939C"  # confirmed tie inside one area (or in G1/G3)
TIE_BETWEEN = "#AEB6BE"  # confirmed tie between areas: thinner, lighter, dashed
TEST_RED = "#B03A2E"
AREA_TINTS = {
    Area.MARBURG: "#E9F1F8",
    Area.MITTELHESSEN: "#F0F5FA",
    Area.GERMANY_OTHER: "#F3F5F7",
    Area.EUROPE_OTHER: "#F8F5EF",
    Area.OUTSIDE_EUROPE: "#FAF3EB",
}
GROUP_COLORS = ("#3E6A9A", "#9A6B2F", "#6B4E8A", "#2F7F72", "#A04A5C", "#5E6B2E", "#4A5560", "#B0602A")
HEAT = "#2B6A99"  # one blue scale for shares (P3, P4)
HEAT_NEUTRAL = "#F1F3F5"  # cells of a column with n = 1: no shading
CELL_RIM = "#DDE2E7"

NODE_PT = 20.0  # diameter of a network node
DOT_PT = 7.0  # diameter of a matrix dot


def node_size(diameter_pt: float = NODE_PT) -> float:
    return diameter_pt ** 2  # scatter sizes are areas in points^2


def relation_fill(case: Case, contact_id: str) -> str | None:
    cell = case.contact(contact_id).relation_type
    return RELATION_COLORS.get(cell.value) if cell.recorded else None


def relation_entries(case: Case) -> list[tuple]:
    """Legend entries of the relation types -- same order, labels and colours in every figure."""
    entries: list[tuple] = [("dot", label, RELATION_COLORS[code]) for code, label in codes.RELATION_TYPE.items()]
    if any(relation_fill(case, cid) is None for cid in case.contact_ids):
        entries.append(("dot", "keine Angabe", None))
    return entries


# ------------------------------------------------------------------------------------------------ case context ---
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

    def resolved(self) -> list[str]:
        return [cid for cid in self.case.contact_ids if self.derived.area(cid) is not Area.UNRESOLVED]

    def unresolved(self) -> list[str]:
        return [cid for cid in self.case.contact_ids if self.derived.area(cid) is Area.UNRESOLVED]

    def unresolved_note(self, where: str = "nicht dargestellt") -> str:
        ids = self.unresolved()
        return f"Wohnort nicht zuordenbar ({where}): {', '.join(ids)}." if ids else ""

    def coverage_line(self) -> str:
        cov = self.derived.coverage
        if not cov.pairs:
            return ""
        return f"Kontaktpaare: {cov.pairs} · bestätigt {cov.confirmed} · verneint {cov.denied} · unbekannt {cov.unknown}."


def case_badge(ctx: Context) -> str:
    """Top right: a test case with its number and status, a real case with its pseudonymous code (never a name)."""
    m = ctx.case.metadata
    number = ctx.code[:3]
    if ctx.is_test:
        kind = {"fully_synthetic": "SYNTHETISCH", "v0_derived_fictionalized": "FIKTIONALISIERT"}.get(m.get("provenance"), "FIKTIV")
        return f"TESTFALL {number}* · {kind}"
    return f"FALL · {m.get('display_code') or f'MARES-{number}'}"


def footer_line(ctx: Context) -> str:
    n_groups = len(ctx.case.groups)
    line = f"MARES · network_v1 · {len(ctx.case.contacts)} Kontakte · {n_groups} Gruppen"
    quality = ctx.case.metadata.get("data_quality")
    if not ctx.is_test and quality:
        line += f" · Datenqualität: {quality}"
    return line


def file_name(case_code: str, figure_code: str, name: str, ext: str) -> str:
    """``<case>_<figure>_<name>.<ext>`` -- ASCII letters, digits and underscores only."""
    stem = f"{case_code}_{figure_code}_{name}"
    if not all(ch.isascii() and (ch.isalnum() or ch == "_") for ch in stem):
        raise ValueError(f"file name {stem!r} must contain ASCII letters, digits and underscores only")
    return f"{stem}.{ext}"


# -------------------------------------------------------------------------------------------- text measuring ---
def text_width(text: str, size: float, *, bold: bool = False) -> float:
    """Width in inches of the widest line of ``text`` in the bundled font."""
    prop = FontProperties(family=FONT, weight="bold" if bold else "normal")
    widest = 0.0
    for line in text.split("\n"):
        if line.strip():
            widest = max(widest, TextPath((0, 0), line, size=size, prop=prop).get_extents().width / 72)
    return widest


# ---------------------------------------------------------------------------------------------------- legends ---
# A legend is a list of sections ``(title, entries)``. Entries:
#   ("dot", label, fill)            node or dot of a relation type (fill None = no answer)
#   ("line", label, style)          a tie; style = Line2D keyword arguments
#   ("area", label, style)          a background area or outline; style = patch keyword arguments
#   ("ring", label, colors)         a node with ring segments (several group memberships)
#   ("ramp", label, None)           the blue share scale of P3/P4
#   ("scale", label, value)         the five-dot scale of an ordinal answer (value '1'..'5', or None: no answer)
#   ("text", label, None)           a short explanation
SWATCH_W = 0.26
ENTRY_GAP = 0.2
SECTION_GAP = 0.42


def _swatch_width(kind: str) -> float:
    return {"ramp": 5 * 0.2 + 0.08, "text": 0.0, "scale": scale_width() + 0.04}.get(kind, SWATCH_W)


def _entry_width(entry: tuple) -> float:
    kind, label, _ = entry
    swatch = _swatch_width(kind)
    return swatch + (0.06 if swatch else 0) + text_width(label, LEGEND_PT)


def _bottom_rows(sections: Sequence[tuple[str | None, Sequence[tuple]]], width: float) -> list[list[tuple[float, str, tuple | None]]]:
    """Flow the sections into rows: (x, 'title'|'entry', entry). A section that does not fit into the rest of a row
    starts a new row; a section wider than a row continues below its own entries."""
    rows: list[list] = [[]]
    x = 0.0
    for title, entries in sections:
        if not entries:
            continue
        title_w = text_width(title, LEGEND_PT, bold=True) + 0.12 if title else 0.0
        section_w = title_w + sum(_entry_width(e) + ENTRY_GAP for e in entries) - ENTRY_GAP
        if x > 0 and x + section_w > width:
            rows.append([])
            x = 0.0
        indent = x + title_w
        if title:
            rows[-1].append((x, "title", (None, title, None)))
            x += title_w
        for entry in entries:
            w = _entry_width(entry)
            if x + w > width and x > indent:
                rows.append([])
                x = indent
            rows[-1].append((x, "entry", entry))
            x += w + ENTRY_GAP
        x += SECTION_GAP - ENTRY_GAP
    return rows


def bottom_legend_height(sections, width: float) -> float:
    return len(_bottom_rows(sections, width)) * LEGEND_ROW_H


def _swatch(ax: Axes, kind: str, x: float, y: float, payload) -> None:
    cx = x + SWATCH_W / 2
    if kind == "dot":
        style = node_style(payload)
        ax.scatter([cx], [y], s=node_size(9.5), zorder=3, clip_on=False, **scatter_kwargs(style))
    elif kind == "line":
        ax.add_line(Line2D([x, x + SWATCH_W], [y, y], clip_on=False, **payload))
    elif kind == "area":
        ax.add_patch(FancyBboxPatch((x + 0.02, y - 0.065), SWATCH_W - 0.04, 0.13, boxstyle="round,pad=0,rounding_size=0.03",
                                    clip_on=False, **payload))
    elif kind == "ring":
        ax.scatter([cx], [y], s=node_size(8.0), zorder=3, clip_on=False, c=["#FFFFFF"], edgecolors=[NODE_RIM], linewidths=0.6)
        n = len(payload)
        for i, color in enumerate(payload):
            ax.add_patch(Wedge((cx, y), 0.085, 90 + 360 * i / n, 90 + 360 * (i + 1) / n, width=0.025, facecolor=color,
                               edgecolor="none", clip_on=False, zorder=4))
    elif kind == "scale":
        ordinal_dots(ax, x + 0.02, y, payload, clip=False)
    elif kind == "ramp":
        for i, share in enumerate((0.0, 0.25, 0.5, 0.75, 1.0)):
            ax.add_patch(Rectangle((x + i * 0.2, y - 0.075), 0.18, 0.15, facecolor=heat_fill(share), edgecolor=CELL_RIM,
                                   linewidth=0.5, clip_on=False))


def draw_legend(ax: Axes, sections, mode: str) -> None:
    """Draw ``sections`` into ``ax`` (inch coordinates, origin bottom left) as a ``side`` or ``bottom`` legend."""
    width, height = ax.get_xlim()[1], ax.get_ylim()[1]
    if mode == "bottom":
        for r, row in enumerate(_bottom_rows(sections, width)):
            y = height - (r + 0.5) * LEGEND_ROW_H
            for x, what, entry in row:
                kind, label, payload = entry
                if what == "title":
                    ax.text(x, y, label, fontsize=LEGEND_PT, fontweight="bold", color=INK, va="center", ha="left")
                    continue
                swatch = _swatch_width(kind)
                _swatch(ax, kind, x, y, payload)
                ax.text(x + swatch + (0.06 if swatch else 0), y, label, fontsize=LEGEND_PT, color=MUTED if kind == "text" else INK,
                        va="center", ha="left")
        return
    if mode != "side":
        raise ValueError(f"legend mode must be 'side' or 'bottom', not {mode!r}")
    y = height
    for title, entries in sections:
        if not entries:
            continue
        if title:
            ax.text(0, y, title, fontsize=LEGEND_PT, fontweight="bold", color=INK, va="top", ha="left")
            y -= 0.24
        for kind, label, payload in entries:
            lines = label.count("\n") + 1
            block = LEGEND_ROW_H + (lines - 1) * 0.16
            centre = y - block / 2
            swatch = _swatch_width(kind)
            _swatch(ax, kind, 0.0, centre, payload)
            ax.text(swatch + (0.06 if swatch else 0), centre, label, fontsize=LEGEND_PT, color=MUTED if kind == "text" else INK,
                    va="center", ha="left", linespacing=1.25)
            y -= block
        y -= 0.2


# ------------------------------------------------------------------------------------------------------- page ---
@dataclass
class Page:
    figure: Figure
    main: Axes  # inch coordinates: x 0 .. main_w, y 0 .. main_h (origin bottom left unless a block flips it)
    main_w: float
    main_h: float
    legend: Axes | None = None
    notes: list[str] = field(default_factory=list)


def page(ctx: Context, title: str, subtitle: str, *, main_w: float, main_h: float, legend: str, sections,
         notes: Sequence[str] = ()) -> Page:
    """The common page of every figure. ``legend`` is ``side`` (right of the main area) or ``bottom`` (below it)."""
    notes = [n for n in notes if n][:2]
    notes_h = len(notes) * NOTE_LINE_H + (0.04 if notes else 0)
    if legend == "side":
        width = MARGIN_X * 2 + main_w + GAP + SIDE_W
        legend_h = 0.0
    elif legend == "bottom":
        width = MARGIN_X * 2 + main_w
        legend_h = bottom_legend_height(sections, main_w)
    else:
        raise ValueError(f"legend must be 'side' or 'bottom', not {legend!r}")
    bottom_block = FOOTER_H + notes_h + (legend_h + GAP if legend_h else 0)
    height = HEADER_H + main_h + GAP + bottom_block
    figure = new_figure(width, height)

    def axes(x: float, y: float, w: float, h: float) -> Axes:
        ax = figure.add_axes((x / width, y / height, w / width, h / height))
        ax.set_xlim(0, w)
        ax.set_ylim(0, h)
        ax.axis("off")
        return ax

    main = axes(MARGIN_X, bottom_block + GAP, main_w, main_h)
    legend_ax = None
    if legend == "side":
        legend_ax = axes(MARGIN_X + main_w + GAP, bottom_block + GAP, SIDE_W, main_h)
        draw_legend(legend_ax, sections, "side")
    elif legend_h:
        legend_ax = axes(MARGIN_X, FOOTER_H + notes_h, main_w, legend_h)
        draw_legend(legend_ax, sections, "bottom")

    figure.text(MARGIN_X / width, 1 - 0.2 / height, title, fontsize=TITLE_PT, fontweight="bold", color=INK, ha="left", va="top")
    figure.text(MARGIN_X / width, 1 - 0.58 / height, subtitle, fontsize=SUBTITLE_PT, color=MUTED, ha="left", va="top")
    badge = case_badge(ctx)
    style = ({"facecolor": TEST_RED, "edgecolor": "none"} if ctx.is_test else {"facecolor": "#FFFFFF", "edgecolor": INK})
    figure.text(1 - MARGIN_X / width, 1 - 0.22 / height, badge, fontsize=BADGE_PT, fontweight="bold",
                color="#FFFFFF" if ctx.is_test else INK, ha="right", va="top", bbox={"boxstyle": "round,pad=0.35", **style})
    for i, note in enumerate(reversed(notes)):
        figure.text(MARGIN_X / width, (FOOTER_H + 0.02 + i * NOTE_LINE_H) / height, note, fontsize=NOTE_PT, color=INK,
                    ha="left", va="bottom")
    figure.text(MARGIN_X / width, 0.1 / height, footer_line(ctx), fontsize=FOOT_PT, color=MUTED, ha="left", va="bottom")
    return Page(figure, main, main_w, main_h, legend_ax, notes)


# ------------------------------------------------------------------------------------------------------ nodes ---
def node_style(fill: str | None) -> dict:
    if fill is None or fill == MISSING_FILL:
        return {"facecolor": MISSING_FILL, "edgecolor": "#6B7280", "linestyle": (0, (1.2, 1.2)), "linewidth": 0.9}
    return {"facecolor": fill, "edgecolor": NODE_RIM, "linewidth": 0.6}


def scatter_kwargs(style: dict) -> dict:
    return {"c": [style["facecolor"]], "edgecolors": [style["edgecolor"]], "linewidths": style["linewidth"],
            "linestyle": style.get("linestyle", "solid")}


def draw_nodes(ax: Axes, positions: dict[str, tuple[float, float]], fills: dict[str, str | None], *, zorder: int = 4) -> None:
    """Network nodes: relation-type fill, fine neutral rim, contact ID inside."""
    for cid, (x, y) in positions.items():
        style = node_style(fills.get(cid))
        ax.scatter([x], [y], s=node_size(), zorder=zorder, **scatter_kwargs(style))
        ax.text(x, y, cid, fontsize=NODE_ID_PT, color=label_color(style["facecolor"]), ha="center", va="center",
                zorder=zorder + 1, fontweight="bold")


SCALE_STEP = 0.13  # inches between the dots of an ordinal scale
SCALE_DOT = 0.085  # dot diameter in inches
SCALE_ON = "#2E3640"  # the recorded answer: one neutral dark dot
SCALE_OFF = "#A7B0B9"  # the other answers: outlined only


def scale_width(n: int = 5) -> float:
    return (n - 1) * SCALE_STEP + SCALE_DOT


def ordinal_dots(ax: Axes, x: float, y: float, value: str | None, n: int = 5, *, zorder: int = 7, clip: bool = True) -> float:
    """A row of ``n`` dots for one ordinal answer (1 left ... n right), starting at ``x`` (inches), centred on ``y``.
    Exactly the recorded answer is filled; without an answer none is. No fill level, no colour intensity -- a single
    self-assessment, not a measure. Returns the width."""
    for i in range(n):
        on = value == str(i + 1)
        dot = Circle((x + SCALE_DOT / 2 + i * SCALE_STEP, y), SCALE_DOT / 2 * (1.0 if on else 0.82),
                     facecolor=SCALE_ON if on else "#FFFFFF", edgecolor=SCALE_ON if on else SCALE_OFF, linewidth=0.8, zorder=zorder,
                     clip_on=clip)
        dot.set_gid("scale-on" if on else "scale-off")
        ax.add_patch(dot)
    return scale_width(n)


def ring_segments(ax: Axes, centre: tuple[float, float], colors: Sequence[str], radius: float, *, zorder: int = 5) -> None:
    """Ring segments around a node, one per group (several memberships)."""
    n = len(colors)
    for i, color in enumerate(colors):
        ax.add_patch(Wedge(centre, radius, 90 + 360 * i / n, 90 + 360 * (i + 1) / n, width=radius * 0.22, facecolor=color,
                           edgecolor="none", zorder=zorder))


# ---------------------------------------------------------------------------------------------------- layouts ---
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
    step: float = 0.06,
) -> dict[str, tuple[float, float]]:
    """A small deterministic force layout with a constraint: after every step each node is projected back into its
    allowed region (a ring, a band ...). Edges pull, all nodes repel, ``pulls`` add attractions to points (fixed or
    recomputed each step). ``step`` is the largest move per step at the start. Same input, same output."""
    if not nodes:
        return {}
    index = {n: i for i, n in enumerate(nodes)}
    pos = np.array([start[n] for n in nodes], dtype=float)
    pos = np.array([project(n, pos[index[n]]) for n in nodes])
    edge_idx = [(index[a], index[b]) for a, b in edges if a in index and b in index]
    for k in range(iterations):
        temperature = step * (1 - k / iterations) + step / 15
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


# ------------------------------------------------------------------------------------ matrices: shared geometry ---
ROW_LABEL_W = 2.0  # inches left of the first column
HEADER_ROWS_H = 0.82  # column headers (two or three lines and n) above the first row
BRACKET_H = 0.3  # 'Marburg und Mittelhessen' above the headers
SLOT_W = 0.39  # one dot with its ID
SLOT_H = 0.22
MIN_ROW_H = 0.38
OUTSIDE_GAP = 0.18  # a little more room before 'außerhalb Europas' (a category step, never a distance)
MISSING_GAP = 0.3  # before 'keine Angabe'


def area_columns() -> list[tuple[Area, str]]:
    """The five display areas in their fixed order; 'nicht zuordenbar' is never a column."""
    return [(a, AREA_LABELS[a].replace("übriges ", "übriges\n").replace("außerhalb ", "außerhalb\n").replace(" (Stadt)", "\n(Stadt)"))
            for a in AREA_ORDER]


def column_offsets(keys: Sequence[object], width: float, gaps: dict[int, float]) -> tuple[dict[object, float], float]:
    """x of every column (left edge) and the common column width, filling ``width``."""
    total_gap = sum(gaps.values())
    col_w = (width - total_gap) / max(len(keys), 1)
    xs, x = {}, 0.0
    for i, key in enumerate(keys):
        x += gaps.get(i, 0.0)
        xs[key] = x
        x += col_w
    return xs, col_w


def area_gaps(keys: Sequence[object]) -> dict[int, float]:
    return {keys.index(Area.OUTSIDE_EUROPE): OUTSIDE_GAP} if Area.OUTSIDE_EUROPE in keys else {}


def _headers(ax: Axes, xs: dict, col_w: float, columns: Sequence[tuple[object, str]], counts: dict[object, int], top: float,
             y_title: str | None) -> None:
    for key, label in columns:
        ax.text(xs[key] + col_w / 2, top - 0.08, f"{label}\nn = {counts.get(key, 0)}", ha="center", va="top", fontsize=LABEL_PT,
                color=INK, linespacing=1.2)
    keys = [k for k, _ in columns]
    if Area.MARBURG in keys and Area.MITTELHESSEN in keys:
        x0, x1 = xs[Area.MARBURG] + 0.1, xs[Area.MITTELHESSEN] + col_w - 0.1
        y = top + 0.08
        ax.plot([x0, x0, x1, x1], [y - 0.06, y, y, y - 0.06], color=MUTED, linewidth=0.8)
        ax.text((x0 + x1) / 2, y + 0.04, "Marburg und Mittelhessen", ha="center", va="bottom", fontsize=LABEL_PT - 0.5, color=MUTED)
    if y_title:
        ax.text(0, top - HEADER_ROWS_H + 0.06, y_title, ha="left", va="bottom", fontsize=LABEL_PT, fontweight="bold", color=INK)


# --------------------------------------------------------------------------------- point matrix (P1, P2, P5) ---
@dataclass(frozen=True)
class Item:
    contact_id: str
    column: object
    row: object
    color: str | None


@dataclass(frozen=True)
class PointGeometry:
    per_line: int
    row_h: float
    height: float  # main area height in inches


def point_geometry(columns: Sequence[tuple[object, str]], rows: Sequence[tuple[object, str]], items: Sequence[Item], width: float,
                   gaps: dict[int, float], row_gaps: dict[int, float], *, bracket: bool) -> PointGeometry:
    """Slots per line and a common row height, so that every cell holds its contacts without overlap."""
    _, col_w = column_offsets([k for k, _ in columns], width - ROW_LABEL_W, gaps)
    per_line = max(1, int((col_w - 0.08) // SLOT_W))
    per_cell: dict[tuple, int] = {}
    for item in items:
        per_cell[(item.column, item.row)] = per_cell.get((item.column, item.row), 0) + 1
    lines = max([math.ceil(n / per_line) for n in per_cell.values()] or [1])
    row_h = max(MIN_ROW_H, lines * SLOT_H + 0.14)
    height = HEADER_ROWS_H + (BRACKET_H if bracket else 0.0) + len(rows) * row_h + sum(row_gaps.values()) + 0.05
    return PointGeometry(per_line, row_h, height)


def point_matrix(
    ax: Axes,
    width: float,
    geometry: PointGeometry,
    columns: Sequence[tuple[object, str]],
    rows: Sequence[tuple[object, str]],
    items: Sequence[Item],
    *,
    gaps: dict[int, float],
    row_gaps: dict[int, float],
    column_counts: dict[object, int],
    tints: dict[object, str] | None = None,
    y_title: str | None = None,
) -> dict[str, tuple[float, float]]:
    """Categories on both axes; every contact is a dot with its ID in its cell, several side by side and in lines.
    Draws into ``ax`` in inch coordinates; returns the dot positions (for tests)."""
    height = geometry.height
    keys = [k for k, _ in columns]
    xs, col_w = column_offsets(keys, width - ROW_LABEL_W, gaps)
    xs = {k: x + ROW_LABEL_W for k, x in xs.items()}
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    top = height - (BRACKET_H if Area.MARBURG in keys else 0.0)
    grid_top = top - HEADER_ROWS_H
    ys, y = {}, grid_top
    for i, (key, _) in enumerate(rows):
        y -= row_gaps.get(i, 0.0)
        ys[key] = y  # top edge of the row
        y -= geometry.row_h
    grid_bottom = y
    shift = ROW_LABEL_W
    for key, _ in columns:
        tint = (tints or {}).get(key, "#F6F7F9")
        ax.add_patch(Rectangle((xs[key] + 0.03, grid_bottom), col_w - 0.06, grid_top - grid_bottom, facecolor=tint, edgecolor="none", zorder=0))
    for key, label in rows:
        y0 = ys[key]
        ax.plot([shift - 0.1, width], [y0, y0], color="#E5E8EB", linewidth=0.6, zorder=1)
        ax.text(shift - 0.14, y0 - geometry.row_h / 2, label, ha="right", va="center", fontsize=LABEL_PT,
                color=MUTED if key == "missing" else INK, style="italic" if key == "missing" else "normal")
    ax.plot([shift - 0.1, width], [grid_bottom, grid_bottom], color="#E5E8EB", linewidth=0.6, zorder=1)
    _headers(ax, xs, col_w, columns, column_counts, top, y_title)
    cells: dict[tuple[object, object], list[Item]] = {}
    for item in items:
        cells.setdefault((item.column, item.row), []).append(item)
    positions = {}
    for (ck, rk), group in sorted(cells.items(), key=lambda kv: str(kv[0])):
        group = sorted(group, key=lambda it: it.contact_id)
        n_lines = math.ceil(len(group) / geometry.per_line)
        used = min(len(group), geometry.per_line) * SLOT_W
        x_start = xs[ck] + (col_w - used) / 2
        for k, item in enumerate(group):
            line, slot = divmod(k, geometry.per_line)
            cx = x_start + slot * SLOT_W + 0.07
            cy = ys[rk] - geometry.row_h / 2 - (line - (n_lines - 1) / 2) * SLOT_H
            style = node_style(item.color)
            ax.scatter([cx], [cy], s=node_size(DOT_PT), zorder=3, **scatter_kwargs(style))
            ax.text(cx + 0.075, cy, item.contact_id, fontsize=ID_PT, color=INK, ha="left", va="center", zorder=4)
            positions[f"{item.contact_id}@{ck}"] = (cx, cy)
    return positions


# ------------------------------------------------------------------------------------- heat matrix (P3, P4) ---
CELL_H = 0.42
SECTION_TITLE_H = 0.26


def heat_fill(share: float) -> tuple[float, float, float]:
    rgb = np.array([int(HEAT[i : i + 2], 16) / 255 for i in (1, 3, 5)])
    return tuple(float(v) for v in 1 - share * 0.9 * (1 - rgb))


def heat_cell(k: int, n: int) -> tuple[object, str]:
    """Fill and text of one cell: count only; empty for 0; neutral for a column with n = 1; blank without a base."""
    if n == 0:
        return "#FFFFFF", ""
    if n == 1:
        return HEAT_NEUTRAL, "1" if k else ""
    if k == 0:
        return "#FFFFFF", ""
    return heat_fill(k / n), str(k)


def heat_height(sections: Sequence[tuple[str | None, Sequence[tuple[object, str]]]], with_missing: bool) -> float:
    rows = sum(len(r) for _, r in sections)
    titles = sum(1 for t, r in sections if t and r)
    return BRACKET_H + HEADER_ROWS_H + rows * CELL_H + titles * SECTION_TITLE_H + (CELL_H + 0.12 if with_missing else 0) + 0.05


def heat_matrix(
    ax: Axes,
    width: float,
    height: float,
    columns: Sequence[tuple[object, str]],
    sections: Sequence[tuple[str | None, Sequence[tuple[object, str]]]],
    counts: dict[tuple[object, object], int],
    bases: dict[object, int],
    missing: dict[object, int],
) -> dict[tuple[object, object], str]:
    """Rows (in visual sections) x area columns. A cell shows the number of contacts; its shade is the share among the
    column's contacts with an answer (n in the header). Returns the cell texts (for tests)."""
    keys = [k for k, _ in columns]
    gaps = area_gaps(keys)
    xs, col_w = column_offsets(keys, width - ROW_LABEL_W, gaps)
    xs = {k: x + ROW_LABEL_W for k, x in xs.items()}
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    top = height - BRACKET_H
    _headers(ax, xs, col_w, columns, bases, top, None)
    y = top - HEADER_ROWS_H
    texts = {}
    for title, rows in sections:
        if not rows:
            continue
        if title:
            ax.text(ROW_LABEL_W - 0.14, y - SECTION_TITLE_H + 0.06, title, ha="right", va="bottom", fontsize=LABEL_PT - 1,
                    color=MUTED, fontweight="bold")
            y -= SECTION_TITLE_H
        for rkey, rlabel in rows:
            ax.text(ROW_LABEL_W - 0.14, y - CELL_H / 2, rlabel, ha="right", va="center", fontsize=LABEL_PT, color=INK)
            for ckey in keys:
                fill, text = heat_cell(counts.get((ckey, rkey), 0), bases.get(ckey, 0))
                ax.add_patch(Rectangle((xs[ckey] + 0.03, y - CELL_H + 0.03), col_w - 0.06, CELL_H - 0.06, facecolor=fill,
                                       edgecolor=CELL_RIM, linewidth=0.6))
                if text:
                    n = bases.get(ckey, 0)
                    share = counts.get((ckey, rkey), 0) / n if n > 1 else 0.0
                    ax.text(xs[ckey] + col_w / 2, y - CELL_H / 2, text, ha="center", va="center", fontsize=LABEL_PT + 1,
                            fontweight="bold", color="#FFFFFF" if share > 0.6 else INK)
                texts[(ckey, rkey)] = text
            y -= CELL_H
    if any(missing.values()):
        y -= 0.12
        ax.text(ROW_LABEL_W - 0.14, y - CELL_H / 2, "ohne Angabe", ha="right", va="center", fontsize=LABEL_PT, color=MUTED, style="italic")
        for ckey in keys:
            k = missing.get(ckey, 0)
            ax.add_patch(FancyBboxPatch((xs[ckey] + 0.1, y - CELL_H + 0.08), col_w - 0.2, CELL_H - 0.16,
                                        boxstyle="round,pad=0,rounding_size=0.04", facecolor="#FFFFFF", edgecolor="#B5BEC7",
                                        linestyle=(0, (2, 2)), linewidth=0.7))
            if k:
                ax.text(xs[ckey] + col_w / 2, y - CELL_H / 2, str(k), ha="center", va="center", fontsize=LABEL_PT, color=MUTED)
    return texts


HEAT_LEGEND = [
    (None, [
        ("ramp", "Farbintensität = Anteil im jeweiligen Wohnortbereich (0–100 %)", None),
        ("area", "n = 1: neutral", {"facecolor": HEAT_NEUTRAL, "edgecolor": CELL_RIM, "linewidth": 0.6}),
        ("text", "Zahlen = Anzahl der Kontakte · leer = keine Nennung · Mehrfachnennungen möglich", None),
    ]),
]


def closeness_rows(include_missing: bool) -> list[tuple[object, str]]:
    rows: list[tuple[object, str]] = [
        (v, f"{codes.closeness_label(v)}" + (f" · {codes.CLOSENESS[v]}" if v == int(v) else "")) for v in codes.CLOSENESS_LEVELS
    ]
    if include_missing:
        rows.append(("missing", "keine Angabe"))
    return rows

