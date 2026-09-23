#!/usr/bin/env python3
"""Edge cases: empty text, pure controls, pathological combining runs,
incomplete sequences, lone surrogates; plus utility functions."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from textseg import (
    graphemes,
    grapheme_count,
    truncate_graphemes,
    iter_word_segments,
    words,
    word_count,
    split_sentences,
    chunk_text,
    grapheme_break_positions,
    word_break_positions,
    sentence_break_positions,
    StreamSegmenter,
)


class EdgeCases(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(graphemes(""), [])
        self.assertEqual(list(iter_word_segments("")), [])
        self.assertEqual(split_sentences(""), [])
        self.assertEqual(grapheme_break_positions(""), [0])
        self.assertEqual(word_break_positions(""), [0])
        self.assertEqual(sentence_break_positions(""), [0])
        self.assertEqual(grapheme_count(""), 0)
        self.assertEqual(word_count(""), 0)
        self.assertEqual(chunk_text("", 5), [])
        self.assertEqual(truncate_graphemes("", 3), "")

    def test_pure_controls(self):
        s = "\x00\x01\x7f"
        self.assertEqual(graphemes(s), ["\x00", "\x01", "\x7f"])
        self.assertEqual(grapheme_count(s), 3)
        # controls are not word chars
        self.assertEqual(words(s), [])
        # sentence: no terminator -> single segment
        self.assertEqual(split_sentences(s), [s])

    def test_only_newlines(self):
        self.assertEqual(graphemes("\n\n"), ["\n", "\n"])
        self.assertEqual(split_sentences("\n\n"), ["\n", "\n"])
        self.assertEqual(split_sentences("\r\n\r\n"), ["\r\n", "\r\n"])

    def test_long_combining_run(self):
        s = "a" + "\u0301" * 10000
        self.assertEqual(graphemes(s), [s])
        self.assertEqual(grapheme_count(s), 1)
        self.assertEqual(list(iter_word_segments(s)), [s])
        self.assertEqual(word_count(s), 1)
        # leading combining char (no base)
        t = "\u0301" * 5000
        self.assertEqual(graphemes(t), [t])

    def test_long_prepend_run(self):
        s = "\u0600" * 1000 + "x"
        self.assertEqual(graphemes(s), [s])

    def test_incomplete_emoji_zwj(self):
        self.assertEqual(graphemes("\U0001F468\u200D"), ["\U0001F468\u200D"])  # trailing ZWJ
        self.assertEqual(graphemes("\u200D"), ["\u200D"])  # lone ZWJ
        # ZWJ at sot: GB11 needs ExtPict before ZWJ, so the emoji breaks off
        self.assertEqual(graphemes("\u200D\U0001F469"), ["\u200D", "\U0001F469"])

    def test_incomplete_regional_indicator(self):
        ri = chr(0x1F1E6)
        self.assertEqual(graphemes(ri), [ri])
        self.assertEqual(graphemes(ri * 3), [ri * 2, ri])

    def test_incomplete_hangul(self):
        self.assertEqual(graphemes("\u1100"), ["\u1100"])  # lone L
        self.assertEqual(graphemes("\u11A8"), ["\u11A8"])  # lone T

    def test_incomplete_indic(self):
        self.assertEqual(graphemes("\u0915\u094D"), ["\u0915\u094D"])  # KA + trailing virama

    def test_lone_cr(self):
        self.assertEqual(graphemes("\r"), ["\r"])
        self.assertEqual(graphemes("\r\r\n"), ["\r", "\r\n"])
        self.assertEqual(split_sentences("a.\r"), ["a.\r"])

    def test_lone_surrogates(self):
        s = "\ud800\udc00"
        self.assertEqual(graphemes(s), ["\ud800", "\udc00"])
        self.assertEqual(grapheme_count("a\ud800b"), 3)

    def test_unassigned_and_private(self):
        self.assertEqual(graphemes("\u0378"), ["\u0378"])  # unassigned -> Other
        # emoji + tag chars (GCB=Extend) form a single cluster
        self.assertEqual(grapheme_count("\U0001F468\U000E0020\U000E007F"), 1)

    def test_mixed_whitespace_words(self):
        self.assertEqual(words(" \t\n "), [])
        self.assertEqual(word_count("  hello   world  "), 2)


class StreamEdgeCases(unittest.TestCase):
    def test_empty_feed_flush(self):
        for kind in ("grapheme", "word", "sentence"):
            st = StreamSegmenter(kind)
            self.assertEqual(st.feed(""), [])
            self.assertEqual(st.flush(), [])
            self.assertEqual(st.pending, "")

    def test_feed_after_flush_raises(self):
        st = StreamSegmenter("grapheme")
        st.flush()
        with self.assertRaises(RuntimeError):
            st.feed("x")

    def test_pending_holdback_grapheme(self):
        st = StreamSegmenter("grapheme")
        self.assertEqual(st.feed("ab"), ["a"])  # last cluster held back
        self.assertEqual(st.pending, "b")
        # 'c' arrives -> boundary before 'c' is final -> "b́" committed
        self.assertEqual(st.feed("\u0301c"), ["b\u0301"])
        self.assertEqual(st.pending, "c")
        self.assertEqual(st.flush(), ["c"])

    def test_pending_holdback_word(self):
        st = StreamSegmenter("word")
        out = st.feed("hello wo")
        self.assertEqual(out, ["hello", " "])  # 2 significant chars of lookahead
        self.assertEqual(st.pending, "wo")
        out = st.feed("rld ")
        self.assertEqual("".join(out), "")
        self.assertEqual(st.pending, "world ")
        self.assertEqual(st.flush(), ["world", " "])

    def test_pending_holdback_sentence(self):
        st = StreamSegmenter("sentence")
        self.assertEqual(st.feed("Mr. "), [])  # waits: next char could be Lower
        self.assertEqual(st.pending, "Mr. ")
        self.assertEqual(st.feed("Smith"), ["Mr. "])
        self.assertEqual(st.flush(), ["Smith"])

    def test_long_combining_run_stream(self):
        s = "a" + "\u0301" * 10000
        st = StreamSegmenter("grapheme")
        out = []
        for i in range(0, len(s), 7):
            out.extend(st.feed(s[i:i + 7]))
        out.extend(st.flush())
        self.assertEqual(out, [s])


class Utils(unittest.TestCase):
    def test_grapheme_count(self):
        self.assertEqual(grapheme_count("hello"), 5)
        self.assertEqual(grapheme_count("👨‍👩‍👧‍👦🇨🇳e\u0301"), 3)

    def test_truncate(self):
        s = "👨‍👩‍👧‍👦🇨🇳e\u0301xy"
        self.assertEqual(truncate_graphemes(s, 2), "👨‍👩‍👧‍👦🇨🇳")
        self.assertEqual(truncate_graphemes(s, 2, ellipsis="…"), "👨‍👩‍👧‍👦🇨🇳…")
        self.assertEqual(truncate_graphemes(s, 10), s)  # no truncation
        self.assertEqual(truncate_graphemes(s, 0), "")
        with self.assertRaises(ValueError):
            truncate_graphemes(s, -1)

    def test_word_count(self):
        self.assertEqual(word_count("The quick brown fox"), 4)
        self.assertEqual(word_count("3.14 is pi"), 3)

    def test_split_sentences_strip(self):
        self.assertEqual(
            split_sentences("One. Two.", strip=True), ["One.", "Two."]
        )

    def test_chunk_text(self):
        s = "👨‍👩‍👧‍👦🇨🇳e\u0301xy"
        pieces = chunk_text(s, 2)
        self.assertEqual(pieces, ["👨‍👩‍👧‍👦🇨🇳", "e\u0301x", "y"])
        self.assertEqual("".join(pieces), s)
        self.assertTrue(all(grapheme_count(p) <= 2 for p in pieces))
        self.assertEqual(chunk_text(s, 100), [s])
        with self.assertRaises(ValueError):
            chunk_text(s, 0)

    def test_chunk_text_prefer_word(self):
        s = "aaa bbb ccc"
        pieces = chunk_text(s, 5, prefer_word=True)
        self.assertEqual(pieces, ["aaa ", "bbb ", "ccc"])
        self.assertEqual("".join(pieces), s)
        # falls back to hard cut when no word boundary fits
        pieces = chunk_text("abcdefgh", 3, prefer_word=True)
        self.assertEqual("".join(pieces), "abcdefgh")
        self.assertTrue(all(grapheme_count(p) <= 3 for p in pieces))


if __name__ == "__main__":
    unittest.main()
