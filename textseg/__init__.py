"""textseg -- text segmentation & normalization engine (stdlib only).

Public API:
  Normalization:  normalize, decompose, compose
  Graphemes:      graphemes, grapheme_boundaries, count_graphemes,
                  truncate_graphemes
  Words:          words, word_spans, count_words
  Sentences:      sentences, sentence_spans, split_sentences
  Chunking:       chunk_text
  Streaming:      GraphemeStream, WordStream, SentenceStream
"""

from .normalization import normalize, decompose, compose
from .segmentation import (
    graphemes, grapheme_boundaries, words, word_spans,
    sentences, sentence_spans,
)
from .api import (
    count_graphemes, truncate_graphemes, count_words,
    split_sentences, chunk_text,
)
from .stream import GraphemeStream, WordStream, SentenceStream

__all__ = [
    'normalize', 'decompose', 'compose',
    'graphemes', 'grapheme_boundaries', 'count_graphemes', 'truncate_graphemes',
    'words', 'word_spans', 'count_words',
    'sentences', 'sentence_spans', 'split_sentences',
    'chunk_text',
    'GraphemeStream', 'WordStream', 'SentenceStream',
]
