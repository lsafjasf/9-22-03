"""High-level utilities built on the boundary engines."""
from .grapheme import iter_grapheme_spans, graphemes
from .word import iter_word_spans, iter_words, word_count, words
from .sentence import split_sentences


def grapheme_count(text):
    """Number of extended grapheme clusters (user-perceived characters)."""
    return sum(1 for _ in iter_grapheme_spans(text))


def truncate_graphemes(text, max_clusters, ellipsis=""):
    """Truncate to at most max_clusters grapheme clusters.

    If truncation happens, `ellipsis` is appended (not counted towards the
    limit).  Never splits a cluster.
    """
    if max_clusters < 0:
        raise ValueError("max_clusters must be >= 0")
    spans = list(iter_grapheme_spans(text))
    if len(spans) <= max_clusters:
        return text
    end = spans[max_clusters][0] if max_clusters < len(spans) else len(text)
    return text[:end] + ellipsis


def chunk_text(text, max_clusters, prefer_word=False):
    """Split text into pieces of at most max_clusters grapheme clusters.

    Pieces never break a cluster.  With prefer_word=True, a piece that would
    overflow is cut at the last word boundary inside it (if any), keeping
    words whole where possible.
    """
    if max_clusters < 1:
        raise ValueError("max_clusters must be >= 1")
    spans = list(iter_grapheme_spans(text))
    if not spans:
        return []
    word_breaks = None
    if prefer_word:
        word_breaks = set()
        for a, _b in iter_word_spans(text):
            word_breaks.add(a)
        word_breaks.discard(0)
    pieces = []
    start_idx = 0
    total = len(spans)
    while start_idx < total:
        end_idx = min(start_idx + max_clusters, total)
        if prefer_word and end_idx < total:
            cut = None
            for j in range(end_idx, start_idx, -1):
                if spans[j][0] in word_breaks:
                    cut = j
                    break
            if cut is not None and cut > start_idx:
                end_idx = cut
        pieces.append(text[spans[start_idx][0]:spans[end_idx - 1][1]])
        start_idx = end_idx
    return pieces


__all__ = [
    "graphemes",
    "grapheme_count",
    "truncate_graphemes",
    "words",
    "word_count",
    "split_sentences",
    "chunk_text",
]
