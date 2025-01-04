import re
import spacy
from spacy.tokenizer import Tokenizer
import spacy.util
from num2words import num2words

def custom_tokenizer(nlp):
    prefix_patterns = list(nlp.Defaults.prefixes)
    infix_patterns = list(nlp.Defaults.infixes)
    suffix_patterns = list(nlp.Defaults.suffixes)
    
    if r"\$" not in prefix_patterns:
        prefix_patterns.append(r"\$")

    extra_infix = r"(?<=[0-9])\.(?=[A-Z])"
    if extra_infix not in infix_patterns:
        infix_patterns.append(extra_infix)

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

nlp = spacy.load("en_core_web_sm")
nlp.tokenizer = custom_tokenizer(nlp)

def convert_number_to_words(number: float, to_year: bool = False) -> str:
    if to_year and number.is_integer():
        return num2words(int(number), to="year")
    return num2words(number)

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

def looks_like_year_context(token) -> bool:
    if token.ent_type_ in ("DATE", "TIME"):
        return True
    return False

def interpret_currency_dollars(number: float) -> str:
    as_str = f"{number:.2f}"  # ensures 2 decimals
    whole_str, fractional_str = as_str.split(".")
    whole_val = int(whole_str)
    fractional_val = int(fractional_str)

    if fractional_val == 0:
        return f"{num2words(whole_val)} dollars"
    return f"{num2words(whole_val)} dollars {num2words(fractional_val)} cents"

def interpret_currency_bucks(number: float) -> str:
    rounded = round(number)
    return f"{num2words(rounded)} bucks"

def analyze_text(text: str) -> str:
    doc = nlp(text)
    transformed_tokens = []
    i = 0

    while i < len(doc):
        token = doc[i]

        if token.is_space:
            transformed_tokens.append(token.text)
            i += 1
            continue
        if token.is_punct:
            transformed_tokens.append(token.text)
            i += 1
            continue

        if token_is_ordinal(token):
            transformed_tokens.append(convert_ordinal_string(token.text))
            i += 1
            continue

        if token.like_num:
            try:
                numeric_val = float(token.text.replace(',', ''))
            except ValueError:
                transformed_tokens.append(token.text)
                i += 1
                continue

            prev_token = doc[i - 1] if i - 1 >= 0 else None
            next_token = doc[i + 1] if i + 1 < len(doc) else None

            if looks_like_year_context(token) and 1000 <= numeric_val <= 2100:
                if next_token and next_token.text == 'times':
                    pass
                else:
                    transformed_tokens.append(convert_number_to_words(numeric_val, to_year=True))
                    i += 1
                    continue

            if prev_token and prev_token.text == "$":
                if transformed_tokens[-1] == '$':
                    transformed_tokens.pop()

                converted = interpret_currency_dollars(numeric_val)
                # If next token is 'dollars' or 'bucks', skip it
                if next_token and next_token.lemma_.lower() in {"dollar", "dollars", "usd"}:
                    transformed_tokens.append(converted)
                    i += 2  # skip numeric and 'dollars'
                    continue
                elif next_token and next_token.lemma_.lower() in {"buck", "bucks"}:
                    transformed_tokens.append(interpret_currency_bucks(numeric_val))
                    i += 2
                    continue
                else:
                    transformed_tokens.append(converted)
                    i += 1
                    continue

            if next_token and next_token.lemma_.lower() in {"dollar", "dollars", "usd"}:
                transformed_tokens.append(interpret_currency_dollars(numeric_val))
                i += 2
                continue

            if next_token and next_token.lemma_.lower() in {"buck", "bucks"}:
                transformed_tokens.append(interpret_currency_bucks(numeric_val))
                i += 2
                continue

            transformed_tokens.append(convert_number_to_words(numeric_val))
            i += 1
            continue

        if token.text == "$":
            transformed_tokens.append(token.text)
            i += 1
            continue

        transformed_tokens.append(token.text)
        i += 1

    final_output = []
    for idx, tok in enumerate(transformed_tokens):
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

if __name__=='__main__':
    input = ("In 1913")
    print(analyze_text(input))

