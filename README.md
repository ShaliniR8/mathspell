# MathSpell

MathSpell is a Python package for converting numbers into contextually appropriate words, such as "twenty-first century" for years or "two thousand and twenty-three" for general numbers.

## Installation

1. Install the package:
    ```bash
    pip install mathspell
    ```

2. Download the required spaCy language model:
    ```bash
    python -m spacy download en_core_web_sm
    ```

## Usage

After installation, you can use MathSpell to process text containing numbers. For example:

```python
from mathspell import analyze_text

text = "This is the 21st century. I was born in 1995."
converted_text = analyze_text(text)
print(converted_text)
# Output: "This is the twenty-first century. I was born in nineteen ninety-five."
