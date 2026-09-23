"""High-level helpers built on the segmentation primitives."""

from .properties import (
    word_break as _wb, is_ideograph as _is_ideograph,
    WB_ALETTER, WB_HEBREW, WB_NUMERIC, WB_KATAKANA,
)
from .segmentation import graphemes, words, sentences

_WORD_CHARS = (WB_ALETTER, WB_HEBREW, WB_NUMERIC, WB_KATAKANA)


def count_graphemes(text):
    """Number of grapheme clusters (user-perceived characters)."""
    return len(graphemes(text))


def truncate_graphemes(text, max_clusters, suffix=''):
    """Truncate to at most max_clusters grapheme clusters.

    Never splits a cluster.  If truncation occurs, `suffix` is appended.
    """
    if max_clusters < 0:
        raise ValueError('max_clusters must be >= 0')
    clusters = graphemes(text)
    if len(clusters) <= max_clusters:
        return text
    return ''.join(clusters[:max_clusters]) + suffix


def count_words(text):
    """Number of tokens containing at least one word character.

    Word characters are letters, numbers, katakana and CJK ideographs
    (each ideograph forms its own token, matching the UAX #29 default).
    """
    count = 0
    for token in words(text):
        if any(_wb(ord(c)) in _WORD_CHARS or _is_ideograph(ord(c))
               for c in token):
            count += 1
    return count


def split_sentences(text):
    """Split text into sentences (sentence-boundary segments)."""
    return sentences(text)


def chunk_text(text, max_clusters):
    """Split text into pieces of at most max_clusters grapheme clusters.

    Pieces are cut only at grapheme-cluster boundaries, so concatenating the
    result reproduces the input exactly.
    """
    if max_clusters < 1:
        raise ValueError('max_clusters must be >= 1')
    clusters = graphemes(text)
    return [''.join(clusters[i:i + max_clusters])
            for i in range(0, len(clusters), max_clusters)]
