import pytest
from . import analyze_text

# --------------------- Tests for Currency and Large Numbers ---------------------

def test_currency_with_decimal():
    text = "$3.8 million dollars"
    expected = "three point eight million dollars"
    assert analyze_text(text) == expected


def test_currency_without_decimal():
    text = "$2 billion dollars"
    expected = "two billion dollars"
    assert analyze_text(text) == expected


def test_mixed_currency_scales():
    text = "$1.2 million and $3.5 billion dollars"
    expected = "one point two million dollars and three point five billion dollars"
    assert analyze_text(text) == expected


def test_scale_without_currency_symbol():
    text = "The revenue was 4.5 million."
    expected = "The revenue was four point five million."
    assert analyze_text(text) == expected


def test_invalid_currency_format():
    text = "I have $3.8."
    expected = "I have three dollars eighty cents."
    assert analyze_text(text) == expected


def test_large_number_with_mixed_scale():
    text = "$1.25 billion and $750 million."
    expected = "one point two five billion dollars and seven hundred and fifty million dollars."
    assert analyze_text(text) == expected


def test_mixed_currencies():
    text = "I have $5 and €10."
    expected = "I have five dollars and ten euros."
    assert analyze_text(text) == expected

    text = "She earned £3.5 million and $2 million."
    expected = "She earned three point five million pounds and two million dollars."
    assert analyze_text(text) == expected

# --------------------- Tests for Numerical Expressions ---------------------

def test_addition():
    text = "5 + 3"
    expected = "five plus three"
    assert analyze_text(text) == expected


def test_subtraction():
    text = "10 - 7"
    expected = "ten minus seven"
    assert analyze_text(text) == expected


def test_multiplication():
    text = "6 * 4"
    expected = "six times four"
    assert analyze_text(text) == expected


def test_combined_operations():
    text = "4 + 5 - 2"
    expected = "four plus five minus two"
    assert analyze_text(text) == expected


def test_parentheses():
    text = "(3 + 2) * 4"
    expected = "open parentheses three plus two close parentheses times four"
    assert analyze_text(text) == expected


def test_fraction_format():
    text = "1/2"
    expected = "one over two"
    assert analyze_text(text) == expected


def test_exponentiation():
    text = "2^3"
    expected = "two to the power of three"
    assert analyze_text(text) == expected


def test_mixed_numbers_and_operators():
    text = "5+-3*2/4"
    expected = "five plus minus three times two over four"
    assert analyze_text(text) == expected


def test_multiple_symbols_together():
    text = "3^4 / (5-2)"
    expected = "three to the power of four divided by open parentheses five minus two close parentheses"
    assert analyze_text(text) == expected

# --------------------- Tests for Dates and Ordinals ---------------------

def test_ordinal_numbers():
    text = "We took the 7th seat."
    expected = "We took the seventh seat."
    assert analyze_text(text) == expected


def test_dates_in_text():
    text = "The meeting is on 12/25/2025."
    expected = "The meeting is on twelve twenty-five twenty twenty-five."
    assert analyze_text(text) == expected


def test_ordinal_and_year_combination():
    text = "This is the 1st time I earned $5 million dollars in 2020."
    expected = "This is the first time I earned five million dollars in twenty twenty."
    assert analyze_text(text) == expected

# --------------------- Tests for Edge Cases ---------------------

def test_negative_numbers():
    text = "-5 + (-3)"
    expected = "minus five plus open parentheses minus three close parentheses"
    assert analyze_text(text) == expected

    text = "The temperature dropped to -20 degrees."
    expected = "The temperature dropped to minus twenty degrees."
    assert analyze_text(text) == expected


def test_zero_cases():
    text = "0"
    expected = "zero"
    assert analyze_text(text) == expected

    text = "0 degrees Celsius is the freezing point."
    expected = "zero degrees Celsius is the freezing point."
    assert analyze_text(text) == expected


def test_multiple_decimal_points():
    text = "The number is 3.14.159"
    expected = "The number is three point fourteen point one hundred and fifty-nine"
    assert analyze_text(text) == expected


def test_scientific_notation():
    text = "The speed of light is approximately 3.00e8 m/s."
    expected = "The speed of light is approximately three times ten to the power of eight meter per second."
    assert analyze_text(text) == expected

# --------------------- Tests for Text with Numbers ---------------------

def test_numbers_with_units():
    text = "I ran 5km today."
    expected = "I ran five kilometer today."
    assert analyze_text(text) == expected


def test_numbers_embedded_in_words():
    text = "version2 update released."
    expected = "version two update released."
    assert analyze_text(text) == expected

    text = "Error code404 detected."
    expected = "Error code four hundred and four detected." #TODO: four 'oh' four would sound cool
    assert analyze_text(text) == expected


def test_text_with_no_numbers():
    text = "Hello, world! This text has no numbers."
    expected = "Hello, world! This text has no numbers."
    assert analyze_text(text) == expected
