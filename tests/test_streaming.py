# -*- coding: utf-8 -*-
"""Streaming vs batch consistency tests."""
import random
import unittest

from textseg import graphemes, words, sentences
from textseg.stream import GraphemeStream, WordStream, SentenceStream


def stream_all(cls, text, sizes):
    seg = cls()
    out = []
    i = 0
    k = 0
    while i < len(text):
        n = sizes[k % len(sizes)]
        out.extend(seg.feed(text[i:i + n]))
        i += n
        k += 1
    out.extend(seg.flush())
    return out


CORPUS = [
    '',
    'a',
    'plain ascii words. And more!',
    'áèô combined marks',
    '👩‍👩‍👧‍👦👍🏽🇨🇳🇯🇵🇰🇷 emoji mix',
    '🏴󠁧󠁢󠁥󠁮󠁧󠁿 tagged flag',
    '한국어 한국어 hangul',
    'कषि क्‍ष devanagari',
    'Mr. Smith paid 3.5 kg. Really? "Yes!"  (He did.)  Next one.',
    'e.g. this. i.e. that. etc. (note).',
    'lines\r\nbreak\nhere\rend',
    'trailing terminators...   ',
    'spaces      runs',
    'a' + '\u0301' * 300 + 'b',
    'x' * 500 + '. ' + 'y' * 500,
    '中文测试。第二句！第三句？',
    'カタカナです。ひらがな',
    'one\ttwo  three\u00a0four',
    '🇦🇧🇨🇩🇪🇫🇬🇭',
    '\x00\x01\x02 controls \x7f',
    'Wait! really. e.g. eggs. Wait! Really.',
]

CHUNKINGS = [(1,), (2,), (3,), (5,), (7,), (16,), (1, 2, 3), (4, 1, 9)]


class StreamConsistency(unittest.TestCase):
    def _check(self, cls, batch, text):
        for sizes in CHUNKINGS:
            got = stream_all(cls, text, sizes)
            want = batch(text)
            self.assertEqual(got, want, (cls.__name__, sizes, text[:40]))
            self.assertEqual(''.join(got), text)

    def test_grapheme_stream(self):
        for text in CORPUS:
            self._check(GraphemeStream, graphemes, text)

    def test_word_stream(self):
        for text in CORPUS:
            self._check(WordStream, words, text)

    def test_sentence_stream(self):
        for text in CORPUS:
            self._check(SentenceStream, sentences, text)

    def test_random_chunk_boundaries(self):
        rng = random.Random(7)
        text = ''.join(CORPUS)
        for _ in range(50):
            sizes = [rng.randrange(1, 40) for _ in range(rng.randrange(1, 6))]
            for cls, batch in ((GraphemeStream, graphemes),
                               (WordStream, words),
                               (SentenceStream, sentences)):
                self.assertEqual(stream_all(cls, text, sizes), batch(text))

    def test_empty_and_single_feeds(self):
        for cls in (GraphemeStream, WordStream, SentenceStream):
            s = cls()
            self.assertEqual(s.feed(''), [])
            self.assertEqual(s.flush(), [])
        for cls in (GraphemeStream, WordStream, SentenceStream):
            s = cls()
            s.feed('a')
            s.feed('')
            out = s.flush()
            self.assertEqual(''.join(out), 'a')

    def test_retention_is_bounded(self):
        # grapheme stream must not accumulate history: buffer stays tiny
        s = GraphemeStream()
        for _ in range(1000):
            s.feed('ab. ')
        self.assertLessEqual(len(s._buf), 4)
        # word stream: current token + lookahead only
        w = WordStream()
        for _ in range(1000):
            w.feed('word ')
        self.assertLessEqual(len(w._buf), 8)


if __name__ == '__main__':
    unittest.main()
