"""Extended grapheme cluster segmentation (UAX #29, Unicode 16.0.0).

Implemented rules: GB1-GB9b, GB9c (Indic conjuncts), GB11 (emoji ZWJ),
GB12/GB13 (regional indicator pairs), GB999.
"""
from ._classify import gcb, incb, is_extended_pictographic

_CONTROL = frozenset(("Control", "CR", "LF"))
_LIKE_L = frozenset(("L", "V", "LV", "LVT"))


def grapheme_break_positions(text):
    """Return sorted boundary offsets (always includes 0 and len(text))."""
    n = len(text)
    if n == 0:
        return [0]
    cls = [gcb(ord(ch)) for ch in text]
    breaks = [0]
    ri_run = 1 if cls[0] == "Regional_Indicator" else 0
    for i in range(1, n):
        prev = cls[i - 1]
        cur = cls[i]
        brk = True
        if prev == "CR" and cur == "LF":
            brk = False  # GB3
        elif prev in _CONTROL:
            brk = True  # GB4
        elif cur in _CONTROL:
            brk = True  # GB5
        elif prev == "L" and cur in _LIKE_L:
            brk = False  # GB6
        elif prev in ("LV", "V") and cur in ("V", "T"):
            brk = False  # GB7
        elif prev in ("LVT", "T") and cur == "T":
            brk = False  # GB8
        elif cur == "Extend" or cur == "ZWJ":
            brk = False  # GB9
        elif cur == "SpacingMark":
            brk = False  # GB9a
        elif prev == "Prepend":
            brk = False  # GB9b
        elif incb(ord(text[i])) == "Consonant" and _has_linker_before(text, i):
            brk = False  # GB9c
        elif (
            is_extended_pictographic(ord(text[i]))
            and prev == "ZWJ"
            and _has_ext_pict_before_zwj(text, cls, i)
        ):
            brk = False  # GB11
        elif cur == "Regional_Indicator" and prev == "Regional_Indicator" and ri_run % 2 == 1:
            brk = False  # GB12 / GB13
        if brk:
            breaks.append(i)
        ri_run = ri_run + 1 if cur == "Regional_Indicator" else 0
    breaks.append(n)
    return breaks


def _has_linker_before(text, i):
    """GB9c: Consonant [Linker Extend]* Linker [Linker Extend]* x <here>."""
    j = i - 1
    seen_linker = False
    while j >= 0:
        c = incb(ord(text[j]))
        if c == "Linker":
            seen_linker = True
        elif c != "Extend":
            break
        j -= 1
    return seen_linker and j >= 0 and incb(ord(text[j])) == "Consonant"


def _has_ext_pict_before_zwj(text, cls, i):
    """GB11: Extended_Pictographic Extend* ZWJ x <here> (text[i-1] is ZWJ)."""
    j = i - 2
    while j >= 0 and cls[j] == "Extend":
        j -= 1
    return j >= 0 and is_extended_pictographic(ord(text[j]))


def iter_grapheme_spans(text):
    """Yield (start, end) offset pairs of extended grapheme clusters."""
    bounds = grapheme_break_positions(text)
    for a, b in zip(bounds, bounds[1:]):
        yield (a, b)


def iter_graphemes(text):
    """Yield the grapheme cluster substrings of text."""
    for a, b in iter_grapheme_spans(text):
        yield text[a:b]


def graphemes(text):
    return list(iter_graphemes(text))
