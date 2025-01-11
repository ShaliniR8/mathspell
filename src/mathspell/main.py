import re
import spacy
import warnings
from spacy.tokenizer import Tokenizer
import spacy.util
from num2words import num2words
from unit_parse import parser as quantity_parser

nlp = spacy.load("en_core_web_sm")

# TODO: Move into a different file
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

CURRENCY_MAP = {
    '$': 'dollar',
    '€': 'euro',
    '£': 'pound',
    '¥': 'yen',
    '₹': 'rupee',
    '₽': 'ruble',
    '₩': 'won',
    '₪': 'shekel',
    '฿': 'baht',
    '₫': 'dong',
    '₱': 'peso',
    '₴': 'hryvnia',
    '₦': 'naira',
    '₲': 'guarani',
    '₵': 'cedi',
    '₡': 'colón',
    '₮': 'tögrög',
    '₸': 'tenge',
    '₺': 'lira',
    '₼': 'manat',
    '₾': 'lari',
    '₿': 'bitcoin',
}

ALTERNATIVE_CURRENCIES = {
    'dollar': '$',
    'usd': '$',
    'euro': '€',
    'eur': '€',
    'pound': '£',
    'gbp': '£',
    'yen': '¥',
    'jpy': '¥',
    'rupee': '₹',
    'inr': '₹',
    'ruble': '₽',
    'rub': '₽',
    'won': '₩',
    'krw': '₩',
    'shekel': '₪',
    'ils': '₪',
    'baht': '฿',
    'thb': '฿',
    'dong': '₫',
    'vnd': '₫',
    'peso': '₱',
    'php': '₱',
    'hryvnia': '₴',
    'uah': '₴',
    'naira': '₦',
    'ngn': '₦',
    'cedi': '₵',
    'ghs': '₵',
    'colón': '₡',
    'crc': '₡',
    'tögrög': '₮',
    'mnt': '₮',
    'tenge': '₸',
    'kzt': '₸',
    'lira': '₺',
    'try': '₺',
    'manat': '₼',
    'azn': '₼',
    'lari': '₾',
    'gel': '₾',
    'bitcoin': '₿',
    'btc': '₿'
}

MINOR_CURRENCY_MAP = {
    'dollar': 'cent',
    'euro': 'cent',
    'pound': 'penny',
    'yen': 'sen',
    'rupee': 'paisa',
    'ruble': 'kopeck',
    'won': 'jeon',
    'shekel': 'agora',
    'baht': 'satang',
    'dong': 'hao',
    'peso': 'centavo',
    'hryvnia': 'kopiyka',
    'naira': 'kobo',
    'cedi': 'pesewa',
    'colón': 'céntimo',
    'tögrög': 'möngö',
    'tenge': 'tiyn',
    'lira': 'kuruş',
    'manat': 'qəpik',
    'lari': 'tetri',
    'bitcoin': 'satoshi'

}

def custom_tokenizer(nlp):
    prefix_patterns = list(nlp.Defaults.prefixes)
    infix_patterns = list(nlp.Defaults.infixes)
    suffix_patterns = list(nlp.Defaults.suffixes)

    if r"(?<=[0-9])/(?=[0-9])" not in infix_patterns:
        infix_patterns.append(r"(?<=[0-9])/(?=[0-9])")
    
    prefix_regex = spacy.util.compile_prefix_regex(prefix_patterns)
    infix_regex = spacy.util.compile_infix_regex(infix_patterns)
    suffix_regex = spacy.util.compile_suffix_regex(suffix_patterns)

    return Tokenizer(
        nlp.vocab,
        prefix_search=prefix_regex.search,
        suffix_search=suffix_regex.search,
        infix_finditer=infix_regex.finditer
    )

nlp.tokenizer = custom_tokenizer(nlp)

# currencies
def interpret_currency(number: float, currency_name: str, minor_currency_name: str) -> str:
    as_str = f"{number:.2f}"
    whole_str, fractional_str = as_str.split(".")
    whole_val = int(whole_str)
    fractional_val = int(fractional_str)
    if whole_val > 1: currency_name += 's'
    if fractional_val > 1: fractional_val += 's'
 
    if fractional_val == 0:
        return f"{num2words(whole_val)} {currency_name}"
    return f"{num2words(whole_val)} {currency_name} {num2words(fractional_val)} {minor_currency_name}"

def token_is_currency(token) -> bool:
    return bool(CURRENCY_MAP.get(token.text, False))

def convert_to_currency(token) -> bool:
    return CURRENCY_MAP.get(token.text)
    
def interpret_currency_bucks(number: float) -> str:
    rounded = round(number)
    return f"{num2words(rounded)} bucks"

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
    return abbreviation in {"m", "b", "tr", 'gaz'}

# math

def token_looks_like_fraction(token, next_token, next_next_token) -> bool:
    return (token.like_num and next_next_token and next_token.text == '/' and next_next_token.like_num)

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

def token_is_a_quantity(token):
    q = quantity_parser(token.text)
    return bool(q and not q.dimensionless)

def convert_token_to_quantity(token):
    q = quantity_parser(token.text)
    magnitude = q.magnitude
    units = " ".join(list(q.units._units))
    # TODO: Handle cases where units is like 'foot ** 2'. Perhaps generate another NLP doc?
    if magnitude > 1:
        if units == 'foot':
            units = 'feet'
        else:
            units += 's'
    return f"{num2words(magnitude)} {units}"

def tokens_are_a_quantity(token, next_token):
    q = quantity_parser(f"{token.text} {next_token.text}")
    return bool(q and not q.dimensionless)

def convert_tokens_to_quantity(token, next_token):
    q = quantity_parser(f"{token.text} {next_token.text}")
    magnitude = q.magnitude
    units = " ".join(list(q.units._units))
    if magnitude > 1:
        if units == 'foot':
            units = 'feet'
        else:
            units += 's'
    return f"{num2words(magnitude)} {units}"

def token_has_exponential_notation(token):
    return bool(re.match(r"(\d+(?:\.\d+)?)[e]([+-]?\d+)", token.text, re.IGNORECASE))
        
def convert_exponential_notation_string(token_text:str):
    match = re.match(r"(\d+(?:\.\d+)?)[eE]([+-]?\d+)", token_text, re.IGNORECASE)
    if not match:
        return token_text
    else:
        base = match.group(1)
        exponent = match.group(2)
        try:
            return f"{num2words(base)} times ten to the power of {num2words(exponent)}"
        except ValueError:
            return token_text

# other helper functions
def convert_number_to_words(number: float, to_year: bool = False) -> str:
    if to_year and number.is_integer():
        return num2words(int(number), to="year")
    return num2words(int(number)) if number.is_integer() else num2words(number)

def preprocess_text(text: str) -> str:
    preprocessed_text = text
    return preprocessed_text

def analyze_text(text: str) -> str:
    doc = nlp(preprocess_text(text))
    # breakpoint()
    transformed_tokens = []
    i = 0

    while i < len(doc):
        token = doc[i]
        prev_token = doc[i - 1] if i - 1 >= 0 else None
        next_token = doc[i + 1] if i + 1 < len(doc) else None
        next_next_token = doc[i + 2] if i + 2 < len(doc) else None

        if token.is_space:
            transformed_tokens.append(token.text)
            i += 1
            continue

        if token.is_punct:
            if token.text in OPERATOR_MAP:
                transformed_tokens.append(OPERATOR_MAP[token.text])
            else:
                transformed_tokens.append(token.text)
            i += 1
            continue

        if token_has_exponential_notation(token):
            transformed_tokens.append(convert_exponential_notation_string(token.text))
            i += 1
            continue

        if token_is_ordinal(token):
            transformed_tokens.append(convert_ordinal_string(token.text))
            i += 1
            continue

        if token_is_a_quantity(token):
            transformed_tokens.append(convert_token_to_quantity(token))
            i += 1
            continue

        if token.like_num and next_token and tokens_are_a_quantity(token, next_token):
            transformed_tokens.append(convert_tokens_to_quantity(token, next_token))
            i += 2
            continue

        if token_looks_like_fraction(token, next_token, next_next_token):
            # TODO: Needs more work separating division operation and fraction
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
        if token_is_currency(token):
            currency = convert_to_currency(token)
            transformed_tokens.append(currency)
            i += 1
            continue

        if token.like_num:
            try:
                numeric_val = float(token.text.replace(',', ''))
            except ValueError:
                if token.text.count('.') > 1: 
                    transformed_text = " point ".join([*map(num2words, token.text.split('.'))])
                    transformed_tokens.append(transformed_text)
                else:
                    transformed_tokens.append(token.text)
                i += 1
                continue

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
# here
            if next_token and is_illion_scale(next_token):
                scale_word = next_token.text.lower()
                if next_next_token.lemma_.lower() in ALTERNATIVE_CURRENCIES.keys() and prev_token and token_is_currency(prev_token):
                    transformed_tokens.pop() 
                    transformed_text = f"{num2words(numeric_val)} {scale_word} {next_next_token.text}"
                    transformed_tokens.append(transformed_text)
                    i += 3
                    continue
                elif next_next_token.lemma_.lower() in ALTERNATIVE_CURRENCIES.keys():
                    transformed_text = f"{num2words(numeric_val)} {scale_word} {next_next_token.text}"
                    transformed_tokens.append(transformed_text)
                    i += 3
                    continue
                elif prev_token and token_is_currency(prev_token):
                    currency = transformed_tokens.pop() 
                    if numeric_val > 1: currency += 's'
                    transformed_text = f"{num2words(numeric_val)} {scale_word} {currency}"
                    transformed_tokens.append(transformed_text)
                    i += 3
                    continue
                else:
                    transformed_text = f"{num2words(numeric_val)} {scale_word}"
                    i += 2
                    continue

            if prev_token and token_is_currency(prev_token):
                if next_token:
                    transformed_tokens.pop()
                    currency_name = next_token.lemma_.lower()
                    if currency_name in {"buck", "bucks"}:
                        converted = interpret_currency_bucks(numeric_val)
                        transformed_tokens.append(converted)
                        i += 2
                        continue
                    elif currency_name in ALTERNATIVE_CURRENCIES.keys():
                        minor_currency_name = MINOR_CURRENCY_MAP.get(currency_name, 'subunit')
                        converted = interpret_currency(numeric_val, currency_name, minor_currency_name)
                        transformed_tokens.append(converted)
                        i += 2
                        continue
                    else:
                        transformed_tokens.append(num2words(numeric_val))
                        i += 1
                        continue

            # if next_token and next_token.lemma_.lower() in {"dollar", "dollars", "usd"}:
            #     converted = interpret_currency(numeric_val, 'dollar', 'cent')
            #     transformed_tokens.append(converted)
            #     i += 2
            #     continue

            # if next_token and next_token.lemma_.lower() in {"buck", "bucks"}:
            #     converted = interpret_currency_bucks(numeric_val)
            #     transformed_tokens.append(converted)
            #     i += 2
            #     continue

            converted = convert_number_to_words(numeric_val)
            transformed_tokens.append(converted)
            i += 1
            continue

        # handle percentage symbol if it's standalone
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
    try:
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
    except TypeError as e:
        raise TypeError(
            f"tok: {tok}\n {e}"
        )


    return "".join(final_output).strip()

if __name__ == '__main__':
    print(analyze_text('I have $3.8'))
