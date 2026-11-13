"""Automatic completion of the place directory from local GeoNames data (ADR-0028); synthetic files only, no network."""

from __future__ import annotations

from datetime import date

from mares.network_v1.figures.maps import read_gazetteer
from mares.network_v1.gazetteer import complete_gazetteer

HEADER = "place;country_iso3;lat;lon;basis;group_with\n"
COUNTRIES = {"DEU": {"properties": {"ISO_A2_EH": "DE"}}, "XXX": {"properties": {"ISO_A2_EH": "-99"}}}


def _row(gid, name, lat, lon, code="PPL", population=0, alternates=""):
    cols = [str(gid), name, name, alternates, str(lat), str(lon), "P", code, "DE", "", "", "", "", "", str(population)]
    return "\t".join(cols + ["", "", "Europe/Berlin", "0000-01-01"]) + "\n"


def _setup(tmp_path, rows, existing=""):
    gazetteer = tmp_path / "gazetteer.csv"
    gazetteer.write_text(HEADER + existing, encoding="utf-8")
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "DE.txt").write_text("".join(rows), encoding="utf-8")
    return gazetteer, cache


def _run(gazetteer, cache, residences, fetch=None):
    return complete_gazetteer(gazetteer, residences, COUNTRIES, cache, fetch=fetch, today=lambda: date(2000, 1, 2))


def test_an_unambiguous_place_is_added_with_its_source(tmp_path):
    gazetteer, cache = _setup(tmp_path, [_row(1, "Musterdorf", 52.8312, 9.6271)])
    result = _run(gazetteer, cache, [("Musterdorf", "DEU")])
    assert [a["place"] for a in result.added] == ["Musterdorf"]
    assert read_gazetteer(gazetteer)[("musterdorf", "DEU")][:2] == (52.83, 9.63)
    assert "GeoNames 1" in gazetteer.read_text(encoding="utf-8")


def test_far_apart_namesakes_are_ambiguous_and_never_chosen(tmp_path):
    gazetteer, cache = _setup(tmp_path, [_row(1, "Neudorf", 50.0, 8.0, population=900), _row(2, "Neudorf", 53.0, 12.0, population=800)])
    result = _run(gazetteer, cache, [("Neudorf", "DEU")])
    assert not result.added and [a["place"] for a in result.ambiguous] == ["Neudorf"]
    assert ("neudorf", "DEU") not in read_gazetteer(gazetteer)


def test_near_namesakes_count_as_one_place_the_largest_wins(tmp_path):
    gazetteer, cache = _setup(tmp_path, [_row(1, "Stadt", 50.00, 8.00, population=50000), _row(2, "Stadt", 50.05, 8.05, population=10)])
    result = _run(gazetteer, cache, [("Stadt", "DEU")])
    assert result.added[0]["geonameid"] == "1"


def test_sections_and_historical_places_are_ignored_alternate_names_only_as_fallback(tmp_path):
    rows = [_row(1, "Altort", 50.0, 8.0, code="PPLH"), _row(2, "Grossstadt", 51.0, 7.0, alternates="Bigtown,Grande Ville")]
    gazetteer, cache = _setup(tmp_path, rows)
    result = _run(gazetteer, cache, [("Altort", "DEU"), ("Bigtown", "DEU")])
    assert [a["place"] for a in result.not_found] == ["Altort"]
    assert [a["place"] for a in result.added] == ["Bigtown"]


def test_existing_rows_regional_statements_and_unmappable_countries_stay_untouched(tmp_path):
    existing = "Musterdorf;DEU;10.00;10.00;von Hand;\n"
    gazetteer, cache = _setup(tmp_path, [_row(1, "Musterdorf", 52.83, 9.63), _row(2, "Muenchen", 48.1, 11.6)], existing)
    result = _run(gazetteer, cache, [("Musterdorf", "DEU"), ("Nähe München", "DEU"), ("Irgendwo", "XXX"), ("Ort", "")])
    assert not result.added
    assert read_gazetteer(gazetteer)[("musterdorf", "DEU")][:2] == (10.0, 10.0)  # never overwritten
    assert {s["reason"] for s in result.skipped} == {"regionale Angabe, kein Ort", "Land ohne ISO-2-Code in der Basiskarte",
                                                    "kein Wohnland codiert"}


def test_a_missing_dump_is_fetched_once_and_a_failed_fetch_is_reported(tmp_path):
    gazetteer, cache = _setup(tmp_path, [])
    (cache / "DE.txt").unlink()
    calls = []

    def fetch(iso2, target):
        calls.append(iso2)
        target.write_text(_row(1, "Musterdorf", 52.8, 9.6), encoding="utf-8")

    assert _run(gazetteer, cache, [("Musterdorf", "DEU")], fetch=fetch).added and calls == ["DE"]
    (cache / "DE.txt").unlink()
    failed = _run(gazetteer, cache, [("Anderswo", "DEU")])  # conftest: no network in tests
    assert failed.fetch_errors and [a["place"] for a in failed.not_found] == ["Anderswo"]


def test_a_much_larger_place_outweighs_far_namesakes_a_municipality_only_without_a_place(tmp_path):
    rows = [_row(1, "Hafenstadt", 53.1, 8.8, code="PPLA", population=500000), _row(2, "Hafenstadt", 48.0, 9.4),
            _row(3, "Klein", 50.0, 8.0, population=700), _row(4, "Klein", 53.0, 12.0)]
    municipal = "\t".join(["5", "Doppelgemeinde", "Doppelgemeinde", "", "50.86", "7.33", "A", "ADM4", "DE"] + [""] * 5 + ["0"]
                          + ["", "", "Europe/Berlin", "0000-01-01"]) + "\n"
    gazetteer, cache = _setup(tmp_path, rows + [municipal])
    result = _run(gazetteer, cache, [("Hafenstadt", "DEU"), ("Klein", "DEU"), ("Doppelgemeinde", "DEU")])
    assert sorted(a["geonameid"] for a in result.added) == ["1", "5"]
    assert [a["place"] for a in result.ambiguous] == ["Klein"]  # too small to outweigh its namesake
