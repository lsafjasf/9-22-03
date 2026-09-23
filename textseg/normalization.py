"""Canonical / compatibility normalization (NFC, NFD, NFKC, NFKD).

Implemented from scratch on top of the stdlib `unicodedata` *character
database* (decomposition mappings and canonical combining classes).  The
runtime's own `unicodedata.normalize` is NOT used here; the test-suite uses
it only as an independent reference oracle.

Algorithm summary (per Unicode Standard, UAX #15):
  * NFD  = recursive canonical decomposition + canonical reordering.
  * NFKD = recursive compatibility decomposition + canonical reordering.
  * NFC  = NFD followed by canonical composition (Hangul is algorithmic).
  * NFKC = NFKD followed by canonical composition.
"""

import unicodedata

S_BASE = 0xAC00
L_BASE = 0x1100
V_BASE = 0x1161
T_BASE = 0x11A7
L_COUNT = 19
V_COUNT = 21
T_COUNT = 28
N_COUNT = V_COUNT * T_COUNT
S_COUNT = L_COUNT * N_COUNT

# Full composition exclusions with multi-char canonical decompositions
# (CompositionExclusions.txt; singletons and non-starter decompositions are
# excluded by rule, not listed here).
_EXCLUSION_RANGES = (
    (0x0958, 0x095F), (0x09DC, 0x09DC), (0x09DD, 0x09DD), (0x09DF, 0x09DF),
    (0x0A33, 0x0A33), (0x0A36, 0x0A36), (0x0A59, 0x0A5B), (0x0A5E, 0x0A5E),
    (0x0B5C, 0x0B5D), (0x0F43, 0x0F43), (0x0F4D, 0x0F4D), (0x0F52, 0x0F52),
    (0x0F57, 0x0F57), (0x0F5C, 0x0F5C), (0x0F69, 0x0F69), (0x0F76, 0x0F76),
    (0x0F78, 0x0F78), (0x0F93, 0x0F93), (0x0F9D, 0x0F9D), (0x0FA2, 0x0FA2),
    (0x0FA7, 0x0FA7), (0x0FAC, 0x0FAC), (0x0FB9, 0x0FB9), (0xFB1D, 0xFB1D),
    (0xFB1F, 0xFB1F), (0xFB2A, 0xFB36), (0xFB38, 0xFB3C), (0xFB3E, 0xFB3E),
    (0xFB40, 0xFB41), (0xFB43, 0xFB44), (0xFB46, 0xFB4F),
    (0x1D15E, 0x1D164), (0x1D1BB, 0x1D1C0), (0x2ADC, 0x2ADC),
    (0x2F800, 0x2FA1D),
)


def _is_excluded(cp):
    for lo, hi in _EXCLUSION_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def _decomposition(cp, compat):
    raw = unicodedata.decomposition(chr(cp))
    if not raw:
        return None
    parts = raw.split()
    if parts[0].startswith('<'):
        if not compat:
            return None
        parts = parts[1:]
    return [int(p, 16) for p in parts]


def _decompose_char(cp, compat, out):
    """Append the full (canonical|compat) decomposition of cp to out."""
    stack = [cp]
    while stack:
        c = stack.pop()
        if S_BASE <= c < S_BASE + S_COUNT:
            s = c - S_BASE
            lead = L_BASE + s // N_COUNT
            vowel = V_BASE + (s % N_COUNT) // T_COUNT
            trail = s % T_COUNT
            if trail:
                stack.extend((T_BASE + trail, vowel, lead))
            else:
                stack.extend((vowel, lead))
            continue
        d = _decomposition(c, compat)
        if d is None:
            out.append(c)
        else:
            stack.extend(reversed(d))


def _canonical_order(cps):
    out = []
    for c in cps:
        out.append(c)
        cc = unicodedata.combining(chr(c))
        if cc == 0:
            continue
        i = len(out) - 1
        while i > 0:
            prev_cc = unicodedata.combining(chr(out[i - 1]))
            if prev_cc == 0 or prev_cc <= cc:
                break
            out[i - 1], out[i] = out[i], out[i - 1]
            i -= 1
    return out


def decompose(text, compat=False):
    raw = []
    for ch in text:
        _decompose_char(ord(ch), compat, raw)
    return ''.join(chr(c) for c in _canonical_order(raw))


_COMPOSITIONS = None


def _composition_table():
    global _COMPOSITIONS
    if _COMPOSITIONS is None:
        table = {}
        for cp in range(0x110000):
            if 0xD800 <= cp <= 0xDFFF or S_BASE <= cp < S_BASE + S_COUNT:
                continue
            d = _decomposition(cp, compat=False)
            if d is None or len(d) != 2 or _is_excluded(cp):
                continue
            if unicodedata.combining(chr(d[0])) != 0:
                continue  # non-starter decompositions are excluded
            table[(d[0], d[1])] = cp
        _COMPOSITIONS = table
    return _COMPOSITIONS


def _hangul_composite(a, b):
    if L_BASE <= a < L_BASE + L_COUNT and V_BASE <= b < V_BASE + V_COUNT:
        return S_BASE + ((a - L_BASE) * V_COUNT + (b - V_BASE)) * T_COUNT
    if S_BASE <= a < S_BASE + S_COUNT and (a - S_BASE) % T_COUNT == 0 \
            and T_BASE < b < T_BASE + T_COUNT:
        return a + (b - T_BASE)
    return None


def compose(text):
    table = _composition_table()
    out = []
    starter_idx = -1
    last_cc = 0
    for ch in text:
        cp = ord(ch)
        cc = unicodedata.combining(ch)
        composite = None
        if starter_idx >= 0:
            a = out[starter_idx]
            composite = _hangul_composite(a, cp)
            if composite is None and (cc == 0 or last_cc < cc):
                composite = table.get((a, cp))
        if composite is not None:
            out[starter_idx] = composite
            continue
        out.append(cp)
        if cc == 0:
            starter_idx = len(out) - 1
        last_cc = cc
    return ''.join(chr(c) for c in out)


def normalize(text, form='NFC'):
    if form == 'NFD':
        return decompose(text, compat=False)
    if form == 'NFKD':
        return decompose(text, compat=True)
    if form == 'NFC':
        return compose(decompose(text, compat=False))
    if form == 'NFKC':
        return compose(decompose(text, compat=True))
    raise ValueError('unknown normalization form: %r' % (form,))
