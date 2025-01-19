import spacy
from mathspell.helpers import constants as c 
from mathspell.helpers.spacy_tokenizer import custom_tokenizer
from mathspell.helpers.cases import * # TODO: change this, this is a bad practice

nlp = spacy.load("en_core_web_sm")
nlp.tokenizer = custom_tokenizer(nlp)

def preprocess_text(text: str) -> str:
    """
    Perform various date/time conversions before passing text to the main parser.
    """
    return process_time_patterns_ahead_of_tokenization(text)

def analyze_text(text: str) -> str:
    """
    Main function to parse the text with SpaCy, interpret tokens (numbers, dates,
    currencies, units, etc.), and output a 'spoken' transformation.
    """
    doc = nlp(preprocess_text(text))
    transformed_tokens = []
    i = 0

    while i < len(doc):
        token = doc[i]
        prev_token = doc[i - 1] if i - 1 >= 0 else None
        prev_prev_token = doc[i - 2] if i - 2 >= 0 else None
        next_token = doc[i + 1] if i + 1 < len(doc) else None
        next_next_token = doc[i + 2] if i + 2 < len(doc) else None

        if token.is_space:
            transformed_tokens.append(token.text)
            i += 1
            continue

        # Handle possessive "'s"
        if token.text == "'s" and prev_token and prev_token.tag_ in ['PRP', 'NNP', 'PRON']:
            # Append "'s" directly to the previous token text
            transformed_text = transformed_tokens.pop()
            transformed_tokens.append(f"{transformed_text}'s")
            i += 1
            continue

        if token.is_punct:
            if token.text in c.OPERATOR_MAP:
                # Check if slash is part of a quantity expression
                if operator_is_part_of_quantity(token, prev_token, prev_prev_token, next_token):
                    transformed_tokens.pop()
                    converted = convert_operator_part_of_quantity(prev_token, prev_prev_token, next_token)
                    transformed_tokens.append(converted)
                    i += 2
                    continue
                else:
                    transformed_tokens.append(c.OPERATOR_MAP[token.text])
            else:
                transformed_tokens.append(token.text)
            i += 1
            continue

        if token_has_exponential_notation(token):
            transformed_tokens.append(convert_exponential_notation_string(token.text))
            i += 1
            # If the next token is a unit, convert that as well
            if next_token and tokens_are_a_quantity(f"1 {next_token.text}"):
                units = convert_tokens_to_quantity(f"1 {next_token.text}", magnitude_is_exp=True)
                transformed_tokens.append(units)
                i += 1
            continue

        if token.like_num and next_token and token_is_ordinal(token.text, next_token.text):
            transformed_tokens.append(convert_ordinal_string(token.text, next_token.text))
            i += 2
            continue

        if token_is_a_quantity(token.text):
            transformed_tokens.append(convert_token_to_quantity(token.text))
            i += 1
            continue

        if token.like_num and next_token and tokens_are_a_quantity(f"{token.text} {next_token.text}"):
            combined = f"{token.text} {next_token.text}"
            transformed_tokens.append(convert_tokens_to_quantity(combined))
            i += 2
            continue

        if token_looks_like_fraction(token, next_token, next_next_token):
            try:
                numerator = float(token.text.replace(',', ''))
                denominator = float(next_next_token.text.replace(',', ''))
                # Convert to words (e.g., "three over four")
                numerator_word = (
                    convert_number_to_words(int(numerator)) if numerator.is_integer() 
                    else convert_number_to_words(numerator)
                )
                denominator_word = (
                    convert_number_to_words(int(denominator)) if denominator.is_integer() 
                    else convert_number_to_words(denominator)
                )
                fraction = f"{numerator_word} over {denominator_word}"
                transformed_tokens.append(fraction)
                i += 3  # skip the three tokens
                continue
            except ValueError:
                pass

        if token.like_num:
            try:
                numeric_val = float(token.text.replace(',', ''))
            except ValueError:
                # Handle malformed numeric strings with multiple dots
                if token.text.count('.') > 1:
                    parts = token.text.split('.')
                    # e.g. "192.168.0.1" -> "one ninety-two point one sixty-eight point zero point one" (?)
                    transformed_text = " point ".join(map(lambda x: convert_number_to_words(int(x)), parts))
                    transformed_tokens.append(transformed_text)
                else:
                    transformed_tokens.append(token.text)
                i += 1
                continue

            if next_token and next_token.text == "%":
                converted = handle_percentage(numeric_val)
                transformed_tokens.append(converted)
                i += 2
                continue

            # Handle year context (e.g., "2023" -> "twenty twenty-three")
            if looks_like_year_context(token) and 1000 <= numeric_val <= 2100:
                # Avoid conflict with tokens like "ID" after a year
                if not (next_token and next_token.text.lower() in {"points", "point", "id", "ids"}):
                    transformed_tokens.append(convert_number_to_words(numeric_val, to_year=True))
                    i += 1
                    continue

            # Handle currency
            if prev_token and token_is_currency(prev_token.text):
                transformed_tokens.pop()

                # If next token is a scale (million, etc.)
                if next_token and is_illion_scale(next_token):
                    scale_word = next_token.text.lower()
                    converted = interpret_large_scale(numeric_val, scale_word)

                    if next_next_token:
                        if next_next_token.lemma_.lower() in c.ALTERNATIVE_CURRENCIES:
                            converted += f" {next_next_token.text}"
                            i += 3
                        else:
                            currency_name = c.CURRENCY_MAP[prev_token.text]
                            converted += f" {currency_name}s"
                            i += 2
                    else:
                        i += 2

                    transformed_tokens.append(converted)
                    continue

                else:
                    currency_name = c.CURRENCY_MAP.get(prev_token.text, 'dollar')
                    minor_currency_name = c.MINOR_CURRENCY_MAP.get(currency_name, 'cent')
                    converted = interpret_currency(numeric_val, currency_name, minor_currency_name)
                    transformed_tokens.append(converted)
                    i += 1
                    continue

            if next_token and is_illion_scale(next_token):
                scale_word = next_token.text.lower()
                converted = interpret_large_scale(numeric_val, scale_word)
                if next_next_token:
                    if next_next_token.lemma_.lower() in c.ALTERNATIVE_CURRENCIES:
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

        if token.text in c.OPERATOR_MAP:
            operator_word = c.OPERATOR_MAP[token.text]
            transformed_tokens.append(operator_word)
            i += 1
            continue

        if token.text in c.CURRENCY_MAP:
            currency_name = c.CURRENCY_MAP[token.text]
            transformed_tokens.append(currency_name)
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
        raise TypeError(f"Error with token '{tok}'\n {e}")

    return "".join(final_output).strip()
