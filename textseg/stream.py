"""Streaming segmentation: feed text in arbitrary chunks, receive committed
segments as soon as they are provably final.

Hold-back (how much uncommitted history must be retained):

  grapheme : the current unterminated cluster only.  Every grapheme rule
             decides a boundary from the char at the boundary plus left
             context, so one char of look-ahead suffices.  Worst case is an
             unbounded run of Extend/Prepend/SpacingMark chars, which is
             inherent to the definition of a cluster.
  word     : text since the last committed boundary, plus 2 significant
             (non-Extend/Format/ZWJ) chars of look-ahead, because
             WB6/WB7b/WB12 look one significant char past the char right of
             the boundary (e.g. "a." needs the char after ".").
  sentence : text since the last committed boundary, up to the last
             *decisive* char.  SB8's right context scans over
             Close/Sp/SContinue/Numeric/Other chars for a Lower, so a
             boundary after "A. " stays undecided until a decisive char
             (letter, separator, or terminator) arrives.  In the worst case
             (e.g. "A. " followed by an endless digit run) the tail is
             unbounded; that is inherent to SB8.

`pending` exposes the not-yet-committed buffer at any time.
"""
from ._classify import wb, sb
from .grapheme import grapheme_break_positions
from .word import word_break_positions
from .sentence import sentence_break_positions

_WB_IGNORE = frozenset(("Extend", "Format", "ZWJ"))
_SB_DECISIVE = frozenset(("OLetter", "Upper", "Lower", "Sep", "CR", "LF", "STerm", "ATerm"))


def _threshold_grapheme(buf):
    return len(buf) - 1


def _threshold_word(buf):
    sig = [i for i, ch in enumerate(buf) if wb(ord(ch)) not in _WB_IGNORE]
    return sig[-2] if len(sig) >= 2 else -1


def _threshold_sentence(buf):
    decisive = [i for i, ch in enumerate(buf) if sb(ord(ch)) in _SB_DECISIVE]
    return decisive[-1] if decisive else -1


_KINDS = {
    "grapheme": (grapheme_break_positions, _threshold_grapheme),
    "word": (word_break_positions, _threshold_word),
    "sentence": (sentence_break_positions, _threshold_sentence),
}


class StreamSegmenter:
    """Incremental segmenter.  kind: 'grapheme' | 'word' | 'sentence'."""

    def __init__(self, kind):
        if kind not in _KINDS:
            raise ValueError(f"unknown kind {kind!r}; expected one of {sorted(_KINDS)}")
        self.kind = kind
        self._breaks, self._threshold = _KINDS[kind]
        self._buf = ""
        self._flushed = False

    @property
    def pending(self):
        """Uncommitted tail still needed to decide upcoming boundaries."""
        return self._buf

    def feed(self, chunk):
        """Feed a chunk; return list of newly committed segments."""
        if self._flushed:
            raise RuntimeError("cannot feed after flush()")
        if not chunk:
            return []
        self._buf += chunk
        return self._commit()

    def _commit(self):
        buf = self._buf
        threshold = self._threshold(buf)
        if threshold <= 0:
            return []
        bounds = self._breaks(buf)
        committed = [b for b in bounds if 0 < b <= threshold]
        if not committed:
            return []
        cut = committed[-1]
        points = [0] + committed
        segments = [buf[a:b] for a, b in zip(points, points[1:])]
        self._buf = buf[cut:]
        return segments

    def flush(self):
        """Signal end of input; return all remaining segments."""
        self._flushed = True
        buf, self._buf = self._buf, ""
        if not buf:
            return []
        bounds = self._breaks(buf)
        return [buf[a:b] for a, b in zip(bounds, bounds[1:])]

    def feed_all(self, chunks):
        """Convenience: feed every chunk, flush, return all segments."""
        out = []
        for chunk in chunks:
            out.extend(self.feed(chunk))
        out.extend(self.flush())
        return out


def grapheme_stream():
    return StreamSegmenter("grapheme")


def word_stream():
    return StreamSegmenter("word")


def sentence_stream():
    return StreamSegmenter("sentence")
