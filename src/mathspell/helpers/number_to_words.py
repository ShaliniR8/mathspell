from num2words import num2words

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
