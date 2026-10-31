"""G2-A and G2-B: the confirmed contact-contact ties of a personal network, arranged by where the contacts live.

Both figures answer one question: *how are local, supra-regional and transcontinental relations interwoven -- which
confirmed ties run within and which between geographic areas?* Both show the same contacts, the same five
residence categories (Marburg, Region Marburg, übriges Deutschland, übriges Europa, außerhalb Europas) and exactly the
confirmed contact-contact ties. **Ego has no lines**: ego is not part of the graph; in G2-B it is only the point of
reference in the centre. No tie is added, none is hidden, an undocumented pair stays unknown.

* **G2-A** -- geographic *bands* side by side, near to far from left to right. Band widths follow the number of contacts
  (a band with one contact stays narrow). Inside a band the height follows the order of the social structure.
* **G2-B** -- a *geographically constrained force layout*: the categories are radial zones around ego; the confirmed
  ties pull tied contacts together (an attraction along the tie), contacts repel each other, and the radius of a contact is
  bound to a narrow window around its zone. Social sub-networks keep their natural shape and reach across zones.

What the arrangement means -- and what not: a band or a radial zone is a **category**, never a distance in kilometres, a
degree of subjective closeness or a graph distance. The gaps between the zones are conventions of the drawing. Nothing here
measures integration or segregation, and nothing says why a tie runs where it does.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations

import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.patches import Ellipse, FancyBboxPatch, Rectangle

from mares.core import ids

from ..analysis import AnalysisParams, SurveyStatus
from ..build import Network
from ..geo import GeoCategory
from ..model import NetworkDataset
from . import design, geo_zones, layouts
from .common import ContactView, contact_views
from .geo_zones import (
    _draw_small_nodes, _draw_ties, _label_nodes, _spread, classify_ties, structure_order, tie_styles, zones_present,
)
from .network import _halo, _to_pt, build_structure
from .style import GEO_COLORS, INK, MUTED, new_figure, rc, wrap

HIGHLIGHT_DEFAULT = "between"

# ---------------------------------------------------------------- G2-A: bands ----------------------------------------
BAND_PAD = 0.55  # horizontal room at the edge of a band
BAND_COL_W = 1.30  # horizontal distance of two columns of one band (room for the id beside a node)
BAND_MIN_W = 1.95
BAND_GAP = 0.40
BAND_ROW_STEP = 0.62  # least vertical distance of two contacts in one column
BAND_PER_COLUMN = 5  # a band holds this many contacts per column before it gets another column
BAND_COLUMNS_MAX = 3


@dataclass(frozen=True)
class BandBox:
    category: GeoCategory
    x0: float
    x1: float
    members: tuple[str, ...]


@dataclass(frozen=True)
class BandsLayout:
    positions: dict[str, tuple[float, float]]
    bands: tuple[BandBox, ...]
    width: float
    height: float


def bands_layout(views: list[ContactView], order: list[str]) -> BandsLayout:
    """Bands from left (near) to right (far). A band is as wide as its contacts need, never wider; its contacts keep the
    circular order of the ties from top to bottom, so tied contacts stand at similar heights in neighbouring bands."""
    rank = {c: i for i, c in enumerate(order)}
    total = max(len(order) - 1, 1)
    zones = zones_present(views)
    members = {z: sorted((v.contact_id for v in views if v.geo is z), key=lambda c: rank.get(c, 0)) for z in zones}
    columns = {z: max(1, min(BAND_COLUMNS_MAX, math.ceil(len(members[z]) / BAND_PER_COLUMN))) for z in zones}
    rows = max((math.ceil(len(members[z]) / columns[z]) for z in zones), default=1)
    height = max(4.0, rows * BAND_ROW_STEP + 1.3)
    top, bottom = height - 0.65, 0.65
    positions: dict[str, tuple[float, float]] = {}
    boxes: list[BandBox] = []
    x = 0.0
    for zone in zones:
        n_cols = columns[zone]
        width = max(BAND_MIN_W, 2 * BAND_PAD + (n_cols - 1) * BAND_COL_W + 0.3)
        buckets: list[list[str]] = [[] for _ in range(n_cols)]
        for k, contact in enumerate(members[zone]):
            buckets[k % n_cols].append(contact)
        for c, bucket in enumerate(buckets):
            wanted = [-(top - (top - bottom) * rank.get(contact, 0) / total) for contact in bucket]
            ys = [-y for y in _spread(wanted, BAND_ROW_STEP, -top, -bottom)] if bucket else []
            cx = x + width / 2 + (c - (n_cols - 1) / 2) * BAND_COL_W
            for contact, y in zip(bucket, ys):
                positions[contact] = (round(cx, 9), round(y, 9))
        boxes.append(BandBox(zone, x, x + width, tuple(members[zone])))
        x += width + BAND_GAP
    return BandsLayout(positions, tuple(boxes), x - BAND_GAP, height)


def _draw_bands_a(ax, layout: BandsLayout, params: AnalysisParams, *, counts: bool) -> None:
    ax.set_xlim(-0.15, layout.width + 0.15)
    ax.set_ylim(-0.1, layout.height + 1.05)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.apply_aspect()
    for index, box in enumerate(layout.bands):
        ax.add_patch(FancyBboxPatch((box.x0, 0.0), box.x1 - box.x0, layout.height, boxstyle="round,pad=0,rounding_size=0.14",
                                    facecolor="#F4F6F8" if index % 2 == 0 else "#EEF1F4", edgecolor="none", zorder=1))
        caption = wrap(design.zone_name(box.category, params), 15) + (f"\nn = {len(box.members)}" if counts else "")
        ax.text((box.x0 + box.x1) / 2, layout.height + 0.12, caption, ha="center", va="bottom", fontsize=design.CAPTION_PT,
                fontweight="bold", color=INK, linespacing=1.2)


# ---------------------------------------------------------------- G2-B: radial force layout --------------------------
RING_STEP = 1.00  # distance of two zone centres (a convention of the drawing)
RING_FIRST = 1.45
MIN_CHORD = 0.92  # least comfortable distance of two contacts (picture units)
ASPECT = 1.3  # the drawing is stretched horizontally by this factor (the zones become ellipses): a convention to use a landscape page
WINDOW = 0.30  # contacts may deviate from their zone centre by this share of the ring step
GAP_DEG = 28.0  # free sector at 12 o'clock for the zone names
ITERATIONS = 900
OVERLAP_REPEL = 1.12


@dataclass(frozen=True)
class RingZone:
    category: GeoCategory
    centre: float
    inner: float
    outer: float
    members: tuple[str, ...]


@dataclass(frozen=True)
class RadialLayout:
    positions: dict[str, tuple[float, float]]
    zones: tuple[RingZone, ...]
    outer_radius: float  # vertical radius of the outermost zone; the horizontal one is ``ASPECT`` times larger
    score: float
    start: str  # which start gave the best result


def _zone_rings(views: list[ContactView], members_of: dict[GeoCategory, list[str]]) -> list[RingZone]:
    zones = zones_present(views)
    usable = (360.0 - 2 * GAP_DEG) / 360.0
    centres: list[float] = []
    for zone in zones:
        n = len(members_of[zone])
        need = n * MIN_CHORD / (2 * math.pi * usable)
        previous = centres[-1] + (RING_STEP if n else 1.0) if centres else RING_FIRST  # an empty zone stays visible, but narrow
        centres.append(max(previous, need))
    rings = []
    for index, zone in enumerate(zones):
        below = centres[index - 1] if index else 0.0
        above = centres[index + 1] if index + 1 < len(zones) else centres[index] + RING_STEP
        inner = (below + centres[index]) / 2 if index else max(0.0, centres[index] - RING_STEP / 2)
        outer = (centres[index] + above) / 2
        rings.append(RingZone(zone, centres[index], inner, outer, tuple(members_of[zone])))
    return rings


def _clamp_angle(theta_deg: np.ndarray, start: float, span: float) -> np.ndarray:
    relative = (theta_deg - start) % 360.0
    over = relative > span
    relative = np.where(over, np.where(relative > span + (360.0 - span) / 2, 0.0, span), relative)
    return start + relative


def _project(points: np.ndarray, centres: np.ndarray, half: np.ndarray, start: float, span: float) -> np.ndarray:
    radius = np.hypot(points[:, 0], points[:, 1])
    radius = np.clip(radius, centres - half, centres + half)
    theta = _clamp_angle(np.degrees(np.arctan2(points[:, 1], points[:, 0])), start, span)
    return np.column_stack([radius * np.cos(np.radians(theta)), radius * np.sin(np.radians(theta))])


def _relax(points: np.ndarray, edges: np.ndarray, rest: np.ndarray, centres: np.ndarray, half: np.ndarray, start: float, span: float) -> np.ndarray:
    n = len(points)
    for step in range(ITERATIONS):
        rate = 0.16 * (1.0 - step / ITERATIONS) + 0.015
        delta = points[:, None, :] - points[None, :, :]
        dist = np.hypot(delta[..., 0], delta[..., 1]) + np.eye(n) + 1e-9
        push = np.clip(OVERLAP_REPEL - dist, 0.0, None) * (1 - np.eye(n))
        force = ((push / dist)[..., None] * delta).sum(axis=1) * 1.0
        if len(edges):
            a, b = edges[:, 0], edges[:, 1]
            vec = points[b] - points[a]
            length = np.hypot(vec[:, 0], vec[:, 1]) + 1e-9
            pull = ((length - rest) * 0.55 / length)[:, None] * vec
            np.add.at(force, a, pull)
            np.add.at(force, b, -pull)
        points = _project(points + rate * force, centres, half, start, span)
    return points


def radial_layout(views: list[ContactView], network: Network, order: list[str] | None = None) -> RadialLayout:
    """Contacts around ego in radial zones by residence category; the ties decide the rest.

    Deterministic: sorted inputs, three fixed starts (the circular order of the ties, its mirror image and the angles of the
    B1/B2 layout), a fixed number of steps; the start with the best score wins (score = tie-length deviation + overlaps +
    crossings). The radius of a contact never leaves the window of its zone: the geographic meaning is kept."""
    order = order if order is not None else structure_order(network)
    names = sorted((v.contact_id for v in views), key=ids.contact_number)
    index = {c: i for i, c in enumerate(names)}
    zone_of = {v.contact_id: v.geo for v in views}
    members_of = {z: sorted((c for c in names if zone_of[c] is z), key=lambda c: order.index(c) if c in order else 0) for z in zones_present(views)}
    rings = _zone_rings(views, members_of)
    centre_of = {ring.category: ring.centre for ring in rings}
    centres = np.array([centre_of[zone_of[c]] for c in names])
    half = np.array([RING_STEP * WINDOW for _ in names])
    start, span = 90.0 + GAP_DEG, 360.0 - 2 * GAP_DEG
    edges = np.array([(index[t.a], index[t.b]) for t in network.positive_ties], dtype=int).reshape(-1, 2)
    rest = np.array([MIN_CHORD if zone_of[names[a]] is zone_of[names[b]] else abs(centres[a] - centres[b]) for a, b in edges])
    n = len(names)

    rank = {c: i for i, c in enumerate(order)}
    ranked = np.array([start + span * rank.get(c, 0) / max(len(order) - 1, 1) for c in names])
    structure = build_structure(network).positions
    cx = float(np.mean([structure[c][0] for c in names])) if names else 0.0
    cy = float(np.mean([structure[c][1] for c in names])) if names else 0.0
    from_structure = np.array([start + ((math.degrees(math.atan2(structure[c][1] - cy, structure[c][0] - cx)) - start) % 360.0) * span / 360.0 for c in names])
    starts = {"order": ranked, "mirror": 2 * start + span - ranked, "structure": from_structure}

    best: tuple[float, str, np.ndarray] | None = None
    for label, angles in starts.items():
        points = np.column_stack([centres * np.cos(np.radians(angles)), centres * np.sin(np.radians(angles))]) if n else np.zeros((0, 2))
        points = _relax(points, edges, rest, centres, half, start, span) if n else points
        positions = {c: (float(points[i, 0]), float(points[i, 1])) for i, c in enumerate(names)}
        stress = float(sum((math.dist(positions[names[a]], positions[names[b]]) - r) ** 2 for (a, b), r in zip(edges, rest)))
        overlap = sum(max(0.0, MIN_CHORD * 0.85 - math.dist(positions[p], positions[q])) ** 2 for p, q in combinations(names, 2)) * 20.0
        crossings = layouts.count_crossings(positions, [tuple((names[a], names[b])) for a, b in edges]) if len(edges) > 1 else 0
        score = stress + overlap + 0.8 * crossings
        if best is None or score < best[0] - 1e-9:
            best = (score, label, points)
    score, label, points = best if best else (0.0, "order", np.zeros((0, 2)))
    positions = {c: (round(float(points[i, 0]) * ASPECT, 9), round(float(points[i, 1]), 9)) for i, c in enumerate(names)}
    return RadialLayout(positions, tuple(rings), rings[-1].outer if rings else RING_FIRST, round(score, 6), label)


def _draw_rings_b(ax, layout: RadialLayout, params: AnalysisParams, *, counts: bool) -> None:
    limit = layout.outer_radius + 0.35
    ax.set_xlim(-limit * ASPECT, limit * ASPECT)
    ax.set_ylim(-limit, limit)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.apply_aspect()
    for index, ring in enumerate(layout.zones):
        if index % 2 == 0:  # a faint tint on every second annulus; no outlines of its own
            ax.add_patch(Ellipse((0, 0), 2 * ring.outer * ASPECT, 2 * ring.outer, facecolor="#F4F6F8", edgecolor="none", zorder=0.5 + 0.01 * (len(layout.zones) - index)))
        else:
            ax.add_patch(Ellipse((0, 0), 2 * ring.outer * ASPECT, 2 * ring.outer, facecolor="#FFFFFF", edgecolor="none", zorder=0.5 + 0.01 * (len(layout.zones) - index)))
        ax.add_patch(Ellipse((0, 0), 2 * ring.outer * ASPECT, 2 * ring.outer, facecolor="none", edgecolor="#C5CCD3", linewidth=0.8, linestyle=(0, (1.5, 3.0)), zorder=0.9))
    for ring in layout.zones:
        text = design.zone_name(ring.category, params) + (f"  (n = {len(ring.members)})" if counts else "")
        ax.text(0, ring.centre, text, ha="center", va="center", fontsize=design.CAPTION_PT, fontweight="bold", color=INK, zorder=3,
                path_effects=[_halo()])


# ---------------------------------------------------------------- the figures ---------------------------------------

def _hint(status: SurveyStatus, what: str) -> str:
    return (f"{what} sind Wohnort-Kategorien, keine Entfernungen. "
            + ("Paare ohne Linie sind ausdrücklich verneint." if status.completeness == "complete" else "Paare ohne Linie: unbekannt."))


def _legend_entries(within, between, highlight):
    styles = tie_styles(highlight)
    return [("line", styles["within"][0], "Beziehung innerhalb eines Bereichs"), ("line", styles["between"][0], "Beziehung zwischen Bereichen")]


def _note(status: SurveyStatus, within, between, extra: str) -> str:
    return (
        f"{len(within) + len(between)} bestätigte Beziehungen zwischen Kontakten, davon {len(within)} innerhalb und {len(between)} zwischen den geografischen Bereichen. "
        "Ego ist nicht Teil dieses Graphen und trägt keine Linien. Nicht eingezeichnete Paare sind unbekannt, nicht verneint (solange die Paarabdeckung nicht belegt ist). "
        + extra + " Die Bereiche sind Wohnort-Kategorien, keine Karte, kein Kilometermaß, keine subjektive Nähe (Abbildung A) und kein Netzwerk-Layout (B1–B3); "
        "die Anordnung misst weder Integration noch Segregation und erklärt nicht, warum Beziehungen so verlaufen."
    )


def geographic_bands_figure(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams, *, network: Network,
                            profile: str = "clean", highlight: str | None = HIGHLIGHT_DEFAULT):
    """G2-A: geographic bands, variable widths, no ego lines; ties between the bands stand out."""
    design.check_profile(profile)
    if highlight not in geo_zones.HIGHLIGHTS:
        raise ValueError("highlight is None, 'between' or 'within'")
    with rc():
        views = contact_views(dataset, params)
        by_id = {v.contact_id: v for v in views}
        within, between = classify_ties(network, views)
        edges = within + between
        layout = bands_layout(views, structure_order(network))
        width = 13.0
        x_span, y_span = layout.width + 0.3, layout.height + 1.15
        axes_h = width * 0.96 * y_span / x_span
        fig = new_figure(width, axes_h + 2.0)
        note = _note(status, within, between, "Die Höhe im Band folgt der Reihenfolge der sozialen Struktur (verbundene Kontakte stehen auf ähnlicher Höhe) und zeigt keine Nähe; "
                     "die Breite eines Bandes folgt der Zahl seiner Kontakte.")
        top, bottom = design.clean_frame(fig, "Geografische Verflechtung", "Beziehungen zwischen Kontakten, nach Wohnort", _hint(status, "Bereiche"), status, note=note, profile=profile)
        top = design.legend_strip(fig, _legend_entries(within, between, highlight), top=top)
        ax = fig.add_axes([0.02, bottom, 0.96, top - bottom])
        _draw_bands_a(ax, layout, params, counts=profile == "analysis")
        _draw_ties(ax, layout.positions, within, between, ego=None, ego_lines=False, highlight=highlight)
        _draw_small_nodes(ax, layout.positions, by_id, node_pt=design.NODE_DIAMETER_PT)
        centre = (layout.width / 2, layout.height / 2)
        _label_nodes(ax, layout.positions, edges, centre, font_pt=design.ID_PT, node_pt=design.NODE_DIAMETER_PT)
    return fig


def geographic_radial_figure(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams, *, network: Network,
                             profile: str = "clean", highlight: str | None = HIGHLIGHT_DEFAULT):
    """G2-B: the geographically constrained force layout around ego; ties between the zones stand out."""
    design.check_profile(profile)
    if highlight not in geo_zones.HIGHLIGHTS:
        raise ValueError("highlight is None, 'between' or 'within'")
    with rc():
        views = contact_views(dataset, params)
        by_id = {v.contact_id: v for v in views}
        within, between = classify_ties(network, views)
        edges = within + between
        layout = radial_layout(views, network)
        limit = layout.outer_radius + 0.35
        width = 10.5  # smaller than the other figures: with few contacts a large page would only enlarge the empty zones
        axes_h = width * 0.96 / ASPECT
        fig = new_figure(width, axes_h + 2.0)
        note = _note(status, within, between, "Die Anordnung ist ein kraftbasiertes Layout der bestätigten Beziehungen, dessen Abstand zu Ego an die Wohnort-Kategorie gebunden ist; "
                     "Winkel und Abstände innerhalb einer Zone tragen keine eigene Bedeutung. Der Abstand zwischen den Zonen ist eine grafische Konvention.")
        top, bottom = design.clean_frame(fig, "Geografische Verflechtung", "Kontakte um Ego nach Wohnort, Beziehungen zwischen Kontakten",
                                         _hint(status, "Ringe"), status, note=note, profile=profile)
        top = design.legend_strip(fig, _legend_entries(within, between, highlight), top=top)
        ax = fig.add_axes([0.02, bottom, 0.96, top - bottom])
        _draw_rings_b(ax, layout, params, counts=profile == "analysis")
        _draw_ties(ax, layout.positions, within, between, ego=None, ego_lines=False, highlight=highlight)
        _draw_small_nodes(ax, layout.positions, by_id, node_pt=design.NODE_DIAMETER_PT)
        geo_zones._draw_ego(ax, (0.0, 0.0), size=design.EGO_DIAMETER_PT, label_pt=design.EGO_LABEL_PT)
        _label_nodes(ax, layout.positions, edges, (0.0, 0.0), obstacles_pt=((*_to_pt(ax, (0.0, 0.0)), design.EGO_DIAMETER_PT / 2),),
                     font_pt=design.ID_PT, node_pt=design.NODE_DIAMETER_PT)
    return fig


# ---------------------------------------------------------------- comparison ---------------------------------------

@dataclass(frozen=True)
class ABMeasures:
    crossings: int
    min_node_distance: float  # relative to the median tie length
    between_ties: int
    group_compactness: float | None  # mean pairwise distance within a confirmed group / mean pairwise distance of all contacts (smaller = more compact)
    radius_deviation: float | None  # largest deviation of a contact from its zone's centre, as a share of the ring step (G2-B only)

    def summary(self) -> str:
        parts = [f"Kreuzungen {self.crossings}", f"Knotenabstand {self.min_node_distance:.2f}", f"Beziehungen zwischen Bereichen {self.between_ties}"]
        if self.group_compactness is not None:
            parts.append(f"Gruppenkompaktheit {self.group_compactness:.2f}")
        return " · ".join(parts)


def measure_ab(positions: dict[str, tuple[float, float]], network: Network, within, between) -> ABMeasures:
    edges = within + between
    base = geo_zones.measure_geo(positions, edges, between) if len(positions) > 1 and edges else None
    mean_all = _mean_pair_distance(list(positions))(positions)
    compact = []
    for _, members in network.confirmed_groups:
        members = [m for m in members if m in positions]
        if len(members) > 1 and mean_all:
            compact.append(_mean_pair_distance(members)(positions) / mean_all)
    return ABMeasures(base.crossings if base else 0, base.min_node_distance if base else 0.0, len(between),
                      float(np.mean(compact)) if compact else None, None)


def _mean_pair_distance(members: list[str]):
    def measure(positions: dict[str, tuple[float, float]]) -> float:
        pairs = list(combinations(members, 2))
        return float(np.mean([math.dist(positions[a], positions[b]) for a, b in pairs])) if pairs else 0.0

    return measure


def geographic_ab_comparison_figure(dataset: NetworkDataset, status: SurveyStatus, params: AnalysisParams, *, network: Network):
    """The two G2 variants side by side with readability measures: a working figure that documents the choice."""
    with rc():
        views = contact_views(dataset, params)
        by_id = {v.contact_id: v for v in views}
        within, between = classify_ties(network, views)
        edges = within + between
        order = structure_order(network)
        bands = bands_layout(views, order)
        radial = radial_layout(views, network, order)
        fig = new_figure(18.0, 9.4)
        figure_note = (
            "Kreuzungen: Linienpaare, die sich schneiden (Linien mit gemeinsamem Kontakt ausgenommen). Knotenabstand: kleinster Abstand zweier Kontakte relativ zur mittleren Beziehungslänge. "
            "Gruppenkompaktheit: mittlerer Abstand der Mitglieder einer erhobenen Gruppe relativ zum mittleren Abstand aller Kontakte (kleiner = die Gruppe bleibt zusammen). "
            "Die Kennzahlen vergleichen Darstellungen und sagen nichts über die Daten."
        )
        design.clean_frame(fig, "Variantenvergleich G2: geografische Verflechtung", "Arbeitsabbildung: dieselben Kontakte, Kategorien und bestätigten Beziehungen", figure_note, status, profile="analysis")
        panels = (("G2-A · geografische Bänder", bands.positions, "bands"), ("G2-B · geografisch eingeschränktes Kraftlayout", radial.positions, "radial"))
        for index, (title, positions, kind) in enumerate(panels):
            left = 0.015 + index * 0.495
            ax = fig.add_axes([left, 0.15, 0.47, 0.66])
            ax.set_anchor("N")
            if kind == "bands":
                _draw_bands_a(ax, bands, params, counts=False)
            else:
                _draw_rings_b(ax, radial, params, counts=False)
                geo_zones._draw_ego(ax, (0.0, 0.0), size=design.EGO_DIAMETER_PT, label_pt=design.EGO_LABEL_PT)
            _draw_ties(ax, positions, within, between, ego=None, ego_lines=False, highlight=HIGHLIGHT_DEFAULT)
            _draw_small_nodes(ax, positions, by_id, node_pt=10.0)
            _label_nodes(ax, positions, edges, (bands.width / 2, bands.height / 2) if kind == "bands" else (0.0, 0.0), font_pt=8.0, node_pt=10.0)
            measures = measure_ab(positions, network, within, between)
            fig.text(left + 0.005, 0.868, title, fontsize=design.TEXT_PT + 1, fontweight="bold", color=INK, ha="left", va="bottom")
            fig.text(left + 0.005, 0.862, wrap(measures.summary(), 100), fontsize=design.SMALL_PT, color=MUTED, ha="left", va="top")
    return fig
