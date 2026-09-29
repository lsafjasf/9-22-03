"""Normalization-aware segmentation pipeline.

The `normalize_form` switch controls whether text is normalized *before*
segmentation, and to which form:

  normalize_form=None   -> raw engines; results are identical, example by
                           example, to the module-level segmentation API.
  "NFC"/"NFD"/"NFKC"/"NFKD" -> text is normalized to that form first.

Combined entries for the two orders of operation:

  normalize_then_segment(text, kind, form)   -- normalize, then segment
  segment_then_normalize(text, kind, form)   -- segment, then normalize each segment

For canonical forms (NFC/NFD), UAX #29 boundaries are invariant under
canonical equivalence, so the two orders agree; `verify_order_invariance`
checks this per sample.  Compatibility forms (NFKC/NFKD) may legitimately
change boundaries (e.g. U+FB01 LATIN SMALL LIGATURE FI -> "fi"); such
differences are reported, not hidden.
"""
from collections import namedtuple

from .grapheme import grapheme_break_positions, graphemes as _graphemes
from .word import (
    word_break_positions,
    iter_word_segments,
    words as _words,
)
from .sentence import sentence_break_positions, split_sentences
from .normalize import normalize, FORMS, CANONICAL_FORMS

KINDS = ("grapheme", "word", "sentence")

_BREAKS = {
    "grapheme": grapheme_break_positions,
    "word": word_break_positions,
    "sentence": sentence_break_positions,
}
_SEGMENTS = {
    "grapheme": _graphemes,
    "word": lambda text: list(iter_word_segments(text)),
    "sentence": split_sentences,
}


def _check_kind(kind):
    if kind not in KINDS:
        raise ValueError(f"unknown segmentation kind {kind!r}; expected one of {KINDS}")


def _check_form(form):
    if form is not None and form not in FORMS:
        raise ValueError(f"unknown normalization form {form!r}; expected None or one of {FORMS}")


def break_positions(text, kind="grapheme", normalize_form=None):
    """Boundary offsets of text, optionally normalized first.

    With normalize_form=None this is exactly the raw engine's output.
    """
    _check_kind(kind)
    _check_form(normalize_form)
    if normalize_form is not None:
        text = normalize(text, normalize_form)
    return _BREAKS[kind](text)


def segment(text, kind="grapheme", normalize_form=None):
    """Combined entry: (optionally) normalize, then segment.

    With normalize_form=None the result is identical, example by example,
    to the corresponding module-level segmentation function.
    """
    _check_kind(kind)
    _check_form(normalize_form)
    if normalize_form is not None:
        text = normalize(text, normalize_form)
    return list(_SEGMENTS[kind](text))


def normalize_then_segment(text, kind="grapheme", form="NFC"):
    """Order 1: normalize the whole text to `form`, then segment it."""
    return segment(text, kind, form)


def segment_then_normalize(text, kind="grapheme", form="NFC"):
    """Order 2: segment the original text, then normalize each segment."""
    _check_form(form)
    return [normalize(seg, form) for seg in segment(text, kind, None)]


def orders_agree(text, kind="grapheme", form="NFC"):
    """True iff the two orders of operation produce identical segments."""
    return normalize_then_segment(text, kind, form) == segment_then_normalize(text, kind, form)


InvarianceResult = namedtuple(
    "InvarianceResult",
    ["sample_index", "kind", "form", "ok", "normalize_first", "segment_first"],
)


def verify_order_invariance(samples, forms=CANONICAL_FORMS, kinds=KINDS):
    """Check both orders of operation over `samples` (an iterable of texts).

    Returns a list of InvarianceResult; `ok` is True when
    normalize-then-segment equals segment-then-normalize.
    """
    results = []
    for i, text in enumerate(samples):
        for form in forms:
            _check_form(form)
            for kind in kinds:
                nf = normalize_then_segment(text, kind, form)
                sf = segment_then_normalize(text, kind, form)
                results.append(InvarianceResult(i, kind, form, nf == sf, nf, sf))
    return results


class Segmenter:
    """Configurable segmentation front-end.

    Segmenter() (normalize_form=None) is a pass-through to the raw engines:
    every method returns exactly what the module-level API returns.
    Segmenter(normalize_form="NFC") normalizes before segmenting.
    """

    def __init__(self, normalize_form=None):
        _check_form(normalize_form)
        self.normalize_form = normalize_form

    def _prep(self, text):
        if self.normalize_form is None:
            return text
        return normalize(text, self.normalize_form)

    def break_positions(self, text, kind="grapheme"):
        _check_kind(kind)
        return _BREAKS[kind](self._prep(text))

    def segments(self, text, kind="grapheme"):
        _check_kind(kind)
        return list(_SEGMENTS[kind](self._prep(text)))

    def graphemes(self, text):
        return _graphemes(self._prep(text))

    def word_segments(self, text):
        return list(iter_word_segments(self._prep(text)))

    def words(self, text):
        return _words(self._prep(text))

    def sentences(self, text, strip=False):
        return split_sentences(self._prep(text), strip=strip)


__all__ = [
    "KINDS",
    "InvarianceResult",
    "Segmenter",
    "break_positions",
    "segment",
    "normalize_then_segment",
    "segment_then_normalize",
    "orders_agree",
    "verify_order_invariance",
]
