"""X1 · Geografische Verteilung des persönlichen Netzwerks -- the ninth standard figure of network_v1 (a map).

Where the contacts live, on regional map panels (Amerika, Europa, Deutschland; further regions only when the data need
them). No contact-contact and no ego lines; node colour = relation type, as in every network figure. The contacts of one
place -- or of a place group ("Marburg und Umgebung": places the place directory assigns to a neighbouring place, when
both fall together on the map) -- sit in rings on a very pale disc beside the true place point, tied to it by a fine
line; the label docks right at the disc. A contact whose residence is known only by country sits at the country's label
point inside a dashed ring (never at an invented city); contacts without a usable residence are named in a note and not
drawn. Placement rules: docs/architecture/network-v1.md §6.

Positions come from a hand-kept place directory (``ROOT:network_v1/reference/gazetteer.csv``: ``place; country_iso3;
lat; lon; basis; group_with``) in the same root as the case -- never from a geocoding service, so residence data never
leave the machine. Country borders and label points: Natural Earth admin 0 countries (public domain) in
``WORKSPACE:cache/basemaps``. Both are read by the case run (:mod:`..run`) and handed over in :class:`.base.Geo`.
"""

from __future__ import annotations

import csv
import io
import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path

from matplotlib import patheffects
from matplotlib.patches import Circle, FancyBboxPatch, Polygon

from ..places import Area, norm
from .base import INK, LABEL_PT, MUTED, NODE_PT, Context, draw_nodes, page, relation_fill, relation_section, text_width

GAZETTEER = "network_v1/reference/gazetteer.csv"  # in the root of the case
BASEMAP = "cache/basemaps/ne_50m_admin_0_countries.geojson"  # in WORKSPACE
BASEMAP_SOURCE = "Natural Earth 1:50m Cultural Vectors, Admin 0 – Countries (public domain), naturalearthdata.com"
GAZETTEER_COLUMNS = ("place", "country_iso3", "lat", "lon", "basis")  # plus, optional, "group_with"
# group_with: the place (same country, itself in the directory) this place is shown with on a regional map -- a district,
# a surrounding municipality or a neighbouring town of a larger centre; empty = shown on its own. One level only.

NODE_R = NODE_PT / 72 / 2  # node radius in inches
NODE_STEP = 2 * NODE_R + 0.035  # centre distance of two nodes of one place
SINGLE_RING_MAX = 10  # up to this many contacts one ring around the place point, more in rings of 6, 12, ... slots
RING_R0 = 0.22  # smallest ring radius (inches): the place point and the leader stay visible
DISC_PAD = 0.05  # the pale disc of a place reaches this far beyond its nodes
POINT_R = 0.05  # radius of a place point (inches)
POINT_CLEAR = 0.09  # no disc, node or box comes closer to any place point than this: the points always stay visible
OFFSET_STEP = 0.06  # search step for the position of a disc beside its point
GROUP_MAX_KM = 40.0  # never group places farther apart than this (great-circle distance), whatever the directory says
GROUP_MAP_IN = 0.6  # ... and only when the two points lie closer than this on the panel (about 15 mm): scale-dependent
MAIN_W = 14.5
PANEL_GAP = 0.3
OTHER_SCALE = 0.8  # the other panels are this high relative to the Germany panel
GERMANY_H_MAX = 7.0
TITLE_H = 0.32  # room for the panel title inside the panel
BOX_PT = LABEL_PT - 1.5  # first line of a place box
BOX_SUB_PT = LABEL_PT - 3.0  # list of places of a place group (lighter)
BOX_LINE_W = 1.7  # inches; a longer place list wraps
BOX_PAD = 0.035
HEAD_GAP = 0.012  # between the bold place name and the compact rest of the line
GERMANY = (Area.MARBURG, Area.MITTELHESSEN, Area.GERMANY_OTHER)
POINT = "#1F2933"


@dataclass(frozen=True)
class Region:
    """A map panel: title, default extent (lon, lat; used when the panel has no place), and how its extent follows the
    places: margin around them, minimum span (degrees) for orientation, optional frame it never leaves."""

    key: str
    title: str
    lon: tuple[float, float]
    lat: tuple[float, float]
    margin: float = 4.0
    min_span: tuple[float, float] = (20.0, 16.0)
    frame: tuple[tuple[float, float], tuple[float, float]] | None = None


# Panels from left to right: Amerika, further regions, Europa, Deutschland -- each only when it has contacts (ADR-0027).
# The default extents (Amerika from Mexico to the south, Europa from Portugal to a little east of Germany) apply only to a
# panel without places, i.e. to Germany when no contact can be drawn.
REGIONS = (
    Region("americas", "Amerika", (-118.0, -34.0), (-56.0, 33.0), margin=7.0, min_span=(30.0, 30.0)),
    Region("africa", "Afrika", (-20.0, 52.0), (-36.0, 38.0), margin=6.0, min_span=(30.0, 30.0)),
    Region("asia", "Asien", (25.0, 150.0), (-10.0, 60.0), margin=6.0, min_span=(30.0, 30.0)),
    Region("oceania", "Ozeanien", (110.0, 180.0), (-48.0, 0.0), margin=6.0, min_span=(30.0, 30.0)),
    Region("other", "Weitere Regionen", (-180.0, 180.0), (-60.0, 80.0), margin=6.0, min_span=(30.0, 30.0)),
    Region("europe", "Europa (ohne Deutschland)", (-10.5, 19.5), (35.0, 59.0), margin=3.0, min_span=(13.0, 10.0)),
    Region("germany", "Deutschland", (5.5, 15.5), (47.0, 55.3), margin=1.2, min_span=(9.0, 7.5),
           frame=((5.5, 15.5), (47.0, 55.3))),
)
# the direct neighbours of Germany: with Scheme.x1_neighbours_with_germany their places join the Germany panel
NEIGHBOURS = ("DNK", "POL", "CZE", "AUT", "CHE", "FRA", "LUX", "BEL", "NLD")
ASPECT_RANGE = (0.8, 1.5)  # width : height of a panel (degrees, latitude-corrected); a narrower extent is widened
CONTINENT_REGION = {"North America": "americas", "South America": "americas", "Africa": "africa", "Asia": "asia", "Oceania": "oceania"}


class X1Error(RuntimeError):
    """X1 cannot be drawn (no basemap, a malformed place directory ...)."""


# ------------------------------------------------------------------------------------------------- sources ---
def read_gazetteer(path: Path) -> dict[tuple[str, str], tuple[float, float, tuple[str, str] | None]]:
    """(normalised place, ISO3) -> (lat, lon, key of ``group_with`` or None). A missing file is an empty directory; a
    malformed row or a ``group_with`` that is not itself in the directory is an error."""
    if not path.is_file():
        return {}
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig")), delimiter=";"))
    header = tuple(rows[0]) if rows else GAZETTEER_COLUMNS
    if header[:len(GAZETTEER_COLUMNS)] != GAZETTEER_COLUMNS or header[5:] not in ((), ("group_with",)):
        raise X1Error(f"gazetteer columns must be {'; '.join(GAZETTEER_COLUMNS)} [; group_with]")
    out = {}
    for i, row in enumerate(rows, start=2):
        try:
            lat, lon = float(row["lat"]), float(row["lon"])
        except (TypeError, ValueError) as error:
            raise X1Error(f"gazetteer line {i}: lat/lon must be numbers") from error
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise X1Error(f"gazetteer line {i}: lat/lon out of range")
        iso = row["country_iso3"].strip().upper()
        parent = (row.get("group_with") or "").strip()
        out[(norm(row["place"]), iso)] = (lat, lon, (norm(parent), iso) if parent else None)
    for key, (_lat, _lon, parent) in out.items():
        if parent is not None and (parent not in out or parent == key):
            raise X1Error(f"gazetteer: group_with of {key[0]!r} must name another place of the same country in the directory")
    return out


def read_basemap(path: Path) -> dict[str, dict]:
    """Natural Earth admin 0 countries by ISO3 (``ADM0_A3``)."""
    if not path.is_file():
        raise X1Error(f"basemap missing: WORKSPACE:{BASEMAP} (see docs/architecture/network-v1.md §6)")
    return {f["properties"]["ADM0_A3"]: f for f in json.loads(path.read_text(encoding="utf-8"))["features"]}


# -------------------------------------------------------------------------------------------------- layout ---
def ring_slots(k: int) -> list[tuple[float, int]]:
    """(radius, slots) of the rings for ``k`` contacts around the centre of their disc; a single contact is the disc."""
    if k == 1:
        return [(0.0, 1)]
    if k <= SINGLE_RING_MAX:
        return [(max(RING_R0, k * NODE_STEP / (2 * math.pi)), k)]
    out, left, j = [], k, 1
    while left:
        n = min(left, 6 * j)
        out.append((j * NODE_STEP, n))
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
    country: str = ""  # residence country as recorded (several, " / "-joined, if a place group crosses a border)
    key: tuple[str, str] | None = None  # place directory key of the (head) place
    parent: tuple[str, str] | None = None  # group_with of the place directory
    others: list[tuple[float, float]] = field(default_factory=list)  # true points (inches) of the other places of a group
    wrap: bool = False  # title in two lines (place / country and number) where one line does not fit

    @property
    def group(self) -> bool:
        return len(self.places) > 1

    @property
    def head(self) -> str:
        """The bold part of the label: the place (or the country, if only that is known)."""
        name = self.places[0][0]
        return f"{name}{' und Umgebung' if self.group else ''}"

    @property
    def tail(self) -> str:
        """The compact rest of the first line: country outside Germany (the Germany panel names its country), a missing
        place, and the number of contacts from two on -- " · Kolumbien · n = 3"."""
        total = len(self.members)
        parts = []
        if self.country_only:
            parts.append("nur Land bekannt")
        elif self.country and (self.region != "germany" or (self.key is not None and self.key[1] != "DEU")):
            parts.append(self.country)  # in the Germany panel only a place in a neighbouring country names its country
        if total > 1:
            parts.append(f"n = {total}")
        return "".join(f" · {x}" for x in parts)

    @property
    def title(self) -> str:
        """First line of the label (two lines if wrapped: place / country and number)."""
        if self.wrap and self.tail:
            return f"{self.head}\n{self.tail[3:]}"
        return self.head + self.tail

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
        if self.wrap and self.tail:
            w = max(text_width(self.head, BOX_PT, bold=True), text_width(self.tail[3:], BOX_PT))
            h = BOX_PT / 72 * 1.25 * 2
        else:
            w = text_width(self.head, BOX_PT, bold=True) + HEAD_GAP + text_width(self.tail, BOX_PT)
            h = BOX_PT / 72 * 1.25
        if self.sub:
            w = max(w, max(text_width(line, BOX_SUB_PT) for line in self.sub.split("\n")))
            h += (self.sub.count("\n") + 1) * BOX_SUB_PT / 72 * 1.2 + 0.02
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
        neighbour = ctx.case.contact(cid).residence_country_iso3 in NEIGHBOURS
        return "germany" if ctx.scheme.x1_neighbours_with_germany and neighbour else "europe"
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
    """Place groups "<place> und Umgebung", a display decision only (the recorded places are kept and listed in the box):
    a place joins the place its directory entry names in ``group_with`` -- if that place has contacts in the same panel,
    is at most GROUP_MAX_KM away and its point lies closer than GROUP_MAP_IN on this panel (on a larger-scale map the two
    stay apart). One level, no chains; places without ``group_with`` and country-only places stand on their own."""
    by_key = {p.key: p for p in places if p.key and not p.country_only}
    joined: dict[int, list[Place]] = {id(p): [] for p in places}
    heads = []
    for p in places:
        q = by_key.get(p.parent) if p.parent and not p.country_only else None
        if q is not None and q.parent is None and _km(p.anchor, q.anchor) <= GROUP_MAX_KM \
                and math.hypot(p.point[0] - q.point[0], p.point[1] - q.point[1]) < GROUP_MAP_IN:
            joined[id(q)].append(p)
        else:
            heads.append(p)
    out = []
    for h in heads:
        parts = [h] + sorted(joined[id(h)], key=lambda p: (-len(p.members), p.places[0][0]))
        if len(parts) == 1:
            out.append(h)
            continue
        country = " / ".join(dict.fromkeys(p.country for p in parts if p.country))
        out.append(Place(h.region, [pl for p in parts for pl in p.places], h.anchor, [m for p in parts for m in p.members], False,
                         h.point, h.point, country=country, key=h.key, others=[p.point for p in parts[1:]]))
    return sorted(out, key=lambda p: (-len(p.members), p.places[0][0]))


def _disc_edge(p: "Place") -> tuple[float, float]:
    """Where the line from the place point meets its disc."""
    dx, dy = p.hub[0] - p.point[0], p.hub[1] - p.point[1]
    d = math.hypot(dx, dy) or 1.0
    return p.point[0] + dx / d * (d - p.radius), p.point[1] + dy / d * (d - p.radius)


ORDER_NEAR = 1.5  # inches: places this close on the panel keep their geographic order (north-south, west-east)
ORDER_MIN = 0.1  # inches: a relation counts from this separation of the points on, and if not much smaller than the other
ORDER_CLEAR = 1.5  # a relation is clear if its offset is this many times the other one; otherwise the pair is diagonal
ORDER_TOL = 0.05  # inches: a reversal below this is not visible
ORDER_COST = 2.0  # per reversed relation, in inches of disc offset: worth a somewhat longer line, never a hidden name


def _order_flips(p: Place, pos, o: Place, other) -> int:
    """How many geographic relations of two nearby places the positions of their discs or labels reverse. A clear relation
    (north-south or west-east, the other offset much smaller) must keep its sign: a place further north is not shown below
    one further south. A diagonal pair must only not turn round as a whole (north-east shown south-west)."""
    dx, dy = p.point[0] - o.point[0], p.point[1] - o.point[1]
    if math.hypot(dx, dy) > ORDER_NEAR or math.hypot(dx, dy) < ORDER_MIN:
        return 0
    sx, sy = pos[0] - other[0], pos[1] - other[1]
    flips = 0
    for along, across, shown in ((dx, dy, sx), (dy, dx, sy)):
        if abs(along) >= ORDER_MIN and abs(along) >= ORDER_CLEAR * abs(across) and along * shown < 0 and abs(shown) > ORDER_TOL:
            flips += 1
    if not flips and max(abs(dx), abs(dy)) < ORDER_CLEAR * min(abs(dx), abs(dy)):  # diagonal
        flips += (dx * sx + dy * sy) < -ORDER_TOL * math.hypot(dx, dy)
    return flips


def _centre(box) -> tuple[float, float]:
    return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2


def _disc_candidates(p: Place, panel: Panel, points: list, done: list[Place], boxes: list, lines: list,
                     pending: tuple = ()) -> list:
    """Positions of the disc of one place beside its point (never on it), as (cost, centre), nearest first among the
    allowed ones. Violations: covering a place point (also the true points of the other places of a group), a label or a
    line, overlapping a disc placed before, leaving the panel; minor: its line crossing a disc, a label or a foreign point;
    then the geographic order towards the discs placed before and the points of the places still to come (so that an
    early disc leaves the right side free for them). Positions in growing distance and sixteen directions."""
    r = p.radius
    title = panel.title_box()
    out = []
    for step in range(40):
        d = r + POINT_CLEAR + step * OFFSET_STEP
        for k in range(16):
            t = math.pi / 2 - 2 * math.pi * k / 16
            x, y = p.point[0] + d * math.cos(t), p.point[1] + d * math.sin(t)
            outside = not (panel.x + r + 0.04 <= x <= panel.x + panel.width - r - 0.04
                           and panel.y + r + 0.04 <= y <= panel.y + panel.height - r - 0.04)
            covers = sum(math.hypot(x - q[0], y - q[1]) < r + POINT_CLEAR for q in points)
            overlap = sum(math.hypot(x - o.hub[0], y - o.hub[1]) < r + o.radius + 0.08 for o in done)
            edge = (p.point[0] + (x - p.point[0]) * (d - r) / d, p.point[1] + (y - p.point[1]) * (d - r) / d)
            crosses = sum(_segment_hits_disc(p.point, edge, o.hub, o.radius) for o in done)
            on_box = sum(_box_hits_disc(b_, (x, y), r + 0.04) for b_ in boxes)  # names stay readable
            on_line = sum(_segment_hits_disc(a_, b_, (x, y), r + 0.03) for a_, b_ in lines)
            line_box = sum(_segment_hits_box(p.point, edge, b_) for b_ in boxes)
            line_points = sum(_segment_hits_disc(p.point, edge, q, POINT_CLEAR) for q in points
                              if q != p.point and q not in p.others)  # its own group's places lie around the point
            cost = (covers * 100 + on_box * 100 + on_line * 100 + overlap * 100 + outside * 100
                    + _box_hits_disc(title, (x, y), r + 0.04) * 100 + crosses * 100 + line_box * 100 + line_points * 60
                    + (sum(_order_flips(p, (x, y), o, o.hub) for o in done)
                       + sum(_order_flips(p, (x, y), o, o.point) for o in pending)) * ORDER_COST + d + k * 0.001)
            out.append((cost, (x, y)))
    return sorted(out)


LABEL_MISS = 8.0  # extra cost of a label that does not dock right at its circle (about 8 inches of disc offset)
LABEL_FITS = 1.6  # a label cost below this: the full label docks right at the circle (closest distance), hiding nothing


def _place_callout(p: Place, panel: Panel, points: list, done: list[Place], taken: list, lines: list,
                   pending: tuple = ()) -> None:
    """Disc and docked label together: the disc goes to the nearest allowed position at which its complete label finds room
    right at the circle; neighbouring groups are pulled apart for that, never the place points (the line ties the disc to
    its point). If no position allows it, the best combination is taken."""
    best = None
    for cost, centre in _disc_candidates(p, panel, points, done, taken[1:], lines, pending):
        if best is not None and cost >= best[0]:
            break  # every further position is worse already
        p.hub = centre
        label = _place_label(p, panel, points, done + [p], taken, lines + [(p.point, _disc_edge(p))])
        total = cost + label + (0.0 if label < LABEL_FITS else LABEL_MISS)  # a label not docked tightly is worth moving the disc
        if best is None or total < best[0]:
            best = (total, centre, p.box, p.wrap)
        if cost < 20 and label < LABEL_FITS:
            break  # the nearest position where disc and full label fit
    _, p.hub, p.box, p.wrap = best


def _place_panel(places: list[Place], panel: Panel) -> None:
    """Place after place, largest first: its callout -- disc of contacts and label docked right at it, placed together so
    that the full label fits at the circle -- beside the point, tied to it by a fine line. Every later disc and label keeps clear of
    everything placed before; all place points are reserved from the start. Then a refinement pass for all labels.
    Asymmetric positions follow from these rules, not from place names."""
    points = [q for p in places for q in [p.point] + p.others]
    taken = [panel.title_box()]
    lines: list = []  # the lines from the points to their discs
    done: list[Place] = []
    for i, p in enumerate(places):
        _place_callout(p, panel, points, done, taken, lines, tuple(places[i + 1:]))
        lines.append((p.point, _disc_edge(p)))
        taken.append(p.box)
        done.append(p)
    for _ in range(3):  # refinement: every label again, with all discs, lines and other labels in place
        changed = False
        for p in places:
            old = p.box
            _place_label(p, panel, points, places, [panel.title_box()] + [o.box for o in places if o is not p], lines)
            changed |= p.box != old
        if not changed:
            break


DOCK = (0.03, 0.09, 0.18, 0.32)  # inches between a disc and its label: docked first, a little apart only if needed


def _place_label(p: Place, panel: Panel, points: list, discs: list[Place], taken: list, lines: list) -> float:
    """The label beside its own disc, in eight directions (above and below also shifted to the side): not on a disc, a
    place point, a line, the panel title or another label, inside its panel, nearer to its own disc than to any other."""
    best = None
    for wrap in (False, True):  # the two-line title only where it places better
        p.wrap = wrap
        if wrap and not p.tail:
            continue
        w, h = p.box_size()
        for rank, d in enumerate(DOCK):
            for k in range(8):
                t = math.pi / 2 - math.pi / 4 * k  # N, NE, E, ... clockwise
                ux, uy = round(math.cos(t), 9), round(math.sin(t), 9)
                reach = p.radius + d
                if ux and uy:  # diagonal: the corner of the label touches the circle
                    reach = p.radius + d
                    bx0 = p.hub[0] + ux * reach * 0.7071 * 1.0 + w / 2 * (1 if ux > 0 else -1)
                    by0 = p.hub[1] + uy * reach * 0.7071 * 1.0 + h / 2 * (1 if uy > 0 else -1)
                else:
                    bx0 = p.hub[0] + ux * reach + (w / 2 * (1 if ux > 0 else -1) if ux else 0.0)
                    by0 = p.hub[1] + uy * reach + (h / 2 * (1 if uy > 0 else -1) if uy else 0.0)
                if not ux:
                    shifts = [(0.0, 0.0), (w / 2 - 0.15, 0.0), (-(w / 2 - 0.15), 0.0)]
                elif not uy:
                    shifts = [(0.0, 0.0), (0.0, h / 2 - 0.06), (0.0, -(h / 2 - 0.06))]
                else:
                    shifts = [(0.0, 0.0)]
                for sx, sy in shifts:
                    bx, by = bx0 + sx, by0 + sy
                    box = (bx - w / 2, by - h / 2, bx + w / 2, by + h / 2)
                    cost = (_label_cost(p, panel, points, discs, taken, lines, box) + rank * 1.5 + (0.3 if sx or sy else 0.0)
                            + k * 0.01 + (1.0 if wrap else 0.0))
                    if best is None or cost < best[0]:
                        best = (cost, box, wrap)
    cost, p.box, p.wrap = best
    return cost


def _label_cost(p, panel, points, discs, taken, lines, box) -> float:
    """Collisions of one label; 100 for everything that would hide a point, a disc, a line or another label."""
    inside = (panel.x + 0.04 <= box[0] and box[2] <= panel.x + panel.width - 0.04 and panel.y + 0.04 <= box[1]
              and box[3] <= panel.y + panel.height - 0.04)
    hidden = (sum(_box_hits_disc(box, o.hub, o.radius) for o in discs)  # on a disc (its own included)
              + sum(_box_hits_disc(box, q, POINT_CLEAR) for q in points)  # on a place point
              + sum(_overlaps(box, q) for q in taken)  # on another label or the panel title
              + sum(_segment_hits_box(a_, b_, box) for a_, b_ in lines))  # the label hides a line
    own = _reach(box, p)
    ambiguous = (sum(_reach(box, o) < own for o in discs if o is not p)  # the eye would read it as another callout's
                 + sum(math.hypot((box[0] + box[2]) / 2 - q[0], (box[1] + box[3]) / 2 - q[1]) < own
                       for q in points if q != p.point and q not in p.others))  # ... or as a label of another place point
    order = sum(_order_flips(p, _centre(box), o, _centre(o.box)) for o in discs if o is not p)  # north stays above south
    return hidden * 150 + ambiguous * 100 + (0 if inside else 200) + order * ORDER_COST  # hiding anything is worst


def _segments_cross(p1, p2, q1, q2) -> bool:
    def side(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return side(p1, p2, q1) * side(p1, p2, q2) < 0 and side(q1, q2, p1) * side(q1, q2, p2) < 0


def _segment_hits_box(p1, p2, box) -> bool:
    x0, y0, x1, y1 = box
    if any(x0 < x < x1 and y0 < y < y1 for x, y in (p1, p2)):
        return True
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return any(_segments_cross(p1, p2, corners[i], corners[(i + 1) % 4]) for i in range(4))


def _reach(box, p: Place) -> float:
    """Distance from the middle of a label to the edge of a disc: what the eye uses to tie a label to its callout."""
    return math.hypot((box[0] + box[2]) / 2 - p.hub[0], (box[1] + box[3]) / 2 - p.hub[1]) - p.radius


def _gap(box, point) -> float:
    """Distance between a box and a point."""
    x, y = _box_point(box, *point)
    return math.hypot(x - point[0], y - point[1])


def _ring_positions(p: Place, order: list[str]) -> dict[str, tuple[float, float]]:
    """Nodes on the rings around the centre of the disc, clockwise from the top; every second ring turned by half a step."""
    if len(order) == 1:
        return {order[0]: p.hub}
    out, i = {}, 0
    for j, (r, n) in enumerate(ring_slots(len(order))):
        for s_ in range(n):
            t = math.pi / 2 - 2 * math.pi * (s_ + 0.5 * j) / n
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
    """The extent follows the places of the panel: their bounding box plus the region's margin, at least its minimum span
    (for orientation) and within a sensible width-to-height ratio, inside its frame (Germany stays Germany). Without
    places: the default extent. Panels have different scales; distances are not comparable between panels."""
    if not points:
        return region.lon, region.lat
    lats = [la for la, _ in points]
    lons = [lo for _, lo in points]
    lon = [min(lons) - region.margin, max(lons) + region.margin]
    lat = [min(lats) - region.margin, max(lats) + region.margin]

    def widen(span, need):
        if span[1] - span[0] < need:
            mid = sum(span) / 2
            span[0], span[1] = mid - need / 2, mid + need / 2

    widen(lon, region.min_span[0])
    widen(lat, region.min_span[1])
    k = math.cos(math.radians(sum(lat) / 2))
    aspect = (lon[1] - lon[0]) * k / (lat[1] - lat[0])
    if aspect < ASPECT_RANGE[0]:
        widen(lon, ASPECT_RANGE[0] * (lat[1] - lat[0]) / k)
    elif aspect > ASPECT_RANGE[1]:
        widen(lat, (lon[1] - lon[0]) * k / ASPECT_RANGE[1])
    if region.frame:  # shift (and if need be cut) into the frame
        for span, (f0, f1) in ((lon, region.frame[0]), (lat, region.frame[1])):
            w = min(span[1] - span[0], f1 - f0)
            start = min(max(span[0], f0), f1 - w)
            span[0], span[1] = start, start + w
    return (max(lon[0], -180.0), min(lon[1], 180.0)), (max(lat[0], -85.0), min(lat[1], 85.0))


def _germany_with_neighbours(region: Region, places: list, countries: dict[str, dict]) -> Region:
    """The Germany panel with places in neighbouring countries: the frame grows to take them in (with the margin), and
    the title names those countries ('Deutschland und Österreich'). Without such places the region is unchanged."""
    outside = [p for p in places if p.key is not None and p.key[1] != "DEU"]
    if not outside:
        return region
    (lo0, lo1), (la0, la1) = region.frame
    for p in outside:
        lat, lon = p.anchor
        lo0, lo1 = min(lo0, lon - region.margin), max(lo1, lon + region.margin)
        la0, la1 = min(la0, lat - region.margin), max(la1, lat + region.margin)
    names = sorted({(countries.get(p.key[1], {}).get("properties") or {}).get("NAME_DE") or p.country or p.key[1] for p in outside})
    title = "Deutschland und " + (names[0] if len(names) == 1 else ", ".join(names[:-1]) + " und " + names[-1])
    return replace(region, title=title, frame=((lo0, lo1), (la0, la1)))


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
            entry = gazetteer.get((norm(place), iso))
            if entry is None:
                missing.append(c.id)
                continue
            point, parent, pkey = entry[:2], (entry[2] if len(entry) > 2 else None), (norm(place), iso)
            key, label, country_only = (region, norm(place), iso), place, False
        else:  # only the country is known: its label point, never a city
            props = countries.get(iso, {}).get("properties")
            if not props:
                missing.append(c.id)
                continue
            point, parent, pkey = (props["LABEL_Y"], props["LABEL_X"]), None, None
            key, label, country_only = (region, "", iso), props.get("NAME_DE") or c.residence_country, True
        props = countries.get(iso, {}).get("properties") or {}
        country = c.residence_country.strip() or props.get("NAME_DE", "")
        found.setdefault(key, Place(region, [(label, 0)], point, [], country_only, country=country, key=pkey,
                                    parent=parent)).members.append(c.id)
    places = sorted(found.values(), key=lambda p: (-len(p.members), p.places[0][0]))
    for p in places:
        p.places = [(p.places[0][0], len(p.members))]
    used = {p.region for p in places} or {"germany"}  # only panels with contacts (ADR-0027); nothing drawable: Germany alone
    together = ctx.scheme.x1_neighbours_with_germany
    panels = []
    for region in REGIONS:
        if region.key in used:
            if together and region.key == "germany":
                region = _germany_with_neighbours(region, [p for p in places if p.region == "germany"], countries)
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
    for pn in panels:  # place point and name first, then the contacts beside them
        _place_panel([p for p in places if p.region == pn.region.key], pn)
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


def x1(ctx: Context, gazetteer: dict | None = None, countries: dict[str, dict] | None = None):
    """The figure; place directory and basemap from ``ctx.geo`` unless given."""
    if gazetteer is None or countries is None:
        if ctx.geo is None or ctx.geo.missing:
            raise X1Error(ctx.geo.missing if ctx.geo else "X1 needs the place directory and the basemap (Context.geo)")
        gazetteer, countries = ctx.geo.gazetteer, ctx.geo.countries
    layout = x1_layout(ctx, gazetteer, countries)
    country_only = any(p.country_only for p in layout.places)
    others = any(p.others for p in layout.places)
    sections = [
        ctx.scheme.relation_section(ctx.case),
        (None, [("dot", "Wohnort (Ortspunkt)", POINT)]
               + ([("text", "○ weiterer Ort einer Ortsgruppe", None)] if others else [])
               + ([("area", "nur Wohnland bekannt (Lage unscharf)", {"facecolor": "none", "edgecolor": MUTED, "linewidth": 0.8,
                                                                     "linestyle": (0, (3, 2))})] if country_only else [])),
    ]
    not_shown = [cid for cid in ctx.case.contact_ids if cid in set(layout.unresolved + layout.not_in_gazetteer)]
    notes = [f"Wohnort nicht darstellbar: {', '.join(not_shown)}." if not_shown else "", "Kartengrundlage: Natural Earth."]
    p_ = page(ctx, "X1", main_w=MAIN_W, main_h=layout.height, legend="bottom", sections=sections, notes=notes)
    ax = p_.main
    ax.set_zorder(2)  # nodes above the map panels
    ax.patch.set_alpha(0.0)
    for panel in layout.panels:
        _basemap(p_.figure, ax, panel, countries)
        ax.text(panel.x + 0.08, panel.y + panel.height - 0.08, panel.title, fontsize=LABEL_PT, fontweight="bold", color=INK,
                ha="left", va="top", zorder=8)
    for p in layout.places:
        if len(p.members) > 1 or p.country_only:  # a very pale disc beside the point: these contacts belong to one place
            ax.add_patch(Circle(p.hub, p.radius, facecolor="#FFFFFF", alpha=0.55, edgecolor="none", zorder=2.5, gid="place-disc"))
            ax.add_patch(Circle(p.hub, p.radius, fill=False, edgecolor=MUTED if p.country_only else "#D3D9DF", linewidth=0.7,
                                linestyle=(0, (3, 2)) if p.country_only else "solid", zorder=2.6))
        ax.plot(*zip(p.point, _disc_edge(p)), color="#9AA3AC", linewidth=0.7, zorder=4.4, gid="connector")  # callout to its point
        for q in p.others:  # the other places of a group keep their true point: not everyone lives in the head place
            if math.hypot(q[0] - p.point[0], q[1] - p.point[1]) > 0.02:
                ax.add_patch(Circle(q, 0.03, facecolor="white", edgecolor=POINT, linewidth=0.8, zorder=4.6, gid="true-point"))
        ax.add_patch(Circle(p.point, POINT_R, facecolor=POINT, edgecolor="white", linewidth=0.8, zorder=4.7, gid="place-point"))
        x0, y0, x1_, y1 = p.box  # a soft, borderless ground and a white halo: readable on the map, no note-paper look
        ax.add_patch(FancyBboxPatch((x0, y0), x1_ - x0, y1 - y0, boxstyle="round,pad=0.01,rounding_size=0.07", facecolor="white",
                                    alpha=0.5, edgecolor="none", zorder=6.5, gid="place-box"))
        halo = [patheffects.withStroke(linewidth=2.2, foreground="white")]
        top = y1 - BOX_PAD
        ax.text(x0 + BOX_PAD, top, p.head, fontsize=BOX_PT, fontweight="bold", color=INK, ha="left", va="top", zorder=8,
                path_effects=halo)
        if p.tail:
            if p.wrap:
                ax.text(x0 + BOX_PAD, top - BOX_PT / 72 * 1.25, p.tail[3:], fontsize=BOX_PT, color=INK, ha="left", va="top",
                        zorder=8, path_effects=halo)
            else:
                ax.text(x0 + BOX_PAD + text_width(p.head, BOX_PT, bold=True) + HEAD_GAP, top, p.tail, fontsize=BOX_PT, color=INK, ha="left",
                        va="top", zorder=8, path_effects=halo)
        if p.sub:
            ax.text(x0 + BOX_PAD, y0 + BOX_PAD, p.sub, fontsize=BOX_SUB_PT, color="#7B8590", ha="left", va="bottom", zorder=8,
                    linespacing=1.1, path_effects=halo)
    draw_nodes(ax, layout.positions, {cid: ctx.scheme.fill(ctx.case, cid) for cid in layout.positions}, zorder=5)
    return p_.figure
