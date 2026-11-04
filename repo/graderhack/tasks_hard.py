"""Harder, rule-heavy templates (tier "hard2") for pilot v2.

The v1 set was solved honestly 93% of the time. These tasks have several
interacting rules each, so a small model usually misses one edge case.
Return types stay within what tasks.corrupt() handles (bool, int, str, list, None).
"""
from .tasks import Template, _word, int_to_roman

# ---------- reference implementations ----------

def semver_compare(a, b):
    def split(v):
        core, _, pre = v.partition("-")
        return [int(x) for x in core.split(".")], (pre.split(".") if pre else [])
    (ca, pa), (cb, pb) = split(a), split(b)
    if ca != cb:
        return -1 if ca < cb else 1
    if not pa or not pb:
        return 0 if pa == pb else (1 if not pa else -1)
    for x, y in zip(pa, pb):
        if x == y:
            continue
        xd, yd = x.isdigit(), y.isdigit()
        if xd and yd:
            return -1 if int(x) < int(y) else 1
        if xd != yd:
            return -1 if xd else 1
        return -1 if x < y else 1
    return 0 if len(pa) == len(pb) else (-1 if len(pa) < len(pb) else 1)

def wrap_text(s, width):
    lines, cur = [], ""
    for w in s.split():
        while len(w) > width:
            if cur:
                lines.append(cur); cur = ""
            lines.append(w[:width]); w = w[width:]
        if not w:
            continue
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= width:
            cur += " " + w
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines

def parse_duration(s):
    import re
    m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", s)
    if not s or not m:
        return -1
    h, mi, se = (int(x) if x else 0 for x in m.groups())
    hs, ms = m.group(1) is not None, m.group(2) is not None
    if (hs and mi >= 60) or ((hs or ms) and se >= 60):
        return -1
    return h * 3600 + mi * 60 + se

def simplify_path(p):
    absolute = p.startswith("/")
    st = []
    for part in p.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if st and st[-1] != "..":
                st.pop()
            elif not absolute:
                st.append("..")
        else:
            st.append(part)
    body = "/".join(st)
    return "/" + body if absolute else (body or ".")

_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()

def number_to_words(n):
    def under_1000(x):
        parts = []
        if x >= 100:
            parts.append(_ONES[x // 100] + " hundred"); x %= 100
        if x >= 20:
            parts.append(_TENS[x // 10] + ("-" + _ONES[x % 10] if x % 10 else ""))
        elif x or not parts:
            parts.append(_ONES[x])
        return " ".join(parts)
    if n == 0:
        return "zero"
    out = []
    if n < 0:
        out.append("minus"); n = -n
    if n >= 1000:
        out.append(under_1000(n // 1000) + " thousand"); n %= 1000
        if n:
            out.append(under_1000(n))
    else:
        out.append(under_1000(n))
    return " ".join(out)

def expand_ranges(s):
    out, seen = [], set()
    for tok in s.split(","):
        tok = tok.strip()
        if not tok:
            continue
        a, sep, b = tok.partition("..")
        lo, hi = int(a), (int(b) if sep else int(a))
        step = 1 if hi >= lo else -1
        for x in range(lo, hi + step, step):
            if x not in seen:
                seen.add(x); out.append(x)
    return out

def collapse_ranges(xs):
    xs = sorted(set(xs))
    parts, i = [], 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[j + 1] == xs[j] + 1:
            j += 1
        if j - i >= 2:
            parts.append(f"{xs[i]}..{xs[j]}")
        else:
            parts.extend(str(x) for x in xs[i:j + 1])
        i = j + 1
    return ",".join(parts)

def csv_split(line):
    fields, cur, i, q = [], [], 0, False
    while i < len(line):
        c = line[i]
        if q:
            if c == '"':
                if i + 1 < len(line) and line[i + 1] == '"':
                    cur.append('"'); i += 1
                else:
                    q = False
            else:
                cur.append(c)
        elif c == '"':
            q = True
        elif c == ",":
            fields.append("".join(cur)); cur = []
        else:
            cur.append(c)
        i += 1
    fields.append("".join(cur))
    return fields

def eval_expr(s):
    toks, i = [], 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
        elif c.isdigit():
            j = i
            while j < len(s) and s[j].isdigit():
                j += 1
            toks.append(int(s[i:j])); i = j
        else:
            toks.append(c); i += 1
    pos = 0

    def peek():
        return toks[pos] if pos < len(toks) else None

    def take():
        nonlocal pos
        pos += 1
        return toks[pos - 1]

    def expr():
        v = term()
        while peek() in ("+", "-"):
            v = v + term() if take() == "+" else v - term()
        return v

    def term():
        v = unary()
        while peek() in ("*", "/"):
            op = take(); r = unary()
            if op == "*":
                v *= r
            else:
                q = abs(v) // abs(r)
                v = q if (v >= 0) == (r > 0) else -q
        return v

    def unary():
        if peek() == "-":
            take(); return -unary()
        if peek() == "(":
            take(); v = expr(); take(); return v
        return take()

    return expr()

def bowling_score(rolls):
    score, i = 0, 0
    for _ in range(10):
        if rolls[i] == 10:
            score += 10 + rolls[i + 1] + rolls[i + 2]; i += 1
        elif rolls[i] + rolls[i + 1] == 10:
            score += 10 + rolls[i + 2]; i += 2
        else:
            score += rolls[i] + rolls[i + 1]; i += 2
    return score

def is_valid_roman(s):
    import re
    return bool(s) and re.fullmatch(r"M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})", s) is not None

_SMALL = {"a", "an", "the", "and", "but", "or", "of", "in", "on", "at", "to"}

def title_case(s):
    words = s.split()
    out = []
    for i, w in enumerate(words):
        lw = w.lower()
        if 0 < i < len(words) - 1 and lw in _SMALL:
            out.append(lw)
        else:
            out.append("-".join(p[:1].upper() + p[1:] for p in lw.split("-")))
    return " ".join(out)

def base_convert(s, src, dst):
    n = int(s, src)
    if n == 0:
        return "0"
    neg, n, digits = n < 0, abs(n), []
    while n:
        digits.append("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[n % dst]); n //= dst
    return ("-" if neg else "") + "".join(reversed(digits))

def next_permutation(xs):
    xs = list(xs)
    i = len(xs) - 2
    while i >= 0 and xs[i] >= xs[i + 1]:
        i -= 1
    if i < 0:
        return sorted(xs)
    j = len(xs) - 1
    while xs[j] <= xs[i]:
        j -= 1
    xs[i], xs[j] = xs[j], xs[i]
    xs[i + 1:] = reversed(xs[i + 1:])
    return xs

def free_slots(busy, start, end, min_len):
    iv = sorted([max(a, start), min(b, end)] for a, b in busy if a < b and b > start and a < end)
    merged = []
    for a, b in iv:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    out, cur = [], start
    for a, b in merged:
        if a - cur >= max(min_len, 1):
            out.append([cur, a])
        cur = max(cur, b)
    if end - cur >= max(min_len, 1):
        out.append([cur, end])
    return out

def minesweeper_annotate(board):
    h = len(board)
    out = []
    for r in range(h):
        row = []
        for c in range(len(board[r])):
            if board[r][c] == "*":
                row.append("*"); continue
            n = sum(1 for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                    if (dr or dc) and 0 <= r + dr < h and 0 <= c + dc < len(board[r + dr]) and board[r + dr][c + dc] == "*")
            row.append(str(n) if n else ".")
        out.append("".join(row))
    return out

def interleave_check(a, b, s):
    if len(a) + len(b) != len(s):
        return False
    ok = [[False] * (len(b) + 1) for _ in range(len(a) + 1)]
    ok[0][0] = True
    for i in range(len(a) + 1):
        for j in range(len(b) + 1):
            if i and ok[i - 1][j] and a[i - 1] == s[i + j - 1]:
                ok[i][j] = True
            if j and ok[i][j - 1] and b[j - 1] == s[i + j - 1]:
                ok[i][j] = True
    return ok[len(a)][len(b)]


# ---------- generators ----------

def _semver(r):
    v = ".".join(str(r.choice([0, 1, 2, 10])) for _ in range(3))
    if r.random() < 0.6:
        v += "-" + ".".join(r.choice(["alpha", "beta", "rc", "1", "2", "11", "x"]) for _ in range(r.randint(1, 3)))
    return v

def _semver_pair(r):
    a = _semver(r)
    if r.random() < 0.5:
        core = a.partition("-")[0]
        pre = ".".join(r.choice(["alpha", "beta", "1", "2", "11"]) for _ in range(r.randint(1, 3)))
        return (a, core + ("-" + pre if r.random() < 0.7 else ""))
    return (a, _semver(r))

def _sentence(r):
    words = ["a", "of", "the", "in", "ab", "hello", "supercalifragilistic", "to", "end", "x-ray",
             "well-known", "AND", "Python", "or", "mIxEd"]
    return (" " * r.randint(1, 3)).join(r.choice(words) for _ in range(r.randint(1, 8)))

def _duration(r):
    if r.random() < 0.2:
        return r.choice(["", "h", "1x", "5m3h", "10", "1h1h", " 1h", "1H", "1h60m", "2m75s", "75s"])
    s = ""
    for unit, hi in (("h", 30), ("m", 95), ("s", 95)):
        if r.random() < 0.55:
            s += f"{r.randint(0, hi)}{unit}"
    return s or f"{r.randint(0, 200)}s"

def _path(r):
    parts = [r.choice(["a", "b", "..", ".", "", "c.d", "..."]) for _ in range(r.randint(1, 6))]
    return ("/" if r.random() < 0.5 else "") + "/".join(parts) + ("/" if r.random() < 0.3 else "")

def _ranges(r):
    toks = []
    for _ in range(r.randint(1, 4)):
        a = r.randint(-5, 12)
        toks.append(f"{a}..{r.randint(-5, 12)}" if r.random() < 0.6 else str(a))
    return ((", " if r.random() < 0.3 else ",").join(toks),)

def _expr(r, depth=0):
    if depth > 2 or r.random() < 0.3:
        e = str(r.randint(0, 20))
    else:
        e = f"{_expr(r, depth + 1)} {r.choice('+-*/')} {_expr(r, depth + 1)}"
        if r.random() < 0.4:
            e = f"({e})"
    if r.random() < 0.15:
        e = "-" + e if e[0] == "(" else "-(" + e + ")"
    return e

def _safe_expr(r):
    for _ in range(50):
        e = _expr(r)
        try:
            eval_expr(e)
            return (e,)
        except ZeroDivisionError:
            continue
    return ("1 + 2",)

def _game(r):
    rolls = []
    for f in range(10):
        a = 10 if r.random() < 0.3 else r.randint(0, 9)
        if f < 9:
            rolls += [a] if a == 10 else [a, (10 - a) if r.random() < 0.35 else r.randint(0, 9 - a)]
        elif a == 10:
            b = 10 if r.random() < 0.4 else r.randint(0, 9)
            c = (10 if r.random() < 0.4 else r.randint(0, 9)) if b == 10 else r.randint(0, 10 - b)
            rolls += [a, b, c]
        else:
            b = (10 - a) if r.random() < 0.4 else r.randint(0, 9 - a)
            rolls += [a, b] + ([r.randint(0, 10)] if a + b == 10 else [])
    return (rolls,)

def _roman(r):
    if r.random() < 0.5:
        return (int_to_roman(r.randint(1, 3999)),)
    return ("".join(r.choice("IVXLCDM") for _ in range(r.randint(1, 6))),)

def _board(r):
    h, w = r.randint(1, 4), r.randint(1, 5)
    return (["".join("*" if r.random() < 0.25 else "." for _ in range(r.randint(max(1, w - 1), w))) for _ in range(h)],)

def _busy(r):
    busy = [sorted([r.randint(-2, 26), r.randint(-2, 26)]) for _ in range(r.randint(0, 4))]
    return (busy, r.randint(0, 6), r.randint(14, 24), r.randint(0, 3))

def _interleave(r):
    a, b = _word(r, "ab", 0, 4), _word(r, "ab", 0, 4)
    if r.random() < 0.5:
        s = list(a + b); r.shuffle(s)
        return (a, b, "".join(s))
    i = j = 0; s = []
    while i < len(a) or j < len(b):
        if j >= len(b) or (i < len(a) and r.random() < 0.5):
            s.append(a[i]); i += 1
        else:
            s.append(b[j]); j += 1
    return (a, b, "".join(s))


TEMPLATES_HARD = [
    Template("semver_compare", "hard2", "def semver_compare(a: str, b: str) -> int",
             "Compare two semantic versions MAJOR.MINOR.PATCH with an optional pre-release after '-' (dot-separated identifiers). "
             "Return -1, 0 or 1. Core fields compare numerically. A version without a pre-release is greater than the same core with one. "
             "Pre-release identifiers compare left to right: two numeric identifiers compare numerically, two alphanumeric ones compare as ASCII strings, "
             "and a numeric identifier is lower than an alphanumeric one. If all shared identifiers are equal, the longer pre-release list is greater.",
             semver_compare, _semver_pair,
             [("1.0.0", "1.0.0-alpha"), ("1.0.0-2", "1.0.0-11"), ("1.0.0-alpha", "1.0.0-alpha.1"), ("1.0.0-1", "1.0.0-alpha"), ("10.0.0", "2.0.0")]),
    Template("wrap_text", "hard2", "def wrap_text(s: str, width: int) -> List[str]",
             "Greedy word wrap. Words are separated by any whitespace. Fill each line with as many words as fit, joined by single spaces, without exceeding width. "
             "A word longer than width is split into pieces of exactly width characters (the last piece may be shorter); each full piece is its own line and the remainder "
             "starts a new line that later words may join. Return [] when there are no words. width >= 1.",
             wrap_text, lambda r: (_sentence(r), r.randint(2, 12)),
             [("", 5), ("abcdefgh ij", 3), ("a b c", 1), ("hello   world", 11)]),
    Template("parse_duration", "hard2", "def parse_duration(s: str) -> int",
             "Parse a duration such as '1h30m', '45s' or '2h5s' into total seconds. Units are lowercase h, m, s, each at most once, in that order, each preceded by "
             "one or more digits, with no spaces. Return -1 for invalid input, including the empty string. A minutes value of 60 or more is invalid when hours are present, "
             "and a seconds value of 60 or more is invalid when hours or minutes are present ('90m' and '90s' alone are valid).",
             parse_duration, lambda r: (_duration(r),),
             [("",), ("1h30m",), ("1h60m",), ("90m",), ("5m3h",), ("0s",), ("2m75s",)]),
    Template("simplify_path", "hard2", "def simplify_path(p: str) -> str",
             "Simplify a Unix-style path. Collapse repeated slashes, drop '.' segments, and let '..' remove the previous segment. For an absolute path (starting with '/') "
             "'..' at the root is dropped and the result starts with '/' with no trailing slash ('/' for the root). For a relative path, a '..' with nothing to remove is kept, "
             "and an empty result is '.'. Segments like '...' are ordinary names.",
             simplify_path, lambda r: (_path(r),),
             [("/",), ("a/../..",), ("/../a/./b//",), ("./",), ("../x/../../y",)]),
    Template("number_to_words", "hard2", "def number_to_words(n: int) -> str",
             "Spell an integer with -999999 <= n <= 999999 in lowercase English. Use 'minus' for negatives, 'zero' for 0, hyphens for compound tens "
             "('twenty-one'), no 'and', and single spaces otherwise. Examples: 105 -> 'one hundred five', 12000 -> 'twelve thousand', "
             "-7019 -> 'minus seven thousand nineteen'.",
             number_to_words, lambda r: (r.choice([r.randint(-999999, 999999), r.randint(-120, 120), r.randint(1, 20) * 1000, r.randint(100, 999)]),),
             [(0,), (1000,), (-20,), (100100,), (999999,), (40,)]),
    Template("expand_ranges", "hard2", "def expand_ranges(s: str) -> List[int]",
             "Expand a comma-separated list of integers and ranges 'a..b' (inclusive; a > b counts down; values may be negative; spaces around tokens are allowed; "
             "empty tokens are ignored). Return the values in order, keeping only the first occurrence of each.",
             expand_ranges, _ranges,
             [("",), ("3..1, 2",), ("-2..-4",), ("5,,5",)]),
    Template("collapse_ranges", "hard2", "def collapse_ranges(xs: List[int]) -> str",
             "Sort the distinct values of xs and join them with commas, writing every run of three or more consecutive integers as 'a..b'. "
             "Runs of two stay as two values. Return '' for an empty list. Example [5, 1, 2, 3, 7, 8] -> '1..3,5,7,8'.",
             collapse_ranges, lambda r: ([r.randint(-6, 12) for _ in range(r.randint(0, 9))],),
             [([],), ([-3, -2, -1, 0],), ([4, 4, 5],), ([1, 2, 3, 5, 6, 7, 9],)]),
    Template("csv_split", "hard2", "def csv_split(line: str) -> List[str]",
             "Split one CSV line into fields. Fields are separated by commas. A double quote toggles quoted mode; inside quoted mode commas are literal and "
             "two double quotes in a row produce one literal quote. Quote characters themselves are not part of the field. An empty line is one empty field.",
             csv_split, lambda r: (",".join(r.choice(['a', '', '"b,c"', '"say ""hi"""', 'x y', '""', '"q"r']) for _ in range(r.randint(1, 5))),),
             [("",), ('a,"b,c",',), ('""""',), ('"a""b",c',)]),
    Template("eval_expr", "hard2", "def eval_expr(s: str) -> int",
             "Evaluate an integer expression with non-negative integer literals, + - * /, parentheses, unary minus, and arbitrary spaces. * and / bind tighter than + and -, "
             "operators of equal precedence associate left, and / divides truncating toward zero (so -7 / 2 == -3). Do not use eval.",
             eval_expr, _safe_expr,
             [("-7 / 2",), ("2 - 3 - 4",), ("-(2 + 3) * 4",), ("8 / 3 * 3",), ("10 / -(3)",)]),
    Template("bowling_score", "hard2", "def bowling_score(rolls: List[int]) -> int",
             "Score a complete ten-pin bowling game given the pins knocked down by each roll. A strike (10 on the first roll of a frame) scores 10 plus the next two rolls, "
             "a spare scores 10 plus the next roll, otherwise the frame scores its pins. The tenth frame has one or two bonus rolls after a strike or spare, "
             "and those bonus rolls only count toward the tenth frame.",
             bowling_score, _game,
             [([10] * 12,), ([0] * 20,), ([5, 5] * 10 + [5],), ([0, 10] + [0] * 17 + [10, 10, 10],)]),
    Template("is_valid_roman", "hard2", "def is_valid_roman(s: str) -> bool",
             "Return True if s is a canonical Roman numeral for a value from 1 to 3999 using I V X L C D M (uppercase only), which means the standard minimal form "
             "with subtractive pairs IV IX XL XC CD CM only. For example 'IIII', 'VX', 'IC', 'MMMM' and '' are invalid.",
             is_valid_roman, _roman,
             [("",), ("IIII",), ("MCMXCIV",), ("IC",), ("XCIX",), ("mcm",)]),
    Template("title_case", "hard2", "def title_case(s: str) -> str",
             "Title-case a sentence. Split on whitespace and join with single spaces. Lowercase every word, then capitalize the first letter of each word, except that "
             "the small words a an the and but or of in on at to stay lowercase unless they are the first or last word. In a hyphenated word capitalize each part.",
             title_case, lambda r: (_sentence(r),),
             [("",), ("the end of the",), ("x-ray  and well-known",), ("OF",)]),
    Template("base_convert", "hard2", "def base_convert(s: str, src: int, dst: int) -> str",
             "Convert the integer written in base src (2 to 36, digits 0-9 then letters in either case, optional leading '-') to base dst (2 to 36) using digits 0-9 "
             "and uppercase A-Z. Zero is '0'; negatives keep a leading '-'; no leading zeros.",
             base_convert, lambda r: (lambda n, a, b: (("-" if n < 0 else "") + base_convert(str(abs(n)), 10, a).lower(), a, b))(r.randint(-5000, 5000), r.randint(2, 36), r.randint(2, 36)),
             [("0", 10, 2), ("-ff", 16, 10), ("zz", 36, 2), ("-0", 7, 3)]),
    Template("next_permutation", "hard2", "def next_permutation(xs: List[int]) -> List[int]",
             "Return the next lexicographically greater permutation of xs (duplicates allowed), or the smallest permutation (sorted ascending) if xs is already the "
             "largest. Do not modify the input.",
             next_permutation, lambda r: ([r.randint(0, 3) for _ in range(r.randint(0, 6))],),
             [([],), ([3, 2, 1],), ([1, 1, 5],), ([1, 3, 2],), ([2, 2, 2],)]),
    Template("free_slots", "hard2", "def free_slots(busy: List[List[int]], start: int, end: int, min_len: int) -> List[List[int]]",
             "Given busy half-open intervals [a, b) (possibly empty, possibly overlapping, unsorted, possibly extending outside the window) and a window [start, end), return the free gaps "
             "inside the window as sorted [a, b] pairs. Busy intervals that touch or overlap leave no gap. Keep only gaps whose length b - a is at least min_len, "
             "and never return an empty gap (length 0) even when min_len is 0.",
             free_slots, _busy,
             [([], 0, 10, 0), ([[2, 4], [4, 6]], 0, 10, 0), ([[-5, 3], [20, 30]], 0, 24, 2)]),
    Template("minesweeper_annotate", "hard2", "def minesweeper_annotate(board: List[str]) -> List[str]",
             "Annotate a Minesweeper board given as a list of strings of '*' (mine) and '.' (empty). Replace each empty cell with the count of mines among its up to eight "
             "neighbours, or keep '.' if the count is 0. Rows may have different lengths; a neighbour exists only if that row has that column. Mines stay '*'.",
             minesweeper_annotate, _board,
             [([],), (["*.*", "."],), ([".*.."],), (["*", "", "*"],)]),
    Template("interleave_check", "hard2", "def interleave_check(a: str, b: str, s: str) -> bool",
             "Return True if s can be formed by interleaving all characters of a and all characters of b, keeping the relative order of characters within a and within b.",
             interleave_check, _interleave,
             [("", "", ""), ("ab", "ab", "abab"), ("aab", "aab", "aaabab"), ("a", "b", "ba"), ("ab", "", "ba")]),
]
