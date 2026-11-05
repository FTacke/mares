"""Experimental figures of network_v1 -- for evaluation only, not part of the eight standard figures.

X1 · Geografische Verteilung (version 2): where the contacts live, on regional map panels (Amerika, Europa, Deutschland;
further regions only when the data need them). No contact-contact and no ego lines; node colour = relation type, as in
every network figure. The contacts of one place -- or of a place group ("Marburg und Umgebung": places within
UMGEBUNG_KM of each other or falling together on the map) -- sit in rings around the place point on a very pale disc; a
small place box names the place and is tied to the point by a fine leader that runs through a gap in the rings. A
contact whose residence is known only by country sits at the country's label point inside a dashed ring (never at an
invented city); contacts without a usable residence are named in a note and not drawn.

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

from matplotlib.patches import Circle, FancyBboxPatch, Polygon

from mares.core import ids
from mares.core.refs import StorageRef
from mares.core.roots import Roots
from mares.network_v0.figures.style import rc, save_figure

from .case import read_case
from .figures.base import INK, LABEL_PT, MUTED, NODE_PT, Context, draw_nodes, file_name, page, relation_entries, relation_fill, text_width
from .places import Area, norm
from .run import check_case_ref
from .validate import FAILED, validate

X1_CODE, X1_NAME, X1_VERSION = "X1", "geografische_verteilung", 2
EXPERIMENTAL_DIR = "experimental"
GAZETTEER = "network_v1/reference/gazetteer.csv"  # in the root of the case
BASEMAP = "cache/basemaps/ne_50m_admin_0_countries.geojson"  # in WORKSPACE
GAZETTEER_COLUMNS = ("place", "country_iso3", "lat", "lon", "basis")

NODE_R = NODE_PT / 72 / 2  # node radius in inches
NODE_STEP = 2 * NODE_R + 0.035  # centre distance of two nodes of one place
SINGLE_RING_MAX = 10  # up to this many contacts one ring around the place point, more in rings of 6, 12, ... slots
RING_R0 = 0.22  # smallest ring radius (inches): the place point and the leader stay visible
DISC_PAD = 0.07  # the pale disc of a place reaches this far beyond its nodes
UMGEBUNG_KM = 20.0  # places at most this far apart form a place group ("… und Umgebung")
MERGE_IN = 0.12  # ... and so do places closer than this on the map (inches, about 3 mm)
MAIN_W = 14.5
PANEL_GAP = 0.3
OTHER_SCALE = 0.8  # the other panels are this high relative to the Germany panel
GERMANY_H_MAX = 7.0
TITLE_H = 0.32  # room for the panel title inside the panel
BOX_PT = LABEL_PT - 1.0  # first line of a place box
BOX_SUB_PT = LABEL_PT - 2.5  # list of places of a place group
BOX_LINE_W = 1.7  # inches; a longer place list wraps
BOX_PAD = 0.05
GERMANY = (Area.MARBURG, Area.MITTELHESSEN, Area.GERMANY_OTHER)
POINT = "#1F2933"


@dataclass(frozen=True)
class Region:
    """A map panel: title and default extent (lon, lat). The extent grows to take in every place of the case."""

    key: str
    title: str
    lon: tuple[float, float]
    lat: tuple[float, float]


# Panels from left to right: Amerika, further regions (only when the data need them), Europa, Deutschland. Amerika, Europa
# and Deutschland are always shown. Amerika by default from Mexico to the south; it reaches north only for contacts in the
# USA or Canada. Europa by default from Portugal to a little east of Germany.
REGIONS = (
    Region("americas", "Amerika", (-118.0, -34.0), (-56.0, 33.0)),
    Region("africa", "Afrika", (-20.0, 52.0), (-36.0, 38.0)),
    Region("asia", "Asien", (25.0, 150.0), (-10.0, 60.0)),
    Region("oceania", "Ozeanien", (110.0, 180.0), (-48.0, 0.0)),
    Region("other", "Weitere Regionen", (-180.0, 180.0), (-60.0, 80.0)),
    Region("europe", "Europa (ohne Deutschland)", (-10.5, 19.5), (35.0, 59.0)),
    Region("germany", "Deutschland", (5.5, 15.5), (47.0, 55.3)),
)
ALWAYS = ("germany", "europe", "americas")
EXTENT_MARGIN = 8.0  # degrees added beyond a place outside (or at the edge of) the default extent
EXTENT_INSET = 1.0  # a place closer than this to the edge of the default extent widens it
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
def ring_slots(k: int) -> list[tuple[float, int]]:
    """(radius, slots) of the rings for ``k`` contacts. Every ring keeps one slot free for the leader of the place box;
    a single contact sits on the place point (no ring)."""
    if k == 1:
        return [(0.0, 1)]
    if k <= SINGLE_RING_MAX:
        return [(max(RING_R0, (k + 1) * NODE_STEP / (2 * math.pi)), k + 1)]
    out, left, j = [], k, 1
    while left:
        slots = 6 * j
        n = min(left, slots - 1)
        out.append((j * NODE_STEP, slots if n == slots - 1 else n + 1))
        left -= n
        j += 1
    return out


def _km(a: tuple[float, float], b: tuple[float, float]) -> float:
    (la1, lo1), (la2, lo2) = (tuple(map(math.radians, a)), tuple(map(math.radians, b)))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


@dataclass
class Place:
    """The contacts of one place -- or of a place group, or of one country if only the country is known."""

    region: str
    places: list[tuple[str, int]]  # (place as recorded, contacts), largest first; the country name if country_only
    anchor: tuple[float, float]  # lat, lon of the largest place
    members: list[str]
    country_only: bool = False
    point: tuple[float, float] = (0.0, 0.0)  # true place point in inches
    hub: tuple[float, float] = (0.0, 0.0)  # centre of the rings (= point unless the place had to give way)
    box: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # place box (inches)
    gap: float = math.pi / 2  # direction of the leader from the hub (radians)

    @property
    def group(self) -> bool:
        return len(self.places) > 1

    @property
    def title(self) -> str:
        name, n = self.places[0]
        total = len(self.members)
        if self.country_only:
            return f"{name} · nur Land bekannt" + (f" · n = {total}" if total > 1 else "")
        if self.group:
            return f"{name} und Umgebung · n = {total}"
        return name + (f" · n = {total}" if total > 1 else "")

    @property
    def sub(self) -> str:
        """The places of a place group (multi-line), empty otherwise."""
        if not self.group:
            return ""
        parts = [f"{p} {c}" if c > 1 else p for p, c in self.places]
        lines = [parts[0]]
        for part in parts[1:]:
            if text_width(f"{lines[-1]} · {part}", BOX_SUB_PT) > BOX_LINE_W:
                lines.append(part)
            else:
                lines[-1] += f" · {part}"
        return "\n".join(lines)

    @property
    def ring(self) -> float:
        return ring_slots(len(self.members))[-1][0]

    @property
    def radius(self) -> float:
        """Radius of the pale disc (and of the place in the collision tests)."""
        return self.ring + NODE_R + (DISC_PAD if len(self.members) > 1 or self.country_only else 0.02)

    def box_size(self) -> tuple[float, float]:
        w = text_width(self.title, BOX_PT, bold=True)
        h = BOX_PT / 72 * 1.35
        if self.sub:
            w = max(w, max(text_width(line, BOX_SUB_PT) for line in self.sub.split("\n")))
            h += (self.sub.count("\n") + 1) * BOX_SUB_PT / 72 * 1.3
        return w + 2 * BOX_PAD, h + 2 * BOX_PAD


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

    @property
    def title(self) -> str:
        return f"{self.region.title} · n = {self.count}"

    def to_in(self, lat: float, lon: float) -> tuple[float, float]:
        return (self.x + (lon - self.lon[0]) / (self.lon[1] - self.lon[0]) * self.width,
                self.y + (lat - self.lat[0]) / (self.lat[1] - self.lat[0]) * self.height)

    def title_box(self) -> tuple[float, float, float, float]:
        top = self.y + self.height
        return self.x, top - TITLE_H, self.x + text_width(self.title, LABEL_PT, bold=True) + 0.2, top


@dataclass
class X1Layout:
    panels: list[Panel]
    places: list[Place]
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


def _overlaps(a, b) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _box_hits_disc(box, centre, r) -> bool:
    x = min(max(centre[0], box[0]), box[2])
    y = min(max(centre[1], box[1]), box[3])
    return math.hypot(x - centre[0], y - centre[1]) < r


def _segment_hits_disc(p, q, centre, r) -> bool:
    (x0, y0), (x1, y1) = p, q
    dx, dy = x1 - x0, y1 - y0
    t = max(0.0, min(1.0, ((centre[0] - x0) * dx + (centre[1] - y0) * dy) / (dx * dx + dy * dy or 1e-12)))
    return math.hypot(x0 + t * dx - centre[0], y0 + t * dy - centre[1]) < r


def _box_point(box, x: float, y: float) -> tuple[float, float]:
    return min(max(x, box[0]), box[2]), min(max(y, box[1]), box[3])


def _group(places: list[Place]) -> list[Place]:
    """Places of one panel within UMGEBUNG_KM of each other, or closer than MERGE_IN on the map, form one place group
    (single linkage) at the point of its largest place. Country-only places are never grouped."""
    parent = list(range(len(places)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, a in enumerate(places):
        for j in range(i + 1, len(places)):
            b = places[j]
            if a.country_only or b.country_only:
                continue
            near_map = math.hypot(a.point[0] - b.point[0], a.point[1] - b.point[1]) < MERGE_IN
            if near_map or _km(a.anchor, b.anchor) <= UMGEBUNG_KM:
                parent[find(j)] = find(i)
    groups: dict[int, list[Place]] = {}
    for i, p in enumerate(places):
        groups.setdefault(find(i), []).append(p)
    out = []
    for parts in groups.values():
        parts.sort(key=lambda p: (-len(p.members), p.places[0][0]))
        head = parts[0]
        out.append(Place(head.region, [pl for p in parts for pl in p.places], head.anchor, [m for p in parts for m in p.members],
                         head.country_only, head.point, head.point))
    return sorted(out, key=lambda p: (-len(p.members), p.places[0][0]))


def _separate(places: list[Place], panel: Panel) -> None:
    """Place the discs of one panel without overlap: the largest first at its point, every further one at the free position
    closest to its point (spiral search), inside the panel and below its title. Deterministic."""
    done: list[Place] = []
    title = panel.title_box()
    for p in places:
        r = p.radius
        x0, x1 = panel.x + r + 0.05, panel.x + panel.width - r - 0.05
        y0, y1 = panel.y + r + 0.05, panel.y + panel.height - r - 0.05
        px, py = min(max(p.point[0], x0), x1), min(max(p.point[1], y0), y1)
        best = None
        for step in range(500):
            d = step * 0.03
            n = 1 if step == 0 else 24
            for i in range(n):
                t = math.pi / 2 + 2 * math.pi * i / n
                x, y = px + d * math.cos(t), py + d * math.sin(t)
                if not (x0 <= x <= x1 and y0 <= y <= y1) or _box_hits_disc(title, (x, y), r + 0.04):
                    continue
                if all(math.hypot(x - o.hub[0], y - o.hub[1]) >= r + o.radius + 0.08 for o in done):
                    best = (x, y)
                    break
            if best:
                break
        p.hub = best or (px, py)
        done.append(p)


BOX_DISTANCES = (0.12, 0.3, 0.55, 0.85)  # inches between a disc and its place box


def _place_boxes(places: list[Place], panels: list[Panel]) -> None:
    """A box per place beside its disc, in eight directions and four distances: not on any disc, place point, panel title
    or other box, inside its panel, its leader not across another disc; close to its place."""
    taken = [pn.title_box() for pn in panels]
    for p in places:
        panel = next(pn for pn in panels if pn.region.key == p.region)
        w, h = p.box_size()
        best = None
        for rank, d in enumerate(BOX_DISTANCES):
            for k in range(8):
                t = math.pi / 2 - math.pi / 4 * k  # N, NE, E, ... clockwise
                ux, uy = round(math.cos(t), 9), round(math.sin(t), 9)
                bx = p.hub[0] + ux * (p.radius + d) + (w / 2 * (1 if ux > 0 else -1) if ux else 0.0)
                by = p.hub[1] + uy * (p.radius + d) + (h / 2 * (1 if uy > 0 else -1) if uy else 0.0)
                box = (bx - w / 2, by - h / 2, bx + w / 2, by + h / 2)
                inside = (panel.x + 0.04 <= box[0] and box[2] <= panel.x + panel.width - 0.04 and panel.y + 0.04 <= box[1]
                          and box[3] <= panel.y + panel.height - 0.04)
                start = _box_point(box, *p.hub)
                discs = sum(_box_hits_disc(box, o.hub, o.radius + 0.03) for o in places if o.region == p.region)
                crossing = sum(_segment_hits_disc(start, p.hub, o.hub, o.radius) for o in places if o is not p and o.region == p.region)
                boxes = sum(_overlaps(box, q) for q in taken)
                cost = discs * 10 + boxes * 10 + crossing * 6 + (0 if inside else 25) + rank * 1.5 + k * 0.01
                if best is None or cost < best[0]:
                    best = (cost, box, math.atan2(start[1] - p.hub[1], start[0] - p.hub[0]))
        _, p.box, p.gap = best
        taken.append(p.box)


def _ring_positions(p: Place, order: list[str]) -> dict[str, tuple[float, float]]:
    """Nodes on the rings around the hub, the slot towards the place box left free for its leader."""
    if len(order) == 1:
        return {order[0]: p.hub}
    out, i = {}, 0
    for r, slots in ring_slots(len(order)):
        for s in range(1, slots):  # slot 0 points at the box
            if i == len(order):
                break
            t = p.gap - 2 * math.pi * s / slots  # clockwise from the leader
            out[order[i]] = (p.hub[0] + r * math.cos(t), p.hub[1] + r * math.sin(t))
            i += 1
    return out


def _member_order(ctx: Context, p: Place, rank: dict[str, int]) -> list[str]:
    """By place (largest first, in a place group), then by relation type (as in G1), then by ID."""
    def key(cid):
        cell = ctx.case.contact(cid).relation_type
        return (rank.get(cid, 0), cell.value if cell.recorded else "9", cid)
    return sorted(p.members, key=key)


def _extent(region: Region, points: list[tuple[float, float]]) -> tuple[tuple[float, float], tuple[float, float]]:
    """The default extent, widened only where a place lies outside it or closer than EXTENT_INSET to its edge."""
    lon0, lon1 = region.lon
    lat0, lat1 = region.lat
    for la, lo in points:
        if lo < region.lon[0] + EXTENT_INSET:
            lon0 = min(lon0, lo - EXTENT_MARGIN)
        if lo > region.lon[1] - EXTENT_INSET:
            lon1 = max(lon1, lo + EXTENT_MARGIN)
        if la < region.lat[0] + EXTENT_INSET:
            lat0 = min(lat0, la - EXTENT_MARGIN)
        if la > region.lat[1] - EXTENT_INSET:
            lat1 = max(lat1, la + EXTENT_MARGIN)
    lon, lat = (lon0, lon1), (lat0, lat1)
    return (max(lon[0], -180.0), min(lon[1], 180.0)), (max(lat[0], -85.0), min(lat[1], 85.0))


def x1_layout(ctx: Context, gazetteer: dict, countries: dict[str, dict]) -> X1Layout:
    """Places (or place groups, or countries), panels per region, place boxes and node positions. Deterministic."""
    unresolved, missing = [], []
    found: dict[tuple, Place] = {}
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
        found.setdefault(key, Place(region, [(label, 0)], point, [], country_only)).members.append(c.id)
    places = sorted(found.values(), key=lambda p: (-len(p.members), p.places[0][0]))
    for p in places:
        p.places = [(p.places[0][0], len(p.members))]
    used = {p.region for p in places}
    panels = []
    for region in REGIONS:
        if region.key in ALWAYS or region.key in used:
            lon, lat = _extent(region, [p.anchor for p in places if p.region == region.key])
            panels.append(Panel(region, lon, lat))
    scale = [1.0 if pn.region.key == "germany" else OTHER_SCALE for pn in panels]
    height = min(GERMANY_H_MAX, (MAIN_W - PANEL_GAP * (len(panels) - 1)) / sum(pn.aspect * s for pn, s in zip(panels, scale)))
    x = (MAIN_W - sum(pn.aspect * s * height for pn, s in zip(panels, scale)) - PANEL_GAP * (len(panels) - 1)) / 2
    for pn, s in zip(panels, scale):  # top-aligned; Deutschland is the largest panel
        pn.width, pn.height = pn.aspect * s * height, s * height
        pn.x, pn.y = x, height - pn.height
        pn.count = sum(len(p.members) for p in places if p.region == pn.region.key)
        x += pn.width + PANEL_GAP
    by_key = {pn.region.key: pn for pn in panels}
    for p in places:
        p.point = p.hub = by_key[p.region].to_in(*p.anchor)
    grouped = []
    for pn in panels:
        grouped += _group([p for p in places if p.region == pn.region.key])
    places = grouped
    for pn in panels:
        _separate([p for p in places if p.region == pn.region.key], pn)
    _place_boxes(places, panels)
    positions = {}
    for p in places:
        rank, start = {}, 0
        for i, (_name, n) in enumerate(p.places):
            for cid in p.members[start:start + n]:
                rank[cid] = i
            start += n
        positions.update(_ring_positions(p, _member_order(ctx, p, rank)))
    return X1Layout(panels, places, positions, unresolved, missing, height)


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
    for iso, feature in countries.items():
        fill = "#E1E6EB"
        if panel.region.key == "germany" and iso == "DEU":
            fill = "#E8ECF0"
        elif panel.region.key == "europe" and iso == "DEU":
            fill = "#EEF1F4"  # shown in its own panel
        for ring in _rings(feature["geometry"]):
            ax.add_patch(Polygon(ring, closed=True, facecolor=fill, edgecolor="#FFFFFF", linewidth=0.5))


def x1(ctx: Context, gazetteer: dict, countries: dict[str, dict]):
    layout = x1_layout(ctx, gazetteer, countries)
    country_only = any(p.country_only for p in layout.places)
    moved = any(math.hypot(p.hub[0] - p.point[0], p.hub[1] - p.point[1]) > 0.02 for p in layout.places)
    sections = [
        ("Beziehungstyp", relation_entries(ctx.case)),
        (None, [("dot", "Wohnort (Ortspunkt)", POINT)]
               + ([("line", "ausgewichen: gepunktet zur wahren Lage (○)", {"color": "#8A939C", "linewidth": 0.8,
                                                                         "linestyle": (0, (1, 1.5))})] if moved else [])
               + ([("area", "nur Wohnland bekannt (Lage unscharf)", {"facecolor": "none", "edgecolor": MUTED, "linewidth": 0.8,
                                                                     "linestyle": (0, (3, 2))})] if country_only else [])),
    ]
    grouped = any(p.group for p in layout.places)
    first = ("Experimentelle Zusatzgrafik (Fassung 2), keine Standardgrafik. Lage = Wohnort; Kontakte eines Ortes um den Ortspunkt"
             + (f"; „und Umgebung“: Orte bis {UMGEBUNG_KM:.0f} km Abstand oder auf der Karte zusammenfallend" if grouped else "")
             + ". Keine Verbindungslinien (siehe G2). Karte: Natural Earth.")
    missing = []
    if layout.unresolved:
        missing.append(f"Wohnort nicht darstellbar: {', '.join(layout.unresolved)}.")
    if layout.not_in_gazetteer:
        missing.append(f"Ort ohne Koordinaten im Ortsverzeichnis: {', '.join(layout.not_in_gazetteer)}.")
    p_ = page(ctx, f"{X1_CODE} · Geografische Verteilung des persönlichen Netzwerks",
              "Wo leben die Kontakte? Wohnorte nach Region (experimentell)",
              main_w=MAIN_W, main_h=layout.height, legend="bottom", sections=sections, notes=[first, " ".join(missing)])
    ax = p_.main
    ax.set_zorder(2)  # nodes above the map panels
    ax.patch.set_alpha(0.0)
    for panel in layout.panels:
        _basemap(p_.figure, ax, panel, countries)
        ax.text(panel.x + 0.08, panel.y + panel.height - 0.08, panel.title, fontsize=LABEL_PT, fontweight="bold", color=INK,
                ha="left", va="top", zorder=8)
    for p in layout.places:
        if len(p.members) > 1 or p.country_only:  # a very pale disc: these contacts belong to one place
            ax.add_patch(Circle(p.hub, p.radius, facecolor="#FFFFFF", alpha=0.55, edgecolor="none", zorder=2.5, gid="place-disc"))
            ax.add_patch(Circle(p.hub, p.radius, fill=False, edgecolor=MUTED if p.country_only else "#D3D9DF", linewidth=0.7,
                                linestyle=(0, (3, 2)) if p.country_only else "solid", zorder=2.6))
        if math.hypot(p.hub[0] - p.point[0], p.hub[1] - p.point[1]) > 0.02:  # the place gave way: dotted line to its true point
            ax.plot(*zip(p.point, p.hub), color="#8A939C", linewidth=0.6, linestyle=(0, (1, 1.5)), zorder=3, gid="offset")
            ax.add_patch(Circle(p.point, 0.03, facecolor="white", edgecolor=POINT, linewidth=0.8, zorder=3.5, gid="true-point"))
        start = _box_point(p.box, *p.hub)
        ax.plot(*zip(start, p.hub), color="#7B8590", linewidth=0.6, zorder=3, gid="leader")  # through the free ring slot
        ax.add_patch(Circle(p.hub, 0.05, facecolor=POINT, edgecolor="white", linewidth=0.8, zorder=3.6, gid="place-point"))
        x0, y0, x1_, y1 = p.box
        ax.add_patch(FancyBboxPatch((x0, y0), x1_ - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=0.04", facecolor="white",
                                    edgecolor="#B8C0C8", linewidth=0.6, zorder=7, gid="place-box"))
        ax.text(x0 + BOX_PAD, y1 - BOX_PAD, p.title, fontsize=BOX_PT, fontweight="bold", color=INK, ha="left", va="top", zorder=8)
        if p.sub:
            ax.text(x0 + BOX_PAD, y0 + BOX_PAD, p.sub, fontsize=BOX_SUB_PT, color=MUTED, ha="left", va="bottom", zorder=8,
                    linespacing=1.15)
    draw_nodes(ax, layout.positions, {cid: relation_fill(ctx.case, cid) for cid in layout.positions}, zorder=5)
    return p_.figure


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
    record = {"format": "mares-run-record/v0-draft", "pipeline": "network_v1 experimental X1", "version": X1_VERSION,
              "run_id": run_id, "case": {"ref": f"{case_ref.root}:{case_ref.rel}", "code": case.code}, "standard_figure": False,
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
                  country_only=[cid for p in layout.places if p.country_only for cid in p.members],
                  place_groups=[[name for name, _ in p.places] for p in layout.places if p.group],
                  panels=[pn.region.key for pn in layout.panels])
    (run_dir / "run_record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return X1Result(case_ref, "COMPLETED", outputs, run_id, layout)
