import re
import spacy
from spacy.tokenizer import Tokenizer
import spacy.util
from num2words import num2words

nlp = spacy.load("en_core_web_sm")

def custom_tokenizer(nlp):
    prefix_patterns = list(nlp.Defaults.prefixes)
    infix_patterns = list(nlp.Defaults.infixes)
    suffix_patterns = list(nlp.Defaults.suffixes)

    if r"\$" not in prefix_patterns:
        prefix_patterns.append(r"\$")

    extra_infix = r"(?<=[0-9])\.(?=[A-Z])"
    if extra_infix not in infix_patterns:
        infix_patterns.append(extra_infix)

    if r"(?<=[0-9])/(?=[0-9])" not in infix_patterns:
        infix_patterns.append(r"(?<=[0-9])/(?=[0-9])")
    
    prefix_regex = spacy.util.compile_prefix_regex(prefix_patterns)
    infix_regex = spacy.util.compile_infix_regex(infix_patterns)
    suffix_regex = spacy.util.compile_suffix_regex(suffix_patterns)

    return Tokenizer(
        nlp.vocab,
        rules=nlp.Defaults.tokenizer_exceptions,
        prefix_search=prefix_regex.search,
        suffix_search=suffix_regex.search,
        infix_finditer=infix_regex.finditer
    )

nlp.tokenizer = custom_tokenizer(nlp)

OPERATOR_MAP = {
    '+': 'plus',
    '-': 'minus',
    '*': 'times',
    '/': 'divided by',  # TODO: divided by or over?
    '=': 'equals',
    '^': 'to the power of',
    '**': 'to the power of',
    '//': 'integer division by',
    '(': 'open parentheses',
    ')': 'close parentheses',
}

UNIT_MAP = {
    'kg': 'kilograms',
    'km': 'kilometers',
    'm': 'meters',
    'cm': 'centimeters',
    'mm': 'millimeters',
    'ft': 'feet',
    'in': 'inches',
    # TODO: More units
}

# currencies
def interpret_currency_dollars(number: float) -> str: 
    as_str = f"{number:.2f}"
    whole_str, fractional_str = as_str.split(".")
    whole_val = int(whole_str)
    fractional_val = int(fractional_str)

    if fractional_val == 0:
        return f"{num2words(whole_val)} dollars"
    return f"{num2words(whole_val)} dollars {num2words(fractional_val)} cents"

def interpret_currency_bucks(number: float) -> str:
    rounded = round(number)
    return f"{num2words(rounded)} bucks"

def interpret_currency_large_scale(number: float, scale: str) -> str:
    if number.is_integer():
        number_words = num2words(int(number))
    else:
        whole_part = int(number)
        fractional_part = int(round((number - whole_part) * 10**len(str(number).split('.')[-1])))
        
        whole_words = num2words(whole_part)
        fractional_words = num2words(fractional_part)
        
        number_words = f"{whole_words} point {fractional_words}"
    
    return f"{number_words} {scale}"


# ordinals
def convert_ordinal_string(token_text: str) -> str:
    match = re.match(r"^(-?\d+)(st|nd|rd|th)$", token_text, re.IGNORECASE)
    if not match:
        return token_text
    number_part = match.group(1)
    try:
        return num2words(int(number_part), to="ordinal")
    except ValueError:
        return token_text

def token_is_ordinal(token) -> bool:
    return bool(re.match(r"^-?\d+(st|nd|rd|th)$", token.text, re.IGNORECASE))

# datetime
def looks_like_year_context(token) -> bool:
    return token.ent_type_ in ("DATE", "TIME")

def is_illion_scale(token):
    if re.search(r'illion$', token.lemma_.lower()):
        return True

    abbreviation = token.text.lower()
    return abbreviation in {"m", "b", "t"}

# math
def handle_percentage(number: float) -> str:
    if number == 100:
        return "hundred percent"
    elif number.is_integer():
        number_words = num2words(int(number))
    else:
        whole_part = int(number)
        fractional_part = int(round((number - whole_part) * 10**len(str(number).split('.')[-1])))
        whole_words = num2words(whole_part)
        fractional_words = num2words(fractional_part)
        number_words = f"{whole_words} point {fractional_words}"
    
    return f"{number_words} percent"

def convert_number_to_words(number: float, to_year: bool = False) -> str:
    if to_year and number.is_integer():
        return num2words(int(number), to="year")
    return num2words(int(number)) if number.is_integer() else num2words(number)

def analyze_text(text: str) -> str:
    doc = nlp(text)
    transformed_tokens = []
    i = 0

    while i < len(doc):
        token = doc[i]
        if token.like_num and (i + 2) < len(doc):
            next_token = doc[i + 1]
            next_next_token = doc[i + 2]
            if next_token.text == '/' and next_next_token.like_num:
                try:
                    numerator = float(token.text.replace(',', ''))
                    denominator = float(next_next_token.text.replace(',', ''))
                    numerator_word = num2words(int(numerator)) if numerator.is_integer() else num2words(numerator)
                    denominator_word = num2words(int(denominator)) if denominator.is_integer() else num2words(denominator)
                    fraction = f"{numerator_word} over {denominator_word}"
                    transformed_tokens.append(fraction)
                    i += 3  # skip the three tokens: number, '/', number
                    continue
                except ValueError:
                    pass

        if '/' in token.text and token.text.count('/') == 1:
            parts = token.text.split('/')
            if len(parts) == 2 and all(part.isdigit() for part in parts):
                numerator, denominator = parts
                numerator_word = num2words(int(numerator)) if float(numerator).is_integer() else num2words(float(numerator))
                denominator_word = num2words(int(denominator)) if float(denominator).is_integer() else num2words(float(denominator))
                fraction = f"{numerator_word} over {denominator_word}"
                transformed_tokens.append(fraction)
                i += 1  # skip the fraction token
                continue

        if token.is_space:
            transformed_tokens.append(token.text)
            i += 1
            continue

        # Handle punctuation separately (including parentheses)
        if token.is_punct:
            if token.text in OPERATOR_MAP:
                # Parentheses handling
                transformed_tokens.append(OPERATOR_MAP[token.text])
            else:
                transformed_tokens.append(token.text)
            i += 1
            continue

        # Handle ordinals
        if token_is_ordinal(token):
            transformed_tokens.append(convert_ordinal_string(token.text))
            i += 1
            continue

        # Handle numerical values
        if token.like_num:
            try:
                numeric_val = float(token.text.replace(',', ''))
            except ValueError:
                transformed_tokens.append(token.text)
                i += 1
                continue

            prev_token = doc[i - 1] if i - 1 >= 0 else None
            next_token = doc[i + 1] if i + 1 < len(doc) else None

            if next_token and next_token.text == "%":
                converted = handle_percentage(numeric_val)
                transformed_tokens.append(converted)
                i += 2  # skip number and '%'
                continue

            if looks_like_year_context(token) and 1000 <= numeric_val <= 2100:
                if not (next_token and next_token.text.lower() in {"points", "point", "id", "ids"}):
                    transformed_tokens.append(convert_number_to_words(numeric_val, to_year=True))
                    i += 1
                    continue

            if prev_token and prev_token.text == "$":
                if transformed_tokens and transformed_tokens[-1] == '$':
                    transformed_tokens.pop()

                if next_token and is_illion_scale(next_token):
                    scale_word = next_token.text.lower()
                    converted = interpret_currency_large_scale(numeric_val, scale_word)

                    if (i + 2) < len(doc):
                        subsequent_token = doc[i + 2]
                        if subsequent_token.lemma_.lower() in {"dollar", "dollars", "usd"}:
                            converted += " dollars"
                            i += 3
                        else:
                            i += 2
                    else:
                        i += 2

                    transformed_tokens.append(converted)
                    continue
                else:
                    converted = interpret_currency_dollars(numeric_val)
                    if next_token and next_token.lemma_.lower() in {"dollar", "dollars", "usd"}:
                        transformed_tokens.append(converted)
                        i += 2  # skip numeric and 'dollars'
                        continue
                    elif next_token and next_token.lemma_.lower() in {"buck", "bucks"}:
                        converted = interpret_currency_bucks(numeric_val)
                        transformed_tokens.append(converted)
                        i += 2
                        continue
                    else:
                        transformed_tokens.append(converted)
                        i += 1
                        continue

            if next_token and is_illion_scale(next_token):
                scale_word = next_token.text.lower()
                converted = interpret_currency_large_scale(numeric_val, scale_word)

                # check if 'dollars' follows the scale word
                if (i + 2) < len(doc):
                    subsequent_token = doc[i + 2]
                    if subsequent_token.lemma_.lower() in {"dollar", "dollars", "usd"}:
                        converted += " dollars"
                        i += 3  # skip number, scale word, and 'dollars'
                    else:
                        i += 2  # skip number and scale word
                else:
                    i += 2  # skip number and scale word

                transformed_tokens.append(converted)
                continue

            if next_token and next_token.lemma_.lower() in {"dollar", "dollars", "usd"}:
                converted = interpret_currency_dollars(numeric_val)
                transformed_tokens.append(converted)
                i += 2
                continue

            if next_token and next_token.lemma_.lower() in {"buck", "bucks"}:
                converted = interpret_currency_bucks(numeric_val)
                transformed_tokens.append(converted)
                i += 2
                continue

            converted = convert_number_to_words(numeric_val)
            transformed_tokens.append(converted)
            i += 1
            continue

        # Handle percentage symbol if it's standalone
        if token.text == "%":
            transformed_tokens.append("percent")
            i += 1
            continue

        if token.text in OPERATOR_MAP:
            operator_word = OPERATOR_MAP[token.text]
            transformed_tokens.append(operator_word)
            i += 1
            continue
        
        transformed_tokens.append(token.text)
        i += 1

    final_output = []
    for tok in transformed_tokens:
        if re.fullmatch(r"[.,!?;:]+", tok):
            if final_output:
                final_output[-1] = final_output[-1].rstrip() + tok
            else:
                final_output.append(tok)
        else:
            if final_output and re.search(r"[.,!?;:]$", final_output[-1].rstrip()):
                final_output.append(" " + tok)
            else:
                if final_output and not final_output[-1].isspace():
                    final_output.append(" " + tok)
                else:
                    final_output.append(tok)

    return "".join(final_output).strip()
