"""Code cells: single codes, ``|`` lists, numeric ranges, and the codebook that validates them."""

from __future__ import annotations

import pytest

from mares.network_v0.codes import Codebook, CodebookError, CodeSyntaxError, parse_codes


def test_empty_cell_is_not_collected_and_never_a_code():
    for cell in ("", "   ", None):
        parsed = parse_codes(cell)
        assert parsed.codes == () and not parsed


def test_single_and_multiple_codes_keep_order_and_stay_strings():
    assert parse_codes("3").codes == ("3",)
    assert parse_codes("1|2|3|4|5|6").codes == ("1", "2", "3", "4", "5", "6")
    assert parse_codes(" 4 | 1 ").codes == ("4", "1")  # order of appearance, no sorting
    assert parse_codes("G2|G3").codes == ("G2", "G3")
    assert parse_codes("07").codes == ("07",)  # no numeric conversion


@pytest.mark.parametrize(
    ("cell", "expected"),
    [
        ("1-6", ("1", "2", "3", "4", "5", "6")),
        ("1–6", ("1", "2", "3", "4", "5", "6")),  # en dash as written by hand
        ("2-4|7", ("2", "3", "4", "7")),
        ("G1-G3", ("G1", "G2", "G3")),
        ("G1-3", ("G1", "G2", "G3")),
        ("1-3|2-4", ("1", "2", "3", "4")),
    ],
)
def test_ranges_are_expanded_to_single_codes(cell, expected):
    parsed = parse_codes(cell)
    assert parsed.codes == expected
    assert parsed.expanded_ranges


def test_duplicates_are_reported_not_hidden():
    parsed = parse_codes("1|2|1")
    assert parsed.codes == ("1", "2") and parsed.duplicates == ("1",)
    assert parse_codes("1-3|2").duplicates == ("2",)


@pytest.mark.parametrize("cell", ["1||2", "1|", "|1", "6-1", "3-3", "1-500", "1,2", "1;2", "a b", "1-"])
def test_malformed_cells_are_errors_not_guesses(cell):
    with pytest.raises(CodeSyntaxError):
        parse_codes(cell)


def test_codebook_reads_validates_and_rejects_ambiguity(tmp_path):
    path = tmp_path / "codebook.csv"
    path.write_text("﻿field;code;meaning_de\nmedia;1;persönlich\nmedia;2;Chat\nlanguage;1;Spanisch\n", encoding="utf-8")
    book = Codebook.read(path)
    assert book.codes("media") == ("1", "2") and book.is_valid("media", "2") and not book.is_valid("media", "3")
    assert book.meaning("language", "1") == "Spanisch" and not book.is_valid("unknown_field", "1")

    path.write_text("field;code;meaning_de\nmedia;1;a\nmedia;1;b\n", encoding="utf-8")
    with pytest.raises(CodebookError, match="twice"):
        Codebook.read(path)
    path.write_text("field;code\nmedia;1\n", encoding="utf-8")
    with pytest.raises(CodebookError):
        Codebook.read(path)
