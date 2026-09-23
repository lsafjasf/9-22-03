#!/usr/bin/env python3
"""Rule-by-rule self tests for grapheme/word/sentence segmentation and
normalization invariance."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from textseg import (
    graphemes,
    iter_word_segments,
    words,
    split_sentences,
    normalize,
    canonical_equal,
    compatibility_equal,
    is_normalized,
)


def wsegs(s):
    return list(iter_word_segments(s))


class GraphemeRules(unittest.TestCase):
    def test_GB1_GB2_sot_eot(self):
        self.assertEqual(graphemes(""), [])
        self.assertEqual(graphemes("a"), ["a"])

    def test_GB3_CR_LF(self):
        self.assertEqual(graphemes("\r\n"), ["\r\n"])
        self.assertEqual(graphemes("a\r\nb"), ["a", "\r\n", "b"])

    def test_GB4_GB5_control(self):
        self.assertEqual(graphemes("a\x00b"), ["a", "\x00", "b"])
        self.assertEqual(graphemes("\x00a"), ["\x00", "a"])
        self.assertEqual(graphemes("a\x7f"), ["a", "\x7f"])
        self.assertEqual(graphemes("a\nb"), ["a", "\n", "b"])

    def test_GB6_hangul_L(self):
        self.assertEqual(graphemes("\u1100\u1100"), ["\u1100\u1100"])  # L x L
        self.assertEqual(graphemes("\u1100\u1161"), ["\u1100\u1161"])  # L x V
        self.assertEqual(graphemes("\u1100\uAC00"), ["\u1100\uAC00"])  # L x LV
        self.assertEqual(graphemes("\u1100\uAC01"), ["\u1100\uAC01"])  # L x LVT

    def test_GB7_hangul_V(self):
        self.assertEqual(graphemes("\uAC00\u1161"), ["\uAC00\u1161"])  # LV x V
        self.assertEqual(graphemes("\u1161\u11A8"), ["\u1161\u11A8"])  # V x T

    def test_GB8_hangul_T(self):
        self.assertEqual(graphemes("\uAC01\u11A8"), ["\uAC01\u11A8"])  # LVT x T
        self.assertEqual(graphemes("\u11A8\u11A8"), ["\u11A8\u11A8"])  # T x T

    def test_GB6_8_full_syllable(self):
        jamo = "\u1100\u1161\u11A8"  # L V T
        self.assertEqual(graphemes(jamo), [jamo])
        self.assertEqual(graphemes("\uAC01\u11A8\uAC00"), ["\uAC01\u11A8", "\uAC00"])

    def test_GB9_extend_zwj(self):
        self.assertEqual(graphemes("a\u0301"), ["a\u0301"])
        self.assertEqual(graphemes("a\u200d"), ["a\u200d"])
        self.assertEqual(graphemes("e\u0301\u0327"), ["e\u0301\u0327"])

    def test_GB9a_spacing_mark(self):
        self.assertEqual(graphemes("\u0915\u093E"), ["\u0915\u093E"])  # KA + AA sign

    def test_GB9b_prepend(self):
        self.assertEqual(graphemes("\u06005"), ["\u06005"])  # ARABIC NUMBER SIGN
        self.assertEqual(graphemes("\u0600\u0600a"), ["\u0600\u0600a"])

    def test_GB9c_indic_conjunct(self):
        self.assertEqual(graphemes("\u0915\u094D\u0915"), ["\u0915\u094D\u0915"])  # KA virama KA
        self.assertEqual(
            graphemes("\u0915\u094D\u0937"), ["\u0915\u094D\u0937"]  # KA virama SSA
        )
        # no linker -> break
        self.assertEqual(graphemes("\u0915\u0915"), ["\u0915", "\u0915"])

    def test_GB11_emoji_zwj(self):
        self.assertEqual(graphemes("\U0001F468\u200D\U0001F469"), ["\U0001F468\u200D\U0001F469"])
        family = "\U0001F468\u200D\U0001F469\u200D\U0001F467\u200D\U0001F466"
        self.assertEqual(graphemes(family), [family])
        # ExtPict Extend* ZWJ x ExtPict (modifier between)
        self.assertEqual(
            graphemes("\U0001F44D\U0001F3FD"), ["\U0001F44D\U0001F3FD"]  # thumbs up + skin tone
        )
        self.assertEqual(
            graphemes("\U0001F468\U0001F3FD\u200D\U0001F469"),
            ["\U0001F468\U0001F3FD\u200D\U0001F469"],
        )
        # no ExtPict before ZWJ -> break
        self.assertEqual(graphemes("a\u200D\U0001F469"), ["a\u200D", "\U0001F469"])

    def test_GB12_GB13_regional_indicators(self):
        ri = lambda c: chr(0x1F1E6 + c)
        self.assertEqual(graphemes(ri(0) + ri(1)), [ri(0) + ri(1)])
        self.assertEqual(graphemes(ri(0) + ri(1) + ri(2)), [ri(0) + ri(1), ri(2)])
        self.assertEqual(
            graphemes("".join(ri(i) for i in range(4))),
            [ri(0) + ri(1), ri(2) + ri(3)],
        )
        self.assertEqual(
            graphemes("".join(ri(i) for i in range(5))),
            [ri(0) + ri(1), ri(2) + ri(3), ri(4)],
        )

    def test_GB999_default_break(self):
        self.assertEqual(graphemes("ab"), ["a", "b"])


class WordRules(unittest.TestCase):
    def test_WB3_crlf(self):
        self.assertEqual(wsegs("a\r\nb"), ["a", "\r\n", "b"])

    def test_WB3a_WB3b_newline(self):
        self.assertEqual(wsegs("a\nb"), ["a", "\n", "b"])
        self.assertEqual(wsegs("a\x0bb"), ["a", "\x0b", "b"])

    def test_WB3c_zwj_emoji(self):
        self.assertEqual(wsegs("\U0001F468\u200D\U0001F469"), ["\U0001F468\u200D\U0001F469"])

    def test_WB3d_wsegspace(self):
        self.assertEqual(wsegs("a  b"), ["a", "  ", "b"])

    def test_WB4_ignore_format_extend_zwj(self):
        self.assertEqual(wsegs("a\u0301b"), ["a\u0301b"])
        self.assertEqual(wsegs("a\u200Db"), ["a\u200Db"])
        self.assertEqual(wsegs("a\u2060b"), ["a\u2060b"])  # WORD JOINER (Format)

    def test_WB5_letters(self):
        self.assertEqual(wsegs("abc"), ["abc"])

    def test_WB6_WB7_midletter(self):
        self.assertEqual(wsegs("don't"), ["don't"])
        self.assertEqual(wsegs("a.b"), ["a.b"])
        self.assertEqual(wsegs("a. b"), ["a", ".", " ", "b"])
        self.assertEqual(wsegs("a:b"), ["a:b"])  # ':' is MidLetter

    def test_WB7a_7b_7c_hebrew(self):
        self.assertEqual(wsegs("\u05D0'\u05D1"), ["\u05D0'\u05D1"])  # alef ' bet
        self.assertEqual(wsegs('\u05D0"\u05D1'), ['\u05D0"\u05D1'])  # alef " bet

    def test_WB8_WB9_WB10_numeric(self):
        self.assertEqual(wsegs("123"), ["123"])
        self.assertEqual(wsegs("a1"), ["a1"])
        self.assertEqual(wsegs("1a"), ["1a"])

    def test_WB11_WB12_midnum(self):
        self.assertEqual(wsegs("1,234"), ["1,234"])
        self.assertEqual(wsegs("3.14"), ["3.14"])
        self.assertEqual(wsegs("1, 234"), ["1", ",", " ", "234"])

    def test_WB13_katakana(self):
        self.assertEqual(wsegs("\u30AB\u30BF\u30AB\u30CA"), ["\u30AB\u30BF\u30AB\u30CA"])

    def test_WB13a_WB13b_extendnumlet(self):
        self.assertEqual(wsegs("a_b"), ["a_b"])
        self.assertEqual(wsegs("_a"), ["_a"])
        self.assertEqual(wsegs("a_"), ["a_"])

    def test_WB15_WB16_regional_indicators(self):
        ri = lambda c: chr(0x1F1E6 + c)
        self.assertEqual(wsegs(ri(0) + ri(1)), [ri(0) + ri(1)])
        self.assertEqual(wsegs(ri(0) + ri(1) + ri(2)), [ri(0) + ri(1), ri(2)])

    def test_WB999_default(self):
        self.assertEqual(wsegs("a b"), ["a", " ", "b"])
        self.assertEqual(wsegs("a,b"), ["a", ",", "b"])

    def test_words_filter(self):
        self.assertEqual(words("Hello, world! 3.14"), ["Hello", "world", "3.14"])


class SentenceRules(unittest.TestCase):
    def test_SB3_crlf(self):
        self.assertEqual(split_sentences("a.\r\nb"), ["a.\r\n", "b"])

    def test_SB4_parasep(self):
        self.assertEqual(split_sentences("a\u2029b"), ["a\u2029", "b"])
        self.assertEqual(split_sentences("a\nb"), ["a\n", "b"])

    def test_SB5_extend_after_term(self):
        self.assertEqual(split_sentences("A.\u0301 B"), ["A.\u0301 ", "B"])

    def test_SB6_aterm_numeric(self):
        self.assertEqual(split_sentences("Pi is 3.14. Yes"), ["Pi is 3.14. ", "Yes"])

    def test_SB7_upper_aterm_upper(self):
        # "X.Corp": no break before Upper after (Upper|Lower) ATerm
        self.assertEqual(split_sentences("X.Corp is big. Yes"), ["X.Corp is big. ", "Yes"])
        # "A.B C.": the absorbed "." leaves no terminator before the space,
        # so the whole string is a single sentence (SB998).
        self.assertEqual(split_sentences("A.B C."), ["A.B C."])

    def test_SB8_aterm_lower(self):
        self.assertEqual(split_sentences("e.g. x"), ["e.g. x"])
        self.assertEqual(split_sentences("Mr. smith"), ["Mr. smith"])
        self.assertEqual(split_sentences("Mr. Smith"), ["Mr. ", "Smith"])

    def test_SB8a_sterm_sterm(self):
        self.assertEqual(split_sentences("What?! Really"), ["What?! ", "Really"])

    def test_SB9_close(self):
        self.assertEqual(
            split_sentences('He said "hi." Done.'),
            ['He said "hi." ', "Done."],
        )

    def test_SB10_trailing_spaces(self):
        self.assertEqual(split_sentences("Hi.  There"), ["Hi.  ", "There"])

    def test_SB11_basic(self):
        self.assertEqual(split_sentences("One. Two! Three?"), ["One. ", "Two! ", "Three?"])

    def test_SB998_no_break_default(self):
        self.assertEqual(split_sentences("abc def"), ["abc def"])


class NormalizationInvariance(unittest.TestCase):
    SAMPLES = [
        "Café",
        "한글",
        "क्‍ष",  # ka + virama + zwj + ssa
        "👍🏽👨‍👩‍👧‍👦",
        "don't stop. 3.14, yes!",
        "🇨🇳🇺🇸 flags",
        "ﬁle ①②",  # compatibility chars
        "Σίσυφος",
    ]

    def test_normalize_forms(self):
        s = "Café ﬁ"
        self.assertEqual(normalize(s, "NFC"), "Café ﬁ")
        self.assertEqual(normalize(s, "NFD"), "Café ﬁ")
        self.assertEqual(normalize("ﬁle", "NFKC"), "file")
        self.assertEqual(normalize("①", "NFKC"), "1")
        self.assertTrue(is_normalized("abc", "NFC"))
        self.assertFalse(is_normalized("Café", "NFC"))
        with self.assertRaises(ValueError):
            normalize("x", "BOGUS")

    def test_equivalence(self):
        self.assertTrue(canonical_equal("Café", "Café"))
        self.assertFalse(canonical_equal("ﬁ", "fi"))  # not canonically equivalent
        self.assertTrue(compatibility_equal("ﬁ", "fi"))
        self.assertFalse(compatibility_equal("Café", "Cafe"))

    def test_canonical_invariance_grapheme(self):
        for s in self.SAMPLES:
            nfc, nfd = normalize(s, "NFC"), normalize(s, "NFD")
            self.assertEqual(
                [normalize(g, "NFC") for g in graphemes(nfd)],
                graphemes(nfc),
                f"grapheme invariance failed for {s!r}",
            )
            self.assertEqual(
                [normalize(g, "NFD") for g in graphemes(nfc)],
                graphemes(nfd),
                f"grapheme invariance failed for {s!r}",
            )

    def test_canonical_invariance_word_sentence(self):
        for s in self.SAMPLES:
            nfc, nfd = normalize(s, "NFC"), normalize(s, "NFD")
            self.assertEqual(
                [normalize(g, "NFC") for g in wsegs(nfd)],
                wsegs(nfc),
                f"word invariance failed for {s!r}",
            )
            self.assertEqual(
                [normalize(g, "NFC") for g in split_sentences(nfd)],
                split_sentences(nfc),
                f"sentence invariance failed for {s!r}",
            )

    COMPAT_SAMPLES = [  # NFKC preserves boundary classes for these
        "Café",
        "한글",
        "👍🏽👨‍👩‍👧‍👦",
        "don't stop. 3.14, yes!",
        "🇨🇳🇺🇸 flags",
        "Σίσυφος",
    ]

    def test_compatibility_invariance_samples(self):
        # NFKC/NFKD may change boundary classes in general (e.g. "ﬁ" -> "fi"
        # changes the cluster count); for texts whose compatibility mapping
        # preserves boundary classes, segmentation commutes with normalization.
        for s in self.COMPAT_SAMPLES:
            nfkc = normalize(s, "NFKC")
            self.assertEqual(
                [normalize(g, "NFKC") for g in graphemes(s)],
                graphemes(nfkc),
                f"NFKC grapheme invariance failed for {s!r}",
            )
            self.assertEqual(
                [normalize(g, "NFKC") for g in wsegs(s)],
                wsegs(nfkc),
                f"NFKC word invariance failed for {s!r}",
            )


if __name__ == "__main__":
    unittest.main()
