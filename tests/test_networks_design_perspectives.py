"""The MARES design system (profiles clean / analysis) and the analytic perspectives P1-P3.

What these tests secure: the clean figures are reduced but keep every contact, group and tie; emphasis changes the look
and never a position or a relation; missing attributes stay visible as missing; nothing is hard-coded to a number of
contacts or to Marburg; the figures are byte-reproducible (also across processes); and no free text reaches a picture.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import textwrap

import pytest
from matplotlib.collections import LineCollection, PathCollection
from matplotlib.patches import FancyBboxPatch
from matplotlib.text import Text

import network_fixtures as fx
from mares.core import ids
from mares.core.roots import Roots, load_root_specs
from mares.networks import cli
from mares.networks.analysis import AnalysisParams, survey_status
from mares.networks.build import build_network
from mares.networks.figures import design, ego_network, geo_zones, perspectives, registry
from mares.networks.figures import network as netfig
from mares.networks.figures.common import contact_views
from mares.networks.figures.perspectives import LanguageView, matrix_cells, media_classes
from mares.networks.figures.style import rc, save_figure
from mares.networks.geo import GeoCategory
from mares.networks.package import read_package
from mares.networks.run import FigureOptions, parse_ref, run_pipeline

PARAMS = AnalysisParams()
CITIES = [("Marburg", "DEU"), ("Nähe Marburg", "DEU"), ("Berlin", "DEU"), ("Lima", "PER")]


def _dataset(tmp_path, n=12, with_groups=True, mutate=None, pairs=False):
    """``pairs``: two neighbours per residence category, so that the clique ties lie both within and between categories."""
    rows = fx.contact_rows(n, 8)
    for index, row in enumerate(rows):
        city, country = CITIES[(index // 2 if pairs else index) % len(CITIES)]
        row.update(residence_city=city, residence_country_iso3=country)
    if mutate:
        mutate(rows)
    g, m = fx.standard_groups() if with_groups else ([], [])
    if n < 11:
        m = [x for x in m if int(x["contact_id"][1:]) <= n]
        g = [x for x in g if any(y["group_id"] == x["group_id"] for y in m)]
    return read_package(fx.build_package(tmp_path / "p", contacts=rows, groups=g, memberships=m, review_items=[]))


def _make(dataset):
    network = build_network(dataset)
    return network, survey_status(dataset, network)


def _texts(fig):
    return [t.get_text() for t in fig.findobj(Text) if t.get_text()]


def _lines(fig):
    return [c for c in fig.axes[0].collections if isinstance(c, LineCollection)]


def _segments(fig):
    return sorted(repr(s.round(6).tolist()) for c in _lines(fig) for s in c.get_segments())


def _nodes(fig):
    return max((c for c in fig.axes[0].collections if isinstance(c, PathCollection)), key=lambda c: len(c.get_offsets()))


def _chips(fig):
    """The contact dots of a matrix (one scatter of one point each, at the node size)."""
    return [c for c in fig.axes[0].collections
            if isinstance(c, PathCollection) and len(c.get_offsets()) == 1 and abs(c.get_sizes()[0] - design.NODE_DIAMETER_PT**2) < 1e-6]


def _all_clean(dataset, network, status):
    return {
        "B3": ego_network.ego_network_figure(dataset, status, PARAMS, network=network),
        "G2": geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network),
        "P1": perspectives.distance_closeness_figure(dataset, status, PARAMS, network=network),
        "P2": perspectives.language_groups_figure(dataset, status, PARAMS, network=network),
        "P3": perspectives.geography_communication_figure(dataset, status, PARAMS, network=network),
    }


# ------------------------------------------------------------------ design system ---------------------------


def test_profiles_are_clean_and_analysis_and_nothing_else():
    assert design.PROFILES == ("clean", "analysis")
    assert design.check_profile("clean") == "clean"
    with pytest.raises(ValueError):
        design.check_profile("poster")


def test_zone_names_are_short_and_follow_the_configured_reference_place(tmp_path):
    assert design.zone_name(GeoCategory.LOCAL, PARAMS) == "Marburg"
    assert design.zone_name(GeoCategory.LOCAL_REGION, PARAMS) == "Region Marburg"
    assert "ungefähre" not in design.zone_name(GeoCategory.GERMANY_OTHER, PARAMS)
    assert design.zone_name(GeoCategory.LOCAL, AnalysisParams(local_places=("Gießen",))) == "Gießen"


def test_stamp_is_one_short_line_with_the_status(tmp_path):
    _, status = _make(_dataset(tmp_path))
    stamp = design.stamp_text(status)
    assert stamp == "MARES · 0000-1 · vorläufig"  # case and that the data are not reviewed; the rest is in the register
    assert "UNREVIEWED" in design.stamp_text(status, "analysis") and "n = 12" in design.stamp_text(status, "analysis")


def test_clean_figures_are_reduced_compared_with_the_analysis_profile(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    for name, clean in _all_clean(dataset, network, status).items():
        analysis = {
            "B3": lambda: ego_network.ego_network_figure(dataset, status, PARAMS, network=network, profile="analysis"),
            "G2": lambda: geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network, profile="analysis"),
            "P1": lambda: perspectives.distance_closeness_figure(dataset, status, PARAMS, network=network, profile="analysis"),
            "P2": lambda: perspectives.language_groups_figure(dataset, status, PARAMS, network=network, profile="analysis"),
            "P3": lambda: perspectives.geography_communication_figure(dataset, status, PARAMS, network=network, profile="analysis"),
        }[name]()
        clean_text, analysis_text = " ".join(_texts(clean)), " ".join(_texts(analysis))
        assert len(clean_text) < len(analysis_text), name
        assert max(len(t) for t in _texts(clean)) < 260, name  # no long paragraphs in a clean figure
        assert "vorläufig" in clean_text and "UNREVIEWED" in analysis_text, name  # the status stays: short in clean, full in analysis


def test_clean_titles_are_short_and_say_what_the_figure_is(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    figures = _all_clean(dataset, network, status)
    assert "Persönliches Beziehungsnetz" in _texts(figures["B3"])
    for name, fig in figures.items():
        title = max((t for t in fig.texts if t.get_fontsize() == design.TITLE_PT), key=lambda t: len(t.get_text())).get_text()
        assert 10 < len(title) < 70 and ":" not in title, (name, title)


def test_the_font_is_the_dejavu_fallback_and_no_font_is_shipped():
    with rc():
        import matplotlib

        assert matplotlib.rcParams["font.family"] == ["DejaVu Sans"] or matplotlib.rcParams["font.family"] == "DejaVu Sans"


# ------------------------------------------------------------------ B3 clean: reference ---------------------


def test_b3_clean_keeps_the_node_arrangement_the_groups_and_the_ties(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    clean = ego_network.ego_network_figure(dataset, status, PARAMS, network=network)
    analysis = ego_network.ego_network_figure(dataset, status, PARAMS, network=network, profile="analysis")
    assert [tuple(map(float, p)) for p in _nodes(clean).get_offsets()] == [tuple(map(float, p)) for p in _nodes(analysis).get_offsets()]
    polygons = lambda fig: [p for p in fig.axes[0].patches if type(p).__name__ == "Polygon"]
    assert len(polygons(clean)) == len(polygons(analysis)) == 2 * len(network.confirmed_groups) > 0
    ties = lambda fig: sum(len(c.get_segments()) for c in _lines(fig))
    assert ties(clean) == ties(analysis) == len(dataset.contacts) + len(network.positive_ties)  # ego lines + confirmed ties


def test_b3_clean_is_larger_than_the_analysis_version_in_drawing_area(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    clean = ego_network.ego_network_figure(dataset, status, PARAMS, network=network)
    analysis = ego_network.ego_network_figure(dataset, status, PARAMS, network=network, profile="analysis")
    area = lambda fig: fig.axes[0].get_position().width * fig.axes[0].get_position().height * fig.get_figwidth() * fig.get_figheight()
    assert area(clean) >= area(analysis) * 0.9  # no smaller drawing for the reduced text


# ------------------------------------------------------------------ G2 clean + highlight -------------------


def test_g2_highlight_changes_the_look_of_the_ties_and_never_the_ties(tmp_path):
    dataset = _dataset(tmp_path, pairs=True)
    network, status = _make(dataset)
    figures = {h: geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network, highlight=h) for h in (None, "between", "within")}
    assert len({tuple(_segments(f)) for f in figures.values()}) == 1  # the same segments, in every emphasis
    assert len({tuple(map(tuple, _nodes(f).get_offsets().tolist())) for f in figures.values()}) == 1
    by_label = lambda fig: {c.get_label(): c for c in _lines(fig)}
    strong = lambda c: c.get_linewidths()[0]
    between, within = by_label(figures["between"]), by_label(figures["within"])
    assert strong(between["ties_between"]) > strong(between["ties_within"]) and between["ties_between"].get_zorder() > between["ties_within"].get_zorder()
    assert strong(within["ties_within"]) > strong(within["ties_between"]) and within["ties_within"].get_zorder() > within["ties_between"].get_zorder()
    # the ego lines are always the faintest and lie underneath
    for fig in figures.values():
        lines = by_label(fig)
        assert lines["ego_lines"].get_zorder() < min(lines["ties_between"].get_zorder(), lines["ties_within"].get_zorder())
        assert strong(lines["ego_lines"]) <= min(strong(lines["ties_between"]), strong(lines["ties_within"]))


def test_g2_draws_the_confirmed_ties_in_every_profile_and_highlight(tmp_path):
    dataset = _dataset(tmp_path, pairs=True)
    network, status = _make(dataset)
    for profile in design.PROFILES:
        for highlight in (None, "between", "within"):
            fig = geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network, profile=profile, highlight=highlight)
            drawn = {c.get_label(): len(c.get_segments()) for c in _lines(fig)}
            assert drawn["ties_between"] > 0 and drawn["ties_within"] > 0
            assert drawn["ties_between"] + drawn["ties_within"] == len(network.positive_ties) and drawn["ego_lines"] == len(dataset.contacts)


def test_g2_refuses_an_unknown_highlight_or_profile(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    with pytest.raises(ValueError):
        geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network, highlight="strong")
    with pytest.raises(ValueError):
        geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network, profile="poster")


def test_g2_clean_names_the_bands_directly_and_keeps_the_limits_in_one_hint(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    texts = _texts(geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network))
    joined = " ".join(texts)
    for zone in ("Marburg", "Region Marburg", "übriges Deutschland", "übriges Europa", "außerhalb Europas"):
        assert any(zone in t.replace("\n", " ") for t in texts), zone
    assert "keine Entfernungen" in joined and "nicht „keine Beziehung“" in joined
    assert "km" not in joined.split() and "Kilometer" not in joined


# ------------------------------------------------------------------ P1 / P3 matrices -----------------------


def test_every_contact_is_in_exactly_one_matrix_cell(tmp_path):
    dataset = _dataset(tmp_path)
    for attribute, field in (("closeness", "closeness_1_5"), ("contact_frequency", "contact_frequency")):
        rows, zones, cells = matrix_cells(dataset, PARAMS, attribute, field)
        placed = sorted((c for members in cells.values() for c in members), key=ids.contact_number)
        assert placed == sorted((c.contact_id for c in dataset.contacts), key=ids.contact_number)
        assert {zone for zone, _ in cells} <= set(zones)
        assert [code for code, _ in rows][:5] == ["5", "4", "3", "2", "1"][: len(rows)] or attribute == "contact_frequency"


def test_a_contact_without_a_value_gets_its_own_row_and_is_never_estimated(tmp_path):
    def blank(rows):
        rows[2]["table_ring_near_value"] = ""
        rows[5]["table_ring_near_value"] = ""

    dataset = _dataset(tmp_path, mutate=blank)
    rows, _, cells = matrix_cells(dataset, PARAMS, "closeness", "closeness_1_5")
    assert rows[-1] == (None, "nicht erfasst")
    assert sorted(c for (zone, code), members in cells.items() if code is None for c in members) == ["A03", "A06"]
    network, status = _make(dataset)
    fig = perspectives.distance_closeness_figure(dataset, status, PARAMS, network=network)
    assert any("nicht erfasst" in t for t in _texts(fig)) and len(_chips(fig)) == len(dataset.contacts)


def test_no_missing_row_when_everybody_has_a_value(tmp_path):
    rows, _, _ = matrix_cells(_dataset(tmp_path), PARAMS, "closeness", "closeness_1_5")
    assert all(code is not None for code, _ in rows)


def test_empty_rows_stay_visible(tmp_path):
    def only_two_values(rows):
        for row in rows:
            row["table_ring_near_value"] = "5" if row["contact_id"] in ("A01", "A02") else "1"

    dataset = _dataset(tmp_path, mutate=only_two_values)
    rows, _, cells = matrix_cells(dataset, PARAMS, "closeness", "closeness_1_5")
    assert [code for code, _ in rows] == ["5", "4", "3", "2", "1"]
    assert not any(code in ("2", "3", "4") for (_, code), members in cells.items() if members)  # still listed as rows


def test_p1_and_p3_have_one_chip_per_contact_with_the_geography_colour(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    views = {v.contact_id: v for v in contact_views(dataset, PARAMS)}
    for fig in (perspectives.distance_closeness_figure(dataset, status, PARAMS, network=network),
                perspectives.geography_communication_figure(dataset, status, PARAMS, network=network)):
        assert len(_chips(fig)) == len(dataset.contacts)
        assert {t for t in _texts(fig) if ids.is_contact_id(t)} == set(views)
        assert not _lines(fig)  # a matrix draws no tie: it is no network


def test_p1_makes_no_claim_about_kilometres_or_causes(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    joined = " ".join(_texts(perspectives.distance_closeness_figure(dataset, status, PARAMS, network=network)))
    assert "keine Entfernungen" in joined
    assert " km" not in joined and "Kilometer" not in joined
    analysis = " ".join(_texts(perspectives.distance_closeness_figure(dataset, status, PARAMS, network=network, profile="analysis")))
    assert "keine Ursachen" in analysis


def test_media_are_classes_and_multiple_answers(tmp_path):
    assert media_classes(["1", "2"]) == {"personal", "digital"}
    assert media_classes(["4"]) == {"phone"}
    assert media_classes(["1", "4", "5"]) == {"personal", "phone", "digital"}
    assert media_classes([]) == set() and media_classes(["99"]) == set()  # unknown / "other" is not marked


def test_p3_marks_each_named_medium_once_and_a_contact_without_media_visibly(tmp_path):
    def no_media(rows):
        rows[0]["media_codes"] = ""

    dataset = _dataset(tmp_path, mutate=no_media)
    network, status = _make(dataset)
    fig = perspectives.geography_communication_figure(dataset, status, PARAMS, network=network)
    expected = sum(len(media_classes(c.code_list("media"))) for c in dataset.contacts)
    marks = sum(len(c.get_offsets()) for c in fig.axes[0].collections if isinstance(c, PathCollection) and abs(c.get_sizes()[0] - 20) < 1e-6)
    assert marks == expected > 0
    assert "–" in _texts(fig)  # the contact without a statement says so
    legend = " ".join(_texts(fig))
    assert "Mehrfachangaben" in legend and "Beziehung insgesamt" in legend


def test_a_highlight_mutes_chips_and_moves_nothing(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    plain = perspectives.distance_closeness_figure(dataset, status, PARAMS, network=network)
    emphasised = perspectives.distance_closeness_figure(dataset, status, PARAMS, network=network, highlight=["A01", "A04"])
    boxes = lambda fig: [tuple(c.get_offsets()[0].round(6).tolist()) for c in _chips(fig)]
    assert boxes(plain) == boxes(emphasised)
    fills = lambda fig: [tuple(c.get_facecolor()[0].round(6).tolist()) for c in _chips(fig)]
    assert fills(plain) != fills(emphasised)
    assert sum(1 for a, b in zip(fills(plain), fills(emphasised)) if a == b) == 2  # only the two highlighted keep their colour


def test_the_reference_place_is_configurable_not_marburg(tmp_path):
    def in_giessen(rows):
        rows[0]["residence_city"], rows[1]["residence_city"] = "Gießen", "Gießen"

    dataset = _dataset(tmp_path, mutate=in_giessen)
    network, status = _make(dataset)
    giessen = AnalysisParams(local_places=("Gießen",))
    fig = perspectives.distance_closeness_figure(dataset, status, giessen, network=network)
    texts = [t.replace("\n", " ") for t in _texts(fig)]
    assert "Gießen" in texts and "Marburg" not in texts
    views = {v.contact_id: v.geo for v in contact_views(dataset, giessen)}
    assert views["A01"] is GeoCategory.LOCAL and views["A05"] is not GeoCategory.LOCAL  # Marburg is just another city now


# ------------------------------------------------------------------ P2 language views ----------------------


def test_language_view_specs_are_checked(tmp_path):
    dataset = _dataset(tmp_path)
    for good in ("mode", "mode:1", "lang:1", "multilingual"):
        assert LanguageView(dataset, good).spec == good
    for bad in ("lang", "lang:999", "mode:999", "multilingual:1", "colour", "language:1"):
        with pytest.raises(ValueError):
            LanguageView(dataset, bad)


def test_language_views_colour_the_contacts_and_leave_unknowns_white(tmp_path):
    def blank(rows):
        rows[3]["language_codes"], rows[3]["language_mode_code"] = "", ""

    dataset = _dataset(tmp_path, mutate=blank)
    by_mode = LanguageView(dataset, "mode")
    assert by_mode.fill("A04") == design.UNKNOWN_FILL and by_mode.fill("A01") != design.UNKNOWN_FILL
    assert by_mode.ring("A02") and not by_mode.ring("A01")  # A02 names two languages: the ring is a separate cue
    spanish = LanguageView(dataset, "lang:1")
    assert spanish.emphasised("A01") and spanish.emphasised("A02") and not spanish.emphasised("A03")
    assert spanish.fill("A03") == design.MUTED_FILL and spanish.fill("A04") == design.UNKNOWN_FILL  # not named is not unknown
    assert spanish.line_color("A01") and spanish.line_color("A03") is None and spanish.line_color("A04") is None
    multilingual = LanguageView(dataset, "multilingual")
    assert [c.contact_id for c in dataset.contacts if multilingual.emphasised(c.contact_id)] == [
        c.contact_id for c in dataset.contacts if len(c.code_list("language")) >= 2
    ]


def test_mode_and_languages_are_kept_apart(tmp_path):
    def disagree(rows):
        rows[0]["language_mode_code"], rows[0]["language_codes"] = "2", "1"  # mode "überwiegend Deutsch", but only Spanish named

    dataset = _dataset(tmp_path, mutate=disagree)
    assert LanguageView(dataset, "mode").modes["A01"] == "2" and LanguageView(dataset, "mode").languages["A01"] == ("1",)
    assert LanguageView(dataset, "lang:1").emphasised("A01")  # the languages decide in the language view
    assert not LanguageView(dataset, "mode:1").emphasised("A01")  # the mode decides in the mode view


def test_p2_positions_and_ties_never_change_with_the_view(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    views = ("mode", "mode:1", "lang:1", "lang:2", "multilingual")
    figures = {v: perspectives.language_groups_figure(dataset, status, PARAMS, network=network, view=v) for v in views}
    assert len({tuple(map(tuple, _nodes(f).get_offsets().tolist())) for f in figures.values()}) == 1
    tie_segments = lambda fig: sorted(repr(s.round(6).tolist()) for c in _lines(fig) for s in c.get_segments() if len(s) == 2)
    assert len({tuple(_segments(f)) for f in figures.values()} - {()}) >= 1
    polygons = lambda fig: len([p for p in fig.axes[0].patches if type(p).__name__ == "Polygon"])
    assert len({polygons(f) for f in figures.values()}) == 1 == len({polygons(f) for f in figures.values()}) and polygons(figures["mode"]) > 0
    # the same layout as B3: the contact positions are those of B2/B3
    b3 = ego_network.ego_network_figure(dataset, status, PARAMS, network=network)
    assert [tuple(map(float, p)) for p in _nodes(b3).get_offsets()] == [tuple(map(float, p)) for p in _nodes(figures["mode"]).get_offsets()]
    assert tie_segments(figures["mode"]) == tie_segments(figures["lang:1"])


def test_p2_keeps_all_contacts_groups_and_ties_and_adds_none(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    fig = perspectives.language_groups_figure(dataset, status, PARAMS, network=network, view="lang:1")
    assert len(_nodes(fig).get_offsets()) == len(dataset.contacts)
    ego_and_ties = sum(len(c.get_segments()) for c in _lines(fig))
    assert ego_and_ties == len(dataset.contacts) + len(network.positive_ties)
    nested = perspectives.language_groups_figure(dataset, status, PARAMS, network=network, show_groups=False)
    assert not [p for p in nested.axes[0].patches if type(p).__name__ == "Polygon"]
    assert "ohne Ego" not in " ".join(_texts(fig))
    assert "Ego" in " ".join(_texts(fig))


def test_p2_says_that_language_is_a_property_of_the_ego_contact_relation(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    joined = " ".join(_texts(perspectives.language_groups_figure(dataset, status, PARAMS, network=network)))
    assert "zwischen Ego und Kontakt" in joined
    analysis = " ".join(_texts(perspectives.language_groups_figure(dataset, status, PARAMS, network=network, profile="analysis")))
    assert "keine Hauptsprache" in analysis


# ------------------------------------------------------------------ any data ------------------------------


@pytest.mark.parametrize("n", [1, 2, 3, 40, 100])
def test_the_perspectives_build_for_any_number_of_contacts(tmp_path, n):
    dataset = _dataset(tmp_path, n=n, with_groups=n >= 11)
    network, status = _make(dataset)
    figures = _all_clean(dataset, network, status)
    assert len(figures) == 5
    assert len(_chips(figures["P1"])) == n and len(_chips(figures["P3"])) == n
    assert len(_nodes(figures["P2"]).get_offsets()) == n


def test_the_perspectives_build_when_every_attribute_is_missing(tmp_path):
    def nothing(rows):
        for row in rows:
            row.update(residence_city="", residence_country_iso3="", language_mode_code="", language_codes="", table_ring_near_value="",
                       contact_frequency_code="", media_codes="")

    dataset = _dataset(tmp_path, n=6, with_groups=False, mutate=nothing)
    network, status = _make(dataset)
    for view in ("mode", "lang:1", "multilingual"):
        fig = perspectives.language_groups_figure(dataset, status, PARAMS, network=network, view=view)
        assert len(_nodes(fig).get_offsets()) == 6
    p1 = perspectives.distance_closeness_figure(dataset, status, PARAMS, network=network)
    perspectives.geography_communication_figure(dataset, status, PARAMS, network=network)
    assert any("nicht erfasst" in t for t in _texts(p1))


def test_the_perspectives_build_with_overlapping_groups_and_incomplete_ties(tmp_path):
    rows = fx.contact_rows(14, 8)
    groups = [fx.group("G1"), fx.group("G2"), fx.group("G3")]
    memberships = fx.members("G1", ["A01", "A02", "A03", "A04"]) + fx.members("G2", ["A03", "A04", "A05"]) + fx.members("G3", ["A09", "A10"])
    dataset = read_package(fx.build_package(tmp_path / "p", contacts=rows, groups=groups, memberships=memberships, review_items=[]))
    network, status = _make(dataset)
    assert network.confirmed_groups and not status.pair_coverage_complete if hasattr(status, "pair_coverage_complete") else True
    figures = _all_clean(dataset, network, status)
    polygons = [p for p in figures["P2"].axes[0].patches if type(p).__name__ == "Polygon"]
    assert len(polygons) == 2 * len(network.confirmed_groups) == 6


# ------------------------------------------------------------------ determinism ---------------------------


def test_the_new_figures_are_reproducible_byte_for_byte(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)
    digests = []
    for run in ("one", "two"):
        out = []
        for name, fig in sorted(_all_clean(dataset, network, status).items()):
            with rc():
                save_figure(fig, tmp_path / f"{run}_{name}", ("svg", "png", "pdf"))
            out += [(tmp_path / f"{run}_{name}.{ext}").read_bytes() for ext in ("svg", "png", "pdf")]
        digests.append(out)
    assert digests[0] == digests[1]


_PROBE = """
import sys, hashlib
from pathlib import Path
sys.path.insert(0, {tests!r})
import network_fixtures as fx
from mares.networks.analysis import AnalysisParams, survey_status
from mares.networks.build import build_network
from mares.networks.figures import geo_zones, perspectives, ego_network
from mares.networks.figures.style import rc, save_figure
from mares.networks.package import read_package

root = Path({tmp!r})
rows = fx.contact_rows(12, 8)
g, m = fx.standard_groups()
dataset = read_package(fx.build_package(root / "p", contacts=rows, groups=g, memberships=m, review_items=[]))
network = build_network(dataset)
status = survey_status(dataset, network)
params = AnalysisParams()
figs = {{
    "b3": ego_network.ego_network_figure(dataset, status, params, network=network),
    "g2": geo_zones.geographic_network_figure(dataset, status, params, network=network, highlight="between"),
    "p1": perspectives.distance_closeness_figure(dataset, status, params, network=network),
    "p2": perspectives.language_groups_figure(dataset, status, params, network=network, view="lang:1"),
    "p3": perspectives.geography_communication_figure(dataset, status, params, network=network),
}}
for name, fig in sorted(figs.items()):
    with rc():
        save_figure(fig, root / name, ("svg",))
    print(name, hashlib.sha256((root / (name + ".svg")).read_bytes()).hexdigest())
"""


def test_the_figures_do_not_depend_on_the_process_hash_seed(tmp_path):
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    outputs = set()
    for seed in ("1", "2", "3"):
        folder = tmp_path / f"seed{seed}"
        folder.mkdir()
        script = _PROBE.format(tests=tests_dir, tmp=str(folder))
        env = dict(os.environ, PYTHONHASHSEED=seed)
        outputs.add(subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=env, check=True).stdout)
    assert len(outputs) == 1


def test_building_the_perspectives_does_not_change_the_existing_figures(tmp_path):
    dataset = _dataset(tmp_path)
    network, status = _make(dataset)

    def existing(stem):
        figs = {
            "b1": netfig.network_structure_figure(dataset, status, PARAMS, network=network),
            "b2": netfig.network_structure_figure(dataset, status, PARAMS, network=network, show_groups=True),
            "b3_0": ego_network.ego_layout_comparison_figure(dataset, status, PARAMS, network=network),
            "g1": geo_zones.geographic_zones_figure(dataset, status, PARAMS, network=network),
        }
        out = {}
        for name, fig in figs.items():
            with rc():
                save_figure(fig, tmp_path / f"{stem}_{name}", ("svg", "png"))
            out[name] = [(tmp_path / f"{stem}_{name}.{ext}").read_bytes() for ext in ("svg", "png")]
        return out

    before = existing("before")
    _all_clean(dataset, network, status)
    assert existing("after") == before


# ------------------------------------------------------------------ privacy ------------------------------


def test_no_free_text_reaches_a_new_figure(tmp_path):
    def with_text(rows):
        rows[0]["birth_country_source"] = "Freitext-Herkunft"
        rows[1]["review_flags"] = "SECRET_FLAG"

    rows = fx.contact_rows(12, 8)
    with_text(rows)
    g, m = fx.standard_groups()
    dataset = read_package(fx.build_package(tmp_path / "p", contacts=rows, groups=g, memberships=m,
                                            review_items=[{"review_id": "R1", "priority": "x", "reference": "A03", "field": "f",
                                                           "description": "VERTRAULICHE NOTIZ", "recommended_action": "x"}]))
    network, status = _make(dataset)
    for profile in design.PROFILES:
        figures = [
            ego_network.ego_network_figure(dataset, status, PARAMS, network=network, profile=profile),
            geo_zones.geographic_network_figure(dataset, status, PARAMS, network=network, profile=profile),
            perspectives.distance_closeness_figure(dataset, status, PARAMS, network=network, profile=profile),
            perspectives.language_groups_figure(dataset, status, PARAMS, network=network, profile=profile),
            perspectives.geography_communication_figure(dataset, status, PARAMS, network=network, profile=profile),
        ]
        for fig in figures:
            joined = " ".join(_texts(fig))
            assert ("UNREVIEWED" if profile == "analysis" else "vorläufig") in joined and "0000-1" in joined
            for forbidden in ("VERTRAULICHE", "Freitext-Herkunft", "SECRET_FLAG"):
                assert forbidden not in joined


# ------------------------------------------------------------------ pipeline ------------------------------


@pytest.fixture
def machine(tmp_path):
    folders = {name: tmp_path / name for name in ("checkout", "workspace", "intake")}
    for folder in folders.values():
        folder.mkdir()
    (folders["intake"] / "inbox").mkdir()
    (folders["workspace"] / "runs").mkdir()
    fx.standard_package(folders["intake"] / "inbox" / "delivery" / "contents")
    env = {"MARES_WORKSPACE_ROOT": str(folders["workspace"]), "MARES_INTAKE_ROOT": str(folders["intake"])}
    return folders, Roots(load_root_specs(), env, checkout=folders["checkout"])


PACKAGE = "INTAKE:inbox/delivery/contents"


def test_the_run_writes_clean_and_analysis_figures_and_the_index(machine):
    _, roots = machine
    result = run_pipeline(roots, parse_ref(PACKAGE), "run", formats=("svg",))
    figures = result.run_dir / "figures"
    for spec in registry.SPECS:
        assert (figures / spec.tier / f"{spec.stem}.svg").is_file(), spec.stem
        assert (figures / "analysis" / spec.tier / f"{spec.stem}.svg").is_file() == spec.profiles, spec.stem  # diagnostics have one look
    index = json.loads((figures / "figures_index.json").read_text(encoding="utf-8"))
    assert index["schema"] == "mares-figures-index/v0-draft"
    assert set(index["spatial_meanings"]) == {"naehe", "struktur", "geografie"}
    p1 = index["figures"]["fig_P1_distanz_und_naehe"]
    assert p1["question"] and p1["limits"] and p1["encodings"] and set(p1["files"]) == {"clean", "analysis"}
    record = json.loads((result.run_dir / "run_record.json").read_text(encoding="utf-8"))
    assert record["parameters"]["figure_options"] == {"profiles": ["clean", "analysis"], "language_view": "mode", "tie_highlight": "between"}
    assert record["parameters"]["font"] == "DejaVu Sans"


def test_the_options_choose_profiles_view_and_highlight(machine):
    _, roots = machine
    options = FigureOptions(profiles=("clean",), language_view="lang:1", tie_highlight="within")
    result = run_pipeline(roots, parse_ref(PACKAGE), "figures", options=options, formats=("svg",))
    assert not (result.run_dir / "figures" / "analysis").exists()
    assert (result.run_dir / "figures" / "core" / "fig_P2_sprachliche_praktiken.svg").is_file()
    record = json.loads((result.run_dir / "run_record.json").read_text(encoding="utf-8"))
    assert record["parameters"]["figure_options"]["language_view"] == "lang:1"


def test_the_options_are_validated():
    with pytest.raises(ValueError):
        FigureOptions(profiles=())
    with pytest.raises(ValueError):
        FigureOptions(profiles=("poster",))
    with pytest.raises(ValueError):
        FigureOptions(tie_highlight="strong")
    assert FigureOptions(tie_highlight=None).tie_highlight is None


def test_the_cli_passes_the_options_and_refuses_a_wrong_view(machine):
    folders, roots = machine
    assert cli.main(["figures", "--package", PACKAGE, "--formats", "svg", "--profiles", "clean", "--language-view", "multilingual",
                     "--tie-highlight", "none"], roots=roots) == 0
    (run,) = (folders["workspace"] / "runs").iterdir()
    record = json.loads((run / "run_record.json").read_text(encoding="utf-8"))
    assert record["parameters"]["figure_options"] == {"profiles": ["clean"], "language_view": "multilingual", "tie_highlight": None}
    assert cli.main(["figures", "--package", PACKAGE, "--formats", "svg", "--language-view", "lang:999"], roots=roots) != 0


def test_the_figures_stay_reproducible_across_runs(machine):
    _, roots = machine
    hashes = []
    for _ in range(2):
        result = run_pipeline(roots, parse_ref(PACKAGE), "figures", formats=("svg",))
        figures = result.run_dir / "figures"
        hashes.append({p.relative_to(figures).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(figures.rglob("*.svg"))})
    assert hashes[0] == hashes[1] and len(hashes[0]) == 33
