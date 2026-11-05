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
    ("Kyjiw", "UKR"): (50.45, 30.52),
}


def basemap() -> dict:
    features = []
    for iso, (continent, name, lat, lon, h) in COUNTRIES.items():
        ring = [[lon - h, lat - h], [lon + h, lat - h], [lon + h, lat + h], [lon - h, lat + h], [lon - h, lat - h]]
        features.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring]},
                         "properties": {"ADM0_A3": iso, "CONTINENT": continent, "NAME_DE": name, "LABEL_X": lon, "LABEL_Y": lat}})
    return {"type": "FeatureCollection", "features": features}


def gazetteer_text(places=PLACES) -> str:
    return "place;country_iso3;lat;lon;basis\n" + "".join(f"{p};{iso};{lat};{lon};synthetic\n" for (p, iso), (lat, lon) in places.items())


def countries() -> dict:
    return {f["properties"]["ADM0_A3"]: f for f in basemap()["features"]}


def gazetteer(tmp_path, places=PLACES) -> dict:
    path = tmp_path / "gazetteer.csv"
    path.write_text(gazetteer_text(places), encoding="utf-8")
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


def test_near_places_form_a_place_group_und_umgebung(case, tmp_path):
    layout = x1_layout(context(case), gazetteer(tmp_path), countries())
    marburg = next(p for p in layout.places if p.places[0][0] == "Marburg")
    assert {name for name, _ in marburg.places} == {"Marburg", "Wehrda", "Cölbe", "Lahntal", "Kirchhain"}  # all within 20 km
    assert marburg.title == f"Marburg und Umgebung · n = {len(marburg.members)}" and marburg.sub.startswith("Marburg 10 · ")
    giessen = next(p for p in layout.places if p.places[0][0] == "Gießen")
    assert [name for name, _ in giessen.places] == ["Gießen", "Wetzlar"]  # 26 km from Marburg: a group of its own
    berlin = next(p for p in layout.places if p.places[0][0] == "Berlin")
    assert not berlin.group and berlin.title == "Berlin" and not berlin.sub
    bogota = next(p for p in layout.places if p.places[0][0] == "Bogotá")
    assert [name for name, _ in bogota.places] == ["Bogotá"]  # Medellín (about 240 km) is never "Umgebung", even if symbols collide
    assert any(p.places == [("Medellín", 1)] for p in layout.places)


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


def test_place_boxes_sit_off_the_nodes_and_their_leader_runs_through_a_free_slot(case, tmp_path):
    layout = x1_layout(context(case), gazetteer(tmp_path), countries())
    boxes = [p.box for p in layout.places]
    for i, box in enumerate(boxes):
        for other in boxes[i + 1:]:
            assert not (box[0] < other[2] and other[0] < box[2] and box[1] < other[3] and other[1] < box[3])
        for x, y in layout.positions.values():
            assert not (box[0] < x + NODE_R and x - NODE_R < box[2] and box[1] < y + NODE_R and y - NODE_R < box[3])
    for p in layout.places:
        if len(p.members) < 2:
            continue
        sx, sy = min(max(p.hub[0], p.box[0]), p.box[2]), min(max(p.hub[1], p.box[1]), p.box[3])
        for cid in p.members:  # the leader from the box to the place point passes no node of its place
            x, y = layout.positions[cid]
            dx, dy = p.hub[0] - sx, p.hub[1] - sy
            t = max(0.0, min(1.0, ((x - sx) * dx + (y - sy) * dy) / (dx * dx + dy * dy)))
            assert math.hypot(sx + t * dx - x, sy + t * dy - y) > NODE_R * 0.9, (p.places[0][0], cid)


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
    assert {line.get_gid() for line in ax.lines} <= {"leader", "offset"}  # box leaders and lines to a true place point only
    layout = x1_layout(ctx, gazetteer(tmp_path), countries())
    gids = [p.get_gid() for p in ax.patches]
    assert gids.count("place-box") == gids.count("place-point") == len(layout.places)
    assert gids.count("place-disc") == sum(1 for p in layout.places if len(p.members) > 1)
    texts = " ".join(t.get_text() for t in figure.findobj(Text))
    assert "X1 · Geografische Verteilung des persönlichen Netzwerks" in texts and "TESTFALL 002*" in texts
    assert "Fassung 2.1" in texts and "keine Standardgrafik" in texts and "Keine Verbindungslinien" in texts
    assert "Marburg und Umgebung · n = 14" in texts


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
    assert record["standard_figure"] is False and record["version"] == "2.1" and record["unresolved"] == ["A22"] and str(folders["intake"]) not in json.dumps(record)


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
