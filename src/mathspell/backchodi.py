import spacy
from spacy.tokenizer import Tokenizer
from spacy.lang.en import English
import re

# Initialize spaCy
nlp = spacy.load('en_core_web_sm')

# Create a custom tokenizer function
def custom_tokenizer(nlp):
    infix_patterns = list(nlp.Defaults.infixes)

    if r"(\d+(?:\.\d+)?e\d+)|([a-zA-Z]+)" not in infix_patterns:
        infix_patterns.append(r"(\d+(?:\.\d+)?e\d+)|([a-zA-Z]+)")
    if r"(?<=[0-9])/(?=[0-9])" not in infix_patterns:
        infix_patterns.append(r"(?<=[0-9])/(?=[-+0-9])")
    if r"\)" not in infix_patterns:
        infix_patterns.append(r"\)")
    if r"\(" not in infix_patterns:
        infix_patterns.append(r"\(")
    if r"(?<=[\w\(\)])[^\w\s/.,'](?=[\w\(\)])" not in infix_patterns:
        infix_patterns.append(r"(?<=[\w\(\)])[^\w\s/.,'](?=[\w\(\)])")

    infix_regex = spacy.util.compile_infix_regex(infix_patterns)

    return Tokenizer(
        nlp.vocab,
        infix_finditer=infix_regex.finditer
    )

def custom_tokenizer_2(nlp):
    infix_re = re.compile(r"(\d+(?:\.\d+)?)e([+-]?\d+)|(?<=[a-zA-Z])(?=\d)|(?<=\d)(?=[a-zA-Z])")
    
    # infix_re = re.compile(r"(\d+(?:\.\d+)?e\d+)|([a-zA-Z]+)")
    return Tokenizer(nlp.vocab, infix_finditer=infix_re.finditer)


# Replace the default tokenizer with the custom one
nlp.tokenizer = custom_tokenizer_2(nlp)

# Test the custom tokenizer
doc = nlp("A12 10.7 X5Y7 10e5 10.4e3 0.6767e-5 $56.5")
tokens = [token.text for token in doc]

print(tokens)
