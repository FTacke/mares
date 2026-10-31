"""Experiment: a cartographic variant of G2 for the fully synthetic test case 002 -- not a standard figure.

Three panels (Americas, Europe, Mittelhessen) on a pale Natural Earth basemap, contacts at their place of residence,
confirmed contact-contact ties only (no ego lines), node colour = relation type. Contacts at the same place sit around
the place point, held by a small force layout; a thin leader connects each node with its true point. Ties between
panels run across the gap. The Europe panel marks the extent of the Mittelhessen panel; Mittelhessen contacts are
drawn only there.

Two variants: ``exact`` (place known) and ``country`` (abroad only the residence country is used, as if the place were
unknown: the contacts sit at the country's label point inside a dashed ring, never at an invented city).

Data rules: only the synthetic case 002 (``provenance: fully_synthetic``) is accepted; positions come from the small
coordinate table below (public city coordinates of the invented places), never from a geocoding service. The basemap is
read from ``WORKSPACE:cache/basemaps`` (see README). Output: ``WORKSPACE:runs/<RUN-ID>/``.

    .venv\\Scripts\\python pilots\\network_v1_map\\g2_map.py
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone

import numpy as np
from matplotlib.patches import Circle, Polygon, Rectangle

from mares.core import ids
from mares.core.refs import StorageRef
from mares.core.roots import Roots
from mares.network_v0.figures.style import rc, save_figure
from mares.network_v1.case import read_case
from mares.network_v1.figures.base import (
    INK, MUTED, NODE_PT, TIE, TIE_BETWEEN, Context, draw_nodes, force_layout, page, relation_entries, relation_fill,
)
from mares.network_v1.places import Area
from mares.network_v1.testcases import synthetic_source
from mares.network_v1.validate import validate

BASEMAP = "cache/basemaps/ne_50m_admin_0_countries.geojson"
# Public coordinates (lat, lon) of the places used by the synthetic case 002; no geocoding service is used.
PLACES = {
    "Marburg": (50.81, 8.77), "Wehrda": (50.84, 8.76), "Cölbe": (50.85, 8.78), "Lahntal": (50.87, 8.69),
    "Kirchhain": (50.83, 8.92), "Gießen": (50.58, 8.68), "Wetzlar": (50.56, 8.50), "Kassel": (51.31, 9.48),
    "Frankfurt am Main": (50.11, 8.68), "Berlin": (52.52, 13.40), "Madrid": (40.42, -3.70), "Barcelona": (41.39, 2.17),
    "Lyon": (45.76, 4.84), "Bogotá": (4.71, -74.07), "Medellín": (6.24, -75.58), "Quito": (-0.18, -78.47),
    "Miami": (25.76, -80.19), "Toronto": (43.65, -79.38),
}
NODE_R = NODE_PT / 72 / 2


class Panel:
    """A map panel: lon/lat extent, equirectangular with the cosine of its middle latitude, drawn in inches."""

    def __init__(self, name: str, lon: tuple[float, float], lat: tuple[float, float], width: float, x: float, top: float):
        self.name, self.lon, self.lat = name, lon, lat
        self.k = math.cos(math.radians(sum(lat) / 2))
        self.scale = width / ((lon[1] - lon[0]) * self.k)
        self.width = width
        self.height = (lat[1] - lat[0]) * self.scale
        self.x, self.y = x, top - self.height  # lower left corner in main-area inches

    def to_in(self, lat: float, lon: float) -> tuple[float, float]:
        return self.x + (lon - self.lon[0]) * self.k * self.scale, self.y + (lat - self.lat[0]) * self.scale

    def contains(self, lat: float, lon: float) -> bool:
        return self.lon[0] <= lon <= self.lon[1] and self.lat[0] <= lat <= self.lat[1]


def _rings(geometry: dict):
    if geometry["type"] == "Polygon":
        yield geometry["coordinates"][0]
    elif geometry["type"] == "MultiPolygon":
        for polygon in geometry["coordinates"]:
            yield polygon[0]


def draw_basemap(figure, main, panel: Panel, countries: list[dict], highlight: set[str]) -> None:
    """The panel as an axes of its own in lon/lat (it clips the countries); placed below the main area, which carries
    nodes and ties."""
    box = main.get_position()
    fw, fh = figure.get_figwidth(), figure.get_figheight()
    mw, mh = box.width * fw, box.height * fh  # main area in inches
    ax = figure.add_axes((box.x0 + panel.x / mw * box.width, box.y0 + panel.y / mh * box.height,
                          panel.width / mw * box.width, panel.height / mh * box.height), zorder=0)
    ax.set_xlim(*panel.lon)
    ax.set_ylim(*panel.lat)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("#F7F9FB")
    for spine in ax.spines.values():
        spine.set_edgecolor("#C9CED3")
        spine.set_linewidth(0.7)
    for feature in countries:
        iso = feature["properties"].get("ADM0_A3")
        for ring in _rings(feature["geometry"]):
            ax.add_patch(Polygon(ring, closed=True, facecolor="#E3E7EB" if iso not in highlight else "#D5DEE7", edgecolor="#FFFFFF",
                                 linewidth=0.5))
    main.text(panel.x + 0.08, panel.y + panel.height - 0.08, panel.name, fontsize=9, fontweight="bold", color=MUTED, va="top", zorder=8)


def positions_for(ctx: Context, variant: str, countries: dict[str, dict]) -> tuple[dict, dict, list[str], set[str]]:
    """Anchor (lat, lon) per contact; contacts without a usable position; countries placed only by their label point."""
    anchors, kinds, unplaced, country_only = {}, {}, [], set()
    for c in ctx.case.contacts:
        area = ctx.derived.area(c.id)
        if area is Area.UNRESOLVED:
            unplaced.append(c.id)
            continue
        abroad = area in (Area.EUROPE_OTHER, Area.OUTSIDE_EUROPE)
        if variant == "country" and abroad:
            props = countries[c.residence_country_iso3]["properties"]
            anchors[c.id] = (props["LABEL_Y"], props["LABEL_X"])
            kinds[c.id] = "country"
            country_only.add(c.residence_country_iso3)
        elif c.residence_place in PLACES:
            anchors[c.id] = PLACES[c.residence_place]
            kinds[c.id] = "place"
        else:
            unplaced.append(c.id)
    return anchors, kinds, unplaced, country_only


def render(ctx: Context, variant: str, countries: list[dict]):
    by_iso = {f["properties"]["ADM0_A3"]: f for f in countries}
    anchors, kinds, unplaced, country_only = positions_for(ctx, variant, by_iso)
    main_w, main_h = 14.0, 5.3
    top = main_h - 0.1
    panels = [
        Panel("Amerika", (-128, -56), (-8, 63), 4.6, 0.0, top),
        Panel("Europa", (-11, 21), (35, 57), 4.3, 4.8, top),
        Panel("Mittelhessen (Ausschnitt)", (8.3, 9.2), (50.45, 51.0), 4.7, 9.3, top),
    ]
    local = panels[2]
    sections = [("Beziehungstyp", relation_entries(ctx.case)),
                ("Verbindungen", [("line", "im selben Bereich", {"color": TIE, "linewidth": 1.0}),
                                  ("line", "zwischen Bereichen", {"color": TIE_BETWEEN, "linewidth": 0.8, "linestyle": (0, (4, 2.5))})]),
                (None, [("dot", "Wohnort (genaue Lage)", "#1F2933")])]
    notes = ["EXPERIMENT – keine Standardgrafik. Nur bestätigte Verbindungen; Kontakte am selben Ort um den Ortspunkt gruppiert (dünne Linie = Ortspunkt)."]
    if variant == "country":
        notes.append("Variante „nur Wohnland“: Kontakte im Ausland am Länderpunkt (gestrichelter Kreis), keine erfundenen Städte.")
    if unplaced:
        notes[-1] += f" Ohne Position: {', '.join(unplaced)}."
    p = page(ctx, "G2-Karte · Experiment: geografische Lage der Kontakte",
             "Bestätigte Verbindungen zwischen Kontakten auf einer groben Karte (Testfall 002, synthetisch)",
             main_w=main_w, main_h=main_h, legend="bottom", sections=sections, notes=notes)
    ax = p.main
    ax.set_zorder(2)  # nodes and ties above the map panels
    for panel in panels:
        draw_basemap(p.figure, ax, panel, countries, country_only)
    lx0, ly0 = panels[1].to_in(local.lat[0], local.lon[0])
    lx1, ly1 = panels[1].to_in(local.lat[1], local.lon[1])
    ax.add_patch(Rectangle((lx0, ly0), lx1 - lx0, ly1 - ly0, fill=False, edgecolor=MUTED, linewidth=0.8, linestyle=(0, (2, 2)), zorder=3))

    def panel_of(cid):
        lat, lon = anchors[cid]
        if local.contains(lat, lon) and ctx.derived.area(cid) in (Area.MARBURG, Area.MITTELHESSEN, Area.GERMANY_OTHER):
            return local
        return next(pn for pn in panels[:2] if pn.contains(lat, lon))

    points = {cid: panel_of(cid).to_in(*anchors[cid]) for cid in anchors}
    nodes = sorted(points)
    start = {}
    for cid in nodes:
        same = sorted(c for c in nodes if points[c] == points[cid])
        i, k = same.index(cid), len(same)
        r = 0.0 if k == 1 else max(0.32, k * 0.34 / (2 * math.pi))
        start[cid] = (points[cid][0] + r * math.cos(2 * math.pi * i / k), points[cid][1] + r * math.sin(2 * math.pi * i / k))
    placed = force_layout(nodes, [], start=start, project=lambda _n, q: q, pulls=[(c, points[c], 0.25) for c in nodes],
                          repulsion=0.0, spring=0.0, iterations=300, min_distance=2 * NODE_R + 0.06, step=0.03)
    for cid in nodes:
        (x0, y0), (x1, y1) = points[cid], placed[cid]
        if math.hypot(x1 - x0, y1 - y0) > 0.02:
            ax.plot([x0, x1], [y0, y1], color="#8A939C", linewidth=0.5, zorder=3)
    for (lat, lon) in {anchors[c] for c in nodes if kinds[c] == "place"}:
        pn = next(pn for pn in panels if pn.contains(lat, lon))
        if pn is panels[1] and local.contains(lat, lon):
            pn = local
        ax.add_patch(Circle(pn.to_in(lat, lon), 0.035, facecolor="#1F2933", edgecolor="none", zorder=3.5))
    for iso in country_only:
        props = by_iso[iso]["properties"]
        members = [c for c in nodes if kinds[c] == "country" and anchors[c] == (props["LABEL_Y"], props["LABEL_X"])]
        cx = np.mean([placed[c][0] for c in members])
        cy = np.mean([placed[c][1] for c in members])
        radius = max(math.hypot(placed[c][0] - cx, placed[c][1] - cy) for c in members) + NODE_R + 0.12
        ax.add_patch(Circle((cx, cy), radius, fill=False, edgecolor=MUTED, linewidth=0.8, linestyle=(0, (3, 2)), zorder=3))
        ax.text(cx, cy + radius + 0.04, f"{props['NAME_DE']} (nur Land)", fontsize=7.5, color=INK, ha="center", va="bottom", zorder=8)
    labelled = set()
    for cid in nodes:
        c = ctx.case.contact(cid)
        name = c.residence_place if kinds[cid] == "place" else None
        if name and name not in labelled and ctx.derived.area(cid) is not Area.MARBURG:
            labelled.add(name)
            x, y = points[cid]
            ax.text(x + 0.07, y - 0.07, name, fontsize=7.5, color=MUTED, ha="left", va="top", zorder=8)
    mx, my = local.to_in(*PLACES["Marburg"])
    ax.text(mx, my + 0.62, "Marburg", fontsize=8.5, fontweight="bold", color=INK, ha="center", va="bottom", zorder=8)
    area = {cid: ctx.derived.area(cid) for cid in nodes}
    for a, b in ctx.derived.confirmed_edges:
        if a not in placed or b not in placed:
            continue
        same = area[a] is area[b]
        ax.plot(*zip(placed[a], placed[b]), color=TIE if same else TIE_BETWEEN, linewidth=0.9 if same else 0.7,
                linestyle="solid" if same else (0, (4, 2.5)), zorder=4)
    draw_nodes(ax, placed, {cid: relation_fill(ctx.case, cid) for cid in placed}, zorder=5)
    return p.figure


def main() -> int:
    roots = Roots.load()
    folder = synthetic_source()
    case = read_case(folder)
    if case.metadata.get("provenance") != "fully_synthetic" or case.metadata.get("case_type") != "test":
        print("only the fully synthetic test case is accepted", file=sys.stderr)
        return 1
    validation = validate(case)
    ctx = Context(case, validation.derived)
    basemap = roots.resolve(StorageRef("WORKSPACE", BASEMAP))
    countries = json.loads(basemap.read_text(encoding="utf-8"))["features"]
    run_id = ids.new_run_id(datetime.now(timezone.utc))
    out = roots.resolve(StorageRef("WORKSPACE", f"runs/{run_id}"), writable=True)
    out.mkdir(parents=True, exist_ok=False)
    written = []
    for variant in ("exact", "country"):
        with rc():
            figure = render(ctx, variant, countries)
            written += save_figure(figure, out / f"002_test_synthetic_G2map_experiment_{variant}", ("png", "svg"))
    (out / "run_record.json").write_text(json.dumps({
        "format": "mares-run-record/v0-draft", "pipeline": "network_v1 experiment g2_map", "run_id": run_id,
        "case": case.code, "status": "COMPLETED", "standard_figure": False,
        "basemap": {"ref": f"WORKSPACE:{BASEMAP}", "source": "Natural Earth 1:50m admin 0 countries (public domain)"},
        "outputs": [p.name for p in written],
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"WORKSPACE:runs/{run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
