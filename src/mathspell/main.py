import re
import spacy
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

    if r"(\d+(?:\.\d+)?)e([+-]?\d+)|(?<=[a-zA-Z])(?=\d)|(?<=\d)(?=[a-zA-Z])" not in infix_patterns:
        infix_patterns.append(r"(\d+(?:\.\d+)?)e([+-]?\d+)|(?<=[a-zA-Z])(?=\d)|(?<=\d)(?=[a-zA-Z])")
    if r"(?<=[0-9])/(?=[0-9])" not in infix_patterns:
        infix_patterns.append(r"(?<=[0-9])/(?=[-+0-9])")
    if r"\)" not in infix_patterns:
        infix_patterns.append(r"\)")
    if r"\(" not in infix_patterns:
        infix_patterns.append(r"\(")
    if r"(?<=[\w\(\)])[^\w\s/.,'](?=[\w\(\)])" not in infix_patterns:
        infix_patterns.append(r"(?<=[\w\(\)])[^\w\s/.,'](?=[\w\(\)])")
    
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
    if fractional_val > 1: minor_currency_name += 's'
    if fractional_val == 0:
        return f"{num2words(whole_val)} {currency_name}"
    return f"{num2words(whole_val)} {currency_name} {num2words(fractional_val)} {minor_currency_name}"

def token_is_currency(token) -> bool:
    return bool(CURRENCY_MAP.get(token.lemma_.lower(), False))
    
def interpret_currency_bucks(number: float) -> str:
    rounded = round(number)
    return f"{num2words(rounded)} bucks"

# ordinals
def convert_ordinal_string(token_text: str, next_token_text: str) -> str:
    match = re.match(r"^(-?\d+)(st|nd|rd|th)$", f"{token_text}{next_token_text}", re.IGNORECASE)
    number_part = match.group(1)
    try:
        return num2words(int(number_part), to="ordinal")
    except ValueError:
        return token_text

def token_is_ordinal(token, next_token) -> bool:
    return bool(re.match(r"^(-?\d+)(st|nd|rd|th)$", f"{token.text}{next_token.text}", re.IGNORECASE))

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

def operator_is_part_of_quantity(token, prev_token, prev_prev_token, next_token) -> bool:
    if prev_prev_token and prev_prev_token.like_num:
        string = f"{prev_prev_token.text} {prev_token.text}/{next_token.text}"
    elif prev_prev_token and token_has_exponential_notation(prev_prev_token):
        string = f"1 {prev_token.text}/{next_token.text}"
    else:
        return False
    return bool(token.text == '/' and token_is_a_quantity(string))

def convert_operator_part_of_quantity(prev_token, prev_prev_token, next_token) -> str:
    if prev_prev_token.like_num:
        string = f"{prev_prev_token.text} {prev_token.text}/{next_token.text}"
        return convert_token_to_quantity(string)
    elif token_has_exponential_notation(prev_prev_token):
        string = f"1 {prev_token.text}/{next_token.text}"
        return convert_token_to_quantity(string, True)
               
def token_is_a_quantity(string: str):
    try:
        q = quantity_parser(string)
        return bool(q and not q.dimensionless)
    except AttributeError as e:
        return False

def units_to_string(units: dict) -> str: 
    format_map = { 1: "{key}", -1: "per {key}" } 
    parts = [] 
    for key, val in units.items(): 
        if val in format_map: 
            parts.append(format_map[val].format(key=key)) 
        elif val > 1: 
            parts.append(f"{key} to the power of {val}") 
        elif val < -1: 
            parts.append(f"per {key} to the power of {-val}") 
    return " ".join(parts)
    
def convert_token_to_quantity(string: str, magnitude_is_exp: bool = False):
    q = quantity_parser(string)
    magnitude = q.magnitude
    units = units_to_string(dict(q.units._units))
    if magnitude_is_exp:
        return units
    return f"{num2words(magnitude)} {units}"

def tokens_are_a_quantity(combined_token_text: str) -> bool:
    q = quantity_parser(combined_token_text)
    return bool(q and not q.dimensionless)

def convert_tokens_to_quantity(combined_token_text: str, magnitude_is_exp: bool = False) -> str:
    q = quantity_parser(combined_token_text)
    magnitude = q.magnitude
    units = units_to_string(dict(q.units._units))
    if magnitude_is_exp:
        return units
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

def interpret_large_scale(number: float, scale: str) -> str:
    if number.is_integer():
        number_words = num2words(int(number))
    else:
        whole_part = int(number)
        fractional_part = int(round((number - whole_part) * 10**len(str(number).split('.')[-1])))
        
        whole_words = num2words(whole_part)
        fractional_words = num2words(fractional_part)
        
        number_words = f"{whole_words} point {fractional_words}"
    
    return f"{number_words} {scale}"

def analyze_text(text: str) -> str:
    doc = nlp(preprocess_text(text))
    transformed_tokens = []
    i = 0
    while i < len(doc):
        token = doc[i]
        prev_token = doc[i - 1] if i - 1 >= 0 else None
        prev_prev_token = doc[i-2] if i - 2 >= 0 else None
        next_token = doc[i + 1] if i + 1 < len(doc) else None
        next_next_token = doc[i + 2] if i + 2 < len(doc) else None
        if token.is_space:
            transformed_tokens.append(token.text)
            i += 1
            continue

        if token.is_punct:
            if token.text in OPERATOR_MAP:
                if operator_is_part_of_quantity(token, prev_token, prev_prev_token, next_token):
                    transformed_tokens.pop()
                    converted = convert_operator_part_of_quantity(prev_token, prev_prev_token, next_token)
                    transformed_tokens.append(converted)
                    i += 2
                    continue
                else:
                    transformed_tokens.append(OPERATOR_MAP[token.text])
            else:
                transformed_tokens.append(token.text)
            i += 1
            continue

        if token_has_exponential_notation(token):
            transformed_tokens.append(convert_exponential_notation_string(token.text))
            i += 1
            if next_token and tokens_are_a_quantity(f"1 {next_token.text}"):
                units = convert_tokens_to_quantity(f"1 {next_token.text}", True)
                transformed_tokens.append(units)
                i += 1
            continue

        if token.like_num and next_token and token_is_ordinal(token, next_token):
            transformed_tokens.append(convert_ordinal_string(token.text, next_token.text))
            i += 2
            continue

        if token_is_a_quantity(token.text):
            transformed_tokens.append(convert_token_to_quantity(token.text))
            i += 1
            continue

        if token.like_num and next_token and tokens_are_a_quantity(f"{token.text} {next_token.text}"):
            transformed_tokens.append(convert_tokens_to_quantity(f"{token.text} {next_token.text}"))
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
            if prev_token and token_is_currency(prev_token):
                transformed_tokens.pop()

                if next_token and is_illion_scale(next_token):
                    scale_word = next_token.text.lower()
                    converted = interpret_large_scale(numeric_val, scale_word)

                    if next_next_token:
                        if next_next_token.lemma_.lower() in ALTERNATIVE_CURRENCIES.keys():
                            converted += f" {next_next_token.text}"
                            i += 3
                        else:
                            currency_name = CURRENCY_MAP[prev_token.text]
                            converted += f" {currency_name}s"
                            i += 2
                    else:
                        i += 2

                    transformed_tokens.append(converted)
                    continue
                else:
                    currency_name = CURRENCY_MAP.get(prev_token.text)
                    minor_currency_name = MINOR_CURRENCY_MAP.get(currency_name, 'subunit')
                    converted = interpret_currency(numeric_val, currency_name, minor_currency_name)
                    transformed_tokens.append(converted)
                    i += 1
                    continue

            if next_token and is_illion_scale(next_token):
                scale_word = next_token.text.lower()
                converted = interpret_large_scale(numeric_val, scale_word)

                # check if 'dollars' follows the scale word
                if next_next_token:
                    if next_next_token.lemma_.lower() in ALTERNATIVE_CURRENCIES.keys():
                        converted += f" {next_next_token.text}"
                        i += 3 
                    else:
                        i += 2 
                else:
                    i += 2

                transformed_tokens.append(converted)
                continue

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
        
        if token.text in CURRENCY_MAP:
            currency_name = CURRENCY_MAP[token.text]
            transformed_tokens.append(currency_name)
            i+= 1
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
    print(analyze_text("7th"))
