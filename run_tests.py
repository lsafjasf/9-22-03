#!/usr/bin/env python3
"""Run the full test suite: rule tests, edge cases, official UCD conformance,
and the streaming-vs-whole differential."""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def main():
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.join(ROOT, "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    if not result.wasSuccessful():
        return 1
    print("\n--- streaming differential (tests/diff_stream.py) ---")
    proc = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "diff_stream.py")])
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
