"""Unicode character properties used by the segmentation engine.

All properties are derived from the stdlib `unicodedata` *character database*
(general category, combining class) plus explicit range tables modelled on
UAX #29.  No runtime segmentation / tokenization facilities are used.
"""

import unicodedata
from bisect import bisect_right
from functools import lru_cache


def _flatten(ranges):
    flat = []
    for lo, hi in ranges:
        flat.append(lo)
        flat.append(hi)
    return tuple(flat)


def _make_lookup(ranges):
    flat = _flatten(ranges)

    def lookup(cp):
        i = bisect_right(flat, cp)
        return i % 2 == 1

    return lookup


# ---------------------------------------------------------------------------
# Extended_Pictographic (approximation of emoji-data.txt, used by GB11/WB3c)
# ---------------------------------------------------------------------------
_EXT_PICT_RANGES = [
    (0x00A9, 0x00A9), (0x00AE, 0x00AE), (0x203C, 0x203C), (0x2049, 0x2049),
    (0x2122, 0x2122), (0x2139, 0x2139), (0x2194, 0x2199), (0x21A9, 0x21AA),
    (0x231A, 0x231B), (0x2328, 0x2328), (0x23CF, 0x23CF), (0x23E9, 0x23F3),
    (0x23F8, 0x23FA), (0x24C2, 0x24C2), (0x25AA, 0x25AB), (0x25B6, 0x25B6),
    (0x25C0, 0x25C0), (0x25FB, 0x25FE), (0x2600, 0x27BF), (0x2934, 0x2935),
    (0x2B05, 0x2B07), (0x2B1B, 0x2B1C), (0x2B50, 0x2B50), (0x2B55, 0x2B55),
    (0x3030, 0x3030), (0x303D, 0x303D), (0x3297, 0x3297), (0x3299, 0x3299),
    (0x1F000, 0x1F0FF), (0x1F10D, 0x1F1E5),  # excludes Regional Indicators
    (0x1F200, 0x1F64F), (0x1F680, 0x1F6FF), (0x1F700, 0x1F7FF),
    (0x1F900, 0x1F9FF), (0x1FA00, 0x1FAFF),
]
is_extended_pictographic = _make_lookup(_EXT_PICT_RANGES)

# ---------------------------------------------------------------------------
# Grapheme_Cluster_Break
# ---------------------------------------------------------------------------
(GCB_OTHER, GCB_CONTROL, GCB_CR, GCB_LF, GCB_EXTEND, GCB_ZWJ, GCB_RI,
 GCB_PREPEND, GCB_SPACINGMARK, GCB_L, GCB_V, GCB_T, GCB_LV,
 GCB_LVT) = range(14)

_PREPEND_RANGES = [
    (0x0600, 0x0605), (0x06DD, 0x06DD), (0x070F, 0x070F), (0x0890, 0x0891),
    (0x08E2, 0x08E2), (0x0D4E, 0x0D4E), (0x110BD, 0x110BD), (0x110CD, 0x110CD),
    (0x111C2, 0x111C3), (0x1193D, 0x1193E), (0x11A3A, 0x11A3A),
    (0x11A84, 0x11A89), (0x11D46, 0x11D46), (0x11F02, 0x11F02),
]
_is_prepend = _make_lookup(_PREPEND_RANGES)

_HANGUL_L = _make_lookup([(0x1100, 0x115F), (0xA960, 0xA97C)])
_HANGUL_V = _make_lookup([(0x1160, 0x11A7), (0xD7B0, 0xD7C6)])
_HANGUL_T = _make_lookup([(0x11A8, 0x11FF), (0xD7CB, 0xD7FB)])


@lru_cache(maxsize=4096)
def grapheme_cluster_break(cp):
    if cp == 0x0D:
        return GCB_CR
    if cp == 0x0A:
        return GCB_LF
    if cp == 0x200D:
        return GCB_ZWJ
    if 0x1F1E6 <= cp <= 0x1F1FF:
        return GCB_RI
    if _HANGUL_L(cp):
        return GCB_L
    if _HANGUL_V(cp):
        return GCB_V
    if _HANGUL_T(cp):
        return GCB_T
    if 0xAC00 <= cp <= 0xD7A3:
        return GCB_LV if (cp - 0xAC00) % 28 == 0 else GCB_LVT
    if _is_prepend(cp):
        return GCB_PREPEND
    cat = unicodedata.category(chr(cp))
    if cat in ('Mn', 'Me'):
        return GCB_EXTEND
    # Tag characters & ZWNJ behave as Extend; emoji modifiers too.
    if 0xE0020 <= cp <= 0xE007F or cp == 0x200C or 0x1F3FB <= cp <= 0x1F3FF:
        return GCB_EXTEND
    if cat == 'Mc':
        return GCB_SPACINGMARK
    if cat in ('Cc', 'Cf', 'Zl', 'Zp', 'Cs'):
        return GCB_CONTROL
    return GCB_OTHER


# ---------------------------------------------------------------------------
# Word_Break
# ---------------------------------------------------------------------------
(WB_OTHER, WB_CR, WB_LF, WB_NEWLINE, WB_EXTEND, WB_FORMAT, WB_ZWJ, WB_RI,
 WB_WSEGSPACE, WB_ALETTER, WB_HEBREW, WB_NUMERIC, WB_KATAKANA,
 WB_EXTENDNUMLET, WB_MIDLETTER, WB_MIDNUM, WB_MIDNUMLET,
 WB_SINGLE_QUOTE, WB_DOUBLE_QUOTE) = range(19)

WB_NEWLINE_CHARS = frozenset((0x0A, 0x0B, 0x0C, 0x0D, 0x85, 0x2028, 0x2029))

_KATAKANA_RANGES = [
    (0x30A0, 0x30FA), (0x30FC, 0x30FF), (0x31F0, 0x31FF), (0xFF66, 0xFF9D),
]
_is_katakana = _make_lookup(_KATAKANA_RANGES)

_HEBREW_RANGES = [(0x05D0, 0x05EA), (0x05EF, 0x05F2), (0xFB1D, 0xFB4F)]
_is_hebrew = _make_lookup(_HEBREW_RANGES)

# Han ideographs and hiragana form their own per-character words (as in the
# UAX #29 default rules, which leave CJK to dictionary-based tailoring).
_IDEOGRAPH_RANGES = [
    (0x3040, 0x3096), (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF),
    (0x20000, 0x2A6DF), (0x2A700, 0x2EBEF), (0x3005, 0x3005),
]
is_ideograph = _make_lookup(_IDEOGRAPH_RANGES)

_MIDLETTER = frozenset((0x3A, 0xB7, 0x387, 0x5F3, 0x2027, 0xFE13, 0xFE55, 0xFF1A))
_MIDNUM = frozenset((0x2C, 0x3B, 0x66B, 0x66C, 0xFE10, 0xFE14, 0xFE50, 0xFE54, 0xFF0C, 0xFF1B))
_MIDNUMLET = frozenset((0x2E, 0x2018, 0x2019, 0x2024, 0xFE52, 0xFF07, 0xFF0E))


@lru_cache(maxsize=4096)
def word_break(cp):
    if cp == 0x0D:
        return WB_CR
    if cp == 0x0A:
        return WB_LF
    if cp in WB_NEWLINE_CHARS:
        return WB_NEWLINE
    if cp == 0x200D:
        return WB_ZWJ
    cat = unicodedata.category(chr(cp))
    if cat in ('Mn', 'Me') or cp == 0x200C or 0x1F3FB <= cp <= 0x1F3FF \
            or 0xE0020 <= cp <= 0xE007F:
        return WB_EXTEND
    if cat == 'Cf':
        return WB_FORMAT
    if 0x1F1E6 <= cp <= 0x1F1FF:
        return WB_RI
    if cat == 'Zs':
        return WB_WSEGSPACE
    if cat == 'Nd':
        return WB_NUMERIC
    if _is_katakana(cp):
        return WB_KATAKANA
    if _is_hebrew(cp):
        return WB_HEBREW
    if cp == 0x27:
        return WB_SINGLE_QUOTE
    if cp == 0x22:
        return WB_DOUBLE_QUOTE
    if cp in _MIDLETTER:
        return WB_MIDLETTER
    if cp in _MIDNUM:
        return WB_MIDNUM
    if cp in _MIDNUMLET:
        return WB_MIDNUMLET
    if cat == 'Pc':
        return WB_EXTENDNUMLET
    if cat in ('Lu', 'Ll', 'Lt', 'Lm', 'Lo') and not is_ideograph(cp):
        return WB_ALETTER
    return WB_OTHER


# ---------------------------------------------------------------------------
# Sentence_Break
# ---------------------------------------------------------------------------
(SB_OTHER, SB_STERM, SB_ATERM, SB_CLOSE, SB_SP, SB_NUMERIC, SB_UPPER,
 SB_LOWER, SB_OLETTER, SB_SCONTINUE, SB_EXTEND, SB_FORMAT) = range(12)

SB_NEWLINE_CHARS = frozenset((0x0A, 0x0D, 0x2028, 0x2029))

_STERM = frozenset((
    0x21, 0x3F, 0x589, 0x61F, 0x6D4, 0x700, 0x701, 0x702, 0x7F9,
    0x964, 0x965, 0x104A, 0x104B, 0x1362, 0x1367, 0x1368, 0x166E,
    0x1735, 0x1736, 0x1803, 0x1809, 0x1944, 0x1945,
    0x1AA8, 0x1AA9, 0x1AAA, 0x1AAB, 0x1B5A, 0x1B5B, 0x1B5E, 0x1B5F,
    0x1C3B, 0x1C3C, 0x1C7E, 0x1C7F, 0x203C, 0x203D, 0x2047, 0x2048,
    0x2049, 0x2E2E, 0x3002, 0xA4FF, 0xA60E, 0xA60F, 0xA6F3, 0xA6F7,
    0xFE56, 0xFE57, 0xFF01, 0xFF1F, 0xFF61, 0x10A56, 0x10A57,
    0x111C5, 0x111C6, 0x111CD, 0x111DE, 0x111DF, 0x11238, 0x11239,
    0x1123B, 0x1123C, 0x112A9, 0x1144B, 0x1144C,
))
_ATERM = frozenset((0x2E, 0x2024, 0xFE52, 0xFF0E))
_SCONTINUE = frozenset((0x2C, 0x3A, 0x3B))
_CLOSE_QUOTES = frozenset((0x22, 0x27, 0x2018, 0x2019, 0x201C, 0x201D, 0xBB))


@lru_cache(maxsize=4096)
def sentence_break(cp):
    if cp in _STERM:
        return SB_STERM
    if cp in _ATERM:
        return SB_ATERM
    cat = unicodedata.category(chr(cp))
    if cat in ('Mn', 'Me') or cp in (0x200C, 0x200D) \
            or 0x1F3FB <= cp <= 0x1F3FF or 0xE0020 <= cp <= 0xE007F:
        return SB_EXTEND
    if cat == 'Cf':
        return SB_FORMAT
    if cat == 'Zs':
        return SB_SP
    if cat in ('Pe', 'Pf') or cp in _CLOSE_QUOTES:
        return SB_CLOSE
    if cat == 'Nd':
        return SB_NUMERIC
    if cat in ('Lu', 'Lt'):
        return SB_UPPER
    if cat == 'Ll':
        return SB_LOWER
    if cat in ('Lm', 'Lo'):
        return SB_OLETTER
    if cp in _SCONTINUE:
        return SB_SCONTINUE
    return SB_OTHER
