"""network_v1 coding rules and geographic classification."""

from __future__ import annotations

import pytest

from mares.network_v1 import codes
from mares.network_v1.codes import Missing
from mares.network_v1.places import (
    AREA_ORDER, MITTELHESSEN_DISTRICTS, Area, PlaceResolution, Primary, classify, resolution_key,
)


@pytest.mark.parametrize("raw, value", [("1", "1"), ("2,5", "2.5"), ("2.5", "2.5"), (" 3,5 ", "3.5"), ("4", "4")])
def test_closeness_keeps_raw_text_and_normalises_half_steps(raw, value):
    cell = codes.read_closeness(raw)
    assert cell.recorded and cell.value == value and cell.raw == raw.strip()


@pytest.mark.parametrize("raw", ["0", "4,5", "1,25", "sehr nah", "1|2"])
def test_invalid_closeness_is_an_error(raw):
    assert codes.read_closeness(raw).error


def test_closeness_5_points_to_the_v0_scale():
    assert "network_v0" in codes.read_closeness("5").error


@pytest.mark.parametrize("raw, missing", [("", Missing.NOT_COLLECTED), ("NS", Missing.UNKNOWN), ("ka", Missing.NO_ANSWER), ("NA", Missing.NOT_APPLICABLE)])
def test_four_kinds_of_absence_stay_apart_and_are_never_zero(raw, missing):
    for cell in (codes.read_closeness(raw), codes.read_single(raw, codes.RELATION_TYPE), codes.read_multi(raw, codes.FUNCTIONS)):
        assert cell.missing is missing and not cell.recorded and cell.values == ()


@pytest.mark.parametrize("raw", ["1, 3", "1;3", "3,1", "1 ; 3"])
def test_multiple_codes_by_comma_or_semicolon_in_code_order(raw):
    assert codes.read_multi(raw, codes.COMMUNICATION_FORMS).values == ("1", "3")


@pytest.mark.parametrize("raw", ["1|3", "1,,3", "1,1", "1,7", "1,KA"])
def test_bad_multiple_answers_are_errors(raw):
    assert codes.read_multi(raw, codes.COMMUNICATION_FORMS).error


def test_function_0_is_exclusive():
    assert codes.read_multi("0", codes.FUNCTIONS, exclusive="0").values == ("0",)
    assert codes.read_multi("0, 2", codes.FUNCTIONS, exclusive="0").error


@pytest.mark.parametrize("raw, values", [("M", ("M",)), ("S", ("S",)), ("M;S", ("M", "S")), ("S,M", ("M", "S")), ("2", ("2",))])
def test_language_use(raw, values):
    assert codes.read_language_use(raw).values == values


@pytest.mark.parametrize("raw", ["M;M", "1;M", "X", "6"])
def test_invalid_language_use(raw):
    assert codes.read_language_use(raw).error


def test_ns_is_a_valid_group_status_not_a_missing_value():
    cell = codes.read_group_status("NS")
    assert cell.recorded and cell.value == "NS"
    assert codes.read_group_status("").missing is Missing.NOT_COLLECTED
    assert codes.read_group_status("X").error


# ------------------------------------------------------------------------------------------------ places ---
def test_the_gazetteer_lists_101_municipalities_of_the_five_districts():
    assert set(MITTELHESSEN_DISTRICTS) == {"Marburg-Biedenkopf", "Gießen", "Lahn-Dill-Kreis", "Limburg-Weilburg", "Vogelsbergkreis"}
    assert sum(len(v) for v in MITTELHESSEN_DISTRICTS.values()) == 101


@pytest.mark.parametrize("place, area", [
    ("Marburg", Area.MARBURG), ("marburg an der lahn", Area.MARBURG), ("Gießen", Area.MITTELHESSEN), ("Giessen", Area.MITTELHESSEN),
    ("Coelbe", Area.MITTELHESSEN), ("Wetzlar", Area.MITTELHESSEN), ("Limburg", Area.MITTELHESSEN), ("Alsfeld", Area.MITTELHESSEN),
    ("Berlin", Area.GERMANY_OTHER), ("Frankfurt", Area.GERMANY_OTHER), ("Kassel", Area.GERMANY_OTHER),
])
def test_german_places_by_list(place, area):
    assert classify(place, "DEU").area is area


@pytest.mark.parametrize("place", ["Neustadt", "Weimar", "Wetter", "Nähe Marburg", "Landkreis Gießen", "Cappel", "Bad Irgendwo", ""])
def test_unclear_german_places_are_unresolved_never_guessed(place):
    residence = classify(place, "DEU")
    assert residence.area is Area.UNRESOLVED and residence.basis


def test_a_case_resolution_decides_a_listed_unclear_place():
    resolutions = {resolution_key("Cappel"): PlaceResolution("Cappel", Area.MARBURG, "Stadtteil")}
    residence = classify("cappel", "DEU", resolutions)
    assert residence.area is Area.MARBURG and residence.basis.startswith("places.csv")
    assert residence.place == "cappel"  # the original statement is kept


@pytest.mark.parametrize("place, iso, area", [("Wien", "AUT", Area.EUROPE_OTHER), ("Moskau", "RUS", Area.EUROPE_OTHER),
                                               ("Istanbul", "TUR", Area.OUTSIDE_EUROPE), ("Bogotá", "COL", Area.OUTSIDE_EUROPE),
                                               ("Marburg", "", Area.UNRESOLVED), ("X", "XXX", Area.UNRESOLVED)])
def test_countries_decide_outside_germany(place, iso, area):
    assert classify(place, iso).area is area


def test_five_display_areas_and_four_primary_categories():
    assert len(AREA_ORDER) == 5
    assert classify("Marburg", "DEU").primary is classify("Gießen", "DEU").primary is Primary.MARBURG_MITTELHESSEN
    assert len({classify(p, i).primary for p, i in [("Marburg", "DEU"), ("Berlin", "DEU"), ("Wien", "AUT"), ("Lima", "PER")]}) == 4
