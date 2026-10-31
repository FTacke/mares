"""Figures G1 and G2: where the contacts live, relative to ego -- in ordered steps, not on a map.

The residence of a contact falls into one of five categories, from near to far from the reference place:
**Marburg**, **Region Marburg**, **übriges Deutschland**, **übriges Europa**, **außerhalb Europas** (a sixth, "unknown",
only if some residence cannot be classified). These figures show the *category*, nothing else:

* the ring or band a contact stands in is its residence category -- not a distance in kilometres (ring
  widths follow the number of contacts, not geography);
* the position within a ring or band follows the structure of the contact-contact ties (G2) or only
  legibility (G1) -- it is neither subjective closeness (figure A) nor a network layout (B1-B3);
* no line is drawn that was not surveyed.

G1 shows the contacts in the rings; G2 adds the 41 (or n) confirmed contact-contact ties in two variants,
rings (G2a) and bands (G2b). The same contact stands at the same place in G1 and G2a.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from itertools import combinations

import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle, FancyBboxPatch

from mares.core import ids

from ..analysis import AnalysisParams, SurveyStatus, geo_labels
from ..build import Network
from ..geo import GeoCategory
from ..model import NetworkDataset
from . import design, layouts
from .common import ContactView, contact_views, draw_legend, draw_node
from .ego_network import EGO_DIAMETER_PT, EGO_LINE_COLOR, EGO_LINE_WIDTH_PT
from .network import (
    LABEL_FONT_PT, NODE_DIAMETER_PT, TIE_WIDTH_PT, _elicitation_sentence, _frame_axes, _halo, _to_data, _to_pt, build_structure,
    place_labels,
)
from .style import GEO_COLORS, INK, MUTED, FAINT, frame, label_color, new_figure, rc, rim_color, wrap

ZONES = (GeoCategory.LOCAL, GeoCategory.LOCAL_REGION, GeoCategory.GERMANY_OTHER, GeoCategory.EUROPE_OTHER, GeoCategory.OUTSIDE_EUROPE)
RING_START = 0.8  # radius where the first zone begins (ego sits inside)
RING_MIN_WIDTH = 1.0
MIN_CHORD = 0.82  # least distance between two contacts of one zone (picture units)
GAP_DEG = 25.0  # free sector around 12 o'clock for the zone numbers
WITHIN_TIE_COLOR = "#1F2933"  # a tie inside one zone: dark, thin
BETWEEN_TIE_COLOR = "#7C8B99"  # a tie across zones: lighter and a little stronger, clearly more visible than the ego lines
_ZONE_FILL = {GeoCategory.LOCAL: 0.90, GeoCategory.LOCAL_REGION: 0.92, GeoCategory.GERMANY_OTHER: 0.94, GeoCategory.EUROPE_OTHER: 0.955, GeoCategory.OUTSIDE_EUROPE: 0.97, GeoCategory.UNKNOWN: 0.98}


def zone_label(category: GeoCategory, params: AnalysisParams) -> str:
    """The name of a zone: the category without the remark that belongs in a footnote."""
    return design.zone_name(category, params)


def zones_present(views: list[ContactView]) -> list[GeoCategory]:
    """The four zones always (an empty zone stays visible); 'unknown' only if somebody falls into it."""
    zones = list(ZONES)
    if any(v.geo is GeoCategory.UNKNOWN for v in views):
        zones.append(GeoCategory.UNKNOWN)
    return zones


# ---------------------------------------------------------------- order of the contacts ---------

def structure_order(network: Network) -> list[str]:
    """A circular order of the contacts that keeps tied contacts together: the contacts sorted by their
    angle around the centre of the B1/B2 layout, cut at the widest empty angle. Deterministic."""
    positions = build_structure(network).positions
    names = sorted(positions, key=ids.contact_number)
    if len(names) < 3:
        return names
    cx = sum(p[0] for p in positions.values()) / len(names)
    cy = sum(p[1] for p in positions.values()) / len(names)
    angles = sorted((math.atan2(positions[c][1] - cy, positions[c][0] - cx), ids.contact_number(c), c) for c in names)
    gaps = [((angles[(i + 1) % len(angles)][0] - angles[i][0]) % (2 * math.pi), i) for i in range(len(angles))]
    widest = max(gaps, key=lambda g: (g[0], -g[1]))[1]
    rotated = angles[widest + 1 :] + angles[: widest + 1]
    return [c for _, _, c in rotated]


def _spread(values: list[float], delta: float, low: float, high: float) -> list[float]:
    """Keep sorted values at least ``delta`` apart inside [low, high], moving each as little as it must."""
    out = list(values)
    for i in range(1, len(out)):
        out[i] = max(out[i], out[i - 1] + delta)
    if out and out[-1] > high:
        out[-1] = high
        for i in range(len(out) - 2, -1, -1):
            out[i] = min(out[i], out[i + 1] - delta)
    if out and out[0] < low:
        out[0] = low
        for i in range(1, len(out)):
            out[i] = max(out[i], out[i - 1] + delta)
    return out


# ---------------------------------------------------------------- rings (G1, G2a) --------------

@dataclass(frozen=True)
class Band:
    category: GeoCategory
    inner: float
    outer: float
    members: tuple[str, ...]  # contact ids, in the order given


@dataclass(frozen=True)
class RingLayout:
    positions: dict[str, tuple[float, float]]
    bands: tuple[Band, ...]
    outer_radius: float


def ring_layout(views: list[ContactView], order: list[str] | None = None, *, even: bool = False) -> RingLayout:
    """Contacts on concentric zones by residence category. The radius is a function of the category alone;
    a zone's width grows only as far as its contacts need room. The angle follows ``order`` (contacts that are
    tied stand at similar angles in every ring); no zone is ever left out."""
    if even:  # G1: every zone evenly filled, sorted by place and id (readable, no structure implied)
        place = {v.contact_id: (v.city or "", ids.contact_number(v.contact_id)) for v in views}
        order = sorted((v.contact_id for v in views), key=lambda c: place[c])
    order = order or []
    rank = {c: i for i, c in enumerate(order)}
    total = max(len(order) - 1, 1)
    start, span = 90.0 + GAP_DEG, 360.0 - 2 * GAP_DEG
    positions: dict[str, tuple[float, float]] = {}
    bands: list[Band] = []
    previous = RING_START
    for zone_index, category in enumerate(zones_present(views)):
        members = sorted((v.contact_id for v in views if v.geo is category), key=lambda c: rank.get(c, 0))
        need = len(members) * MIN_CHORD / (2 * math.pi * span / 360.0)
        middle = max(previous + RING_MIN_WIDTH / 2, need)
        inner, outer = previous, 2 * middle - previous
        delta = math.degrees(2 * math.asin(min(1.0, MIN_CHORD / (2 * middle))))
        if even:
            n = len(members)
            odd = zone_index % 2 == 1  # neighbouring zones use different margins, so nodes do not line up radially
            step = span / (n + 1) if odd else span / max(n, 1)
            raw = [start + step * (k + 1 if odd else k + 0.5) for k in range(n)]
        else:
            raw = [start + span * rank.get(c, 0) / total for c in members]
        for contact, angle in zip(members, _spread(raw, delta, start, start + span)):
            positions[contact] = (round(middle * math.cos(math.radians(angle)), 9), round(middle * math.sin(math.radians(angle)), 9))
        bands.append(Band(category, inner, outer, tuple(members)))
        previous = outer
    return RingLayout(positions, tuple(bands), previous)


def _draw_rings(ax, layout: RingLayout, params: AnalysisParams) -> None:
    n = len(layout.bands)
    for index in range(n - 1, -1, -1):  # outermost first
        band = layout.bands[index]
        tint = _ZONE_FILL[band.category]
        ax.add_patch(Circle((0, 0), band.outer, facecolor=(tint, tint + 0.004, tint + 0.012), edgecolor="#AEB6BD", linewidth=0.9,
                            linestyle=(0, (4, 3)) if band.category is GeoCategory.UNKNOWN else "solid", zorder=1 + 0.1 * (n - index)))
    for index, band in enumerate(layout.bands, 1):
        mid = (band.inner + band.outer) / 2
        ax.scatter([0], [mid], s=260, c="white", edgecolors="#8D969E", linewidths=1.0, zorder=3)
        ax.text(0, mid, str(index) if band.category is not GeoCategory.UNKNOWN else "?", ha="center", va="center", fontsize=9.5,
                fontweight="bold", color=INK, zorder=4)


def _draw_ego(ax, xy=(0.0, 0.0), *, size: float = EGO_DIAMETER_PT, label_pt: float = 6.6) -> None:
    ax.scatter([xy[0]], [xy[1]], s=size**2, c=INK, edgecolors="white", linewidths=1.2, zorder=6)
    ax.text(xy[0], xy[1], "EGO", ha="center", va="center", fontsize=label_pt, fontweight="bold", color="white", zorder=7)


def _places(views: list[ContactView], category: GeoCategory, params: AnalysisParams) -> str:
    """The places of a zone, without repeating the zone's own name."""
    own = zone_label(category, params).casefold()
    counts = Counter(v.city for v in views if v.geo is category and v.city and v.city.casefold() != own)
    return ", ".join(city for city, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def _zone_legend(views: list[ContactView], layout_bands, params: AnalysisParams, *, numbered: bool = True, title: str = "Wohnort-Zonen (innen → außen)"):
    counts = Counter(v.geo for v in views)
    entries = []
    for index, category in enumerate((b.category for b in layout_bands), 1):
        n = counts.get(category, 0)
        head = f"{index} · {zone_label(category, params)}  (n = {n})" if numbered else f"{zone_label(category, params)}  (n = {n})"
        places = _places(views, category, params)
        tail = ("\n     " + wrap(places, 34).replace("\n", "\n     ")) if places else ("\n     (keine Kontakte)" if n == 0 else "")
        entries.append(("dot", GEO_COLORS[category], head + tail))
    return (title, entries)


_ZONE_NOTE = (
    "Die Zone ordnet den Wohnort in Stufen (Marburg, Region Marburg, übriges Deutschland, übriges Europa, außerhalb Europas); sie ist keine Karte und kein Entfernungsmaß in Kilometern – "
    "die Ringbreiten richten sich nach der Zahl der Kontakte, nicht nach Geografie. Die Lage im Bild ist weder subjektive Nähe (Abbildung A) noch ein Netzwerk-Layout (B1–B3)."
)


def _canvas(title: str, subtitle: str, status: SurveyStatus, note: str, radius: float, width: float = 13.2, height: float = 9.6, *,
            profile: str = "analysis", short_title: str | None = None, hint: str | None = None):
    fig = new_figure(width, height)
    design.frame_for(profile, fig, title, subtitle, status, note, short_title=short_title, hint=hint)
    ax = fig.add_axes([0.02, 0.125, 0.62, 0.765])
    limit = radius + 0.45
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.apply_aspect()
    legend = fig.add_axes([0.665, 0.13, 0.325, 0.76])
    return fig, ax, legend


def geographic_zones_figure(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams, *, network: Network, profile: str = "clean"):
    """G1: the contacts in four geographic zones around ego (no ties)."""
    with rc():
        views = contact_views(dataset, params)
        layout = ring_layout(views, even=True)
        by_id = {v.contact_id: v for v in views}
        note = (
            _ZONE_NOTE + " Winkel und Reihenfolge innerhalb einer Zone dienen nur der Lesbarkeit (sortiert nach Wohnort, dann ID) und tragen keine Information. "
            "Beziehungen zwischen Kontakten sind in G1 nicht dargestellt (siehe G2, B1–B3)."
        )
        fig, ax, legend = _canvas(
            "Geografische Einordnung der Kontakte relativ zu Ego",
            "Jeder Punkt ist ein Kontakt (ID); die Zone ist die Wohnortkategorie – innen Marburg, außen außerhalb Europas",
            status, note, layout.outer_radius,
            profile=profile, short_title="Geografische Einordnung der Kontakte", hint="Zonen sind Wohnort-Kategorien, keine Entfernungen.",
        )
        _draw_rings(ax, layout, params)
        for contact, xy in layout.positions.items():
            draw_node(ax, xy, contact, GEO_COLORS[by_id[contact].geo])
        _draw_ego(ax)
        draw_legend(legend, design.lean_sections([_zone_legend(views, layout.bands, params)], profile), line=0.043)
    return fig


# ---------------------------------------------------------------- bands (G2b) ------------------

@dataclass(frozen=True)
class BandLayout:
    positions: dict[str, tuple[float, float]]
    ego: tuple[float, float]
    boxes: tuple[tuple[GeoCategory, float, float, float, float, tuple[str, ...]], ...]  # category, x0, x1, y0, y1, members
    width: float
    height: float


BAND_WIDTH = 2.4
BAND_GAP = 0.45
NODE_STEP = 0.5  # least vertical distance between two contacts of one band


def band_layout(views: list[ContactView], order: list[str]) -> BandLayout:
    """Four vertical bands side by side, near to far from left to right. Inside a band the contacts keep the
    circular order of the ties (top to bottom) so that tied contacts stand at similar heights; every second
    contact is shifted sideways to give the ties room."""
    rank = {c: i for i, c in enumerate(order)}
    total = max(len(order) - 1, 1)
    zones = zones_present(views)
    biggest = max((sum(1 for v in views if v.geo is z) for z in zones), default=1)
    height = max(3.0, biggest * NODE_STEP + 1.0)
    inner = height - 1.0
    positions: dict[str, tuple[float, float]] = {}
    boxes = []
    ego_x = -1.6
    for index, category in enumerate(zones):
        x0 = index * (BAND_WIDTH + BAND_GAP)
        x1 = x0 + BAND_WIDTH
        members = sorted((v.contact_id for v in views if v.geo is category), key=lambda c: rank.get(c, 0))
        raw = [height - 0.5 - inner * rank.get(c, 0) / total for c in members]
        # sorted from the top: spread downwards by negating
        ys = [-y for y in _spread([-y for y in raw], NODE_STEP, -(height - 0.5), -0.5)]
        for k, (contact, y) in enumerate(zip(members, ys)):
            positions[contact] = (round(x0 + BAND_WIDTH / 2 + (0.42 if k % 2 else -0.42), 9), round(y, 9))
        boxes.append((category, x0, x1, 0.0, height, tuple(members)))
    return BandLayout(positions, (ego_x, height / 2), tuple(boxes), zones.__len__() * (BAND_WIDTH + BAND_GAP) - BAND_GAP, height)


# ---------------------------------------------------------------- the ties -----------------------

def classify_ties(network: Network, views: list[ContactView]) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """(within, between): the confirmed ties whose two contacts live in the same zone / in different zones."""
    zone = {v.contact_id: v.geo for v in views}
    within, between = [], []
    for tie in network.positive_ties:
        (within if zone[tie.a] is zone[tie.b] else between).append(tie.pair)
    return within, between


HIGHLIGHTS = (None, "between", "within")


def tie_styles(highlight: str | None) -> dict[str, tuple[str, float, float]]:
    """(colour, width, zorder) of the two kinds of contact-contact tie. ``highlight`` brings one kind forward and
    lets the other step back; neither is ever hidden and none is added."""
    if highlight == "between":
        return {"between": (design.TIE_STRONG, design.TIE_STRONG_WIDTH_PT, 2.5), "within": (design.TIE_MUTED, design.TIE_MUTED_WIDTH_PT, 2.0)}
    if highlight == "within":
        return {"within": (design.TIE_STRONG, design.TIE_STRONG_WIDTH_PT, 2.5), "between": (design.TIE_MUTED, design.TIE_MUTED_WIDTH_PT, 2.0)}
    return {"between": (BETWEEN_TIE_COLOR, TIE_WIDTH_PT + 0.45, 2.0), "within": (WITHIN_TIE_COLOR, TIE_WIDTH_PT + 0.05, 2.2)}


def _draw_ties(ax, positions, within, between, *, ego: tuple[float, float] | None, ego_lines: bool, highlight: str | None = None,
               ego_color: str = EGO_LINE_COLOR, ego_width: float = EGO_LINE_WIDTH_PT) -> list:
    """Ties and, if asked, the ego lines (always underneath). Returns the soft segments in data units.

    The collections carry labels (``ego_lines``, ``ties_between``, ``ties_within``) so that they can be told apart.
    """
    soft = []
    if ego_lines and ego is not None:
        segments = [(ego, positions[c]) for c in sorted(positions, key=ids.contact_number)]
        ax.add_collection(LineCollection(segments, colors=ego_color, linewidths=ego_width, zorder=1.6, capstyle="round", label="ego_lines"))
        soft = segments
    styles = tie_styles(highlight)
    for kind, pairs in (("between", between), ("within", within)):
        if pairs:
            colour, width, z = styles[kind]
            ax.add_collection(LineCollection([(positions[a], positions[b]) for a, b in pairs], colors=colour, linewidths=width, alpha=0.95,
                                             zorder=z, capstyle="round", label=f"ties_{kind}"))
    return soft


def _draw_small_nodes(ax, positions, by_id, node_pt: float = NODE_DIAMETER_PT) -> None:
    nodes = sorted(positions, key=ids.contact_number)
    colors = [GEO_COLORS[by_id[c].geo] for c in nodes]
    ax.scatter([positions[c][0] for c in nodes], [positions[c][1] for c in nodes], s=node_pt**2, c=colors,
               edgecolors=[rim_color(c) for c in colors], linewidths=0.8, zorder=4)


def _label_nodes(ax, positions, edges, centre_xy, obstacles_pt=(), soft_data=(), *, font_pt: float = LABEL_FONT_PT, node_pt: float = NODE_DIAMETER_PT) -> None:
    nodes = sorted(positions, key=ids.contact_number)
    pts = {c: _to_pt(ax, positions[c]) for c in nodes}
    centre = _to_pt(ax, centre_xy)
    soft = tuple((_to_pt(ax, a), _to_pt(ax, b)) for a, b in soft_data)
    placed = place_labels(pts, edges, centre, obstacles=tuple(obstacles_pt), soft_segments=soft, font_pt=font_pt, node_pt=node_pt)
    for cx, cy, text in placed.values():
        x, y = _to_data(ax, (cx, cy))
        ax.text(x, y, text, ha="center", va="center", fontsize=font_pt, color=INK, zorder=7, path_effects=[_halo()])


def _tie_legend(within, between, ego_lines: bool, highlight: str | None = None):
    styles = tie_styles(highlight)
    entries = [
        ("line", styles["within"][0], wrap(f"Beziehung innerhalb einer Zone  (n = {len(within)})", 44)),
        ("line", styles["between"][0], wrap(f"Beziehung zwischen Zonen  (n = {len(between)})", 44)),
    ]
    if ego_lines:
        entries.append(("line", EGO_LINE_COLOR, wrap("Ego – Kontakt: Zugehörigkeit zum persönlichen Netzwerk", 36)))
    return ("Bestätigte Kontakt–Kontakt-Beziehungen", entries)


def _tie_note(status: SurveyStatus, within, between) -> str:
    return (
        f"{_elicitation_sentence(status)} {status.short_note()} "
        f"Von den {len(within) + len(between)} bestätigten Beziehungen verlaufen {len(within)} innerhalb und {len(between)} zwischen den Zonen; "
        "dass die Zonen räumlich getrennt gezeichnet sind, heißt nicht, dass die Kontakte sozial getrennt sind."
    )


def _band_extent(layout: BandLayout) -> tuple[float, float, float, float]:
    """x0, x1, y0, y1 of the drawing area: ego on the left, the band captions below."""
    return layout.ego[0] - 0.55, layout.width + 0.15, -1.25, layout.height + 0.15


def _draw_bands(ax, layout: BandLayout, params: AnalysisParams, *, size: float = 9.0, counts: bool = True) -> None:
    """The band boxes with one caption each (number, zone, count); the axes get their final limits."""
    x0, x1, y0, y1 = _band_extent(layout)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.apply_aspect()
    for index, (category, bx0, bx1, by0, by1, members) in enumerate(layout.boxes, 1):
        tint = _ZONE_FILL[category]
        ax.add_patch(FancyBboxPatch((bx0, by0), bx1 - bx0, by1 - by0, boxstyle="round,pad=0,rounding_size=0.18", facecolor=(tint, tint + 0.004, tint + 0.012),
                                    edgecolor="#AEB6BD", linewidth=0.9, zorder=1))
        caption = (wrap(f"{index} · {zone_label(category, params)}", 17) + f"\nn = {len(members)}") if counts else wrap(zone_label(category, params), 17)
        ax.text((bx0 + bx1) / 2, by0 - 0.12, caption, ha="center", va="top", fontsize=size, fontweight="bold", color=INK, linespacing=1.3)


def _band_figure_size(layout: BandLayout, width: float = 13.2, axes_width_fraction: float = 0.665) -> tuple[float, float, float]:
    """Figure height that fits the equal-aspect drawing without empty bands above and below.
    Returns (height, axes bottom as a fraction, axes height as a fraction)."""
    x0, x1, y0, y1 = _band_extent(layout)
    axes_w = width * axes_width_fraction
    axes_h = axes_w * (y1 - y0) / (x1 - x0)
    top, bottom = 0.95, 1.4  # inches: title block above, note and stamp below
    height = axes_h + top + bottom
    return height, bottom / height, axes_h / height


def geographic_network_figure(
    dataset: NetworkDataset,
    status: SurveyStatus,
    params: AnalysisParams,
    *,
    network: Network,
    variant: str = "bands",
    ego_lines: bool = True,
    profile: str = "clean",
    highlight: str | None = None,
):
    """G2: the confirmed contact-contact ties in a geographic arrangement.

    ``variant``: ``bands`` (G2b, the regular figure) or ``rings`` (G2a, concentric zones; kept for comparison).
    Ego is shown; its light lines (one per contact) say only that the contact belongs to the personal network.
    ``highlight`` (``None``, ``"between"`` or ``"within"``) brings the ties between / within the geographic zones
    forward and lets the others step back -- without hiding or adding any. ``profile``: ``clean`` (the standard for
    the bands: reduced text, large drawing) or ``analysis`` (the working version with the fuller notes).
    """
    if variant not in ("rings", "bands"):
        raise ValueError("variant is 'rings' or 'bands'")
    if highlight not in HIGHLIGHTS:
        raise ValueError("highlight is None, 'between' or 'within'")
    design.check_profile(profile)
    if variant == "bands" and profile == "clean":
        return _bands_clean(dataset, status, params, network=network, ego_lines=ego_lines, highlight=highlight)
    with rc():
        views = contact_views(dataset, params)
        by_id = {v.contact_id: v for v in views}
        order = structure_order(network)
        within, between = classify_ties(network, views)
        edges = within + between
        if variant == "rings":
            layout = ring_layout(views, order)
            fig, ax, legend = _canvas(
                "Beziehungen zwischen den Kontakten, geografisch gegliedert (konzentrische Zonen)",
                f"{len(views)} Kontakte in fünf Wohnort-Zonen um Ego · {len(edges)} bestätigte Beziehungen · Zonen innen → außen: Marburg, Region Marburg, übriges Deutschland, übriges Europa, außerhalb Europas",
                status,
                _tie_note(status, within, between) + " " + _ZONE_NOTE.replace("Die Zone ordnet", "Die Ringe ordnen"),
                layout.outer_radius,
            )
            _draw_rings(ax, layout, params)
            soft = _draw_ties(ax, layout.positions, within, between, ego=(0.0, 0.0), ego_lines=ego_lines, highlight=highlight)
            _draw_small_nodes(ax, layout.positions, by_id)
            _draw_ego(ax)
            _label_nodes(ax, layout.positions, edges, (0.0, 0.0), obstacles_pt=((*_to_pt(ax, (0.0, 0.0)), EGO_DIAMETER_PT / 2),), soft_data=soft)
            draw_legend(legend, [_zone_legend(views, layout.bands, params), _tie_legend(within, between, ego_lines, highlight)], line=0.04)
        else:
            layout = band_layout(views, order)
            height, bottom, axes_h = _band_figure_size(layout)
            fig = new_figure(13.2, height)
            frame(
                fig,
                "Beziehungen zwischen den Kontakten, geografisch gegliedert",
                f"{len(views)} Kontakte in fünf Wohnort-Bändern · {len(edges)} bestätigte Beziehungen · Bänder von links nach rechts: Marburg → außerhalb Europas",
                status,
                _tie_note(status, within, between) + " Die Bänder ordnen den Wohnort in Stufen; sie sind keine Karte und kein Entfernungsmaß, alle Bänder sind gleich breit. "
                "Die Höhe im Band folgt der Struktur der Beziehungen (verbundene Kontakte stehen auf ähnlicher Höhe) – sie ist weder Nähe zu Ego (Abbildung A) noch ein Netzwerk-Layout (B1–B3). "
                "Ego links: die hellen Linien zeigen die Zugehörigkeit zum persönlichen Netzwerk, nicht Nähe.",
            )
            ax = fig.add_axes([0.02, bottom, 0.665, axes_h])
            legend = fig.add_axes([0.70, bottom, 0.295, axes_h])
            _draw_bands(ax, layout, params)
            soft = _draw_ties(ax, layout.positions, within, between, ego=layout.ego, ego_lines=ego_lines, highlight=highlight)
            _draw_small_nodes(ax, layout.positions, by_id)
            _draw_ego(ax, layout.ego)
            centre = (sum(p[0] for p in layout.positions.values()) / max(len(layout.positions), 1), layout.height / 2)
            _label_nodes(ax, layout.positions, edges, centre, obstacles_pt=((*_to_pt(ax, layout.ego), EGO_DIAMETER_PT / 2),), soft_data=soft)
            draw_legend(legend, [_zone_legend(views, tuple(Band(b[0], 0, 0, b[5]) for b in layout.boxes), params, title="Wohnort-Zonen (links → rechts)"), _tie_legend(within, between, ego_lines, highlight)], line=0.045)
    return fig


def _bands_clean(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams, *, network: Network, ego_lines: bool, highlight: str | None):
    """G2b in the reduced design: bands captioned directly, a one-row line legend, one hint, a short provenance line."""
    with rc():
        views = contact_views(dataset, params)
        by_id = {v.contact_id: v for v in views}
        order = structure_order(network)
        within, between = classify_ties(network, views)
        edges = within + between
        layout = band_layout(views, order)
        x0, x1, y0, y1 = _band_extent(layout)
        width = 13.0
        axes_h = width * 0.96 * (y1 - y0) / (x1 - x0)
        fig = new_figure(width, axes_h + 1.95)
        styles = tie_styles(highlight)
        entries = [("line", styles["within"][0], "Beziehung innerhalb eines Bereichs"), ("line", styles["between"][0], "Beziehung zwischen Bereichen")]
        if ego_lines:
            entries.append(("line", design.EGO_LINE, "Ego – Kontakt"))
        complete = status.completeness == "complete"
        hint = ("Die Bereiche sind Wohnortkategorien, keine Entfernungen; die Höhe im Band zeigt keine Nähe. "
                + ("Paare ohne Linie sind ausdrücklich verneint." if complete else "Paare ohne Linie: unbekannt, nicht „keine Beziehung“."))
        top, bottom = design.clean_frame(fig, "Kontakte und Beziehungen nach Wohnort", "Beziehungen innerhalb und zwischen den Wohnort-Bereichen", hint, status)
        top = design.legend_strip(fig, entries, top=top)
        ax = fig.add_axes([0.02, bottom, 0.96, top - bottom])
        _draw_bands(ax, layout, params, size=design.CAPTION_PT, counts=False)
        soft = _draw_ties(ax, layout.positions, within, between, ego=layout.ego, ego_lines=ego_lines, highlight=highlight,
                          ego_color=design.EGO_LINE, ego_width=design.EGO_LINE_WIDTH_PT)
        _draw_small_nodes(ax, layout.positions, by_id, node_pt=design.NODE_DIAMETER_PT)
        _draw_ego(ax, layout.ego, size=design.EGO_DIAMETER_PT, label_pt=design.EGO_LABEL_PT)
        centre = (sum(p[0] for p in layout.positions.values()) / max(len(layout.positions), 1), layout.height / 2)
        _label_nodes(ax, layout.positions, edges, centre, obstacles_pt=((*_to_pt(ax, layout.ego), design.EGO_DIAMETER_PT / 2),), soft_data=soft,
                     font_pt=design.ID_PT, node_pt=design.NODE_DIAMETER_PT)
    return fig


# ---------------------------------------------------------------- comparison -------------------

@dataclass(frozen=True)
class GeoMeasures:
    crossings: int
    median_tie_length_share: float  # median tie length as a share of the picture's longer side (not a quality: only a reference)
    between_share_of_length: float  # share of the total tie length that the between-zone ties take
    min_node_distance: float  # relative to the median tie length
    ties_between_zones: int

    def summary(self) -> str:
        return (f"Kreuzungen {self.crossings} · Knotenabstand {self.min_node_distance:.2f} (rel. zur mittleren Beziehungslänge) · "
                f"Beziehungen zwischen Zonen {self.ties_between_zones}, deren Anteil an der Linienlänge {self.between_share_of_length:.0%}")


def measure_geo(positions: dict[str, tuple[float, float]], edges, between) -> GeoMeasures:
    pts = list(positions.values())
    side = max(max(p[0] for p in pts) - min(p[0] for p in pts), max(p[1] for p in pts) - min(p[1] for p in pts)) or 1.0
    lengths = [math.dist(positions[a], positions[b]) for a, b in edges]
    median = float(np.median(lengths)) if lengths else 0.0
    nearest = min((math.dist(p, q) for p, q in combinations(pts, 2)), default=0.0)
    between_set = {tuple(e) for e in between}
    total = sum(lengths) or 1.0
    between_len = sum(math.dist(positions[a], positions[b]) for a, b in edges if tuple((a, b)) in between_set)
    return GeoMeasures(layouts.count_crossings(positions, edges), median / side if side else 0.0, between_len / total,
                       nearest / median if median else 0.0, len(between_set))


def geographic_variants_figure(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams, *, network: Network):
    """The two G2 variants side by side, with readability measures (a working figure documenting the choice)."""
    with rc():
        views = contact_views(dataset, params)
        by_id = {v.contact_id: v for v in views}
        order = structure_order(network)
        within, between = classify_ties(network, views)
        edges = within + between
        fig = new_figure(16.5, 7.8)
        frame(
            fig,
            "Variantenvergleich G2: geografisch gegliedertes Beziehungsnetz",
            "Arbeitsabbildung zur Wahl von G2; beide Varianten zeigen dieselben Kontakte, Zonen und bestätigten Beziehungen",
            status,
            "Kreuzungen: Linienpaare, die sich schneiden (Linien mit gemeinsamem Kontakt ausgenommen). Die Kennzahlen vergleichen Darstellungen und sagen nichts über die Daten. "
            "Gewählt für G2: die Bänder (G2b) – klare Staffelung von Marburg bis außerhalb Europas, weniger Kreuzungen, größere Knotenabstände, Beziehungen zwischen Zonen als eigene, gut verfolgbare Linien; die Ringe (G2a) bündeln die Linien einer Gruppe auf engem Raum.",
        )
        rings = ring_layout(views, order)
        bands = band_layout(views, order)
        panels = (("G2a · konzentrische Zonen", rings.positions, "rings"), ("G2b · geografische Bänder", bands.positions, "bands"))
        for index, (title, positions, kind) in enumerate(panels):
            left = 0.015 + index * 0.495
            ax = fig.add_axes([left, 0.12, 0.47, 0.64])
            if kind == "rings":
                limit = rings.outer_radius + 0.3
                ax.set_xlim(-limit, limit)
                ax.set_ylim(-limit, limit)
                ax.set_aspect("equal")
                ax.axis("off")
                ax.apply_aspect()
                _draw_rings(ax, rings, params)
                _draw_ego(ax)
            else:
                _draw_bands(ax, bands, params, size=7.6)
                _draw_ego(ax, bands.ego)
            _draw_ties(ax, positions, within, between, ego=None, ego_lines=False)
            _draw_small_nodes(ax, positions, by_id, node_pt=9.0)
            _label_nodes(ax, positions, edges, (0.0, 0.0) if kind == "rings" else (bands.width / 2, bands.height / 2))
            measures = measure_geo(positions, edges, between)
            fig.text(left + 0.005, 0.885, title, fontsize=10.5, fontweight="bold", color=INK, ha="left", va="bottom")
            fig.text(left + 0.005, 0.87, wrap(measures.summary(), 88), fontsize=7.6, color=MUTED, ha="left", va="top")
    return fig
