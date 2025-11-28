from requests import get
from string import punctuation
from sys import argv, stderr, stdout
from unicodedata import category
from yaml import safe_dump

output_to_stdout = False
if len(argv) == 1:
    output_to_stdout = True
elif len(argv) != 2:
    print(f"Usage: {argv[0]} <output-file>", file=stderr)
    exit(1)


def get_emoji_list() -> list:
    def convert(s: bytes) -> str:
        s = s.strip()
        assert s.startswith(b"U+")
        return chr(int(s[2:], base=16))

    s = []
    for line in get(
        "https://unicode.org/emoji/charts/emoji-ordering.txt"
    ).content.split(b"\n"):
        if line.startswith(b"#") or b":" in line:
            # Use ':' in comment to filter different tones
            continue
        s.append("".join(map(convert, line.split(b";")[0].split())))
    return list(filter(None, s))


def get_math_list() -> list:
    # https://www.unicode.org/charts/PDF/U2200.pdf
    return [chr(i) for i in range(0x2200, 0x2300)]


def get_greek_list() -> list:
    # https://www.unicode.org/charts/PDF/U0370.pdf
    return list(
        filter(lambda c: category(c) != "Cn", [chr(i) for i in range(0x0388, 0x03CF)])
    )


safe_dump(
    {
        "en": {"name": "英文", "type": "SINGLE", "keys": list(punctuation)},
        "emoji": {"name": "绘文字", "type": "SINGLE", "keys": get_emoji_list()},
        "math": {"name": "数学", "type": "SINGLE", "keys": get_math_list()},
        "greek": {"name": "希腊", "type": "SINGLE", "keys": get_greek_list()},
    },
    stdout if output_to_stdout else open(argv[1], "w"),
    allow_unicode=True,
)
