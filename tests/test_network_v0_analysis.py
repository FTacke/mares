"""Descriptive analysis: counts, geography, survey status, and the metrics that are refused."""

from __future__ import annotations

import json

import network_v0_fixtures as fx
from mares.core.model import QualityState
from mares.network_v0.analysis import (
    REFUSED_METRICS,
    AnalysisParams,
    attribute_counts,
    descriptive_tables,
    language_combinations,
    survey_status,
)
from mares.network_v0.build import build_network
from mares.network_v0.geo import GeoCategory, classify_residence
from mares.network_v0.package import read_package


def _load(tmp_path, n=12):
    groups, memberships = fx.standard_groups()
    dataset = read_package(fx.build_package(tmp_path / "p", contacts=fx.contact_rows(n, 8), groups=groups, memberships=memberships))
    return dataset, build_network(dataset)


def test_counts_keep_empty_categories_and_count_multiple_codes_once_each(tmp_path):
    dataset, _ = _load(tmp_path)
    rows, missing = attribute_counts(dataset, "language", "language")
    counts = {code: n for code, _, n in rows}
    assert set(counts) == {"1", "2", "3", "4", "5"} and counts["3"] == 0 and counts["5"] == 0  # unused codes stay visible
    assert counts["1"] + counts["2"] > 12  # a contact naming two languages counts for both
    assert missing == 0


def test_missing_values_are_counted_as_not_collected_not_as_a_category(tmp_path):
    rows = fx.contact_rows(6)
    rows[0]["language_codes"] = ""
    rows[1]["table_ring_near_value"] = ""
    dataset = read_package(fx.build_package(tmp_path / "p", contacts=rows))
    assert attribute_counts(dataset, "language", "language")[1] == 1
    closeness, missing = attribute_counts(dataset, "closeness", "closeness_1_5")
    assert missing == 1 and sum(n for _, _, n in closeness) == 5


def test_geographic_classification_is_rule_based_and_does_not_sharpen_vague_places():
    assert classify_residence("Marburg", "DEU").category is GeoCategory.LOCAL
    assert classify_residence(" marburg ", "DEU").category is GeoCategory.LOCAL
    # a regional statement stays regional: not the city, no concrete place invented
    near = classify_residence("Nähe Marburg", "DEU")
    assert near.category is GeoCategory.LOCAL_REGION and near.region_of == "Marburg"
    assert classify_residence("Region Marburg", "DEU").category is GeoCategory.LOCAL_REGION
    assert classify_residence("Umgebung von Marburg", "DEU").region_of == "Marburg"
    assert classify_residence("Nähe Berlin", "DEU").category is GeoCategory.GERMANY_OTHER  # a region of another place
    assert classify_residence("Nähe Marburg", "PER").category is GeoCategory.OUTSIDE_EUROPE  # the country decides
    assert classify_residence("Berlin", "DEU").category is GeoCategory.GERMANY_OTHER
    assert classify_residence("Lima", "PER").category is GeoCategory.OUTSIDE_EUROPE
    assert classify_residence("Marburg", "PER").category is GeoCategory.OUTSIDE_EUROPE  # the country decides
    assert classify_residence("Berlin", None).category is GeoCategory.UNKNOWN
    assert classify_residence(None, "DEU").category is GeoCategory.GERMANY_OTHER


def test_survey_status_marks_every_structural_statement_as_partial(tmp_path):
    dataset, network = _load(tmp_path)
    status = survey_status(dataset, network)
    assert status.elicitation == "not_stated" and status.pair_coverage == "not_established"
    assert status.completeness == "partial_unknown_not_absent"
    assert status.quality_state is QualityState.UNREVIEWED  # software never sets a quality state
    assert (status.documented_ties, status.pairs_without_statement) == (9, 12 * 11 // 2 - 9)
    assert "UNREVIEWED" in status.stamp() and "0000-1" in status.stamp() and "n = 12" in status.stamp()
    assert "unbekannt" in status.structure_note() and "Erhebungsmethode nicht angegeben" in status.structure_note()
    document = status.to_dict()
    assert document["completeness"] == "partial_unknown_not_absent" and document["refused_metrics"]


def test_no_density_cohesion_or_segregation_is_computed(tmp_path):
    dataset, network = _load(tmp_path)
    assert any("dichte" in metric.lower() for metric in REFUSED_METRICS)
    tables = descriptive_tables(dataset, network, AnalysisParams())
    text = " ".join(t.title.lower() + " " + " ".join(map(str, t.columns)).lower() for t in tables)
    for word in ("dichte", "density", "kohäsion", "cohesion", "segregation", "zentralität", "centrality", "transitivität"):
        assert word not in text
    ties = next(t for t in tables if t.key == "ties_documented")
    values = {row[0]: row[1] for row in ties.rows}
    assert values["ja (dokumentiert)"] == 9 and values["nein (ausdrücklich verneint)"] == 0
    assert values["nicht erhoben / keine Angabe"] == 66 - 9
    assert all(isinstance(v, int) for v in values.values())  # counts, never a share or a density


def test_group_tables_report_sizes_and_multiple_memberships(tmp_path):
    dataset, network = _load(tmp_path)
    tables = {t.key: t for t in descriptive_tables(dataset, network, AnalysisParams())}
    groups = {row[0]: row for row in tables["groups"].rows}
    assert groups["G01"][1:] == ("confirmed", 4, 6) and groups["G03"][1:] == ("needs_review", 3, 0)  # no ties from a candidate
    assert dict(tables["group_memberships_per_contact"].rows) == {0: 5, 1: 5, 2: 2}  # A03, A04 are in two groups
    assert {row[0] for row in tables["multi_group_contacts"].rows} == {"A03", "A04"}


def test_language_combinations_stay_combinations(tmp_path):
    dataset, _ = _load(tmp_path)
    combos = dict((codes, members) for codes, members in language_combinations(dataset))
    assert ("1", "2") in combos and ("1",) in combos  # a bilingual contact is not reduced to one language
    assert all(len(set(codes)) == len(codes) for codes in combos)


def test_tables_are_deterministic_and_serialise_stably(tmp_path):
    dataset, network = _load(tmp_path)
    first = descriptive_tables(dataset, network, AnalysisParams())
    second = descriptive_tables(dataset, network, AnalysisParams())
    assert [t.to_csv() for t in first] == [t.to_csv() for t in second]
    assert all(t.to_csv().startswith("﻿") and "\r" not in t.to_csv() for t in first)


def test_language_modes_5_and_6_stay_as_collected(tmp_path):
    rows = fx.contact_rows(6)
    rows[0]["language_mode_code"] = "5"
    rows[1]["language_mode_code"] = "6"
    rows[2]["language_mode_code"] = "6"
    dataset = read_package(fx.build_package(tmp_path / "p", contacts=rows))
    counts = {code: n for code, _, n in attribute_counts(dataset, "language_mode", "language_mode")[0]}
    assert counts["5"] == 1 and counts["6"] == 2  # never folded into another category
    assert dataset.contacts[1].single("language_mode") == "6"


def test_regional_places_and_ambiguous_birth_countries_enter_the_tables_as_what_they_are(tmp_path):
    rows = fx.contact_rows(6)
    rows[0].update(residence_city="Nähe Marburg", residence_country_iso3="DEU", birth_country_iso3="", birth_country_source="Land A/Land B")
    rows[1].update(birth_country_iso3="", birth_country_source="")
    dataset = read_package(fx.build_package(tmp_path / "p", contacts=rows))
    tables = {t.key: t for t in descriptive_tables(dataset, build_network(dataset), AnalysisParams())}
    places = {row[0] for row in tables["residence_places"].rows}
    assert "Region Marburg" in places and "Nähe Marburg" not in places  # normalised, never a concrete place
    geo = dict(tables["geo_category"].rows)
    assert geo["Region Marburg (ungefähre Angabe)"] == 1
    birth = dict(tables["birth_country_status"].rows)
    assert birth["mehrdeutig (mehrere Länder genannt)"] == 1 and birth["nicht erfasst"] == 2  # contact 2 above and contact 4 of the fixture pattern
    crosstab = tables["residence_by_birth_country"].rows
    assert sum(row[2] for row in crosstab) == 6  # one contact is one cell: an ambiguous birth country is not counted twice
    assert any(row[1] == "mehrdeutig" for row in crosstab) and not any(row[1] in ("Land A", "Land B") for row in crosstab)
    from mares.network_v0.canonical import dataset_json

    document = json.loads(dataset_json(dataset, build_network(dataset), AnalysisParams()))
    first = document["contacts"][0]
    assert first["text"]["birth_country_source"] == "Land A/Land B" and first["text"]["residence_city"] == "Nähe Marburg"  # raw kept
    assert first["derived"]["birth_country_status"] == "ambiguous" and first["derived"]["residence_region_of"] == "Marburg"
