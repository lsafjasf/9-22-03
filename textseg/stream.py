"""Streaming (incremental) segmentation.

Each segmenter accepts arbitrarily chunked input via ``feed()`` and returns
the segments that are *final* (provably identical to batch segmentation of
the complete text).  ``flush()`` must be called at end of input to drain the
retained tail.

Lookbehind retention guarantees (how much history is kept, and why):

  * GraphemeStream  -- keeps exactly the current unfinished cluster.  Every
    grapheme rule (GB1-GB999) decides the boundary before a character using
    only that character plus context inside the current cluster (GB11's
    "ExtPict Extend* ZWJ" lookbehind and the RI parity of GB12/13 can never
    cross a cluster boundary).  Worst case retention = one cluster, which is
    unbounded only for pathological inputs (e.g. an endless run of combining
    marks), which is inherent: such a run is a single cluster.
  * WordStream      -- keeps the text since the last emitted boundary plus a
    one-significant-character lookahead past the boundary character:
    WB6/WB12 ("AHLetter x MidLetter AHLetter" etc.) inspect the significant
    character after the character at the boundary.  Extend/Format/ZWJ are
    transparent (WB4), so retention = current token + next significant char.
  * SentenceStream  -- keeps everything since the last emitted sentence
    boundary.  A break position after a terminator is only final once a
    "decisive" character (not Sp/Close/Extend/Format) has arrived, because
    SB9/SB10 absorb arbitrarily long Close*/Sp* runs and SB8 needs the next
    decisive letter.  A trailing CR is also retained (SB3: CR x LF).  Worst
    case retention is unbounded (e.g. "!" followed by endless spaces), which
    is inherent to the rule set.
"""

from bisect import bisect_right

from .properties import (
    word_break as _wb, sentence_break as _sb,
    WB_EXTEND, WB_FORMAT, WB_ZWJ, SB_EXTEND, SB_FORMAT, SB_SP, SB_CLOSE,
)
from .segmentation import (
    graphemes, words, sentences, word_spans, sentence_spans,
)


def _first_significant(segment):
    for ch in segment:
        if _sb(ord(ch)) not in (SB_EXTEND, SB_FORMAT):
            return ch
    return None


class GraphemeStream:
    def __init__(self):
        self._buf = ''

    def feed(self, chunk):
        self._buf += chunk
        clusters = graphemes(self._buf)
        if len(clusters) <= 1:
            return []
        self._buf = clusters[-1]
        return clusters[:-1]

    def flush(self):
        rest, self._buf = self._buf, ''
        return [rest] if rest else []


class WordStream:
    def __init__(self):
        self._buf = ''

    def feed(self, chunk):
        self._buf += chunk
        buf = self._buf
        sig = [i for i, ch in enumerate(buf)
               if _wb(ord(ch)) not in (WB_EXTEND, WB_FORMAT, WB_ZWJ)]
        if len(sig) < 2:
            return []
        spans = word_spans(buf)
        emit = []
        cut = 0
        for s, e in spans:
            # The boundary after this token lies before significant char
            # b = last_sig + 1 and is final only once sig[b + 1] is known
            # (WB6/WB12 look one significant char past the boundary char).
            last_sig = bisect_right(sig, e - 1) - 1
            if last_sig > len(sig) - 3:
                break
            emit.append(buf[s:e])
            cut = e
        self._buf = buf[cut:]
        return emit

    def flush(self):
        rest, self._buf = self._buf, ''
        return words(rest)


class SentenceStream:
    def __init__(self):
        self._buf = ''

    def feed(self, chunk):
        self._buf += chunk
        buf = self._buf
        held = ''
        if buf.endswith('\r'):
            held, buf = '\r', buf[:-1]  # CR may still pair with LF (SB3)
        spans = sentence_spans(buf)
        emit = []
        cut = 0
        for k in range(len(spans) - 1):
            nxt = buf[spans[k + 1][0]:spans[k + 1][1]]
            decisive = None
            for ch in nxt:
                p = _sb(ord(ch))
                if p not in (SB_EXTEND, SB_FORMAT):
                    decisive = p
                    break
            if decisive == SB_SP:
                break  # break position may still shift right (SB9/SB10)
            emit.append(buf[spans[k][0]:spans[k][1]])
            cut = spans[k][1]
        self._buf = buf[cut:] + held
        return emit

    def flush(self):
        rest, self._buf = self._buf, ''
        return sentences(rest)
