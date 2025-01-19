from spacy.tokenizer import Tokenizer
import spacy.util

def custom_tokenizer(nlp_model: spacy.language.Language) -> Tokenizer:
    prefix_patterns = list(nlp_model.Defaults.prefixes)
    infix_patterns = list(nlp_model.Defaults.infixes)
    suffix_patterns = list(nlp_model.Defaults.suffixes)

    # 1. numbers with exponential notation
    # 2. Mixed characters (numebrs and alphabets)
    if r"(\d+(?:\.\d+)?)e([+-]?\d+)|(?<=[a-zA-Z])(?=\d)|(?<=\d)(?=[a-zA-Z])" not in infix_patterns:
        infix_patterns.append(r"(\d+(?:\.\d+)?)e([+-]?\d+)|(?<=[a-zA-Z])(?=\d)|(?<=\d)(?=[a-zA-Z])")

    if r"(?<=[0-9])(\+|-)(?=[0-9])" not in infix_patterns:
        infix_patterns.append(r"(?<=[0-9])(\+|-)(?=[0-9])")

    if r"(\()|(\))|(\[)|(\])|(\{)|(\}|\*|%|\^|=|/|\+|-)" not in infix_patterns:
        infix_patterns.append(r"(\()|(\))|(\[)|(\])|(\{)|(\}|\*|%|\^|=|/|\+|-)")

    prefix_regex = spacy.util.compile_prefix_regex(prefix_patterns)
    infix_regex = spacy.util.compile_infix_regex(infix_patterns)
    suffix_regex = spacy.util.compile_suffix_regex(suffix_patterns)

    return Tokenizer(
        nlp_model.vocab,
        prefix_search=prefix_regex.search,
        suffix_search=suffix_regex.search,
        infix_finditer=infix_regex.finditer
    )
