"""Sentence boundary segmentation (UAX #29, Unicode 16.0.0).

Two-phase model per UAX #29 Section 6.2 ("Replacing Ignore Rules"):
  phase 1 (original adjacency): SB3, SB4, SB5
  phase 2 (Extend/Format removed, except after sot/Sep/CR/LF):
    SB6-SB11, SB998

The left-context patterns of SB8/SB8a/SB9/SB10/SB11 are tracked with an
O(1) state machine over the reduced token stream:

  TERM  : ... SATerm                  (anchor = last terminator class)
  CLOSE : ... SATerm Close*
  SP    : ... SATerm Close* Sp*
  NONE  : no such suffix

SB8's right context (non-excluded chars)* Lower is precomputed in one
backward pass (lower_ahead).
"""
from ._classify import sb

_IGNORABLE = frozenset(("Extend", "Format"))
_PARASEP = frozenset(("Sep", "CR", "LF"))
_CLOSE_SP_SEP = frozenset(("Close", "Sp", "Sep", "CR", "LF"))
_SP_SEP = frozenset(("Sp", "Sep", "CR", "LF"))
_SATERM_CONTINUE = frozenset(("SContinue", "STerm", "ATerm"))
# SB8 right context: chars allowed between the boundary and the Lower
_SKIP_RHS = frozenset(("Close", "Sp", "SContinue", "Numeric", "Other", "Extend", "Format"))

_NONE, _TERM, _CLOSE, _SP = range(4)


def _reduce(text, cls):
    sig = []
    prev_breaking = True  # start of text behaves like after a separator (SB5)
    for i, c in enumerate(cls):
        if c in _IGNORABLE and not prev_breaking:
            continue
        sig.append((i, c))
        prev_breaking = c in _PARASEP
    return sig


def _advance(state, anchor_aterm, c):
    if c == "ATerm":
        return _TERM, True
    if c == "STerm":
        return _TERM, False
    if c == "Close":
        return (_CLOSE, anchor_aterm) if state in (_TERM, _CLOSE) else (_NONE, False)
    if c == "Sp":
        return (_SP, anchor_aterm) if state in (_TERM, _CLOSE, _SP) else (_NONE, False)
    return _NONE, False


def sentence_break_positions(text):
    """Return sorted boundary offsets (always includes 0 and len(text))."""
    n = len(text)
    if n == 0:
        return [0]
    cls = [sb(ord(ch)) for ch in text]
    sig = _reduce(text, cls)
    m = len(sig)
    # lower_ahead[k]: scanning right from sig[k], a Lower occurs before any
    # char outside SB8's allowed right-context set.
    lower_ahead = [False] * (m + 1)
    for k in range(m - 1, -1, -1):
        c = sig[k][1]
        lower_ahead[k] = c == "Lower" or (c in _SKIP_RHS and lower_ahead[k + 1])
    # phase 2 verdicts, keyed by char offset of the boundary
    phase2 = {}
    state, anchor_aterm = _NONE, False
    for k in range(m):
        i_cur, b = sig[k]
        if k > 0:
            a = sig[k - 1][1]
            prv2 = sig[k - 2][1] if k >= 2 else None
            ctx8 = state in (_TERM, _CLOSE, _SP) and anchor_aterm
            ctx8a = state in (_TERM, _CLOSE, _SP)
            ctx9 = state in (_TERM, _CLOSE)
            ctx10 = state in (_TERM, _CLOSE, _SP)
            brk = False
            if a == "ATerm" and b == "Numeric":
                brk = False  # SB6
            elif prv2 in ("Upper", "Lower") and a == "ATerm" and b == "Upper":
                brk = False  # SB7
            elif ctx8 and lower_ahead[k]:
                brk = False  # SB8
            elif ctx8a and b in _SATERM_CONTINUE:
                brk = False  # SB8a
            elif ctx9 and b in _CLOSE_SP_SEP:
                brk = False  # SB9
            elif ctx10 and b in _SP_SEP:
                brk = False  # SB10
            elif state in (_TERM, _CLOSE, _SP):
                brk = True  # SB11
            # otherwise SB998: no break
            phase2[i_cur] = brk
        state, anchor_aterm = _advance(state, anchor_aterm, b)
    breaks = [0]
    for i in range(1, n):
        a, b = cls[i - 1], cls[i]
        if a == "CR" and b == "LF":
            brk = False  # SB3
        elif a in _PARASEP:
            brk = True  # SB4
        elif b in _IGNORABLE:
            brk = False  # SB5
        else:
            brk = phase2.get(i, False)  # SB6+ / SB998
        if brk:
            breaks.append(i)
    breaks.append(n)
    return breaks


def iter_sentence_spans(text):
    """Yield (start, end) offset pairs of sentences."""
    bounds = sentence_break_positions(text)
    for a, b in zip(bounds, bounds[1:]):
        yield (a, b)


def iter_sentences(text):
    for a, b in iter_sentence_spans(text):
        yield text[a:b]


def split_sentences(text, strip=False):
    """Split text into sentences; optionally strip surrounding whitespace."""
    if strip:
        return [s.strip() for s in iter_sentences(text) if s.strip()]
    return list(iter_sentences(text))
