#!/usr/bin/env python3
"""Differential test: streaming segmentation must equal whole-text segmentation.

Covers:
  1. every official UCD conformance case, streamed with several chunk sizes
     (including 1-char chunks and seeded random chunking);
  2. randomized fuzz over a tricky alphabet (combining marks, emoji, ZWJ,
     regional indicators, Hangul jamo, Indic conjuncts, controls, CRLF),
     optionally normalized to NFC/NFD/NFKC/NFKD first.

Exit code 0 on success, 1 on any mismatch.
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from textseg import (
    grapheme_break_positions,
    word_break_positions,
    sentence_break_positions,
    normalize,
    StreamSegmenter,
)

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
BREAKS = {
    "grapheme": grapheme_break_positions,
    "word": word_break_positions,
    "sentence": sentence_break_positions,
}


def whole_segments(kind, text):
    bounds = BREAKS[kind](text)
    return [text[a:b] for a, b in zip(bounds, bounds[1:])]


def stream_segments(kind, text, chunk_sizes):
    st = StreamSegmenter(kind)
    out = []
    pos = 0
    i = 0
    while pos < len(text):
        w = chunk_sizes[i % len(chunk_sizes)]
        out.extend(st.feed(text[pos:pos + w]))
        pos += w
        i += 1
    out.extend(st.flush())
    return out


def check(kind, text, chunk_sizes, label, failures):
    want = whole_segments(kind, text)
    got = stream_segments(kind, text, chunk_sizes)
    if got != want:
        failures.append((label, kind, chunk_sizes, text, want, got))
        return False
    if "".join(got) != text:
        failures.append((label, kind, chunk_sizes, text, text, "".join(got)))
        return False
    return True


def parse_test_file(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            cps = [int(t, 16) for t in line.split() if t not in ("÷", "×")]
            yield "".join(chr(cp) for cp in cps)


def chunkings(rng, n):
    yield (1,)
    yield (2,)
    yield (3,)
    yield (7,)
    yield tuple(rng.randint(1, 9) for _ in range(64))


TRICKY = [
    "a", "b", "Z", "0", "5", " ", "\t", "\r", "\n", "\x00", "\u2028", "\u2029",
    "\u0301", "\u0327", "\u200D", "\u200B", "\u2060", "\uFE0F",
    "\u0600", "\u0903",
    "\U0001F468", "\U0001F469", "\U0001F44D", "\U0001F3FD", "\u231A",
    "\U0001F1E6", "\U0001F1E7", "\U0001F1E8",
    "\u1100", "\u1161", "\u11A8", "\uAC00", "\uAC01",
    "\u0915", "\u094D", "\u0937",
    ".", ",", "!", "?", "'", '"', ":", ";", "_",
    "\u05D0", "\u05D1", "\u30AB", "\u30BF",
    "\ud800",
]


def main():
    rng = random.Random(20260923)
    failures = []
    total = 0

    # 1) official conformance cases, streamed
    for kind, fname in (
        ("grapheme", "GraphemeBreakTest.txt"),
        ("word", "WordBreakTest.txt"),
        ("sentence", "SentenceBreakTest.txt"),
    ):
        path = os.path.join(DATA, fname)
        if not os.path.exists(path):
            print(f"SKIP {fname} (run tools/gen_tables.py first)")
            continue
        cases = list(parse_test_file(path))
        for text in cases:
            for sizes in chunkings(rng, len(text)):
                total += 1
                check(kind, text, sizes, fname, failures)
        print(f"{fname}: {len(cases)} cases x 5 chunkings checked")

    # 2) randomized fuzz, with optional normalization
    fuzz_n = 1500
    for it in range(fuzz_n):
        text = "".join(rng.choice(TRICKY) for _ in range(rng.randint(0, 60)))
        form = rng.choice([None, "NFC", "NFD", "NFKC", "NFKD"])
        if form:
            text = normalize(text, form)
        kind = rng.choice(list(BREAKS))
        sizes = tuple(rng.randint(1, 11) for _ in range(rng.randint(1, 8)))
        total += 1
        check(kind, text, sizes, f"fuzz#{it}({form})", failures)

    if failures:
        print(f"\nFAIL: {len(failures)} mismatches out of {total} checks")
        for label, kind, sizes, text, want, got in failures[:5]:
            print(f"  [{label}] kind={kind} sizes={sizes} text={text!r}")
            print(f"    want: {want[:8]}")
            print(f"    got : {got[:8]}")
        return 1
    print(f"OK: {total} streaming-vs-whole checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
