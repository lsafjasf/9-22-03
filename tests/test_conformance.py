#!/usr/bin/env python3
"""Run the official UCD segmentation conformance tests.

Reads GraphemeBreakTest.txt / WordBreakTest.txt / SentenceBreakTest.txt
from tests/data/ (downloaded by tools/gen_tables.py).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from textseg import (
    grapheme_break_positions,
    word_break_positions,
    sentence_break_positions,
)

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def parse_test_line(line):
    """'÷ 0061 × 0308 ÷ 0060 ÷' -> (text, expected_break_offsets)."""
    tokens = line.split("#", 1)[0].split()
    cps = []
    expect = []
    pos = 0
    for tok in tokens:
        if tok == "÷":
            expect.append(pos)
        elif tok == "×":
            continue
        else:
            cps.append(int(tok, 16))
            pos += 1
    return "".join(chr(cp) for cp in cps), expect


def make_case(filename, breaks_fn):
    path = os.path.join(DATA, filename)
    if not os.path.exists(path):
        return None

    class ConformanceTest(unittest.TestCase):
        def test_all(self):
            failures = []
            total = 0
            with open(path, encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, 1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    text, expect = parse_test_line(line)
                    got = breaks_fn(text)
                    total += 1
                    if got != expect:
                        failures.append((lineno, line, expect, got))
                        if len(failures) >= 10:
                            break
            self.assertEqual(
                failures,
                [],
                f"{len(failures)}+ failures out of {total} cases; first: {failures[:3]}",
            )
        test_all.__doc__ = f"{filename}: all official cases"

    return ConformanceTest


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for fname, fn in (
        ("GraphemeBreakTest.txt", grapheme_break_positions),
        ("WordBreakTest.txt", word_break_positions),
        ("SentenceBreakTest.txt", sentence_break_positions),
    ):
        case = make_case(fname, fn)
        if case is not None:
            case.__name__ = "Test" + fname.replace(".txt", "")
            suite.addTests(loader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    unittest.main()
