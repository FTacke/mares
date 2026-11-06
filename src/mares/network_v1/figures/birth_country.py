"""Experiment, not a standard figure: the group map G3 coloured by the contacts' birth country.

Two views, each in two labelling variants (four figures per case):

* **total** (``gesamt``): the group map of G3 unchanged -- same contacts, groups, confirmed ties, positions, outlines,
  outline colours, labels and belonging scale; only the node fill is the birth country instead of the relation type.
* **local** (``lokal``): only contacts whose residence area is Marburg (Stadt) or übriges Mittelhessen (the definition of
  :mod:`~mares.network_v1.places`, as in G2 and P1-P4). Memberships and confirmed ties are restricted to them; groups
  without a local member are left out; group IDs and outline colours stay those of the case. The G3 layout runs on this
  sub-network. A group label names local and total members where they differ ('2 von 5').
* **variant 1** (``kuerzel``): ID and the ISO 3166 alpha-3 code of the birth country in the node (slightly larger nodes),
  country legend below the map. **variant 2** (``legende``): ID only, a compact country legend right beside the map.

Only the recorded birth country (``birth_country_iso3``, for the legend its recorded name) is used; nothing about
nationality or ethnic identity is derived, no tie or membership is inferred. Colours: nine colours that stay apart in
every pair, also under protan and deutan simulation (checked with an OKLab/CVD validator); a country keeps its colour in
both views of a case and, as far as the other countries of a case allow, across cases (preferred slot from the code).
More than nine countries: the most frequent get colours, the others share one grey ('weitere Geburtsländer'), their
names stay in the legend. No answer: white node with dotted rim, 'keine Angabe'. No flags, no symbolic national colours.
"""

from __future__ import annotations

import zlib
from collections import Counter
from dataclasses import dataclass, replace

from ..case import Contact
from ..codes import MARKERS
from ..derive import Derived
from ..places import Area
from .base import (
    INK, LEGEND_PT, MISSING_LABEL, NODE_ID_PT, NODE_PT, Context, draw_nodes, label_color, node_size, node_style, page,
    scatter_kwargs, text_width,
)
from .networks import (
    G3_H, G3_W, NODE_R_IN, belonging_sections, belonging_text, display_name, draw_g3, g3_geometry, group_colors,
)

CODE = "G3"  # the figure this experiment derives from (file names, records)
TITLE_TOTAL = "Gruppenstruktur nach Geburtsland"
TITLE_LOCAL = "Lokale Gruppenstruktur nach Geburtsland"
LOCAL_AREAS = (Area.MARBURG, Area.MITTELHESSEN)
VIEWS = ("gesamt", "lokal")
VARIANTS = ("kuerzel", "legende")  # 1: ISO code in the node, 2: ID only, legend beside the map

# nine colours, every pair distinguishable (all-pairs CVD dE >= 8 protan/deutan, normal dE >= 15; OKLab x 100)
PALETTE = (
    "#2A78D6",  # blue
    "#D55E00",  # vermilion
    "#1BAF7A",  # green
    "#332288",  # indigo
    "#EDA100",  # amber
    "#AA3377",  # wine
    "#88CCEE",  # sky
    "#7A4A1E",  # brown
    "#F0E442",  # yellow
)
OTHER_FILL = "#B4BAC1"  # 'weitere Geburtsländer' beyond the nine colours
OTHER_LABEL = "weitere Geburtsländer"
CODE_NODE_PT = 24.0  # variant 1: node diameter with two lines (ID, country code)
CODE_PT = 5.6


def birth_key(contact: Contact) -> str | None:
    """The birth country as recorded: its ISO code; a country named but not coded keeps its name (marked with '~');
    no answer (empty, NS/KA/NA) is None."""
    iso = contact.birth_country_iso3.strip().upper()
    if iso and iso not in MARKERS:
        return iso
    name = contact.birth_country.strip()
    return f"~{name}" if name and name.upper() not in MARKERS else None


def short_code(key: str | None) -> str:
    """The code shown in a node of variant 1: ISO alpha-3, nothing for an uncoded name or no answer."""
    return key if key and not key.startswith("~") else ""


@dataclass(frozen=True)
class Countries:
    """Birth countries of a case: key per contact, colour and name per key, the order of the legend."""

    of: dict[str, str | None]  # contact -> key
    fill: dict[str, str]  # key -> colour (OTHER_FILL for the shared grey)
    name: dict[str, str]
    order: list[str]  # keys by frequency in the case, then key

    def contact_fill(self, cid: str) -> str | None:
        key = self.of[cid]
        return None if key is None else self.fill[key]


def countries(ctx: Context) -> Countries:
    """Colours of the birth countries of the whole case (the local view uses the same). Each key prefers the slot
    given by its code, so a country tends to keep its colour across cases; a taken slot passes to the next free one.
    The most frequent countries get the nine colours, the rest the shared grey."""
    of = {c.id: birth_key(c) for c in ctx.case.contacts}
    counts = Counter(k for k in of.values() if k is not None)
    order = sorted(counts, key=lambda k: (-counts[k], k))
    coloured = sorted(order[:len(PALETTE)])
    taken: dict[int, str] = {}
    for key in coloured:
        slot = zlib.crc32(key.encode()) % len(PALETTE)
        while slot in taken:
            slot = (slot + 1) % len(PALETTE)
        taken[slot] = key
    fill = {key: PALETTE[slot] for slot, key in taken.items()} | {key: OTHER_FILL for key in order[len(PALETTE):]}
    names: dict[str, Counter] = {}
    for c in ctx.case.contacts:
        key = of[c.id]
        if key is not None:
            names.setdefault(key, Counter())[c.birth_country.strip() or short_code(key)] += 1
    name = {key: sorted(n.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for key, n in names.items()}
    return Countries(of, fill, name, order)


def legend_entries(cs: Countries, ids: list[str], variant: str) -> list[tuple]:
    """Entries for the countries of ``ids``, in the order of the case; the grey ones in one entry naming them (variant
    1 with their codes, variant 2 with the contacts, since the node shows no code); 'keine Angabe' last if it occurs."""
    present = {cs.of[cid] for cid in ids}
    entries, others = [], []
    for key in cs.order:
        if key not in present:
            continue
        code = short_code(key)
        if cs.fill[key] == OTHER_FILL:
            who = ", ".join(cid for cid in ids if cs.of[cid] == key)
            others.append(f"{cs.name[key]} ({code or '–'})" if variant == "kuerzel" else f"{cs.name[key]}: {who}")
            continue
        entries.append(("dot", f"{cs.name[key]} ({code})" if variant == "kuerzel" and code else cs.name[key], cs.fill[key]))
    if others:
        entries.append(("dot", f"{OTHER_LABEL}: " + " · ".join(others), OTHER_FILL))
    if None in present:
        entries.append(("dot", MISSING_LABEL, None))
    return entries


# --------------------------------------------------------------------------------------------------- views ---
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


def _code_nodes(fills: dict[str, str | None], keys: dict[str, str | None]):
    """Variant 1: node with the ID and, below it, the country code."""
    def draw(ax, positions):
        for cid, (x, y) in positions.items():
            style = node_style(fills.get(cid))
            ax.scatter([x], [y], s=node_size(CODE_NODE_PT), zorder=4, **scatter_kwargs(style))
            color = label_color(style["facecolor"])
            code = short_code(keys.get(cid))
            ax.text(x, y + (0.035 if code else 0.0), cid, fontsize=NODE_ID_PT, color=color, ha="center", va="center", zorder=5,
                    fontweight="bold")
            if code:
                ax.text(x, y - 0.065, code, fontsize=CODE_PT, color=color, ha="center", va="center", zorder=5)
    return draw


LEGEND_GAP = 0.3  # variant 2: inches between the map and its country legend
ROW = 0.22


def _side_legend(ax, entries: list[tuple], x: float, top: float) -> None:
    ax.text(x, top, "Geburtsland", fontsize=LEGEND_PT, fontweight="bold", color=INK, ha="left", va="top")
    y = top - 0.24 - ROW / 2
    for kind, label, fill in entries:
        if kind == "dot":  # 'text': a continuation line of the entry above
            ax.scatter([x + 0.08], [y], s=node_size(9.5), zorder=3, clip_on=False, **scatter_kwargs(node_style(fill)))
        ax.text(x + 0.22, y, label, fontsize=LEGEND_PT, color=INK, ha="left", va="center")
        y -= ROW if kind == "dot" else ROW * 0.8


def _wrap_others(entries: list[tuple], width: float) -> list[tuple]:
    """Variant 2: a long 'weitere' entry is broken into lines of at most ``width`` inches."""
    out = []
    for kind, label, fill in entries:
        if fill == OTHER_FILL and text_width(label, LEGEND_PT) > width:
            head, _, rest = label.partition(": ")
            lines, line = [f"{head}:"], ""
            for part in rest.split(" · "):
                trial = f"{line} · {part}" if line else part
                if line and text_width(trial, LEGEND_PT) > width:
                    lines.append(line)
                    line = part
                else:
                    line = trial
            lines.append(line)
            out.append((kind, lines[0], fill))
            out += [("text", ln, "") for ln in lines[1:]]
        else:
            out.append((kind, label, fill))
    return out


def birth_figure(ctx: Context, view: str, variant: str):
    """One of the four figures: ``view`` in VIEWS, ``variant`` in VARIANTS."""
    if view not in VIEWS or variant not in VARIANTS:
        raise ValueError(f"view must be one of {VIEWS} and variant one of {VARIANTS}")
    cs = countries(ctx)
    view_ctx = local_context(ctx) if view == "lokal" else ctx
    lines = _label_lines(view_ctx, ctx) if view == "lokal" else None
    node_r = CODE_NODE_PT / 72 / 2 if variant == "kuerzel" else NODE_R_IN
    geometry = g3_geometry(view_ctx, node_r=node_r, label_lines=lines)
    ids = list(geometry.positions)
    fills = {cid: cs.contact_fill(cid) for cid in ids}
    entries = legend_entries(cs, ids, variant)
    rest = belonging_sections(view_ctx, ring=bool(geometry.marked))
    notes = []
    if view == "lokal":
        partial = [(len(view_ctx.case.members(g.id)), len(ctx.case.members(g.id))) for g in view_ctx.case.groups]
        partial = [(n, t) for n, t in partial if n != t]
        notes.append(f"Dargestellt: {len(ids)} von {len(ctx.case.contacts)} Kontakten mit Wohnort in Marburg oder im übrigen "
                     "Mittelhessen" + (f"; „{partial[0][0]} von {partial[0][1]}“ = lokale von allen Mitgliedern der Gruppe."
                                       if partial else "."))
        hidden = [g.id for g in ctx.case.groups if g.id not in {h.id for h in view_ctx.case.groups}]
        tail = [ctx.unresolved_note().rstrip(".")] if ctx.unresolved() else []
        if hidden:
            tail.append(f"ohne lokale Mitglieder, nicht dargestellt: {', '.join(hidden)}")
        if tail:
            line = "; ".join(tail) + "."
            notes.append(line[0].upper() + line[1:])
    main_w = G3_W
    side = None
    if variant == "legende" and entries:
        xs = [x + node_r for x, _ in geometry.positions.values()] + [b[2] for b in geometry.labels.values()]
        ys = [y + node_r for _, y in geometry.positions.values()] + [b[3] for b in geometry.labels.values()]
        entries = _wrap_others(entries, 2.4)
        width = max(0.22 + text_width(label, LEGEND_PT) for _k, label, _f in entries)
        width = max(width, text_width("Geburtsland", LEGEND_PT, bold=True))
        x = max(xs) + LEGEND_GAP
        main_w = max(G3_W, x + width + 0.1)
        side = (x, min(max(ys), G3_H - 0.05))
        sections = rest
    else:
        sections = [("Geburtsland", entries)] + rest
    title = TITLE_LOCAL if view == "lokal" else TITLE_TOTAL
    p = page(ctx, CODE, main_w=main_w, main_h=G3_H, legend="bottom", sections=sections, notes=notes, title=title)
    nodes = (_code_nodes(fills, cs.of) if variant == "kuerzel"
             else (lambda ax, positions: draw_nodes(ax, positions, fills)))
    draw_g3(p.main, view_ctx, geometry, colors=group_colors(ctx), nodes=nodes, node_r=node_r, label_lines=lines)
    if side:
        _side_legend(p.main, entries, *side)
    return p.figure


def figure_name(view: str, variant: str) -> str:
    return f"geburtsland_{view}_{variant}"


EXPERIMENT = [(view, variant) for view in VIEWS for variant in VARIANTS]
