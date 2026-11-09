"""Standard figure X1 (geographic distribution): layout rules, drawing, texts, its place in the case run. Synthetic data
only: case 002, a tiny artificial basemap and a place directory of its invented places (network_v1_fixtures)."""

from __future__ import annotations

import json
import math

import pytest
from matplotlib.patches import PathPatch
from matplotlib.text import Text

from mares.core.refs import StorageRef
from mares.network_v0.figures.style import rc
from mares.network_v1.case import read_case
from mares.network_v1.figures.maps import BASEMAP, GAZETTEER, NODE_R, X1Error, read_gazetteer, x1, x1_layout
from mares.network_v1.figures.base import Context
from mares.network_v1.testcases import SYNTHETIC_CODE
from mares.network_v1.validate import validate
from network_v1_fixtures import (  # noqa: F401  (basemap, gazetteer_text: used by the tests below)
    COUNTRIES, GROUP_WITH, PLACES, basemap, copy_002, countries, gazetteer, gazetteer_text, machine, read_rows, roots_for, write_rows,
)

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
    import mares.network_v1.figures.maps as x1mod

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
    assert titles["Berlin"] == "Berlin" and titles["Marburg"].startswith("Marburg und Umgebung · ")  # Germany: no country
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


def test_a_region_without_contacts_gets_no_panel(tmp_path):
    folder = copy_002(tmp_path / "tree")
    rows = [r for r in read_rows(folder, "contacts.csv") if r["residence_country_iso3"] not in ("ESP", "FRA")]
    write_rows(folder, "contacts.csv", rows)
    ids = {r["contact_id"] for r in rows}
    for table, keys in (("communication.csv", ("contact_id",)), ("group_memberships.csv", ("contact_id",)),
                        ("alter_connections.csv", ("contact_a", "contact_b"))):
        write_rows(folder, table, [r for r in read_rows(folder, table) if all(r[k] in ids for k in keys)],
                   header=list(read_rows(folder, table)[0]))
    layout = x1_layout(context(folder), gazetteer(tmp_path), countries())
    assert [p.region.key for p in layout.panels] == ["americas", "germany"]  # no empty Europa panel
    assert all(p.count for p in layout.panels)


def _geometry(case, tmp_path):
    from mares.network_v1.figures import maps as x

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
        for node in layout.positions.values():  # no name on a contact (its circle, not the square around it)
            assert not x._box_hits_disc(p.box, node, NODE_R), (p.title, node)


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


def test_every_label_docks_at_its_own_disc(case, tmp_path):
    x, layout = _geometry(case, tmp_path)
    connectors = [(p.point, x._disc_edge(p)) for p in layout.places]
    for p in layout.places:
        own = x._gap(p.box, p.hub) - p.radius
        assert -1e-9 <= own <= 0.35, p.title  # docked at the disc, never on it
        for o in layout.places:
            if o is not p and o.region == p.region:
                assert x._reach(p.box, o) >= x._reach(p.box, p), (p.title, o.title)  # read as its own callout's
                assert not x._overlaps(p.box, o.box), (p.title, o.title)
        for a_, b_ in connectors:
            assert not x._segment_hits_box(a_, b_, p.box), p.title  # never hides a line


@pytest.mark.parametrize("variant", ["002", "crowded"])
def test_every_callout_has_its_full_label_right_at_the_circle(case, tmp_path, variant):
    if variant == "crowded":  # more contacts in Gießen: larger discs in the dense part of the Germany panel
        rows = read_rows(case, "contacts.csv")
        for row in rows:
            if row["residence_place"] == "Berlin":
                row["residence_place"] = "Gießen"
        write_rows(case, "contacts.csv", rows)
    x, layout = _geometry(case, tmp_path)
    for p in layout.places:
        same = [o for o in layout.places if o.region == p.region]
        points = [q for o in same for q in [o.point] + o.others]
        lines = [(o.point, x._disc_edge(o)) for o in same]
        taken = [next(pn for pn in layout.panels if pn.region.key == p.region).title_box()] + [o.box for o in same if o is not p]
        panel = next(pn for pn in layout.panels if pn.region.key == p.region)
        assert x._label_cost(p, panel, points, same, taken, lines, p.box) == 0, p.title  # nothing hidden, unambiguous, inside


@pytest.mark.parametrize("variant", ["002", "frankfurt_first"])
def test_callouts_keep_the_geographic_reading_order(case, tmp_path, variant):
    if variant == "frankfurt_first":  # the southern place larger, so placed before the northern one
        rows = read_rows(case, "contacts.csv")
        for row in rows:
            if row["residence_place"] in ("Berlin", "Kassel"):
                row["residence_place"] = "Frankfurt am Main"
        write_rows(case, "contacts.csv", rows)
    x, layout = _geometry(case, tmp_path)
    for i, p in enumerate(layout.places):
        for o in layout.places[i + 1:]:
            if o.region == p.region:
                assert x._order_flips(p, p.hub, o, o.hub) == 0, (p.title, o.title)  # discs
                assert x._order_flips(p, x._centre(p.box), o, x._centre(o.box)) == 0, (p.title, o.title)  # labels
    by = {p.places[0][0]: p for p in layout.places}
    giessen, frankfurt = by["Gießen"], by["Frankfurt am Main"]
    assert giessen.hub[1] > frankfurt.hub[1] and x._centre(giessen.box)[1] > x._centre(frankfurt.box)[1]  # north above south


def test_lines_and_points_are_drawn_above_every_fill(case, tmp_path):
    with rc():
        figure = x1(context(case), gazetteer(tmp_path), countries())
    ax = figure.axes[0]
    line = min(line.get_zorder() for line in ax.lines if line.get_gid() == "connector")
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
    assert f"Wohnort nicht darstellbar: A22, {lyon[0]}." in texts  # one short note, in contact order, no technical reason
    assert "Ortsverzeichnis" not in texts


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
    assert {line.get_gid() for line in ax.lines} <= {"connector"}  # only the line from a callout to its place point
    boxes = [p for p in ax.patches if p.get_gid() == "place-box"]
    assert all(b.get_edgecolor()[3] == 0 for b in boxes)  # no frame: a soft ground only
    layout = x1_layout(ctx, gazetteer(tmp_path), countries())
    gids = [p.get_gid() for p in ax.patches]
    assert gids.count("place-box") == gids.count("place-point") == len(layout.places)
    assert gids.count("place-disc") == sum(1 for p in layout.places if len(p.members) > 1)
    texts = " ".join(t.get_text() for t in figure.findobj(Text))
    assert "Marburg und Umgebung" in texts and " · n = 14" in texts and "Gießen und Umgebung" in texts  # bold name, n = x
    assert gids.count("true-point") >= sum(len(p.others) for p in layout.places)  # other places of a group stay visible


def test_x1_shows_only_the_agreed_texts(case, tmp_path):
    with rc():
        figure = x1(context(case), gazetteer(tmp_path), countries())
    texts = [t.get_text() for t in figure.findobj(Text)]
    joined = " ".join(texts)
    assert "Geografische Verteilung des persönlichen Netzwerks" in texts  # the title, without the code X1
    assert not any(t.startswith("X1") for t in texts) and "Wo leben die Kontakte?" not in joined  # no code, no subtitle
    assert "TESTFALL 002* · SYNTHETISCH" in texts
    assert "MARES · network_v1 · 32 Kontakte" in texts  # no group count, no quality, no version
    assert "Kartengrundlage: Natural Earth." in texts and "Wohnort nicht darstellbar: A22." in texts
    for gone in ("Experimentell", "experimentell", "Fassung", "Standardgrafik", "Verbindungslinien", "Maßstab", "daneben gesetzt",
                 "Zahl = Kontakte", "Nachbarorte", "Gruppen", "Datenqualität"):
        assert gone not in joined, gone
    assert "Beziehungstyp" in texts and "Wohnort (Ortspunkt)" in texts
    assert "Bogotá" in texts and "Kolumbien · n = 3" in joined
    assert "Madrid" in texts and not any(t.endswith("n = 1") for t in texts)  # a single contact needs no number


def test_x1_hides_the_quality_of_a_real_case(case, tmp_path):
    from network_v1_fixtures import set_metadata

    set_metadata(case, case_type="pilot", provenance="survey", data_quality="VALIDATED", display_code="PILOT XY")
    with rc():
        texts = " ".join(t.get_text() for t in x1(context(case), gazetteer(tmp_path), countries()).findobj(Text))
    assert "FALL · PILOT XY" in texts and "VALIDATED" not in texts and "Datenqualität" not in texts


def test_the_case_run_draws_x1_into_graphics_next_to_the_other_figures(tmp_path):
    from mares.network_v1.figures import expected_files
    from mares.network_v1.run import process_case

    folders = machine(tmp_path)  # with place directory and basemap
    case = copy_002(folders["intake"])
    result = process_case(roots_for(folders), StorageRef("INTAKE", f"network_v1/pilots/{SYNTHETIC_CODE}"), formats=("png", "svg"))
    assert result.status == "COMPLETED"
    names = {p.name for p in (case / "graphics").iterdir()}
    assert names == expected_files(SYNTHETIC_CODE, ("png", "svg")) and len(names) == 22
    assert {f"{SYNTHETIC_CODE}_X1_geografische_verteilung.png", f"{SYNTHETIC_CODE}_X1_geografische_verteilung.svg"} <= names
    assert not (case / "experimental").exists()
    sources = result.record["map_sources"]
    assert sources["gazetteer"]["ref"] == {"root": "INTAKE", "rel": GAZETTEER} and sources["basemap"]["ref"]["root"] == "WORKSPACE"
    assert str(folders["intake"]) not in json.dumps(result.record)


def test_without_map_sources_x1_is_skipped_with_the_reason(tmp_path):
    from mares.network_v1.run import process_case

    folders = machine(tmp_path)
    (folders["workspace"] / BASEMAP).unlink()
    case = copy_002(folders["intake"])
    result = process_case(roots_for(folders), StorageRef("INTAKE", f"network_v1/pilots/{SYNTHETIC_CODE}"))
    x1_entry = next(f for f in result.figures if f["code"] == "X1")
    assert x1_entry["status"] == "skipped" and x1_entry["reason"].startswith("Basiskarte fehlt (WORKSPACE:")
    assert not list((case / "graphics").glob("*X1*")) and len(list((case / "graphics").iterdir())) == 10
    bad = tmp_path / "bad.csv"
    bad.write_text("place;country_iso3;lat;lon;basis\nMarburg;DEU;north;8.77;x\n", encoding="utf-8")
    with pytest.raises(X1Error):
        read_gazetteer(bad)


def test_a_malformed_place_directory_stops_the_run_before_anything_is_written(tmp_path):
    from mares.network_v1.run import PipelineError, process_case

    folders = machine(tmp_path)
    (folders["intake"] / GAZETTEER).write_text("place;country_iso3;lat;lon;basis\nMarburg;DEU;north;8.77;x\n", encoding="utf-8")
    case = copy_002(folders["intake"])
    with pytest.raises(PipelineError):
        process_case(roots_for(folders), StorageRef("INTAKE", f"network_v1/pilots/{SYNTHETIC_CODE}"))
    assert not (case / "graphics").exists() and not list((folders["workspace"] / "runs").iterdir())


def test_the_experimental_command_is_gone(tmp_path):
    from mares.network_v1.cli import build_parser

    with pytest.raises(SystemExit):
        build_parser().parse_args(["experimental-x1", "--root", "INTAKE"])


def test_the_neighbour_option_puts_neighbouring_countries_on_the_germany_map(tmp_path):
    """Off in network_v1 (the Europa panel shows them); a scheme may switch it on (network_v0 does)."""
    from mares.network_v1.case import read_case as read
    from mares.network_v1.figures.base import Context as Ctx, Scheme
    from mares.network_v1.figures.maps import x1_layout as layout_of
    from mares.network_v1.testcases import synthetic_source as source
    from mares.network_v1.validate import validate as check
    from network_v1_fixtures import geo as geo_of

    class Together(Scheme):
        x1_neighbours_with_germany = True

    case = read(source())
    g = geo_of(tmp_path)
    plain = layout_of(Ctx(case, check(case).derived, g), g.gazetteer, g.countries)
    together = layout_of(Ctx(case, check(case).derived, g, Together()), g.gazetteer, g.countries)
    french = lambda lay: [p for p in lay.places if p.key and p.key[1] == "FRA"]  # noqa: E731
    assert french(plain) and all(p.region == "europe" for p in french(plain))
    assert french(together) and all(p.region == "germany" for p in french(together))
    germany = next(pn for pn in together.panels if pn.region.key == "germany")
    assert germany.region.title == "Deutschland und Frankreich"
    assert any("Frankreich" in p.tail for p in french(together))  # a place outside Germany names its country
    assert any(pn.region.key == "europe" for pn in together.panels)  # Spain is no neighbour: Europa stays
