#!/usr/bin/env python3
"""Pipeline tests: normalization switch, combined entries, order invariance,
and switch-off identity with the raw engines."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from textseg import (
    graphemes,
    grapheme_break_positions,
    iter_word_segments,
    word_break_positions,
    words,
    split_sentences,
    sentence_break_positions,
    normalize,
    Segmenter,
    segment,
    break_positions,
    normalize_then_segment,
    segment_then_normalize,
    orders_agree,
    verify_order_invariance,
    KINDS,
)
from textseg.normalize import FORMS, CANONICAL_FORMS
from textseg.samples import SAMPLES, COMPAT_SAMPLES

TEXTS = [s["text"] for s in SAMPLES] + [s["text"] for s in COMPAT_SAMPLES]


class ConfigValidation(unittest.TestCase):
    def test_bad_form(self):
        for text in ("x", ""):
            with self.assertRaises(ValueError):
                segment(text, "grapheme", "BOGUS")
        with self.assertRaises(ValueError):
            Segmenter("BOGUS")
        with self.assertRaises(ValueError):
            segment_then_normalize("x", "grapheme", "BOGUS")

    def test_bad_kind(self):
        with self.assertRaises(ValueError):
            segment("x", "morpheme")
        with self.assertRaises(ValueError):
            break_positions("x", "morpheme")
        with self.assertRaises(ValueError):
            Segmenter().break_positions("x", "morpheme")


class SwitchOffIdentity(unittest.TestCase):
    """normalize_form=None must not change existing segmentation results,
    example by example."""

    def test_segment_matches_raw_engines(self):
        raw = {
            "grapheme": graphemes,
            "word": lambda t: list(iter_word_segments(t)),
            "sentence": split_sentences,
        }
        for text in TEXTS:
            for kind in KINDS:
                self.assertEqual(segment(text, kind, None), raw[kind](text))

    def test_break_positions_match_raw_engines(self):
        raw = {
            "grapheme": grapheme_break_positions,
            "word": word_break_positions,
            "sentence": sentence_break_positions,
        }
        for text in TEXTS:
            for kind in KINDS:
                self.assertEqual(break_positions(text, kind, None), raw[kind](text))

    def test_default_segmenter_matches_module_api(self):
        st = Segmenter()
        for text in TEXTS:
            self.assertEqual(st.graphemes(text), graphemes(text))
            self.assertEqual(st.word_segments(text), list(iter_word_segments(text)))
            self.assertEqual(st.words(text), words(text))
            self.assertEqual(st.sentences(text), split_sentences(text))
            self.assertEqual(st.sentences(text, strip=True), split_sentences(text, strip=True))


class NormalizedSegmentation(unittest.TestCase):
    def test_normalize_before_segment(self):
        decomposed = "Café 한글"
        self.assertEqual(Segmenter("NFC").graphemes(decomposed)[3], "é")
        self.assertEqual(Segmenter("NFD").graphemes("Café")[3], "é")
        self.assertEqual(segment(decomposed, "word", "NFC"), ["Café", " ", "한글"])

    def test_combined_entry_orders(self):
        text = "한글 Café"
        self.assertEqual(normalize_then_segment(text, "grapheme", "NFC"),
                         segment(text, "grapheme", "NFC"))
        self.assertEqual(segment_then_normalize(text, "grapheme", "NFC"),
                         [normalize(g, "NFC") for g in graphemes(text)])


class OrderInvariance(unittest.TestCase):
    def test_canonical_forms_agree_on_all_samples(self):
        for text in TEXTS:
            for form in CANONICAL_FORMS:
                for kind in KINDS:
                    self.assertTrue(
                        orders_agree(text, kind, form),
                        f"order mismatch [{kind}/{form}] for {text!r}",
                    )

    def test_all_forms_agree_on_main_samples(self):
        # main samples contain no compatibility characters, so even
        # NFKC/NFKD keep boundaries invariant
        for s in SAMPLES:
            for form in FORMS:
                for kind in KINDS:
                    self.assertTrue(
                        orders_agree(s["text"], kind, form),
                        f"order mismatch [{kind}/{form}] for {s['id']}",
                    )

    def test_verify_report_covers_everything(self):
        results = verify_order_invariance(TEXTS[:4], forms=FORMS)
        self.assertEqual(len(results), 4 * len(FORMS) * len(KINDS))
        self.assertTrue(all(r.ok for r in results if r.form in CANONICAL_FORMS))

    def test_compat_samples_flagged_under_compatibility_forms(self):
        results = verify_order_invariance(
            [s["text"] for s in COMPAT_SAMPLES], forms=FORMS
        )
        canon = [r for r in results if r.form in CANONICAL_FORMS]
        compat = [r for r in results if r.form not in CANONICAL_FORMS]
        self.assertTrue(all(r.ok for r in canon))
        self.assertTrue(any(not r.ok for r in compat))


if __name__ == "__main__":
    unittest.main()
