# -*- coding: utf-8 -*-
"""Tests for the high-level helper API."""
import unittest

from textseg import (
    count_graphemes, truncate_graphemes, count_words, split_sentences,
    chunk_text, graphemes,
)


class CountTruncate(unittest.TestCase):
    def test_count_graphemes(self):
        self.assertEqual(count_graphemes(''), 0)
        self.assertEqual(count_graphemes('hello'), 5)
        self.assertEqual(count_graphemes('áb👩‍👧🇨🇳'), 4)
        self.assertEqual(count_graphemes('क' + 'ि'), 1)

    def test_truncate_graphemes(self):
        self.assertEqual(truncate_graphemes('hello', 10), 'hello')
        self.assertEqual(truncate_graphemes('hello', 3), 'hel')
        self.assertEqual(truncate_graphemes('áb👩‍👧c', 2), 'áb')
        self.assertEqual(truncate_graphemes('áb👩‍👧c', 2, suffix='…'), 'áb…')
        self.assertEqual(truncate_graphemes('', 5), '')
        self.assertEqual(truncate_graphemes('abc', 0), '')

    def test_count_words(self):
        self.assertEqual(count_words(''), 0)
        self.assertEqual(count_words('hello world'), 2)
        self.assertEqual(count_words("can't stop, won't 3.5 stop"), 5)
        self.assertEqual(count_words('中文测试'), 4)   # per-char ideographs
        self.assertEqual(count_words('... !!!'), 0)   # punctuation only
        self.assertEqual(count_words('カタカナ'), 1)

    def test_split_sentences(self):
        self.assertEqual(split_sentences(''), [])
        self.assertEqual(split_sentences('One. Two!'), ['One. ', 'Two!'])
        joined = 'Mr. Smith went. He saw 3.5 things. Wow!'
        self.assertEqual(split_sentences(joined),
                         ['Mr. ', 'Smith went. ', 'He saw 3.5 things. ', 'Wow!'])


class Chunking(unittest.TestCase):
    def test_chunk_text_basic(self):
        self.assertEqual(chunk_text('abcdefg', 3), ['abc', 'def', 'g'])
        self.assertEqual(chunk_text('', 3), [])
        self.assertEqual(chunk_text('abc', 5), ['abc'])

    def test_chunk_respects_clusters(self):
        text = 'áb👩‍👧🇨🇳cd'
        for size in (1, 2, 3):
            chunks = chunk_text(text, size)
            self.assertEqual(''.join(chunks), text)
            for c in chunks:
                self.assertLessEqual(count_graphemes(c), size)
                # every chunk must itself be whole clusters
                self.assertEqual(graphemes(c), [c] if count_graphemes(c) == 1
                                 else graphemes(c))

    def test_chunk_invalid_size(self):
        with self.assertRaises(ValueError):
            chunk_text('abc', 0)

    def test_chunk_long_combining_run(self):
        text = 'a' + '́' * 100 + 'bc'
        chunks = chunk_text(text, 2)
        self.assertEqual(chunks, ['a' + '́' * 100 + 'b', 'c'])


if __name__ == '__main__':
    unittest.main()
