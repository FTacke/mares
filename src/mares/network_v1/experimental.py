"""Experimental figures of network_v1 -- for evaluation only, not part of the eight standard figures.

X1 · Geografische Verteilung: where the contacts live, on regional map panels (Amerika, Europa, Deutschland; further
regions only when the data need them). No contact-contact and no ego lines; node colour = relation type, as in every
network figure. Contacts of one place sit in a small radial cluster around the place point; a contact whose residence is
known only by country sits at the country's label point inside a dashed ring (never at an invented city); contacts
without a usable residence are named in a note and not drawn.

Positions come from a hand-kept place directory (``ROOT:network_v1/reference/gazetteer.csv``: ``place; country_iso3;
lat; lon; basis``) in the same root as the case -- never from a geocoding service, so residence data never leave the
machine. Country borders and label points: Natural Earth admin 0 countries (public domain) in
``WORKSPACE:cache/basemaps``. Output: ``<case>/experimental/<case>_X1_geografische_verteilung.{png,svg}`` -- outside
``graphics/``, which holds the standard figures only; the run record goes to ``WORKSPACE/runs/<RUN-ID>/``.
"""

from __future__ import annotations

import csv
import io
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from matplotlib.patches import Circle, Polygon

from mares.core import ids
from mares.core.refs import StorageRef
from mares.core.roots import Roots
from mares.network_v0.figures.style import rc, save_figure

from .case import read_case
from .figures.base import INK, LABEL_PT, MUTED, NODE_PT, Context, draw_nodes, file_name, page, relation_entries, relation_fill, text_width
from .places import Area, norm
from .run import check_case_ref
from .validate import FAILED, validate

X1_CODE, X1_NAME = "X1", "geografische_verteilung"
EXPERIMENTAL_DIR = "experimental"
GAZETTEER = "network_v1/reference/gazetteer.csv"  # in the root of the case
BASEMAP = "cache/basemaps/ne_50m_admin_0_countries.geojson"  # in WORKSPACE
GAZETTEER_COLUMNS = ("place", "country_iso3", "lat", "lon", "basis")

NODE_R = NODE_PT / 72 / 2  # node radius in inches
NODE_STEP = 2 * NODE_R + 0.05  # centre distance of two nodes of one cluster
SINGLE_RING_MAX = 10  # up to this many contacts one ring around the place point, more in concentric rings
RING_R0 = 0.22  # radius of the innermost ring around the place point (inches); further rings one node step outside
LABEL_LINE_W = 1.7  # inches; a longer place list of a place group wraps
MERGE_IN = 0.12  # places closer than this on the map (inches, about 3 mm) form one place group
MAIN_W = 14.0
PANEL_GAP = 0.3
PANEL_H_MAX = 5.6
TITLE_H = 0.3  # room for the panel title inside the panel
GERMANY = (Area.MARBURG, Area.MITTELHESSEN, Area.GERMANY_OTHER)


@dataclass(frozen=True)
class Region:
    """A map panel: its title and default extent (lon, lat). The extent grows when a contact lies outside it."""

    key: str
    title: str
    lon: tuple[float, float]
    lat: tuple[float, float]


# Panels from left to right: Amerika, further regions (only when the data need them), Europa, Deutschland. Amerika, Europa
# and Deutschland are always shown, so every case has the same three panels.
REGIONS = (
    Region("americas", "Amerika", (-125.0, -32.0), (-56.0, 60.0)),
    Region("africa", "Afrika", (-20.0, 52.0), (-36.0, 38.0)),
    Region("asia", "Asien", (25.0, 150.0), (-10.0, 60.0)),
    Region("oceania", "Ozeanien", (110.0, 180.0), (-48.0, 0.0)),
    Region("other", "Weitere Regionen", (-180.0, 180.0), (-60.0, 80.0)),
    Region("europe", "Europa (ohne Deutschland)", (-11.0, 32.0), (34.0, 61.0)),
    Region("germany", "Deutschland", (5.5, 15.5), (47.0, 55.3)),
)
ALWAYS = ("germany", "europe", "americas")
CONTINENT_REGION = {"North America": "americas", "South America": "americas", "Africa": "africa", "Asia": "asia", "Oceania": "oceania"}


class X1Error(RuntimeError):
    """X1 cannot be drawn (no basemap, a malformed place directory ...)."""


# ------------------------------------------------------------------------------------------------- sources ---
def read_gazetteer(path: Path) -> dict[tuple[str, str], tuple[float, float]]:
    """(normalised place, ISO3) -> (lat, lon). A missing file is an empty directory; a malformed row is an error."""
    if not path.is_file():
        return {}
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig")), delimiter=";"))
    if rows and tuple(rows[0]) != GAZETTEER_COLUMNS:
        raise X1Error(f"gazetteer columns must be {'; '.join(GAZETTEER_COLUMNS)}")
    out = {}
    for i, row in enumerate(rows, start=2):
        try:
            lat, lon = float(row["lat"]), float(row["lon"])
        except (TypeError, ValueError) as error:
            raise X1Error(f"gazetteer line {i}: lat/lon must be numbers") from error
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise X1Error(f"gazetteer line {i}: lat/lon out of range")
        out[(norm(row["place"]), row["country_iso3"].strip().upper())] = (lat, lon)
    return out


def read_basemap(path: Path) -> dict[str, dict]:
    """Natural Earth admin 0 countries by ISO3 (``ADM0_A3``)."""
    if not path.is_file():
        raise X1Error(f"basemap missing: WORKSPACE:{BASEMAP} (see pilots/network_v1_map/README.md)")
    return {f["properties"]["ADM0_A3"]: f for f in json.loads(path.read_text(encoding="utf-8"))["features"]}


# -------------------------------------------------------------------------------------------------- layout ---
def ring_sizes(k: int) -> list[tuple[float, int]]:
    """(radius, number of nodes) of the rings for ``k`` contacts around a place point: inner rings full, the last one
    with the rest. One contact sits on the point itself."""
    if k == 1:
        return [(0.0, 1)]
    if k <= SINGLE_RING_MAX:  # one ring, just wide enough
        return [(max(RING_R0, k * NODE_STEP / (2 * math.pi)), k)]
    out, r = [], RING_R0
    while k:
        n = min(k, max(1, int(2 * math.pi * r / NODE_STEP)))
        out.append((r, n))
        k -= n
        r += NODE_STEP
    return out


@dataclass
class Cluster:
    """The contacts of one place -- or of a place group (places closer than MERGE_IN on the map), or of one country if
    only the country is known -- around one anchor."""

    region: str
    places: list[tuple[str, int]]  # (place as recorded, number of contacts), largest first; the country name if country_only
    anchor: tuple[float, float]  # lat, lon of the largest place
    members: list[str]
    country_only: bool = False
    point: tuple[float, float] = (0.0, 0.0)  # anchor in inches
    centre: tuple[float, float] = (0.0, 0.0)  # cluster centre in inches (moved off the point if clusters collide)

    @property
    def label(self) -> str:
        name, n = self.places[0]
        if self.country_only:
            return f"{name} · nur Land" + (f" · {n}" if n > 1 else "")
        if len(self.places) == 1:
            return name + (f" · {n}" if n > 1 else "")
        parts = [f"{p} {c}" if c > 1 else p for p, c in self.places]
        lines = [parts[0]]
        for part in parts[1:]:  # the place list in lines of at most LABEL_LINE_W
            if text_width(f"{lines[-1]} · {part}", LABEL_PT - 1.5) > LABEL_LINE_W:
                lines.append(part)
            else:
                lines[-1] += f" · {part}"
        return f"{name} u. a. · {len(self.members)}\n" + "\n".join(lines)

    @property
    def ring(self) -> float:
        return ring_sizes(len(self.members))[-1][0]

    @property
    def radius(self) -> float:
        return self.ring + NODE_R + (0.1 if self.country_only else 0.03)


@dataclass
class Panel:
    region: Region
    lon: tuple[float, float]
    lat: tuple[float, float]
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    count: int = 0

    @property
    def k(self) -> float:
        return math.cos(math.radians(sum(self.lat) / 2))

    @property
    def aspect(self) -> float:
        return (self.lon[1] - self.lon[0]) * self.k / (self.lat[1] - self.lat[0])

    def to_in(self, lat: float, lon: float) -> tuple[float, float]:
        return (self.x + (lon - self.lon[0]) / (self.lon[1] - self.lon[0]) * self.width,
                self.y + (lat - self.lat[0]) / (self.lat[1] - self.lat[0]) * self.height)


@dataclass
class X1Layout:
    panels: list[Panel]
    clusters: list[Cluster]
    positions: dict[str, tuple[float, float]]  # contact -> node centre (inches)
    unresolved: list[str] = field(default_factory=list)  # residence not assignable (places.py)
    not_in_gazetteer: list[str] = field(default_factory=list)  # a place without coordinates in the directory
    height: float = 0.0


def _region_of(ctx: Context, cid: str, countries: dict[str, dict]) -> str | None:
    area = ctx.derived.area(cid)
    if area in GERMANY:
        return "germany"
    if area is Area.EUROPE_OTHER:
        return "europe"
    if area is Area.OUTSIDE_EUROPE:
        feature = countries.get(ctx.case.contact(cid).residence_country_iso3)
        continent = feature["properties"].get("CONTINENT") if feature else None
        return CONTINENT_REGION.get(continent, "other")
    return None


def _member_order(ctx: Context, members: list[str], place_rank: dict[str, int]) -> list[str]:
    """Around the point: by place (largest first, in a place group), then by relation type (as in G1), then by ID."""
    def key(cid):
        cell = ctx.case.contact(cid).relation_type
        return (place_rank.get(cid, 0), cell.value if cell.recorded else "9", cid)
    return sorted(members, key=key)


def _ring_positions(c: Cluster) -> list[tuple[float, float]]:
    out = []
    for j, (r, n) in enumerate(ring_sizes(len(c.members))):
        for i in range(n):
            t = math.pi / 2 - 2 * math.pi * (i + 0.5 * j) / n  # clockwise from the top; every second ring turned by half a step
            out.append((c.centre[0] + r * math.cos(t), c.centre[1] + r * math.sin(t)))
    return out


def _merge(clusters: list[Cluster]) -> list[Cluster]:
    """Place clusters of one panel whose points lie closer than MERGE_IN form one place group (single linkage), anchored
    at the point of its largest place. Country-only clusters are never merged."""
    parent = list(range(len(clusters)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, a in enumerate(clusters):
        for j in range(i + 1, len(clusters)):
            b = clusters[j]
            if a.country_only or b.country_only:
                continue
            if math.hypot(a.point[0] - b.point[0], a.point[1] - b.point[1]) < MERGE_IN:
                parent[find(j)] = find(i)
    groups: dict[int, list[Cluster]] = {}
    for i, c in enumerate(clusters):
        groups.setdefault(find(i), []).append(c)
    out = []
    for parts in groups.values():
        parts.sort(key=lambda c: (-len(c.members), c.places[0][0]))
        head = parts[0]
        out.append(Cluster(head.region, [pl for c in parts for pl in c.places], head.anchor, [m for c in parts for m in c.members],
                           head.country_only, head.point, head.point))
    return sorted(out, key=lambda c: (-len(c.members), c.places[0][0]))


def _separate(clusters: list[Cluster], panel: Panel) -> None:
    """Place the clusters of one panel without overlap: the largest first at its point, every further one at the free
    position closest to its point (searched on a spiral around it), inside the panel and below its title. Deterministic."""
    placed: list[Cluster] = []
    for c in clusters:  # already ordered: largest first, then by label
        r = c.radius
        x0, x1 = panel.x + r + 0.04, panel.x + panel.width - r - 0.04
        y0, y1 = panel.y + r + 0.04, panel.y + panel.height - TITLE_H - r - 0.04
        px, py = min(max(c.point[0], x0), x1), min(max(c.point[1], y0), y1)
        best = None
        for step in range(400):
            d = step * 0.03
            n = 1 if step == 0 else 24
            for i in range(n):
                t = math.pi / 2 + 2 * math.pi * i / n
                x, y = px + d * math.cos(t), py + d * math.sin(t)
                if not (x0 <= x <= x1 and y0 <= y <= y1):
                    continue
                if all(math.hypot(x - o.centre[0], y - o.centre[1]) >= r + o.radius + 0.06 for o in placed):
                    best = (x, y)
                    break
            if best:
                break
        c.centre = best or (px, py)
        placed.append(c)


def x1_layout(ctx: Context, gazetteer: dict, countries: dict[str, dict]) -> X1Layout:
    """Clusters per place (or country), panels per region, node positions. Deterministic."""
    unresolved, missing = [], []
    found: dict[tuple, Cluster] = {}
    for c in ctx.case.contacts:
        region = _region_of(ctx, c.id, countries)
        if region is None:
            unresolved.append(c.id)
            continue
        place, iso = c.residence_place.strip(), c.residence_country_iso3
        if place:
            point = gazetteer.get((norm(place), iso))
            if point is None:
                missing.append(c.id)
                continue
            key, label, country_only = (region, norm(place), iso), place, False
        else:  # only the country is known: its label point, never a city
            props = countries.get(iso, {}).get("properties")
            if not props:
                missing.append(c.id)
                continue
            point = (props["LABEL_Y"], props["LABEL_X"])
            key, label, country_only = (region, "", iso), props.get("NAME_DE") or c.residence_country, True
        found.setdefault(key, Cluster(region, [(label, 0)], point, [], country_only)).members.append(c.id)
    clusters = sorted(found.values(), key=lambda cl: (-len(cl.members), cl.places[0][0]))
    for cl in clusters:
        cl.places = [(cl.places[0][0], len(cl.members))]
    used = {cl.region for cl in clusters}
    panels = []
    for region in REGIONS:
        if region.key not in ALWAYS and region.key not in used:
            continue
        lats = [cl.anchor[0] for cl in clusters if cl.region == region.key]
        lons = [cl.anchor[1] for cl in clusters if cl.region == region.key]
        lon = (min([region.lon[0]] + [x - 2 for x in lons]), max([region.lon[1]] + [x + 2 for x in lons]))
        lat = (min([region.lat[0]] + [y - 2 for y in lats]), max([region.lat[1]] + [y + 2 for y in lats]))
        panels.append(Panel(region, (max(lon[0], -180.0), min(lon[1], 180.0)), (max(lat[0], -85.0), min(lat[1], 85.0))))
    height = min(PANEL_H_MAX, (MAIN_W - PANEL_GAP * (len(panels) - 1)) / sum(p.aspect for p in panels))
    x = (MAIN_W - sum(p.aspect * height for p in panels) - PANEL_GAP * (len(panels) - 1)) / 2
    for p in panels:
        p.x, p.y, p.width, p.height = x, 0.0, p.aspect * height, height
        p.count = sum(len(cl.members) for cl in clusters if cl.region == p.region.key)
        x += p.width + PANEL_GAP
    by_key = {p.region.key: p for p in panels}
    for cl in clusters:
        cl.point = cl.centre = by_key[cl.region].to_in(*cl.anchor)
    merged = []
    for p in panels:
        merged += _merge([cl for cl in clusters if cl.region == p.region.key])
    clusters = merged
    for cl in clusters:
        rank, start = {}, 0
        for i, (_place, n) in enumerate(cl.places):
            for cid in cl.members[start:start + n]:
                rank[cid] = i
            start += n
        cl.members = _member_order(ctx, cl.members, rank)
    for p in panels:
        _separate([cl for cl in clusters if cl.region == p.region.key], p)
    positions = {}
    for cl in clusters:
        positions.update(zip(cl.members, _ring_positions(cl)))
    return X1Layout(panels, clusters, positions, unresolved, missing, height)


# ------------------------------------------------------------------------------------------------- drawing ---
def _rings(geometry: dict):
    if geometry["type"] == "Polygon":
        yield geometry["coordinates"][0]
    elif geometry["type"] == "MultiPolygon":
        for polygon in geometry["coordinates"]:
            yield polygon[0]


def _basemap(figure, main, panel: Panel, countries: dict[str, dict]) -> None:
    """The panel as an axes of its own in lon/lat (it clips the countries), below the main area that carries the nodes.
    The x axis is stretched by the cosine of the middle latitude (equirectangular)."""
    box = main.get_position()
    fw, fh = figure.get_figwidth(), figure.get_figheight()
    mw, mh = box.width * fw, box.height * fh
    ax = figure.add_axes((box.x0 + panel.x / mw * box.width, box.y0 + panel.y / mh * box.height,
                          panel.width / mw * box.width, panel.height / mh * box.height), zorder=0)
    ax.set_xlim(*panel.lon)
    ax.set_ylim(*panel.lat)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("#F4F7FA")  # sea
    for spine in ax.spines.values():
        spine.set_edgecolor("#C9CED3")
        spine.set_linewidth(0.7)
    home = "DEU" if panel.region.key == "germany" else None
    for iso, feature in countries.items():
        fill = "#E1E6EB" if iso != home else "#ECEFF2"
        if panel.region.key == "europe" and iso == "DEU":
            fill = "#EEF1F4"  # shown in its own panel
        for ring in _rings(feature["geometry"]):
            ax.add_patch(Polygon(ring, closed=True, facecolor=fill, edgecolor="#FFFFFF", linewidth=0.5))


def _label_box(x: float, y: float, text: str, size: float, ha: str, va: str) -> tuple[float, float, float, float]:
    w, h = text_width(text, size) + 0.04, size / 72 * 1.3 * (text.count("\n") + 1)
    x0 = x - w / 2 if ha == "center" else (x if ha == "left" else x - w)
    y0 = y if va == "bottom" else (y - h if va == "top" else y - h / 2)
    return x0, y0, x0 + w, y0 + h


def _overlaps(a, b) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


LABEL_SIZE = LABEL_PT - 1.5
LABEL_DISTANCES = (0.03, 0.2, 0.45, 0.75)  # inches between a cluster and its label; from 0.45 on with a fine line


def _box_point(box, x: float, y: float) -> tuple[float, float]:
    return min(max(x, box[0]), box[2]), min(max(y, box[1]), box[3])


def place_labels(layout: X1Layout) -> list[tuple[tuple[float, float, float, float], tuple[float, float] | None]]:
    """Per cluster (in layout order) a label box (inches) beside the cluster, in eight directions and four distances: the
    one with no node, no place point, no panel title and no other label under it, inside its panel and close to its
    cluster; otherwise the one with the fewest collisions. Second value: the point of the cluster edge a fine line goes
    to (None when the label sits right at the cluster)."""
    nodes = [(x - NODE_R, y - NODE_R, x + NODE_R, y + NODE_R) for x, y in layout.positions.values()]
    points = [(cl.point[0] - 0.04, cl.point[1] - 0.04, cl.point[0] + 0.04, cl.point[1] + 0.04) for cl in layout.clusters]
    discs = [(c.centre[0] - c.radius - 0.08, c.centre[1] - c.radius - 0.08, c.centre[0] + c.radius + 0.08, c.centre[1] + c.radius + 0.08)
             for c in layout.clusters]
    taken = [_label_box(pn.x + 0.08, pn.y + pn.height - 0.07, f"{pn.region.title} · n = {pn.count}", LABEL_PT, "left", "top")
             for pn in layout.panels]
    out = []
    for cl in layout.clusters:
        panel = next(pn for pn in layout.panels if pn.region.key == cl.region)
        x0, y0, x1, y1 = _label_box(0, 0, cl.label, LABEL_SIZE, "left", "bottom")
        w, h = x1 - x0, y1 - y0
        cx, cy, r = cl.centre[0], cl.centre[1], cl.radius
        best = None
        for rank, d in enumerate(LABEL_DISTANCES):
            for k in range(8):
                t = math.pi / 2 - math.pi / 4 * k  # N, NE, E, ... clockwise
                ux, uy = math.cos(t), math.sin(t)
                ux, uy = (0.0 if abs(ux) < 1e-9 else ux), (0.0 if abs(uy) < 1e-9 else uy)
                bx = cx + ux * (r + d) + (w / 2 * (1 if ux > 0 else -1) if ux else 0.0)
                by = cy + uy * (r + d) + (h / 2 * (1 if uy > 0 else -1) if uy else 0.0)
                box = (bx - w / 2, by - h / 2, bx + w / 2, by + h / 2)
                inside = panel.x + 0.03 <= box[0] and box[2] <= panel.x + panel.width - 0.03 and panel.y + 0.03 <= box[1] \
                    and box[3] <= panel.y + panel.height - 0.03
                foreign = sum(_overlaps(box, q) for q, other in zip(discs, layout.clusters) if other is not cl)  # reads as theirs
                cost = (sum(_overlaps(box, n) for n in nodes) * 10 + sum(_overlaps(box, q) for q in points) * 4 + foreign * 6
                        + sum(_overlaps(box, q) for q in taken) * 10 + (0 if inside else 20) + rank * 1.5 + k * 0.01)
                if best is None or cost < best[0]:
                    best = (cost, box, rank, (cx + ux * r, cy + uy * r))
        _, box, rank, edge = best
        taken.append(box)
        out.append((box, edge if LABEL_DISTANCES[rank] >= 0.45 else None))
    return out


def x1(ctx: Context, gazetteer: dict, countries: dict[str, dict]):
    layout = x1_layout(ctx, gazetteer, countries)
    country_only = any(cl.country_only for cl in layout.clusters)
    sections = [
        ("Beziehungstyp", relation_entries(ctx.case)),
        (None, [("dot", "Wohnort (Ortspunkt)", "#1F2933")]
               + ([("area", "nur Wohnland bekannt (Lage unscharf)", {"facecolor": "none", "edgecolor": MUTED, "linewidth": 0.8,
                                                                     "linestyle": (0, (3, 2))})] if country_only else [])),
    ]
    first = ("Experimentelle Zusatzgrafik, keine Standardgrafik. Lage = Wohnort; Kontakte eines Ortes um den Ortspunkt "
             "gruppiert" + ("; auf der Karte sehr nahe Orte als Ortsgruppe („u. a.“)" if any(len(cl.places) > 1 for cl in layout.clusters)
                            else "") + ". Keine Verbindungslinien (siehe G2). Karte: Natural Earth.")
    missing = []
    if layout.unresolved:
        missing.append(f"Wohnort nicht darstellbar: {', '.join(layout.unresolved)}.")
    if layout.not_in_gazetteer:
        missing.append(f"Ort ohne Koordinaten im Ortsverzeichnis: {', '.join(layout.not_in_gazetteer)}.")
    p = page(ctx, f"{X1_CODE} · Geografische Verteilung des persönlichen Netzwerks",
             "Wo leben die Kontakte? Wohnorte nach Region (experimentell)",
             main_w=MAIN_W, main_h=layout.height, legend="bottom", sections=sections, notes=[first, " ".join(missing)])
    ax = p.main
    ax.set_zorder(2)  # nodes above the map panels
    ax.patch.set_alpha(0.0)
    for panel in layout.panels:
        _basemap(p.figure, ax, panel, countries)
        ax.text(panel.x + 0.08, panel.y + panel.height - 0.07, f"{panel.region.title} · n = {panel.count}", fontsize=LABEL_PT,
                fontweight="bold", color=INK, ha="left", va="top", zorder=8)
    for cl in layout.clusters:
        if cl.country_only:
            ax.add_patch(Circle(cl.centre, cl.radius, fill=False, edgecolor=MUTED, linewidth=0.8, linestyle=(0, (3, 2)), zorder=3))
        if math.hypot(cl.centre[0] - cl.point[0], cl.centre[1] - cl.point[1]) > 0.02:  # the cluster gave way: line to its point
            ax.plot(*zip(cl.point, cl.centre), color="#8A939C", linewidth=0.5, zorder=3, gid="leader")
        ax.add_patch(Circle(cl.point, 0.035, facecolor="#1F2933", edgecolor="none", zorder=3.5))
    for cl, (box, anchor) in zip(layout.clusters, place_labels(layout)):
        if anchor:  # a label away from its cluster: a fine line to the cluster's edge
            ax.plot(*zip(anchor, _box_point(box, *anchor)), color="#AEB6BE", linewidth=0.5, zorder=3, gid="label-leader")
        ax.text((box[0] + box[2]) / 2, (box[1] + box[3]) / 2, cl.label, fontsize=LABEL_SIZE, color=INK, ha="center", va="center",
                zorder=8, multialignment="center", bbox={"boxstyle": "round,pad=0.06", "facecolor": "white", "alpha": 0.8, "edgecolor": "none"})
    draw_nodes(ax, layout.positions, {cid: relation_fill(ctx.case, cid) for cid in layout.positions}, zorder=5)
    return p.figure


# ----------------------------------------------------------------------------------------------------- run ---
@dataclass(frozen=True)
class X1Result:
    case_ref: StorageRef
    status: str  # COMPLETED | FAILED_VALIDATION
    outputs: list[str]
    run_id: str
    layout: X1Layout | None


def render_x1(roots: Roots, case_ref: StorageRef, *, formats: tuple[str, ...] = ("png", "svg")) -> X1Result:
    """Draw X1 for one case into ``<case>/experimental/``. A case with validation errors gets no figure. Replaces only its
    own X1 files; the standard figures in ``graphics/`` are not touched."""
    check_case_ref(case_ref)
    folder = roots.resolve(case_ref)
    case = read_case(folder)
    validation = validate(case)
    gazetteer = read_gazetteer(roots.resolve(StorageRef(case_ref.root, GAZETTEER)))  # sources first: no empty run folder
    countries = read_basemap(roots.resolve(StorageRef("WORKSPACE", BASEMAP)))
    run_id = ids.new_run_id(datetime.now(timezone.utc))
    run_dir = roots.resolve(StorageRef("WORKSPACE", f"runs/{run_id}"), writable=True)
    run_dir.mkdir(parents=True, exist_ok=False)
    record = {"format": "mares-run-record/v0-draft", "pipeline": "network_v1 experimental X1", "run_id": run_id,
              "case": {"ref": f"{case_ref.root}:{case_ref.rel}", "code": case.code}, "standard_figure": False,
              "sources": {"gazetteer": f"{case_ref.root}:{GAZETTEER}", "basemap": f"WORKSPACE:{BASEMAP}",
                          "basemap_source": "Natural Earth 1:50m admin 0 countries (public domain)"}}
    if validation.status == FAILED:
        record.update(status="FAILED_VALIDATION", outputs=[])
        (run_dir / "run_record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return X1Result(case_ref, "FAILED_VALIDATION", [], run_id, None)
    ctx = Context(case, validation.derived)
    target = roots.resolve(case_ref.child(EXPERIMENTAL_DIR), writable=True)
    target.mkdir(exist_ok=True)
    stem = target / file_name(case.code, X1_CODE, X1_NAME, "png")[:-4]
    with rc():
        layout = x1_layout(ctx, gazetteer, countries)
        written = save_figure(x1(ctx, gazetteer, countries), stem, formats)
    outputs = [p.name for p in written]
    record.update(status="COMPLETED", outputs=[f"{EXPERIMENTAL_DIR}/{n}" for n in outputs],
                  placed=len(layout.positions), unresolved=layout.unresolved, not_in_gazetteer=layout.not_in_gazetteer,
                  country_only=[cid for cl in layout.clusters if cl.country_only for cid in cl.members],
                  panels=[pn.region.key for pn in layout.panels])
    (run_dir / "run_record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return X1Result(case_ref, "COMPLETED", outputs, run_id, layout)
