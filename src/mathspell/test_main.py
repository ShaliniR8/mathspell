import pytest
from . import analyze_text

# --------------------- Basic Cases Tests ---------------------

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
    expected = "one point two million dollars and three point five billion dollars"
    assert analyze_text(text) == expected


def test_ordinal():
    text = "We took the 7th seat."
    expected = "We took the seventh seat."
    assert analyze_text(text) == expected


def test_ordinal_and_year():
    text = "This is the 1st time I earned $5 million dollars in 2020."
    expected = "This is the first time I earned five million dollars in twenty twenty."
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

# --------------------- End of Basic Cases Tests ---------------------


# --------------------- Edge Case Tests ---------------------

def test_negative_numbers():
    text = "-5 + (-3)"
    expected = "minus five plus open parentheses minus three close parentheses"
    assert analyze_text(text) == expected

    text = "The temperature dropped to -20 degrees."
    expected = "The temperature dropped to minus twenty degrees."
    assert analyze_text(text) == expected


def test_zero():
    text = "0"
    expected = "zero"
    assert analyze_text(text) == expected

    text = "0 degrees Celsius is the freezing point."
    expected = "zero degrees Celsius is the freezing point."
    assert analyze_text(text) == expected

    text = "Subtracting zero doesn't change the value: 10 - 0 = 10."
    expected = "Subtracting zero doesn't change the value: ten minus zero equals ten."
    assert analyze_text(text) == expected


def test_multiple_decimal_points():
    text = "The number is 3.14.159"
    expected = "The number is three point fourteen point one hundred and fifty-nine"
    assert analyze_text(text) == expected


def test_extremely_large_numbers():
    text = "The national debt is $21 trillion dollars."
    expected = "The national debt is twenty-one trillion dollars."
    assert analyze_text(text) == expected

    text = "A quadrillion is a million billions."
    expected = "A quadrillion is a million billions."
    assert analyze_text(text) == expected


def test_mixed_currencies():
    text = "I have $5 and €10."
    expected = "I have five dollars and ten euros."
    assert analyze_text(text) == expected

    text = "She earned £3.5 million and $2 million."
    expected = "She earned three point five million pounds and two million dollars."
    assert analyze_text(text) == expected


def test_scientific_notation():
    text = "The mass of the object is 1.23e4 kg."
    expected = "The mass of the object is one point two three times ten to the power of four kilogram."
    assert analyze_text(text) == expected


def test_numbers_with_commas():
    text = "The population is 1,000,000."
    expected = "The population is one million."
    assert analyze_text(text) == expected

    text = "Revenue reached $2,500,000.75 this quarter."
    expected = "Revenue reached two million, five hundred thousand dollars seventy-five cents this quarter."
    assert analyze_text(text) == expected


def test_nested_parentheses():
    text = "Calculate (3 + (2 - 1)) * 4."
    expected = "Calculate open parentheses three plus open parentheses two minus one close parentheses close parentheses times four."
    assert analyze_text(text) == expected


def test_operators_without_spaces():
    text = "5+3-2*4/2"
    expected = "five plus three minus two times four over two"
    assert analyze_text(text) == expected


def test_multiple_operators_in_a_row():
    text = "5++-3 --2"
    expected = "five plus plus three minus minus two"
    assert analyze_text(text) == expected

    text = "10 ** -2"
    expected = "ten to the power of minus two"
    assert analyze_text(text) == expected


def test_fraction_with_negative_numbers():
    text = "-1/2"
    expected = "minus one over two"
    assert analyze_text(text) == expected

    text = "3/-4"
    expected = "three over minus four"
    assert analyze_text(text) == expected


def test_exponents_with_negative_numbers():
    text = "(-2)^3"
    expected = "open parentheses minus two close parentheses to the power of three"
    assert analyze_text(text) == expected


def test_parentheses_without_matching_pairs():
    text = "(3 + 2 * 4"
    expected = "open parentheses three plus two times four"
    assert analyze_text(text) == expected

    text = "3 + 2) * 4"
    expected = "three plus two close parentheses times four"
    assert analyze_text(text) == expected


def test_text_with_no_numbers():
    text = "Hello, world! This text has no numbers."
    expected = "Hello, world! This text has no numbers."
    assert analyze_text(text) == expected


def test_numbers_embedded_in_words():
    text = "version2 update released."
    expected = "version two update released."
    assert analyze_text(text) == expected

    text = "Error code404 detected."
    expected = "Error code four hundred and four detected." # TODO: four 'oh' four if I wasn't being lazy
    assert analyze_text(text) == expected

def test_scientific_and_standard_numbers():
    text = "The speed of light is approximately 3.00e8 m/s."
    expected = "The speed of light is approximately three times ten to the power of eight meter per second."
    assert analyze_text(text) == expected

# def test_currency_without_space():
#     text = "$1000dollars"
#     expected = "one thousand dollars"
#     assert analyze_text(text) == expected

#     text = "€2500million"
#     expected = "two thousand five hundred euros million"
#     assert analyze_text(text) == expected


def test_numbers_with_units():
    text = "I ran 5km today."
    expected = "I ran five kilometer today."
    assert analyze_text(text) == expected

    text = "The box weighs 10kg."
    expected = "The box weighs ten kilogram."
    assert analyze_text(text) == expected


def test_repeating_patterns():
    text = "1 + 1 + 1 + 1 + 1"
    expected = "one plus one plus one plus one plus one"
    assert analyze_text(text) == expected


def test_multiple_sentences():
    text = "I have $5.5. Can you lend me $3?"
    expected = "I have five dollars fifty cents. Can you lend me three dollars?"
    assert analyze_text(text) == expected


def test_numbers_with_letters():
    text = "The room number is A12."
    expected = "The room number is A twelve."
    assert analyze_text(text) == expected

    text = "Product code X5Y7."
    expected = "Product code X five Y seven."
    assert analyze_text(text) == expected

# --------------------- End of Edge Case Tests ---------------------
