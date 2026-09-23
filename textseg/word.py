"""Word boundary segmentation (UAX #29, Unicode 16.0.0).

Two-phase model per UAX #29 Section 6.2 ("Replacing Ignore Rules"):
  phase 1 (original adjacency): WB3, WB3a/WB3b, WB3c, WB3d, WB4
  phase 2 (Extend/Format/ZWJ removed, except after sot/CR/LF/Newline):
    WB5-WB13b, WB15/WB16, WB999
"""
from ._classify import wb, is_extended_pictographic

_IGNORABLE = frozenset(("Extend", "Format", "ZWJ"))
_NEWLINE = frozenset(("CR", "LF", "Newline"))
_AH = frozenset(("ALetter", "Hebrew_Letter"))
_MID_LETTER_Q = frozenset(("MidLetter", "MidNumLet", "Single_Quote"))
_MID_NUM_Q = frozenset(("MidNum", "MidNumLet", "Single_Quote"))
_AH_NK = frozenset(("ALetter", "Hebrew_Letter", "Numeric", "Katakana"))
_AH_NK_E = _AH_NK | frozenset(("ExtendNumLet",))
_WORD_CHARS = _AH_NK  # classes that make a segment count as a "word"


def _reduce(text, cls):
    """Mark WB4-ignored chars; return (sig, ignored) with sig a list of
    (offset, class) for the remaining tokens."""
    sig = []
    ignored = set()
    prev_breaking = True  # start of text behaves like after a newline (WB4)
    for i, c in enumerate(cls):
        if c in _IGNORABLE and not prev_breaking:
            ignored.add(i)
        else:
            sig.append((i, c))
            prev_breaking = c in _NEWLINE
    return sig, ignored


def word_break_positions(text):
    """Return sorted boundary offsets (always includes 0 and len(text))."""
    n = len(text)
    if n == 0:
        return [0]
    cls = [wb(ord(ch)) for ch in text]
    sig, _ = _reduce(text, cls)
    m = len(sig)
    # phase 2 verdicts, keyed by char offset of the boundary
    phase2 = {}
    ri_run = 1 if m > 0 and sig[0][1] == "Regional_Indicator" else 0
    for k in range(1, m):
        i_cur, b = sig[k]
        a = sig[k - 1][1]
        nxt = sig[k + 1][1] if k + 1 < m else None
        prv2 = sig[k - 2][1] if k >= 2 else None
        nb = False
        if a in _AH and b in _AH:
            nb = True  # WB5
        elif a in _AH and b in _MID_LETTER_Q and nxt in _AH:
            nb = True  # WB6
        elif prv2 in _AH and a in _MID_LETTER_Q and b in _AH:
            nb = True  # WB7
        elif a == "Hebrew_Letter" and b == "Single_Quote":
            nb = True  # WB7a
        elif a == "Hebrew_Letter" and b == "Double_Quote" and nxt == "Hebrew_Letter":
            nb = True  # WB7b
        elif prv2 == "Hebrew_Letter" and a == "Double_Quote" and b == "Hebrew_Letter":
            nb = True  # WB7c
        elif a == "Numeric" and b == "Numeric":
            nb = True  # WB8
        elif a in _AH and b == "Numeric":
            nb = True  # WB9
        elif a == "Numeric" and b in _AH:
            nb = True  # WB10
        elif prv2 == "Numeric" and a in _MID_NUM_Q and b == "Numeric":
            nb = True  # WB11
        elif a == "Numeric" and b in _MID_NUM_Q and nxt == "Numeric":
            nb = True  # WB12
        elif a == "Katakana" and b == "Katakana":
            nb = True  # WB13
        elif a in _AH_NK_E and b == "ExtendNumLet":
            nb = True  # WB13a
        elif a == "ExtendNumLet" and b in _AH_NK:
            nb = True  # WB13b
        elif a == "Regional_Indicator" and b == "Regional_Indicator" and ri_run % 2 == 1:
            nb = True  # WB15 / WB16
        phase2[i_cur] = not nb
        ri_run = ri_run + 1 if b == "Regional_Indicator" else 0
    breaks = [0]
    for i in range(1, n):
        a, b = cls[i - 1], cls[i]
        if a == "CR" and b == "LF":
            brk = False  # WB3
        elif a in _NEWLINE:
            brk = True  # WB3a
        elif b in _NEWLINE:
            brk = True  # WB3b
        elif a == "ZWJ" and is_extended_pictographic(ord(text[i])):
            brk = False  # WB3c
        elif a == "WSegSpace" and b == "WSegSpace":
            brk = False  # WB3d
        elif b in _IGNORABLE:
            brk = False  # WB4
        else:
            brk = phase2.get(i, True)  # WB5+ / WB999
        if brk:
            breaks.append(i)
    breaks.append(n)
    return breaks


def iter_word_spans(text):
    """Yield (start, end) offset pairs of word segments (incl. spaces/punct)."""
    bounds = word_break_positions(text)
    for a, b in zip(bounds, bounds[1:]):
        yield (a, b)


def iter_word_segments(text):
    """Yield every segment between word boundaries (spaces, punctuation too)."""
    for a, b in iter_word_spans(text):
        yield text[a:b]


def is_word_segment(segment):
    """True if the segment contains letters/numbers (UAX #29 'word')."""
    return any(wb(ord(ch)) in _WORD_CHARS for ch in segment)


def iter_words(text):
    """Yield only word-like segments (those containing letters or digits)."""
    for seg in iter_word_segments(text):
        if is_word_segment(seg):
            yield seg


def words(text):
    return list(iter_words(text))


def word_count(text):
    return sum(1 for _ in iter_words(text))
