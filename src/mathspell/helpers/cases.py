import re
import spacy
from typing import Optional
from num2words import num2words
from mathspell.helpers import constants as c 
from unit_parse import parser as quantity_parser

def interpret_currency(number: float, currency_name: str, minor_currency_name: str) -> str:
    """
    Handle major units and minor currency units.
    """
    as_str = f"{number:.2f}"
    whole_str, fractional_str = as_str.split(".")
    whole_val = int(whole_str)
    fractional_val = int(fractional_str)

    if whole_val > 1:
        currency_name += 's'
    if fractional_val > 1:
        minor_currency_name += 's'

    if fractional_val == 0:
        return f"{convert_number_to_words(whole_val)} {currency_name}"
    return (
        f"{convert_number_to_words(whole_val)} {currency_name} {convert_number_to_words(fractional_val)} {minor_currency_name}"
    )

def token_is_currency(symbol: str) -> bool:
    """
    Check if a token corresponds to a currency symbol from CURRENCY_MAP.
    """
    return bool(c.CURRENCY_MAP.get(symbol, False))

def convert_ordinal_string(token_text: str, next_token_text: str) -> str:
    """
    Convert a numeric ordinal token (e.g., 1st) into word (e.g., 'first')
    """
    match = re.match(r"^(-?\d+)(st|nd|rd|th)$", f"{token_text}{next_token_text}", re.IGNORECASE)
    if not match:
        return token_text
    number_part = match.group(1)
    try:
        return convert_number_to_words(int(number_part), to_ordinal=True)
    except ValueError:
        return token_text

def token_is_ordinal(token_text: str, next_token_text: str) -> bool:
    """
    Check if current token together with next token forms an ordinal 
    """
    combined = f"{token_text}{next_token_text}"
    return bool(re.match(r"^(-?\d+)(st|nd|rd|th)$", combined, re.IGNORECASE))
    
def convert_numeric_date_simple(date_str: str) -> str:
    """
    Replace date separators like / with spaces.
    E.g. '12/25/2023' -> '12 25 2023'.
    """
    return re.sub(r"[./]", " ", date_str)

def convert_time(time_str: str) -> str:
    """
    Convert a time string (e.g., '3:45 PM') into spoken form (e.g., 'three forty-five PM').
    """
    time_str = time_str.strip()
    am_pm_match = re.search(r"\b(AM|PM)\b", time_str, re.IGNORECASE)
    has_am_pm = bool(am_pm_match)

    try:
        if has_am_pm:
            dt = datetime.strptime(time_str, "%I:%M %p")
            hour = dt.hour if dt.hour != 0 else 12
            if dt.hour > 12:
                hour = dt.hour - 12
            am_pm = am_pm_match.group(1).upper()
        else:
            dt = datetime.strptime(time_str, "%H:%M")
            hour = dt.hour
    except ValueError:
        return time_str

    hour_words = num2words(hour)
    if dt.minute:
        minute_words = num2words(dt.minute)
        time_words = f"{hour_words} {minute_words}"
    else:
        time_words = hour_words

    if has_am_pm:
        time_words += f" {am_pm}"
    return time_words

def replace_numeric_datetime(sentence: str) -> str:
    """
    Preprocess datetime patterns like '12/25/2023 at 3:45 PM' to '12 25 2023 at three forty-five PM' to avoid confusion with mathematical signs.
    """
    pattern = re.compile(
        r"(?P<date>\d{1,2}/\d{1,2}/\d{4})"
        r"(?P<sep>\s+(?:at\s+)?)"
        r"(?P<time>\d{1,2}:\d{2}(?:\s*[APMapm]{2})?)(?=\b|$)",
        re.IGNORECASE
    )

    def repl(match):
        date_str = match.group("date")
        sep = match.group("sep")
        time_str = match.group("time")
        new_date = convert_numeric_date_simple(date_str)
        new_time = convert_time(time_str)
        return f"{new_date}{sep}{new_time}"

    return re.sub(pattern, repl, sentence)

def replace_numeric_date_only(sentence: str) -> str:
    """
    Replace date-only patterns like '12/25/2023' with '12 25 2023'.
    """
    pattern = re.compile(r"(?P<date>\d{1,2}/\d{1,2}/\d{2,4})\b")

    def repl(match):
        date_str = match.group("date")
        return convert_numeric_date_simple(date_str)

    return re.sub(pattern, repl, sentence)

def replace_time_shorthand(sentence: str) -> str:
    """
    Replace time shorthand like 'at 3PM' or '4:30AM' with spoken equivalents.
    """
    pattern = re.compile(
        r"\b(?:at\s*)?(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<ampm>(AM|PM))\b",
        re.IGNORECASE
    )

    def repl(match):
        hour = match.group("hour")
        minute = match.group("minute") if match.group("minute") else "00"
        ampm = match.group("ampm").upper()
        standard_time = f"{hour}:{minute} {ampm}"
        converted = convert_time(standard_time)

        original_text = match.group(0)
        if original_text.lower().strip().startswith("at"):
            return f"at {converted}"
        return converted

    return re.sub(pattern, repl, sentence)

def process_time_patterns_ahead_of_tokenization(sentence: str) -> str:
    """
    Orchestrate multiple time/date replacements before tokenizing.
    """
    s = replace_numeric_datetime(sentence)
    s = replace_numeric_date_only(s)
    s = replace_time_shorthand(s)
    return s

def looks_like_year_context(token: spacy.tokens.Token) -> bool:
    """
    Check if a token is marked by SpaCy as a date/time entity.
    """
    return token.ent_type_ in ("DATE", "TIME")

def token_looks_like_fraction(token, next_token, next_next_token) -> bool:
    """
    Check if three consecutive tokens form a fraction pattern: num / num.
    """
    return (
        token.like_num
        and next_token
        and next_token.text == '/'
        and next_next_token
        and next_next_token.like_num
    )

def handle_percentage(number: float) -> str:
    """
    Convert numeric percentage into a spoken form.
    """
    if number == 100:
        return "hundred percent"
    elif number.is_integer():
        number_words = convert_number_to_words(int(number))
    else:
        whole_part = int(number)
        fractional_part = int(round((number - whole_part) * 10 ** len(str(number).split('.')[-1])))
        whole_words = convert_number_to_words(whole_part)
        fractional_words = num2words(fractional_part)
        number_words = f"{whole_words} point {fractional_words}"

    return f"{number_words} percent"

def token_is_a_quantity(string: str) -> bool:
    """
    Use `unit_parse` to check if the string is a measurable quantity.
    """
    try:
        q = quantity_parser(string)
        return bool(q and not q.dimensionless)
    except AttributeError:
        return False

def units_to_string(units: dict) -> str:
    """
    Convert parsed units into a readable string.
    E.g., {meter: 1, second: -1} -> 'meter per second'.
    """
    format_map = {1: "{key}", -1: "per {key}"}
    parts = []
    for key, val in units.items():
        if val in format_map:
            parts.append(format_map[val].format(key=key))
        elif val > 1:
            parts.append(f"{key} to the power of {val}")
        elif val < -1:
            parts.append(f"per {key} to the power of {-val}")
    return " ".join(parts)

def convert_token_to_quantity(string: str, magnitude_is_exp: bool = False) -> str:
    """
    Convert a quantity string into spoken form (e.g. 'three kilograms').
    If `magnitude_is_exp` is True, only output the units, ignoring numeric magnitude.
    """
    q = quantity_parser(string)
    magnitude = q.magnitude
    units = units_to_string(dict(q.units._units))

    if magnitude_is_exp:
        return units
    return f"{convert_number_to_words(magnitude)} {units}"

def tokens_are_a_quantity(combined_token_text: str) -> bool:
    """
    Check if the combined text of multiple tokens is a measurable quantity.
    """
    q = quantity_parser(combined_token_text)
    return bool(q and not q.dimensionless)

def convert_tokens_to_quantity(combined_token_text: str, magnitude_is_exp: bool = False) -> str:
    """
    Convert multiple tokens forming a quantity into spoken form.
    """
    q = quantity_parser(combined_token_text)
    magnitude = q.magnitude
    units = units_to_string(dict(q.units._units))

    if magnitude_is_exp:
        return units
    return f"{convert_number_to_words(magnitude)} {units}"

def token_has_exponential_notation(token: spacy.tokens.Token) -> bool:
    """
    Check if a token contains exponential notation, e.g., 3.2e+5.
    """
    return bool(re.match(r"(\d+(?:\.\d+)?)[eE]([+-]?\d+)", token.text))

def convert_exponential_notation_string(token_text: str) -> str:
    """
    Convert a single token with exponential notation into a spoken form.
    E.g. '3.2e5' -> 'three point two times ten to the power of five'.
    """
    match = re.match(r"(\d+(?:\.\d+)?)[eE]([+-]?\d+)", token_text)
    if not match:
        return token_text

    base = float(match.group(1))
    exponent = int(match.group(2))
    try:
        return (
            f"{convert_number_to_words(base)} "
            f"times ten to the power of {convert_number_to_words(exponent)}"
        )
    except ValueError:
        return token_text

def operator_is_part_of_quantity(token, prev_token, prev_prev_token, next_token) -> bool:
    """
    Check if a slash operator is part of a quantity expression (e.g., '3 kg / s').
    """
    if prev_prev_token and prev_prev_token.like_num and next_token:
        string = f"{prev_prev_token.text} {prev_token.text}/{next_token.text}"
    elif prev_prev_token and token_has_exponential_notation(prev_prev_token) and next_token:
        string = f"1 {prev_token.text}/{next_token.text}"
    else:
        return False

    return bool(token.text == '/' and token_is_a_quantity(string))

def convert_operator_part_of_quantity(prev_token, prev_prev_token, next_token) -> str:
    """
    Convert an operator that is part of a quantity expression into a spoken form.
    """
    if prev_prev_token.like_num:
        string = f"{prev_prev_token.text} {prev_token.text}/{next_token.text}"
        return convert_token_to_quantity(string)
    elif token_has_exponential_notation(prev_prev_token):
        string = f"1 {prev_token.text}/{next_token.text}"
        return convert_token_to_quantity(string, True)
    return ""

def interpret_large_scale(number: float, scale: str) -> str:
    """
    Convert numeric value and a scale word (e.g., 'million') into spoken form.
    """
    # TODO: This turned out to be a silly function. Just put it in analyze_text.
    result = convert_number_to_words(number)
    return f"{result} {scale}"

def is_illion_scale(token: spacy.tokens.Token) -> bool:
    """
    Check if a token refers to million/billion/trillion or an abbreviation (m, b, tr).
    """
    if re.search(r'illion$', token.lemma_.lower()):
        return True

    abbreviation = token.text.lower()
    return abbreviation in {"m", "b", "tr", 'gaz'}

######################################################################

def convert_number_to_words(number: float, to_year: bool = False, to_ordinal: bool = False) -> str:
     """
     Uses num2words to convert float to string.
     Handles cases like 'to_year' or 'to_ordinal'
     """
     if to_year and number.is_integer():
          return num2words(int(number), to="year")

     if to_ordinal:
          return num2words(int(number), to="ordinal")

     # Workaround for num2words issue with negative numbers: https://github.com/savoirfairelinux/num2words/issues/402
     result = num2words(number)
     if number < 0 and 'minus' not in result:
          result = f"minus {result}"
     return result


