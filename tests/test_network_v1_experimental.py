"""Experimental figure X1 (geographic distribution): layout rules, drawing, output location. Synthetic data only: case
002, a tiny artificial basemap and a place directory of its invented places."""

from __future__ import annotations

import json
import math

import pytest
from matplotlib.patches import PathPatch
from matplotlib.text import Text

from mares.core.refs import StorageRef
from mares.network_v0.figures.style import rc
from mares.network_v1.case import read_case
from mares.network_v1.experimental import (
    BASEMAP, GAZETTEER, NODE_R, X1Error, read_gazetteer, render_x1, x1, x1_layout,
)
from mares.network_v1.figures.base import Context
from mares.network_v1.testcases import SYNTHETIC_CODE
from mares.network_v1.validate import validate
from network_v1_fixtures import copy_002, machine, read_rows, roots_for, write_rows

# country: (continent, German name, label point lat, lon, half size of the square in degrees)
COUNTRIES = {
    "DEU": ("Europe", "Deutschland", 51.0, 10.0, 4.0), "ESP": ("Europe", "Spanien", 40.0, -4.0, 4.0),
    "FRA": ("Europe", "Frankreich", 46.5, 2.5, 4.0), "COL": ("South America", "Kolumbien", 4.0, -73.0, 5.0),
    "ECU": ("South America", "Ecuador", -1.5, -78.0, 2.0), "USA": ("North America", "Vereinigte Staaten", 39.0, -98.0, 15.0),
    "CAN": ("North America", "Kanada", 56.0, -100.0, 12.0), "JPN": ("Asia", "Japan", 36.0, 138.0, 3.0),
    "UKR": ("Europe", "Ukraine", 49.0, 31.0, 4.0),
}
PLACES = {  # public coordinates of the invented places of case 002 (as in pilots/network_v1_map)
    ("Marburg", "DEU"): (50.81, 8.77), ("Wehrda", "DEU"): (50.84, 8.76), ("Cölbe", "DEU"): (50.85, 8.78),
    ("Lahntal", "DEU"): (50.87, 8.69), ("Kirchhain", "DEU"): (50.83, 8.92), ("Gießen", "DEU"): (50.58, 8.68),
    ("Wetzlar", "DEU"): (50.56, 8.50), ("Kassel", "DEU"): (51.31, 9.48), ("Frankfurt am Main", "DEU"): (50.11, 8.68),
    ("Berlin", "DEU"): (52.52, 13.40), ("Madrid", "ESP"): (40.42, -3.70), ("Barcelona", "ESP"): (41.39, 2.17),
    ("Lyon", "FRA"): (45.76, 4.84), ("Bogotá", "COL"): (4.71, -74.07), ("Medellín", "COL"): (6.24, -75.58),
    ("Quito", "ECU"): (-0.18, -78.47), ("Miami", "USA"): (25.76, -80.19), ("Toronto", "CAN"): (43.65, -79.38),
    ("Kyjiw", "UKR"): (50.45, 30.52), ("Chía", "COL"): (4.86, -74.06),
}


def basemap() -> dict:
    features = []
    for iso, (continent, name, lat, lon, h) in COUNTRIES.items():
        ring = [[lon - h, lat - h], [lon + h, lat - h], [lon + h, lat + h], [lon - h, lat + h], [lon - h, lat - h]]
        features.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring]},
                         "properties": {"ADM0_A3": iso, "CONTINENT": continent, "NAME_DE": name, "LABEL_X": lon, "LABEL_Y": lat}})
    return {"type": "FeatureCollection", "features": features}


GROUP_WITH = {"Wehrda": "Marburg", "Cölbe": "Marburg", "Lahntal": "Marburg", "Kirchhain": "Marburg", "Wetzlar": "Gießen",
              "Chía": "Bogotá"}  # the regional assignment of the place directory (synthetic)


def gazetteer_text(places=PLACES, *, group_with=GROUP_WITH) -> str:
    if group_with is None:
        return "place;country_iso3;lat;lon;basis\n" + "".join(f"{p};{iso};{lat};{lon};synthetic\n" for (p, iso), (lat, lon) in places.items())
    return "place;country_iso3;lat;lon;basis;group_with\n" + "".join(
        f"{p};{iso};{lat};{lon};synthetic;{group_with.get(p, '')}\n" for (p, iso), (lat, lon) in places.items())


def countries() -> dict:
    return {f["properties"]["ADM0_A3"]: f for f in basemap()["features"]}


def gazetteer(tmp_path, places=PLACES, *, group_with=GROUP_WITH) -> dict:
    path = tmp_path / "gazetteer.csv"
    path.write_text(gazetteer_text(places, group_with=group_with), encoding="utf-8")
    return read_gazetteer(path)


def context(folder):
    case = read_case(folder)
    return Context(case, validate(case).derived)


@pytest.fixture
def case(tmp_path):
    return copy_002(tmp_path / "tree")


def test_panels_are_america_europe_germany_from_left_to_right(case, tmp_path):
    layout = x1_layout(context(case), gazetteer(tmp_path), countries())
    assert [p.region.key for p in layout.panels] == ["americas", "europe", "germany"]
    xs = [p.x for p in layout.panels]
    assert xs == sorted(xs) and all(a.x + a.width < b.x for a, b in zip(layout.panels, layout.panels[1:]))
    assert {p.region.key: p.count for p in layout.panels} == {"americas": 7, "europe": 3, "germany": 21}


def test_every_assignable_contact_is_placed_once_and_nodes_never_overlap(case, tmp_path):
    ctx = context(case)
    layout = x1_layout(ctx, gazetteer(tmp_path), countries())
    assert layout.unresolved == ["A22"] and not layout.not_in_gazetteer  # A22: ambiguous place, not drawn
    assert set(layout.positions) == set(ctx.case.contact_ids) - {"A22"}
    points = list(layout.positions.values())
    for i, (x0, y0) in enumerate(points):
        for x1_, y1 in points[i + 1:]:
            assert math.hypot(x1_ - x0, y1 - y0) >= 2 * NODE_R
    for cl in layout.places:  # every node inside the panel of its region
        panel = next(p for p in layout.panels if p.region.key == cl.region)
        for cid in cl.members:
            x, y = layout.positions[cid]
            assert panel.x < x < panel.x + panel.width and panel.y < y < panel.y + panel.height


def _names(layout) -> dict:
    return {p.places[0][0]: [n for n, _ in p.places] for p in layout.places}


def test_places_join_the_place_the_directory_assigns_them_to(case, tmp_path):
    ctx = context(case)
    layout = x1_layout(ctx, gazetteer(tmp_path), countries())
    names = _names(layout)
    assert names["Marburg"] == ["Marburg", "Cölbe", "Kirchhain", "Lahntal", "Wehrda"] and names["Gießen"] == ["Gießen", "Wetzlar"]
    marburg = next(p for p in layout.places if p.places[0][0] == "Marburg")
    in_marburg = [c.id for c in ctx.case.contacts if c.residence_place in ("Marburg", "Cölbe", "Kirchhain", "Lahntal", "Wehrda")]
    assert marburg.title == f"Marburg und Umgebung · n = {len(in_marburg)}" and sorted(marburg.members) == sorted(in_marburg)
    assert marburg.sub.replace("\n", " · ") == "Marburg 10 · Cölbe · Kirchhain · Lahntal · Wehrda" and len(marburg.others) == 4
    for alone in ("Kassel", "Frankfurt am Main", "Berlin", "Bogotá", "Medellín"):
        assert names[alone] == [alone]
    assert sum(len(p.members) for p in layout.places) == len(ctx.case.contacts) - 1  # nobody lost (A22: not assignable)


def test_without_an_assignment_nothing_is_grouped(case, tmp_path):
    assert not any(p.group for p in x1_layout(context(case), gazetteer(tmp_path, group_with=None), countries()).places)


def test_grouping_depends_on_the_map_scale_and_a_distance_limit(case, tmp_path, monkeypatch):
    import mares.network_v1.experimental as x1mod

    monkeypatch.setattr(x1mod, "GROUP_MAP_IN", 0.01)  # a larger-scale map: the places stand apart again
    assert not any(p.group for p in x1_layout(context(case), gazetteer(tmp_path), countries()).places)
    monkeypatch.undo()
    far = {**GROUP_WITH, "Kassel": "Marburg"}  # 77 km: beyond GROUP_MAX_KM, whatever the directory says
    assert _names(x1_layout(context(case), gazetteer(tmp_path, group_with=far), countries()))["Kassel"] == ["Kassel"]


def test_no_chains_and_no_group_without_the_head_place(case, tmp_path):
    chain = {**GROUP_WITH, "Wehrda": "Lahntal"}  # Lahntal itself belongs to Marburg: Wehrda stays apart (one level only)
    names = _names(x1_layout(context(case), gazetteer(tmp_path, group_with=chain), countries()))
    assert names["Wehrda"] == ["Wehrda"] and "Lahntal" in names["Marburg"]
    rows = read_rows(case, "contacts.csv")
    for row in rows:
        if row["residence_place"] == "Gießen":
            row["residence_place"] = "Marburg"
    write_rows(case, "contacts.csv", rows)
    assert _names(x1_layout(context(case), gazetteer(tmp_path), countries()))["Wetzlar"] == ["Wetzlar"]  # no Gießen contact


def test_an_unknown_group_with_is_an_error(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("place;country_iso3;lat;lon;basis;group_with\nCölbe;DEU;50.85;8.78;x;Atlantis\n", encoding="utf-8")
    with pytest.raises(X1Error):
        read_gazetteer(bad)


def test_place_boxes_name_the_country_outside_germany_only(case, tmp_path):
    rows = read_rows(case, "contacts.csv")
    medellin = next(r for r in rows if r["residence_place"] == "Medellín")
    medellin["residence_place"] = "Chía"  # about 17 km from Bogotá: a place group abroad
    write_rows(case, "contacts.csv", rows)
    layout = x1_layout(context(case), gazetteer(tmp_path), countries())
    titles = {p.places[0][0]: p.title.replace("\n", " · ") for p in layout.places}  # a title may wrap
    assert titles["Bogotá"] == "Bogotá und Umgebung · Kolumbien · n = 4"  # group abroad: with the country
    assert titles["Madrid"] == "Madrid · Spanien" and titles["Toronto"] == "Toronto · Kanada"  # single places abroad
    assert titles["Berlin"] == "Berlin" and titles["Marburg"].startswith("Marburg und Umgebung · n = ")  # Germany: no country
    rows = read_rows(case, "contacts.csv")
    next(r for r in rows if r["residence_place"] == "Toronto")["residence_place"] = ""
    write_rows(case, "contacts.csv", rows)
    only = next(p for p in x1_layout(context(case), gazetteer(tmp_path), countries()).places if p.country_only)
    assert only.title.replace("\n", " · ") == "Kanada · nur Land bekannt"  # the country is the name already, not repeated


def test_extents_follow_the_contacts_and_germany_stays_the_largest_panel(case, tmp_path):
    layout = x1_layout(context(case), gazetteer(tmp_path), countries())
    panels = {p.region.key: p for p in layout.panels}
    assert panels["germany"].height > panels["europe"].height and panels["germany"].height > panels["americas"].height
    assert all(p.y + p.height == pytest.approx(layout.height) for p in layout.panels)  # top-aligned
    for p in layout.places:  # every place inside its panel, with room around it
        lat, lon = p.anchor
        pn = panels[p.region]
        assert pn.lon[0] < lon < pn.lon[1] and pn.lat[0] < lat < pn.lat[1]
    de = panels["germany"]
    assert 5.5 <= de.lon[0] and de.lon[1] <= 15.5 and 47.0 <= de.lat[0] and de.lat[1] <= 55.3  # Germany stays Germany
    assert de.lon[1] - de.lon[0] >= 9.0 - 1e-9  # ... and recognisable
    assert panels["europe"].lon[1] < 19.5  # 002: Spain and France only, no empty Eastern Europe
    assert panels["americas"].lat[1] > 43.65  # 002 has a contact in Toronto
    rows = read_rows(case, "contacts.csv")
    for row in rows:
        if row["residence_country_iso3"] in ("USA", "CAN"):
            row.update(residence_place="Bogotá", residence_country="Kolumbien", residence_country_iso3="COL")
    rows[0].update(residence_place="Kyjiw", residence_country="Ukraine", residence_country_iso3="UKR")
    write_rows(case, "contacts.csv", rows)
    panels = {p.region.key: p for p in x1_layout(context(case), gazetteer(tmp_path), countries()).panels}
    assert panels["americas"].lat[1] < 25  # only South America: no North America shown
    assert panels["europe"].lon[1] > 30.52  # an eastern contact widens Europe


def test_a_panel_without_contacts_shows_its_default_extent(tmp_path):
    folder = copy_002(tmp_path / "tree")
    rows = [r for r in read_rows(folder, "contacts.csv") if r["residence_country_iso3"] not in ("ESP", "FRA")]
    write_rows(folder, "contacts.csv", rows)
    ids = {r["contact_id"] for r in rows}
    for table, keys in (("communication.csv", ("contact_id",)), ("group_memberships.csv", ("contact_id",)),
                        ("alter_connections.csv", ("contact_a", "contact_b"))):
        write_rows(folder, table, [r for r in read_rows(folder, table) if all(r[k] in ids for k in keys)],
                   header=list(read_rows(folder, table)[0]))
    layout = x1_layout(context(folder), gazetteer(tmp_path), countries())
    europe = next(p for p in layout.panels if p.region.key == "europe")
    assert (europe.lon, europe.lat, europe.count) == ((-10.5, 19.5), (35.0, 59.0), 0)


def _geometry(case, tmp_path):
    from mares.network_v1 import experimental as x

    layout = x1_layout(context(case), gazetteer(tmp_path), countries())
    return x, layout


@pytest.mark.parametrize("variant", ["002", "no_north"])
def test_place_points_and_names_always_stay_visible(case, tmp_path, variant):
    if variant == "no_north":  # another arrangement of the same places
        rows = read_rows(case, "contacts.csv")
        for row in rows:
            if row["residence_country_iso3"] in ("USA", "CAN"):
                row.update(residence_place="Medellín", residence_country="Kolumbien", residence_country_iso3="COL")
        write_rows(case, "contacts.csv", rows)
    x, layout = _geometry(case, tmp_path)
    for p in layout.places:
        same = [o for o in layout.places if o.region == p.region]
        points = [q for o in same for q in [o.point] + o.others]
        for q in points:  # no disc and no box on any place point
            assert math.hypot(p.hub[0] - q[0], p.hub[1] - q[1]) >= p.radius + x.POINT_R, (p.title, q)
            assert not x._box_hits_disc(p.box, q, x.POINT_R), (p.title, q)
        for o in same:  # names are never covered by contacts
            assert not x._box_hits_disc(p.box, o.hub, o.radius), (p.title, o.title)
        for x_, y_ in layout.positions.values():
            assert not (p.box[0] < x_ + NODE_R and x_ - NODE_R < p.box[2] and p.box[1] < y_ + NODE_R and y_ - NODE_R < p.box[3])


def test_discs_sit_beside_their_point_tied_by_a_line_and_never_overlap(case, tmp_path):
    x, layout = _geometry(case, tmp_path)
    for i, p in enumerate(layout.places):
        assert math.hypot(p.hub[0] - p.point[0], p.hub[1] - p.point[1]) > p.radius  # beside the point, never on it
        for o in layout.places[i + 1:]:
            if o.region == p.region:
                assert math.hypot(p.hub[0] - o.hub[0], p.hub[1] - o.hub[1]) >= p.radius + o.radius, (p.title, o.title)
    marburg = next(p for p in layout.places if p.places[0][0] == "Marburg")
    germany = next(pn for pn in layout.panels if pn.region.key == "germany")
    assert marburg.point == germany.to_in(*marburg.anchor)  # the place point stays where the place is


def test_every_box_belongs_to_its_place_point_at_a_glance(case, tmp_path):
    x, layout = _geometry(case, tmp_path)
    leaders = [(x._box_point(p.box, *p.point), p.point) for p in layout.places]
    connectors = [(p.point, x._disc_edge(p)) for p in layout.places]
    for i, p in enumerate(layout.places):
        start, point = leaders[i]
        same = [o for o in layout.places if o.region == p.region]
        for o in same:
            assert not x._segment_hits_disc(start, point, o.hub, o.radius), (p.title, o.title)  # never under a disc
            if o is not p:
                assert not x._segment_hits_box(start, point, o.box), (p.title, o.title)  # never under another box
                if x._gap(p.box, p.point) < 0.3:  # a box right at its point is nearest to it; a farther box has a free leader
                    assert x._gap(p.box, o.point) >= x._gap(p.box, p.point), (p.title, o.title)
        for j, (a_, b_) in enumerate(leaders):
            assert j == i or not x._segments_cross(start, point, a_, b_), (p.title, layout.places[j].title)
        for j, (a_, b_) in enumerate(connectors):
            assert j == i or not x._segments_cross(start, point, a_, b_), (p.title, layout.places[j].title)
    titles = {p.places[0][0]: p for p in layout.places}
    assert not x._overlaps(titles["Marburg"].box, titles["Gießen"].box)


def test_lines_and_points_are_drawn_above_every_fill(case, tmp_path):
    with rc():
        figure = x1(context(case), gazetteer(tmp_path), countries())
    ax = figure.axes[0]
    line = min(line.get_zorder() for line in ax.lines if line.get_gid() in ("leader", "connector"))
    fills = [p.get_zorder() for p in ax.patches if p.get_gid() == "place-disc"]
    assert line > max(fills)
    point = min(p.get_zorder() for p in ax.patches if p.get_gid() == "place-point")
    assert point > line  # the place point marks the end of its lines


def test_a_contact_known_only_by_country_sits_at_the_country_point_marked_as_unsharp(case, tmp_path):
    rows = read_rows(case, "contacts.csv")
    for row in rows:
        if row["residence_place"] == "Toronto":
            row["residence_place"] = ""
            cid = row["contact_id"]
    write_rows(case, "contacts.csv", rows)
    ctx = context(case)
    layout = x1_layout(ctx, gazetteer(tmp_path), countries())
    cluster = next(cl for cl in layout.places if cid in cl.members)
    assert cluster.country_only and cluster.anchor == (56.0, -100.0) and "nur Land bekannt" in cluster.title  # never a city
    with rc():
        figure = x1(ctx, gazetteer(tmp_path), countries())
    assert "nur Wohnland bekannt (Lage unscharf)" in " ".join(t.get_text() for t in figure.findobj(Text))


def test_a_place_missing_in_the_directory_is_named_not_guessed(case, tmp_path):
    places = {k: v for k, v in PLACES.items() if k[0] != "Lyon"}
    ctx = context(case)
    layout = x1_layout(ctx, gazetteer(tmp_path, places), countries())
    lyon = [c.id for c in ctx.case.contacts if c.residence_place == "Lyon"]
    assert layout.not_in_gazetteer == lyon and not set(lyon) & set(layout.positions)
    with rc():
        figure = x1(ctx, gazetteer(tmp_path, places), countries())
    texts = " ".join(t.get_text() for t in figure.findobj(Text))
    assert f"Ort ohne Koordinaten im Ortsverzeichnis: {lyon[0]}." in texts and "Wohnort nicht darstellbar: A22." in texts


def test_further_regions_appear_only_when_needed_between_america_and_europe(case, tmp_path):
    rows = read_rows(case, "contacts.csv")
    rows[-1].update(residence_place="", residence_country="Japan", residence_country_iso3="JPN")
    write_rows(case, "contacts.csv", rows)
    layout = x1_layout(context(case), gazetteer(tmp_path), countries())
    assert [p.region.key for p in layout.panels] == ["americas", "asia", "europe", "germany"]


def test_x1_has_no_ties_but_place_boxes_points_and_pale_discs(case, tmp_path):
    ctx = context(case)
    with rc():
        figure = x1(ctx, gazetteer(tmp_path), countries())
    ax = figure.axes[0]
    assert not [p for p in ax.patches if isinstance(p, PathPatch)]  # no contact-contact ties
    assert {line.get_gid() for line in ax.lines} <= {"leader", "connector"}  # box and disc lines to the place point only
    layout = x1_layout(ctx, gazetteer(tmp_path), countries())
    gids = [p.get_gid() for p in ax.patches]
    assert gids.count("place-box") == gids.count("place-point") == len(layout.places)
    assert gids.count("place-disc") == sum(1 for p in layout.places if len(p.members) > 1)
    texts = " ".join(t.get_text() for t in figure.findobj(Text))
    assert "X1 · Geografische Verteilung des persönlichen Netzwerks" in texts and "TESTFALL 002*" in texts
    assert "Fassung 2.5" in texts and "keine Standardgrafik" in texts and "keine Verbindungslinien" in texts
    assert "Marburg und Umgebung · n = 14" in texts.replace("\n", " · ") and "Gießen und Umgebung" in texts
    assert gids.count("true-point") >= sum(len(p.others) for p in layout.places)  # other places of a group stay visible


def test_render_x1_writes_into_experimental_and_leaves_graphics_alone(tmp_path):
    folders = machine(tmp_path)
    case = copy_002(folders["intake"])
    gaz = folders["intake"] / GAZETTEER
    gaz.parent.mkdir(parents=True)
    gaz.write_text(gazetteer_text(), encoding="utf-8")
    base = folders["workspace"] / BASEMAP
    base.parent.mkdir(parents=True)
    base.write_text(json.dumps(basemap()), encoding="utf-8")
    result = render_x1(roots_for(folders), StorageRef("INTAKE", f"network_v1/pilots/{SYNTHETIC_CODE}"))
    assert result.status == "COMPLETED"
    assert sorted(p.name for p in (case / "experimental").iterdir()) == [
        f"{SYNTHETIC_CODE}_X1_geografische_verteilung.png", f"{SYNTHETIC_CODE}_X1_geografische_verteilung.svg"]
    assert not (case / "graphics").exists()  # the standard figures are not touched
    record = json.loads((folders["workspace"] / "runs" / result.run_id / "run_record.json").read_text(encoding="utf-8"))
    assert record["standard_figure"] is False and record["version"] == "2.5" and record["unresolved"] == ["A22"] and str(folders["intake"]) not in json.dumps(record)


def test_render_x1_needs_the_basemap_and_a_valid_directory(tmp_path):
    folders = machine(tmp_path)
    copy_002(folders["intake"])
    with pytest.raises(X1Error):
        render_x1(roots_for(folders), StorageRef("INTAKE", f"network_v1/pilots/{SYNTHETIC_CODE}"))
    bad = tmp_path / "bad.csv"
    bad.write_text("place;country_iso3;lat;lon;basis\nMarburg;DEU;north;8.77;x\n", encoding="utf-8")
    with pytest.raises(X1Error):
        read_gazetteer(bad)


def test_the_command_line_draws_x1_for_one_case(tmp_path, capsys):
    from mares.network_v1.cli import main

    folders = machine(tmp_path)
    copy_002(folders["intake"])
    (folders["intake"] / GAZETTEER).parent.mkdir(parents=True)
    (folders["intake"] / GAZETTEER).write_text(gazetteer_text(), encoding="utf-8")
    (folders["workspace"] / BASEMAP).parent.mkdir(parents=True)
    (folders["workspace"] / BASEMAP).write_text(json.dumps(basemap()), encoding="utf-8")
    code = main(["experimental-x1", "--case", f"INTAKE:network_v1/pilots/{SYNTHETIC_CODE}", "--formats", "png"], roots=roots_for(folders))
    assert code == 0 and "X1 COMPLETED" in capsys.readouterr().out
