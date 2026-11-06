"""Experiment, not a standard figure: the group map G3 coloured by the contacts' birth country ("G3-Herkunft").

Two views per case:

* **total** (``gesamt``): the group map of G3 unchanged -- same contacts, groups, confirmed ties, positions, outlines,
  outline colours, labels and belonging scale; the node fill is the birth country instead of the relation type.
* **local** (``lokal``): only contacts whose residence area is Marburg (Stadt) or übriges Mittelhessen (the definition of
  :mod:`~mares.network_v1.places`). The residence is a filter only, never a position: the G3 layout runs unchanged on
  this sub-network. Memberships and confirmed ties are restricted to the shown contacts; groups without a local member are
  left out; group IDs and outline colours stay those of the case; a label names local and total members where they
  differ ('5 von 7'). Unconnected parts of the sub-network move together, and the main area is fitted to it
  (:func:`local_size`), so a small one gets no empty bands.

Nodes carry the contact ID and, smaller, the ISO 3166 alpha-3 code of the birth country (``k. A.`` without an answer,
``–`` for a country named but not coded). The full names are in the legend.

**Colours** are fixed per ISO code (:data:`COUNTRY_COLORS`), the same in every case and view, never reassigned by
order or frequency. Countries without a fixed colour get one of :data:`EXTENSION` by their code. Similar colours can
meet in a case; the code in the node keeps them apart. No flags or symbolic national colours; the relation-type
palette is not touched.

Only the recorded birth country is used; nothing about nationality or ethnic identity is derived, no tie or membership
is inferred.
"""

from __future__ import annotations

import math
import zlib
from collections import Counter
from dataclasses import dataclass, replace

from mares.network_v0.figures.style import luminance

from ..case import Contact
from ..codes import MARKERS
from ..derive import Derived
from ..places import Area
from .base import INK, LABEL_PT, MISSING_LABEL, NODE_ID_PT, Context, node_size, node_style, page, scatter_kwargs, text_width
from .networks import (
    G3_H, G3_W, LOOSE_LABEL, belonging_sections, belonging_text, display_name, draw_g3, g3_geometry, group_colors,
)

CODE = "G3"  # the figure this experiment derives from (file names, records)
TITLE_TOTAL = "Gruppenstruktur nach Geburtsland"
TITLE_LOCAL = "Lokale Gruppenstruktur nach Geburtsland"
LOCAL_AREAS = (Area.MARBURG, Area.MITTELHESSEN)
VIEWS = ("gesamt", "lokal")

# ------------------------------------------------------------------------------------------------ colours ---
# Fixed per ISO code, the same in every case. The first ten are the expected frequent birth countries of MARES: they
# differ in every pair for normal vision (OKLab dE >= 16); under protan/deutan simulation the closest pair is VEN/ESP
# (dE 6.1) -- legal only with a second encoding, which the code in the node is. Every colour keeps a text contrast of
# at least 4.5:1 with black or white (the node text takes the better one).
COUNTRY_COLORS = {
    "DEU": "#AA3377",  # wine
    "COL": "#88CCEE",  # sky
    "PER": "#7A4A1E",  # brown
    "MEX": "#EDA100",  # amber
    "ECU": "#332288",  # indigo
    "CHL": "#1F6CC6",  # blue
    "CUB": "#F0E442",  # yellow
    "VEN": "#E87BA4",  # pink
    "ESP": "#1BAF7A",  # green
    "ARG": "#D55E00",  # vermilion
    # further fixed countries on the extension colours (Latin America, then frequent European countries)
    "BRA": "#661100", "BOL": "#004949", "URY": "#5D3A9B", "PRY": "#B66DFF", "DOM": "#DDCC77", "GTM": "#117733",
    "ITA": "#6699CC", "GBR": "#A37F00", "FRA": "#FABFD2", "POL": "#79706E",
}
# any other code: one of these by its code (crc32), the same in every case. None of them is a fixed country's colour
# (OKLab dE >= 10 to each), so such a country never looks like a fixed one; two such countries may share a colour.
EXTENSION = ("#000066", "#660066", "#AA66AA", "#88CC66", "#882244", "#226666")
UNCODED_FILL = "#B4BAC1"  # a country named but not coded: neutral grey (no colour of a country)
LEGEND_FIRST = tuple(COUNTRY_COLORS)  # legend order: the fixed countries in this order, then the others by code
NODE_PT_CODE = 22.0  # node diameter with two lines (ID, country code); G3 has 20
CODE_PT = 5.4
NO_ANSWER_SHORT = "k. A."
UNCODED_SHORT = "–"


def birth_key(contact: Contact) -> str | None:
    """The birth country as recorded: its ISO code; a country named but not coded keeps its name (marked with '~');
    no answer (empty, NS/KA/NA) is None."""
    iso = contact.birth_country_iso3.strip().upper()
    if iso and iso not in MARKERS:
        return iso
    name = contact.birth_country.strip()
    return f"~{name}" if name and name.upper() not in MARKERS else None


def country_fill(key: str | None) -> str | None:
    """The fixed colour of a birth country; None without an answer."""
    if key is None:
        return None
    if key.startswith("~"):
        return UNCODED_FILL
    return COUNTRY_COLORS.get(key) or EXTENSION[zlib.crc32(key.encode()) % len(EXTENSION)]


def short_code(key: str | None) -> str:
    """The second line of a node: ISO alpha-3, 'k. A.' without an answer, '–' for an uncoded name."""
    if key is None:
        return NO_ANSWER_SHORT
    return UNCODED_SHORT if key.startswith("~") else key


def text_color(fill: str) -> str:
    """Black or white, whichever has the higher contrast with the fill (WCAG)."""
    lum = luminance(fill)
    return "#FFFFFF" if (1.05 / (lum + 0.05)) >= ((lum + 0.05) / (luminance("#111111") + 0.05)) else "#111111"


def legend_sort_key(key: str) -> tuple:
    if key in LEGEND_FIRST:
        return (0, LEGEND_FIRST.index(key), key)
    return (1 if not key.startswith("~") else 2, 0, key)


@dataclass(frozen=True)
class Countries:
    """Birth countries of a case: key per contact, name per key."""

    of: dict[str, str | None]  # contact -> key
    name: dict[str, str]

    def contact_fill(self, cid: str) -> str | None:
        return country_fill(self.of[cid])


def countries(ctx: Context) -> Countries:
    of = {c.id: birth_key(c) for c in ctx.case.contacts}
    names: dict[str, Counter] = {}
    for c in ctx.case.contacts:
        key = of[c.id]
        if key is not None:
            names.setdefault(key, Counter())[c.birth_country.strip() or key] += 1
    name = {key: sorted(n.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for key, n in names.items()}
    return Countries(of, name)


def legend_entries(cs: Countries, ids) -> list[tuple]:
    """The countries of ``ids`` in the fixed legend order ('Peru (PER)'; an uncoded name 'Name (nicht codiert)'),
    'keine Angabe' last if it occurs."""
    present = {cs.of[cid] for cid in ids}
    entries = []
    for key in sorted((k for k in present if k is not None), key=legend_sort_key):
        label = f"{cs.name[key]} (nicht codiert)" if key.startswith("~") else f"{cs.name[key]} ({key})"
        entries.append(("dot", label, country_fill(key)))
    if None in present:
        entries.append(("dot", MISSING_LABEL, None))
    return entries


# ----------------------------------------------------------------------------------------------- the views ---
def local_context(ctx: Context) -> Context:
    """The sub-network of the contacts living in Marburg or the rest of Mittelhessen: contacts, memberships, groups with
    at least one local member (IDs, names, belonging unchanged) and the derived pairs between local contacts."""
    local = [cid for cid in ctx.case.contact_ids if ctx.derived.area(cid) in LOCAL_AREAS]
    keep = set(local)
    memberships = [m for m in ctx.case.memberships if m[1] in keep]
    with_members = {g for g, _c, _r in memberships}
    case = replace(
        ctx.case,
        contacts=[c for c in ctx.case.contacts if c.id in keep],
        communication={k: v for k, v in ctx.case.communication.items() if k in keep},
        groups=[g for g in ctx.case.groups if g.id in with_members],
        memberships=memberships,
        statements=[s for s in ctx.case.statements if s.a in keep and s.b in keep],
    )
    derived = Derived(
        residence={k: v for k, v in ctx.derived.residence.items() if k in keep},
        pairs={k: p for k, p in ctx.derived.pairs.items() if k[0] in keep and k[1] in keep},
        coverage=ctx.derived.coverage,
    )
    return Context(case, derived, ctx.geo)


def _label_lines(view_ctx: Context, full: Context):
    def lines(group) -> tuple[str, str]:
        n, total = len(view_ctx.case.members(group.id)), len(full.case.members(group.id))
        count = f"{n}" if n == total else f"{n} von {total}"
        return f"{group.id} · {display_name(group.label)} ({count})", belonging_text(group)

    return lines


def _code_nodes(keys: dict[str, str | None]):
    """Nodes with the ID and, smaller below it, the country code."""
    def draw(ax, positions):
        for cid, (x, y) in positions.items():
            fill = country_fill(keys.get(cid))
            style = node_style(fill)
            ax.scatter([x], [y], s=node_size(NODE_PT_CODE), zorder=4, **scatter_kwargs(style))
            color = INK if fill is None else text_color(style["facecolor"])
            ax.text(x, y + 0.033, cid, fontsize=NODE_ID_PT, color=color, ha="center", va="center", zorder=5, fontweight="bold")
            ax.text(x, y - 0.06, short_code(keys.get(cid)), fontsize=CODE_PT, color=color, ha="center", va="center", zorder=5)
    return draw


# ------------------------------------------------------------------------------------------ local: layout ---
MIN_W, MIN_H = 8.6, 4.6  # inches: the main area never gets smaller (title, badge and legend need the width)
SPACING_MAX = 0.8  # inches: typical distance of a node to its nearest neighbour in the local view, at most
CONTENT_PAD = 0.5  # inches kept beside the content when the width is narrowed to it


def local_size(local: Context, node_r: float) -> tuple[float, float]:
    """Width and height of the main area of the local view: G3's size scaled down when the nodes would stand farther
    apart than SPACING_MAX (few contacts), then narrowed to the content; never below MIN_W x MIN_H. Only the scale
    changes -- the layout (and so the group topology) is G3's."""
    if len(local.case.contact_ids) < 2:
        return MIN_W, MIN_H
    positions = g3_geometry(local, node_r=node_r, compact=True).positions
    pts = list(positions.values())
    nearest = sorted(min(math.dist(a, b) for b in pts if b is not a) for a in pts)
    typical = nearest[len(nearest) // 2]
    factor = min(1.0, SPACING_MAX / typical) if typical > 0 else 1.0
    width, height = max(MIN_W, G3_W * factor), max(MIN_H, G3_H * factor)
    geometry = g3_geometry(local, node_r=node_r, width=width, height=height, compact=True)
    xs = [x for x, _ in geometry.positions.values()] + [v for b in geometry.labels.values() for v in (b[0], b[2])]
    xs.append(text_width(LOOSE_LABEL, LABEL_PT - 1.5) + 0.35 + 0.5 * len(geometry.loose) if geometry.loose else min(xs))
    span = max(xs) - min(xs) + 2 * node_r
    if span < width - 2 * CONTENT_PAD:
        width = max(MIN_W, span + 2 * CONTENT_PAD)
    return width, height


# --------------------------------------------------------------------------------------------- the figure ---
def birth_figure(ctx: Context, view: str):
    """One of the two figures (``view`` in VIEWS)."""
    if view not in VIEWS:
        raise ValueError(f"view must be one of {VIEWS}")
    cs = countries(ctx)
    node_r = NODE_PT_CODE / 72 / 2
    if view == "gesamt":
        geometry = g3_geometry(ctx, node_r=node_r)
        ids = list(geometry.positions)
        sections = [("Geburtsland", legend_entries(cs, ids))] + belonging_sections(ctx, ring=bool(geometry.marked))
        p = page(ctx, CODE, main_w=G3_W, main_h=G3_H, legend="bottom", sections=sections, title=TITLE_TOTAL)
        draw_g3(p.main, ctx, geometry, colors=group_colors(ctx), nodes=_code_nodes(cs.of), node_r=node_r)
        return p.figure
    local = local_context(ctx)
    lines = _label_lines(local, ctx)
    width, height = local_size(local, node_r)
    geometry = g3_geometry(local, node_r=node_r, label_lines=lines, width=width, height=height, compact=True)
    ids = list(geometry.positions)
    sections = [("Geburtsland", legend_entries(cs, ids))] + belonging_sections(local, ring=bool(geometry.marked))
    partial = [(len(local.case.members(g.id)), len(ctx.case.members(g.id))) for g in local.case.groups]
    partial = [(n, t) for n, t in partial if n != t]
    notes = [f"Dargestellt: {len(ids)} von {len(ctx.case.contacts)} Kontakten mit Wohnort in Marburg oder im übrigen Mittelhessen"
             + (f"; „{partial[0][0]} von {partial[0][1]}“ = lokale von allen Mitgliedern der Gruppe." if partial else ".")]
    hidden = [g.id for g in ctx.case.groups if g.id not in {h.id for h in local.case.groups}]
    tail = [ctx.unresolved_note().rstrip(".")] if ctx.unresolved() else []
    if hidden:
        tail.append(f"ohne lokale Mitglieder, nicht dargestellt: {', '.join(hidden)}")
    if tail:
        line = "; ".join(tail) + "."
        notes.append(line[0].upper() + line[1:])
    p = page(ctx, CODE, main_w=width, main_h=height, legend="bottom", sections=sections, notes=notes, title=TITLE_LOCAL)
    draw_g3(p.main, local, geometry, colors=group_colors(ctx), nodes=_code_nodes(cs.of), node_r=node_r, label_lines=lines)
    return p.figure


def figure_name(view: str) -> str:
    return f"geburtsland_{view}"
