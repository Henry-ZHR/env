from requests import get
from string import punctuation
from sys import argv, stderr, stdout
from yaml import safe_dump

output_to_stdout = False
if len(argv) == 1:
    output_to_stdout = True
elif len(argv) != 2:
    print(f'Usage: {argv[0]} <output-file>', file=stderr)
    exit(1)


def get_emoji_list() -> list:

    def convert(s: bytes) -> str:
        s = s.strip()
        assert s.startswith(b'U+')
        return chr(int(s[2:], base=16))

    s = []
    for line in get('https://unicode.org/emoji/charts/emoji-ordering.txt'
                    ).content.split(b'\n'):
        if line.startswith(b'#') or b':' in line:
            # Use ':' in comment to filter different tones
            continue
        s.append(''.join(map(convert, line.split(b';')[0].split())))
    return list(filter(None, s))


def get_en_list() -> list:
    return []


def get_zh_list() -> list:
    # https://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno=22EA6D162E4110E752259661E1A0D0A8
    # https://people.ubuntu.com/~happyaron/l10n/GB(T)15834-2011.html
    return [
        '。', '？', '！', '，', '、', '；', '：', '“', '”', '‘', '’', '「', '」', '『',
        '』', '（', '）', '［', '］', '〔', '〕', '【', '】', '——', '……', '～', '·', '《',
        '》', '〈', '〉'
    ]


def get_math_list() -> list:
    # https://www.unicode.org/charts/PDF/U2200.pdf
    return [chr(i) for i in range(0x2200, 0x2300)]


s = {
    'liquid_keyboard': {
        'key_height': 40,
        'key_height_land': 40,
        'single_width': 32,
        'vertical_gap': 4,
        'margin_x': 2,
        'keyboards':
        ['exit', 'clipboard', 'zh', 'en', 'emoji', 'math', 'exit'],
        'exit': {
            'name': '返回',
            'type': 'NO_KEY',
            'keys': 'EXIT'
        },
        'clipboard': {
            'name': '剪贴',
            'type': 'CLIPBOARD'
        },
        'zh': {
            'name': '中文',
            'type': 'SINGLE',
            'keys': get_zh_list()
        },
        'en': {
            'name': '英文',
            'type': 'SINGLE',
            'keys': list(punctuation)
        },
        'emoji': {
            'name': '绘文字',
            'type': 'SINGLE',
            'keys': get_emoji_list()
        },
        'math': {
            'name': '数学',
            'type': 'SINGLE',
            'keys': get_math_list()
        }
    }
}

safe_dump(s,
          stdout if output_to_stdout else open(argv[1], 'w'),
          allow_unicode=True)
