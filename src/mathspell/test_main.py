import pytest
from . import analyze_text


def test_million_with_decimal():
    text = "$3.8 million dollars"
    expected = "three point eight million dollars"
    assert analyze_text(text) == expected


def test_billion_without_decimal():
    text = "$2 billion dollars"
    expected = "two billion dollars"
    assert analyze_text(text) == expected


def test_mixed_scales():
    text = "$1.2 million and $3.5 billion dollars"
    expected = "one point two million and three point five billion dollars"
    assert analyze_text(text) == expected


def test_ordinal():
    text = "We took the 7th seat."
    expected = "We took the seventh seat."
    assert analyze_text(text) == expected


def test_ordinal_and_year():
    text = "This is the 1st time I earned $5 million dollars in 2020."
    expected = "This is the first time I earned five million dollars in twenty twenty."
    assert analyze_text(text) == expected


def test_no_scale_word():
    text = "$1000 dollars"
    expected = "one thousand dollars"
    assert analyze_text(text) == expected


def test_scale_without_currency_symbol():
    text = "The revenue was 4.5 million."
    expected = "The revenue was four point five million."
    assert analyze_text(text) == expected


def test_invalid_currency_format():
    text = "I have $3.8."
    expected = "I have three dollars eighty cents."
    assert analyze_text(text) == expected


def test_four_digit_non_year_number():
    text = "We won with 1309 points."
    expected = "We won with one thousand, three hundred and nine points."
    assert analyze_text(text) == expected

    text = "The product ID is 6954"
    expected = "The product ID is six thousand, nine hundred and fifty-four"
    assert analyze_text(text) == expected


def test_percentage():
    text = "We should cover at least 70%"
    expected = "We should cover at least seventy percent"
    assert analyze_text(text) == expected

    text = "We might not cover 100%"
    expected = "We might not cover hundred percent"
    assert analyze_text(text) == expected

    text = "We might not cover a 100%"
    expected = "We might not cover a hundred percent"
    assert analyze_text(text) == expected
