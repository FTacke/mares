"""The geographic classification of a residence: five steps, geographic Europe, no guessing.

Marburg (the configured reference place) / Region Marburg / übriges Deutschland / übriges Europa / außerhalb Europas, and
'unknown' for a residence without a usable country. The classification describes where a contact lives -- never who a contact is,
and not what the place means in the biography of the person (that is a separate dimension and is not classified).
"""

from __future__ import annotations

import pytest

import network_fixtures as fx
from mares.networks.analysis import AnalysisParams, descriptive_tables, geo_labels, residence_of
from mares.networks.build import build_network
from mares.networks.figures.common import contact_views
from mares.networks.figures.style import GEO_COLORS, GEO_ORDER
from mares.networks.geo import EUROPE_ISO3, ISO3, GeoCategory, classify_residence
from mares.networks.package import read_package

PARAMS = AnalysisParams()


def test_the_five_steps_of_the_pilot_residences():
    assert classify_residence("Marburg", "DEU").category is GeoCategory.LOCAL
    assert classify_residence("Nähe Marburg", "DEU").category is GeoCategory.LOCAL_REGION
    assert classify_residence("Berlin", "DEU").category is GeoCategory.GERMANY_OTHER
    assert classify_residence("Wien", "AUT").category is GeoCategory.EUROPE_OTHER  # Europe is not "abroad" in one block
    for city, country in (("Bogotá", "COL"), ("Medellín", "COL"), ("Cali", "COL")):
        assert classify_residence(city, country).category is GeoCategory.OUTSIDE_EUROPE


def test_europe_is_geographic_not_a_membership():
    for country in ("AUT", "CHE", "NOR", "GBR", "ISL", "UKR", "SRB", "XKX", "ALB", "RUS", "MDA", "BLR"):  # EU or not
        assert classify_residence("X", country).category is GeoCategory.EUROPE_OTHER, country
    for country in ("COL", "BRA", "USA", "ARG", "JPN", "EGY", "ZAF", "AUS"):
        assert classify_residence("X", country).category is GeoCategory.OUTSIDE_EUROPE, country
    # conventions for transcontinental countries and overseas territories (UN geoscheme): documented, tested, changeable in one place
    for country in ("TUR", "CYP", "GEO", "ARM", "AZE", "KAZ"):
        assert classify_residence("X", country).category is GeoCategory.OUTSIDE_EUROPE, country
    for territory in ("GUF", "GLP", "MTQ", "REU", "GRL"):  # overseas territories count with their continent, not with their state
        assert classify_residence("X", territory).category is GeoCategory.OUTSIDE_EUROPE, territory


def test_germany_stays_germany_and_europe_is_a_subset_of_the_iso_codes():
    assert classify_residence("Berlin", "DEU").category is GeoCategory.GERMANY_OTHER  # never "übriges Europa"
    assert "DEU" in EUROPE_ISO3 and EUROPE_ISO3 <= ISO3 and len(EUROPE_ISO3) == len(set(EUROPE_ISO3))


def test_unknown_and_unusable_countries_are_never_guessed():
    assert classify_residence("Marburg", None).category is GeoCategory.UNKNOWN  # the place alone does not decide
    assert classify_residence(None, None).category is GeoCategory.UNKNOWN
    assert classify_residence("Paris", "").category is GeoCategory.UNKNOWN
    assert classify_residence("Paris", "ZZZ").category is GeoCategory.UNKNOWN  # no ISO code: not guessed into any step
    assert classify_residence(None, "AUT").category is GeoCategory.EUROPE_OTHER  # a country without a place is still a country


def test_a_regional_statement_keeps_its_country_and_its_reference():
    near = classify_residence("Nähe Wien", "AUT")
    assert near.category is GeoCategory.EUROPE_OTHER and near.region_of == "Wien" and near.city == "Nähe Wien"
    assert classify_residence("Nähe Marburg", "PER").category is GeoCategory.OUTSIDE_EUROPE  # the country decides
    assert classify_residence("Region Gießen", "DEU", ("Gießen",)).category is GeoCategory.LOCAL_REGION


def test_the_reference_place_is_configurable_and_marburg_is_not_special():
    giessen = ("Gießen",)
    assert classify_residence("Gießen", "DEU", giessen).category is GeoCategory.LOCAL
    assert classify_residence("Marburg", "DEU", giessen).category is GeoCategory.GERMANY_OTHER
    assert classify_residence("Marburg", "DEU", ("Marburg", "Gießen")).category is GeoCategory.LOCAL
    assert geo_labels(AnalysisParams(local_places=giessen))[GeoCategory.LOCAL] == "Gießen"
    assert geo_labels(AnalysisParams(local_places=giessen))[GeoCategory.LOCAL_REGION].startswith("Region Gießen")


def test_labels_colours_and_order_cover_every_category():
    labels = geo_labels(PARAMS)
    assert set(labels) == set(GeoCategory) == set(GEO_COLORS) == set(GEO_ORDER)
    assert [labels[c] for c in GEO_ORDER[:5]] == ["Marburg", "Region Marburg (ungefähre Angabe)", "übriges Deutschland", "übriges Europa", "außerhalb Europas"]
    assert labels[GeoCategory.UNKNOWN] == "Wohnort nicht zuordenbar"
    assert len(set(GEO_COLORS.values())) == len(GEO_COLORS)  # one colour per step


def test_the_classification_does_not_change_the_data(tmp_path):
    rows = fx.contact_rows(8)
    rows[0].update(residence_city="Wien", residence_country_iso3="AUT")
    rows[1].update(residence_city="Bogotá", residence_country_iso3="COL")
    dataset = read_package(fx.build_package(tmp_path / "p", contacts=rows))
    before = [(c.contact_id, dict(c.text), {k: v.codes for k, v in c.codes.items()}) for c in dataset.contacts]
    views = {v.contact_id: v for v in contact_views(dataset, PARAMS)}
    residence_of(dataset.contacts[0], PARAMS)
    descriptive_tables(dataset, build_network(dataset), PARAMS)
    assert [(c.contact_id, dict(c.text), {k: v.codes for k, v in c.codes.items()}) for c in dataset.contacts] == before  # attributes unchanged
    assert views["A01"].geo is GeoCategory.EUROPE_OTHER and views["A01"].city == "Wien" and views["A01"].residence_country == "AUT"  # the real place and country stay
    assert views["A02"].geo is GeoCategory.OUTSIDE_EUROPE and views["A02"].residence_country == "COL"


def test_the_residence_table_counts_all_five_steps(tmp_path):
    rows = fx.contact_rows(6)
    for row, (city, country) in zip(rows, [("Marburg", "DEU"), ("Nähe Marburg", "DEU"), ("Berlin", "DEU"), ("Wien", "AUT"), ("Bogotá", "COL"), ("", "")]):
        row.update(residence_city=city, residence_country_iso3=country)
    dataset = read_package(fx.build_package(tmp_path / "p", contacts=rows))
    tables = {t.key: t for t in descriptive_tables(dataset, build_network(dataset), PARAMS)}
    geo = tables["geo_category"]
    flat = " ".join(str(cell) for row in geo.rows for cell in row)
    for label in ("übriges Europa", "außerhalb Europas", "Wohnort nicht zuordenbar"):
        assert label in flat, label
    assert "außerhalb Deutschlands" not in flat
