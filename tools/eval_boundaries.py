#!/usr/bin/env python3
"""Boundary accuracy and normalization-order evaluation.

  A. Official UCD conformance (tests/data/*BreakTest.txt):
     per-case exact-match accuracy and boundary-level precision/recall/F1.
  B. Multilingual gold samples (textseg/samples.py):
     per-sample exact match for grapheme / word / sentence boundaries.
  C. Normalization order invariance on the sample set:
     normalize-then-segment vs segment-then-normalize, per form x kind.
  D. Switch-off identity: pipeline with normalize_form=None must equal
     the raw engines, example by example (samples + all official cases).

Usage: python3 tools/eval_boundaries.py
"""
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

from test_conformance import parse_test_line  # noqa: E402

from textseg import (  # noqa: E402
    grapheme_break_positions,
    word_break_positions,
    sentence_break_positions,
    graphemes,
    words,
    split_sentences,
    iter_word_segments,
    segment,
    verify_order_invariance,
    KINDS,
)
from textseg.normalize import FORMS  # noqa: E402
from textseg.samples import SAMPLES, COMPAT_SAMPLES  # noqa: E402

DATA = os.path.join(ROOT, "tests", "data")
BREAKS = {
    "grapheme": grapheme_break_positions,
    "word": word_break_positions,
    "sentence": sentence_break_positions,
}
FILES = {
    "grapheme": "GraphemeBreakTest.txt",
    "word": "WordBreakTest.txt",
    "sentence": "SentenceBreakTest.txt",
}
GOLD = {
    "grapheme": ("graphemes", graphemes),
    "word": ("words", words),
    "sentence": ("sentences", split_sentences),
}


def load_cases(kind):
    path = os.path.join(DATA, FILES[kind])
    cases = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            cases.append(parse_test_line(line))
    return cases


def section(title):
    print()
    print(title)
    print("-" * len(title))


def eval_official():
    section("A. Official UCD conformance (Unicode 16.0.0)")
    print(f"{'kind':<10} {'cases':>6} {'exact':>6} {'accuracy':>9} {'P':>7} {'R':>7} {'F1':>7}")
    all_cases = {}
    for kind in ("grapheme", "word", "sentence"):
        cases = load_cases(kind)
        all_cases[kind] = cases
        fn = BREAKS[kind]
        exact = 0
        tp = fp = fn_ = 0
        for text, expect in cases:
            got = fn(text)
            if got == expect:
                exact += 1
            gold_in = set(expect[1:-1])
            pred_in = set(got[1:-1])
            tp += len(gold_in & pred_in)
            fp += len(pred_in - gold_in)
            fn_ += len(gold_in - pred_in)
        p = tp / (tp + fp) if tp + fp else 1.0
        r = tp / (tp + fn_) if tp + fn_ else 1.0
        f1 = 2 * p * r / (p + r) if p + r else 1.0
        print(f"{kind:<10} {len(cases):>6} {exact:>6} {exact/len(cases):>9.2%} "
              f"{p:>7.4f} {r:>7.4f} {f1:>7.4f}")
    return all_cases


def eval_samples():
    section("B. Multilingual gold samples (hand-annotated)")
    print(f"{'id':<12} {'lang':<14} {'grapheme':>9} {'word':>6} {'sentence':>9}")
    totals = {k: [0, 0] for k in GOLD}  # kind -> [matches, total]
    for s in SAMPLES:
        marks = {}
        for kind, (key, fn) in GOLD.items():
            ok = fn(s["text"]) == s[key]
            marks[kind] = "OK" if ok else "FAIL"
            totals[kind][0] += ok
            totals[kind][1] += 1
        print(f"{s['id']:<12} {s['lang']:<14} {marks['grapheme']:>9} "
              f"{marks['word']:>6} {marks['sentence']:>9}")
    for kind in GOLD:
        m, t = totals[kind]
        print(f"  {kind:<9} accuracy: {m}/{t} = {m/t:.2%}")


def eval_invariance():
    section("C. Normalization order invariance (normalize-then-segment == segment-then-normalize)")
    texts = [s["text"] for s in SAMPLES]
    results = verify_order_invariance(texts, forms=FORMS)
    print("main samples (no compatibility characters):")
    print(f"{'form':<6} " + " ".join(f"{k:>10}" for k in KINDS))
    for form in FORMS:
        cells = []
        for kind in KINDS:
            sub = [r for r in results if r.form == form and r.kind == kind]
            ok = sum(r.ok for r in sub)
            cells.append(f"{ok}/{len(sub)}")
        print(f"{form:<6} " + " ".join(f"{c:>10}" for c in cells))
    bad = [r for r in results if not r.ok]
    print(f"main samples: {len(results) - len(bad)}/{len(results)} consistent"
          + ("" if not bad else f"  UNEXPECTED mismatches: {len(bad)}"))

    ctexts = [s["text"] for s in COMPAT_SAMPLES]
    cresults = verify_order_invariance(ctexts, forms=FORMS)
    print("compatibility-sensitive samples (NFKC/NFKD differences are expected):")
    for form in FORMS:
        sub = [r for r in cresults if r.form == form]
        ok = sum(r.ok for r in sub)
        print(f"  {form:<6} consistent {ok}/{len(sub)}")
    shown = 0
    for r in cresults:
        if not r.ok and shown < 3:
            s = COMPAT_SAMPLES[r.sample_index]
            print(f"    e.g. {s['id']} [{r.kind}/{r.form}] ({s['why']}): "
                  f"norm-first={r.normalize_first!r} seg-first={r.segment_first!r}")
            shown += 1


def eval_off_switch(all_cases):
    section("D. Switch-off identity (normalize_form=None == raw engines, per example)")
    raw_segments = {
        "grapheme": graphemes,
        "word": lambda t: list(iter_word_segments(t)),
        "sentence": split_sentences,
    }
    for kind in KINDS:
        total = same = 0
        for s in SAMPLES + COMPAT_SAMPLES:
            total += 1
            same += segment(s["text"], kind, None) == raw_segments[kind](s["text"])
        for text, _expect in all_cases[kind]:
            total += 1
            same += segment(text, kind, None) == raw_segments[kind](text)
        print(f"  {kind:<10} identical {same}/{total} examples"
              f" ({'OK' if same == total else 'MISMATCH'})")


def main():
    all_cases = eval_official()
    eval_samples()
    eval_invariance()
    eval_off_switch(all_cases)
    return 0


if __name__ == "__main__":
    sys.exit(main())
