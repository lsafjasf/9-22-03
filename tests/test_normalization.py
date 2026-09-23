# -*- coding: utf-8 -*-
"""Normalization tests: oracle comparison against unicodedata.normalize and
segmentation invariance under canonical normalization."""
import random
import unicodedata
import unittest

from textseg.normalization import normalize, decompose, compose
from textseg import graphemes, words, sentences


class KnownValues(unittest.TestCase):
    def test_nfc_compose(self):
        self.assertEqual(normalize('e\u0301', 'NFC'), '\u00e9')
        self.assertEqual(normalize('A\u030a', 'NFC'), '\u00c5')

    def test_nfd_decompose(self):
        self.assertEqual(normalize('\u00e9', 'NFD'), 'e\u0301')
        self.assertEqual(normalize('\ufb01', 'NFD'), '\ufb01')  # compat only

    def test_nfkc_nfkd_compat(self):
        self.assertEqual(normalize('\ufb01', 'NFKC'), 'fi')
        self.assertEqual(normalize('\u2460', 'NFKD'), '1')
        self.assertEqual(normalize('\uff21', 'NFKC'), 'A')

    def test_hangul_algorithmic(self):
        self.assertEqual(normalize('\u1100\u1161', 'NFC'), '\uac00')
        self.assertEqual(normalize('\u1101\u1161\u11a8', 'NFC'), '\uae4d')
        self.assertEqual(normalize('\uae4d', 'NFD'), '\u1101\u1161\u11a8')
        self.assertEqual(normalize('\uac00\u11a8', 'NFC'), '\uac01')

    def test_canonical_ordering(self):
        # ccc(0315)=232 > ccc(0300)=230 -> reordered in NFD
        self.assertEqual(normalize('a\u0315\u0300', 'NFD'), 'a\u0300\u0315')

    def test_composition_exclusion(self):
        # U+0958 is a composition exclusion: NFC must NOT produce it
        self.assertEqual(normalize('\u0915\u093c', 'NFC'), '\u0915\u093c')

    def test_blocking(self):
        # equal combining classes: the second 0301 is blocked from the
        # starter by the first (last_cc == cc), so no double composition
        self.assertEqual(normalize('a\u0301\u0301', 'NFC'), '\u00e1\u0301')

    def test_idempotence(self):
        samples = ['e\u0301\u0300', '\uac01', '\ufb01x', '①②', '한국어']
        for form in ('NFC', 'NFD', 'NFKC', 'NFKD'):
            for s in samples:
                once = normalize(s, form)
                self.assertEqual(normalize(once, form), once, (form, s))


class OracleSweep(unittest.TestCase):
    """Compare against unicodedata.normalize over targeted codepoint sets."""

    def _check(self, cps):
        for cp in cps:
            ch = chr(cp)
            # canonical forms only; compat forms change text by design
            for form in ('NFC', 'NFD'):
                got = normalize(ch, form)
                want = unicodedata.normalize(form, ch)
                self.assertEqual(got, want, 'U+%04X %s: %r != %r'
                                 % (cp, form, got, want))

    def test_all_decomposable_codepoints(self):
        cps = [cp for cp in range(0x110000)
               if not 0xD800 <= cp <= 0xDFFF and unicodedata.decomposition(chr(cp))]
        self.assertGreater(len(cps), 5000)
        self._check(cps)

    def test_hangul_syllables_sample(self):
        cps = list(range(0xAC00, 0xD7A4, 37)) + [0xAC00, 0xAC01, 0xD7A3]
        self._check(cps)

    def test_combining_marks(self):
        cps = [cp for cp in range(0x300, 0x370)]
        self._check(cps)

    def test_random_strings(self):
        rng = random.Random(20260923)
        alphabet = [chr(cp) for cp in range(0x20, 0x300)]
        alphabet += [chr(cp) for cp in range(0x300, 0x370)]
        alphabet += ['\uac00', '\u1100', '\u1161', '\u11a8', '\ufb01',
                     '\u0915', '\u093c', '\u1f600', '한', '글']
        for _ in range(300):
            s = ''.join(rng.choice(alphabet) for _ in range(rng.randrange(1, 12)))
            # canonical forms only; compat forms change text by design
            for form in ('NFC', 'NFD'):
                self.assertEqual(normalize(s, form),
                                 unicodedata.normalize(form, s), (form, s))


CORPUS = [
    'Café naïve résumé',
    'e\u0301lan a\u0300 la ge\u0301ne',
    '한국어 \u1112\u1161\u11ab\u1100\u1173\u11a8',
    'क\u093cष\u093f',
    '👩\u200d👩\u200d👧\u200d👦 family 👍\U0001f3fd',
    '🇨🇳🇯🇵🇰🇷 flags',
    'Mr. Smith paid 3.5. Really? Yes!',
    'ﬁle ①②③ ＡＢＣ',
    'a\u0315\u0300 ordered marks',
    '\u0e01\u0e49\u0e32\u0e19 Thai',
]


class SegmentationInvariance(unittest.TestCase):
    """Segmentation must be invariant under canonical normalization: segment
    counts match and segments are pairwise canonically equivalent."""

    def _assert_invariant(self, segment, name):
        for text in CORPUS:
            base = segment(text)
            for form in ('NFC', 'NFD'):
                alt = segment(normalize(text, form))
                self.assertEqual(len(base), len(alt), (name, form, text))
                for a, b in zip(base, alt):
                    self.assertEqual(normalize(a, 'NFC'), normalize(b, 'NFC'),
                                     (name, form, text, a, b))

    def test_grapheme_invariance(self):
        self._assert_invariant(graphemes, 'grapheme')

    def test_word_invariance(self):
        self._assert_invariant(words, 'word')

    def test_sentence_invariance(self):
        self._assert_invariant(sentences, 'sentence')

    def test_normalized_mode_byte_identical(self):
        # Segmenting the NFC form gives byte-identical results for any
        # canonically equivalent input.
        for text in CORPUS:
            ref_g = graphemes(normalize(text, 'NFC'))
            ref_w = words(normalize(text, 'NFC'))
            # canonical forms only; compat forms change text by design
            for form in ('NFC', 'NFD'):
                nfc = normalize(normalize(text, form), 'NFC')
                self.assertEqual(graphemes(nfc), ref_g, (form, text))
                self.assertEqual(words(nfc), ref_w, (form, text))


if __name__ == '__main__':
    unittest.main()
