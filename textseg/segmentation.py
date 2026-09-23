"""Grapheme-cluster, word and sentence boundary segmentation (batch).

Rule sets are modelled on UAX #29 and implemented directly; every rule is
named in comments (GB/WB/SB numbers) and exercised by tests/test_rules.py.
Documented simplifications:
  * GB9c (Indic conjunct clusters, Unicode 15.1 InCB) is not implemented.
  * SB8 is simplified to "ATerm Close* Sp* x Lower" (no multi-token scan).
  * Paragraph separators (LF/CR/NEL/U+2028/U+2029) always form their own
    segment (CR+LF is a single segment) instead of being absorbed into the
    preceding sentence per SB11.
"""

from .properties import (
    grapheme_cluster_break as _gcb, word_break as _wb, sentence_break as _sb,
    is_extended_pictographic as _is_ep,
    GCB_OTHER, GCB_CONTROL, GCB_CR, GCB_LF, GCB_EXTEND, GCB_ZWJ, GCB_RI,
    GCB_PREPEND, GCB_SPACINGMARK, GCB_L, GCB_V, GCB_T, GCB_LV, GCB_LVT,
    WB_EXTEND, WB_FORMAT, WB_ZWJ, WB_RI, WB_WSEGSPACE, WB_ALETTER, WB_HEBREW,
    WB_NUMERIC, WB_KATAKANA, WB_EXTENDNUMLET, WB_MIDLETTER, WB_MIDNUM,
    WB_MIDNUMLET, WB_SINGLE_QUOTE, WB_DOUBLE_QUOTE, WB_NEWLINE_CHARS,
    SB_STERM, SB_ATERM, SB_CLOSE, SB_SP, SB_NUMERIC, SB_UPPER, SB_LOWER,
    SB_SCONTINUE, SB_EXTEND, SB_FORMAT, SB_NEWLINE_CHARS,
)

_AH = (WB_ALETTER, WB_HEBREW)
_MID_LETTER_Q = (WB_MIDLETTER, WB_MIDNUMLET, WB_SINGLE_QUOTE)
_MID_NUM_Q = (WB_MIDNUM, WB_MIDNUMLET, WB_SINGLE_QUOTE)


# ---------------------------------------------------------------------------
# Grapheme clusters
# ---------------------------------------------------------------------------
def grapheme_boundaries(text):
    """Return the list of grapheme-cluster boundary offsets (incl. 0 and len)."""
    n = len(text)
    bounds = [0]
    if n == 0:
        return bounds
    props = [_gcb(ord(c)) for c in text]
    ri_run = 1 if props[0] == GCB_RI else 0  # RIs immediately before i
    cluster_start = 0
    for i in range(1, n):
        prev, cur = props[i - 1], props[i]
        brk = True
        if prev == GCB_CR and cur == GCB_LF:
            brk = False                                     # GB3
        elif prev in (GCB_CONTROL, GCB_CR, GCB_LF) \
                or cur in (GCB_CONTROL, GCB_CR, GCB_LF):
            brk = True                                      # GB4 / GB5
        elif prev == GCB_L and cur in (GCB_L, GCB_V, GCB_LV, GCB_LVT):
            brk = False                                     # GB6
        elif prev in (GCB_LV, GCB_V) and cur in (GCB_V, GCB_T):
            brk = False                                     # GB7
        elif prev in (GCB_LVT, GCB_T) and cur == GCB_T:
            brk = False                                     # GB8
        elif cur in (GCB_EXTEND, GCB_ZWJ):
            brk = False                                     # GB9
        elif cur == GCB_SPACINGMARK:
            brk = False                                     # GB9a
        elif prev == GCB_PREPEND:
            brk = False                                     # GB9b
        elif prev == GCB_ZWJ and _is_ep(ord(text[i])):
            # GB11: ExtPict Extend* ZWJ x ExtPict
            j = i - 2
            while j >= cluster_start and props[j] == GCB_EXTEND:
                j -= 1
            brk = not (j >= cluster_start and _is_ep(ord(text[j])))
        elif prev == GCB_RI and cur == GCB_RI and ri_run % 2 == 1:
            brk = False                                     # GB12 / GB13
        # GB999: break otherwise
        if brk:
            bounds.append(i)
            cluster_start = i
        ri_run = ri_run + 1 if cur == GCB_RI else 0
    bounds.append(n)
    return bounds


def graphemes(text):
    b = grapheme_boundaries(text)
    return [text[a:c] for a, c in zip(b, b[1:])]


# ---------------------------------------------------------------------------
# Shared newline pre-splitting
# ---------------------------------------------------------------------------
def _newline_atoms(text, newline_chars):
    """Split into (start, end, is_newline) atoms; CR+LF is one atom."""
    atoms = []
    i, n = 0, len(text)
    while i < n:
        cp = ord(text[i])
        if cp in newline_chars:
            if cp == 0x0D and i + 1 < n and text[i + 1] == '\n':
                atoms.append((i, i + 2, True))
                i += 2
            else:
                atoms.append((i, i + 1, True))
                i += 1
        else:
            j = i
            while j < n and ord(text[j]) not in newline_chars:
                j += 1
            atoms.append((i, j, False))
            i = j
    return atoms


# ---------------------------------------------------------------------------
# Words
# ---------------------------------------------------------------------------
def _word_break_between(text, sig, props, t, ri_run):
    """Decide whether there is a word boundary before sig[t]."""
    prev = props[t - 1]
    cur = props[t]
    prev2 = props[t - 2] if t >= 2 else None
    nxt = props[t + 1] if t + 1 < len(props) else None

    # WB3c: ZWJ x ExtPict (ZWJ itself is transparent per WB4)
    if _is_ep(ord(text[sig[t]])):
        j = sig[t] - 1
        while j > sig[t - 1] and _wb(ord(text[j])) in (WB_EXTEND, WB_FORMAT):
            j -= 1
        if j >= 0 and text[j] == '\u200d':
            return False
    if prev == WB_WSEGSPACE and cur == WB_WSEGSPACE:
        return False                                        # WB3d
    if prev in _AH and cur in _AH:
        return False                                        # WB5
    if prev in _AH and cur in _MID_LETTER_Q and nxt in _AH:
        return False                                        # WB6
    if prev in _MID_LETTER_Q and cur in _AH and prev2 in _AH:
        return False                                        # WB7
    if prev == WB_HEBREW and cur == WB_SINGLE_QUOTE:
        return False                                        # WB7a
    if prev == WB_HEBREW and cur == WB_DOUBLE_QUOTE and nxt == WB_HEBREW:
        return False                                        # WB7b
    if prev == WB_DOUBLE_QUOTE and cur == WB_HEBREW and prev2 == WB_HEBREW:
        return False                                        # WB7c
    if prev == WB_NUMERIC and cur == WB_NUMERIC:
        return False                                        # WB8
    if prev in _AH and cur == WB_NUMERIC:
        return False                                        # WB9
    if prev == WB_NUMERIC and cur in _AH:
        return False                                        # WB10
    if prev in _MID_NUM_Q and cur == WB_NUMERIC and prev2 == WB_NUMERIC:
        return False                                        # WB11
    if prev == WB_NUMERIC and cur in _MID_NUM_Q and nxt == WB_NUMERIC:
        return False                                        # WB12
    if prev == WB_KATAKANA and cur == WB_KATAKANA:
        return False                                        # WB13
    if prev in _AH + (WB_NUMERIC, WB_KATAKANA, WB_EXTENDNUMLET) \
            and cur == WB_EXTENDNUMLET:
        return False                                        # WB13a
    if prev == WB_EXTENDNUMLET \
            and cur in _AH + (WB_NUMERIC, WB_KATAKANA):
        return False                                        # WB13b
    if prev == WB_RI and cur == WB_RI and ri_run % 2 == 1:
        return False                                        # WB15 / WB16
    return True                                             # WB999


def _word_stretch_spans(text, start, end):
    sig = [i for i in range(start, end)
           if _wb(ord(text[i])) not in (WB_EXTEND, WB_FORMAT, WB_ZWJ)]
    if not sig:
        return [(start, end)] if end > start else []
    props = [_wb(ord(text[i])) for i in sig]
    n = len(sig)
    bounds = [0]
    ri_run = 1 if props[0] == WB_RI else 0
    for t in range(1, n):
        if _word_break_between(text, sig, props, t, ri_run):
            bounds.append(t)
        ri_run = ri_run + 1 if props[t] == WB_RI else 0
    bounds.append(n)
    spans = []
    for k in range(len(bounds) - 1):
        a, b = bounds[k], bounds[k + 1]
        raw_start = start if k == 0 else sig[a]
        raw_end = end if b == n else sig[b]
        spans.append((raw_start, raw_end))
    return spans


def word_spans(text):
    """Return (start, end) spans of word-boundary tokens."""
    spans = []
    for s, e, is_nl in _newline_atoms(text, WB_NEWLINE_CHARS):
        if is_nl:
            spans.append((s, e))
        else:
            spans.extend(_word_stretch_spans(text, s, e))
    return spans


def words(text):
    return [text[s:e] for s, e in word_spans(text)]


# ---------------------------------------------------------------------------
# Sentences
# ---------------------------------------------------------------------------
def _sentence_stretch_spans(text, start, end):
    sig = [i for i in range(start, end)
           if _sb(ord(text[i])) not in (SB_EXTEND, SB_FORMAT)]
    if not sig:
        return [(start, end)] if end > start else []
    props = [_sb(ord(text[i])) for i in sig]
    n = len(sig)
    bounds = []
    i = 0
    while i < n:
        if props[i] in (SB_STERM, SB_ATERM):
            has_sterm = props[i] == SB_STERM
            j = i
            while j < n and props[j] in (SB_STERM, SB_ATERM):
                if props[j] == SB_STERM:
                    has_sterm = True
                j += 1
            while j < n and props[j] == SB_CLOSE:
                j += 1                                       # SB9 (Close)
            while j < n and props[j] == SB_SP:
                j += 1                                       # SB9/SB10 (Sp)
            if j < n:
                nxt = props[j]
                nobreak = False
                if nxt in (SB_SCONTINUE, SB_STERM, SB_ATERM):
                    nobreak = True                           # SB8a
                elif not has_sterm and nxt == SB_NUMERIC:
                    nobreak = True                           # SB6
                elif not has_sterm and nxt == SB_LOWER:
                    nobreak = True                           # SB8 (simplified)
                elif not has_sterm and nxt == SB_UPPER and i > 0 \
                        and props[i - 1] == SB_UPPER:
                    nobreak = True                           # SB7
                if not nobreak:
                    bounds.append(j)                         # SB11
            i = j
        else:
            i += 1
    spans = []
    prev_raw = start
    for t in bounds:
        spans.append((prev_raw, sig[t]))
        prev_raw = sig[t]
    spans.append((prev_raw, end))
    return spans


def sentence_spans(text):
    spans = []
    for s, e, is_nl in _newline_atoms(text, SB_NEWLINE_CHARS):
        if is_nl:
            spans.append((s, e))
        else:
            spans.extend(_sentence_stretch_spans(text, s, e))
    return spans


def sentences(text):
    return [text[s:e] for s, e in sentence_spans(text)]
