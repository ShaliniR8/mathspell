import re

pattern = r"(?<=[0-9])/(?=[0-9])"
test_strings = [
    "ABC123",         # allowed
    "abcd123",        # allowed (because it doesn't contain e)
    "abcE123",        # not allowed (contains E)
    "123.456",        # not allowed (contains a dot)
    "2/5",       # not allowed (contains a backslash)
    "()"
]

for s in test_strings:
    if re.fullmatch(pattern, s):
        print(f"{s!r} matches.")
    else:
        print(f"{s!r} does not match.")
