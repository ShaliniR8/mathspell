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

3. Upgrade Pint to it's latest version if it is incompatible with the current version of numpy.
    ```bash
    pip install --upgrade pint
    ```

## Usage

After installation, you can use MathSpell to process text containing numbers. For example:

```python
from mathspell import analyze_text

text = "This is the 21st century. I was born in 1995."
converted_text = analyze_text(text)
print(converted_text)
# Output: "This is the twenty-first century. I was born in nineteen ninety-five."
```

## **Further Examples**

### **1. Year Conversion**
```python
from mathspell import analyze_text

input_text = "Something happened in 2021."
output = analyze_text(input_text)
print(output)
# Output: "Something happened in twenty twenty-one."
```

---

### **2. Ordinal Numbers**
```python
from mathspell import analyze_text

input_text = "This is my 3rd attempt to fix the bug."
output = analyze_text(input_text)
print(output)
# Output: "This is my third attempt to fix the bug."
```

---

### **3. Dates and Years**
```python
from mathspell import analyze_text

input_text = "My birthday is on 4th April, 1993."
output = analyze_text(input_text)
print(output)
# Output: "My birthday is on fourth April, nineteen ninety-three."
```

---

### **4. Quantities**
```python
from mathspell import analyze_text

input_text = "This contains 15 boxes."
output = analyze_text(input_text)
print(output)
# Output: "This contains fifteen boxes."
```

### **5. Handling Ordinal and Non-Ordinal Context**
```python
from mathspell import analyze_text

input_text = "This is the 1st floor, and the elevator can hold 5 people."
output = analyze_text(input_text)
print(output)
# Output: "This is the first floor, and the elevator can hold five people."
```

---

### **6. Temperature Conversion**
```python
from mathspell import analyze_text

input_text = "The temperature is expected to be 25 degrees tomorrow."
output = analyze_text(input_text)
print(output)
# Output: "The temperature is expected to be twenty-five degrees tomorrow."
```

---

### **7. Complex Sentence**
```python
from mathspell import analyze_text

input_text = "The 2nd prize was awarded in 2022 for the 10th time."
output = analyze_text(input_text)
print(output)
# Output: "The second prize was awarded in twenty twenty-two for the tenth time."
```