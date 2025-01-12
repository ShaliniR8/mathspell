import re

pattern = r'([0-9]+)([a-zA-Z]+)([0-9]*)|([0-9]*)([a-zA-Z]+)([0-9]+)'

test_strings = [
    "123abcd",         # allowed
    "abcd123",        # allowed (because it doesn't contain e)
    "abcE123",        # not allowed (contains E)
    "123.456",        # not allowed (contains a dot)
    "2/5",       # not allowed (contains a backslash)
    "a/b",
    '-2)^3'
]

for s in test_strings:
    if re.fullmatch(pattern, s):
        print(f"{s!r} matches.")
    else:
        print(f"{s!r} does not match.")
