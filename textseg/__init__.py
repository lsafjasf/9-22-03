"""textseg -- text segmentation & normalization engine (stdlib only).

- Grapheme cluster / word / sentence boundaries (UAX #29, Unicode 16.0.0),
  implemented from scratch on generated Unicode data tables; no runtime
  segmentation facilities are used.
- Normalization (NFC/NFD/NFKC/NFKD) via unicodedata tables.
- Streaming segmentation with documented hold-back.
"""
from ._data import UNICODE_VERSION
from .grapheme import (
    grapheme_break_positions,
    iter_grapheme_spans,
    iter_graphemes,
    graphemes,
)
from .word import (
    word_break_positions,
    iter_word_spans,
    iter_word_segments,
    iter_words,
    words,
    word_count,
    is_word_segment,
)
from .sentence import (
    sentence_break_positions,
    iter_sentence_spans,
    iter_sentences,
    split_sentences,
)
from .normalize import (
    normalize,
    is_normalized,
    canonical_equal,
    compatibility_equal,
)
from .stream import StreamSegmenter, grapheme_stream, word_stream, sentence_stream
from .utils import grapheme_count, truncate_graphemes, chunk_text

__version__ = "1.0.0"
__all__ = [
    "UNICODE_VERSION",
    "grapheme_break_positions",
    "iter_grapheme_spans",
    "iter_graphemes",
    "graphemes",
    "grapheme_count",
    "truncate_graphemes",
    "word_break_positions",
    "iter_word_spans",
    "iter_word_segments",
    "iter_words",
    "words",
    "word_count",
    "is_word_segment",
    "sentence_break_positions",
    "iter_sentence_spans",
    "iter_sentences",
    "split_sentences",
    "normalize",
    "is_normalized",
    "canonical_equal",
    "compatibility_equal",
    "StreamSegmenter",
    "grapheme_stream",
    "word_stream",
    "sentence_stream",
    "chunk_text",
]
