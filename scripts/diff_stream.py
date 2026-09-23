#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Differential test: streaming segmentation vs batch segmentation.

Generates tricky + random texts, feeds them through the streaming segmenters
in random chunkings, and compares against batch segmentation of the whole
text.  Also cross-checks textseg.normalize against unicodedata.normalize on
random strings, and verifies segmentation invariance across NFC/NFD forms.

Usage:  python3 scripts/diff_stream.py [--iterations N] [--seed S]
Exit code 0 = all consistent, 1 = mismatch found.
"""
import argparse
import os
import random
import sys
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from textseg import graphemes, words, sentences
from textseg.normalization import normalize
from textseg.stream import GraphemeStream, WordStream, SentenceStream

ALPHABET = [
    'a', 'B', 'z', '1', '9', ' ', '  ', '.', ',', '?', '!', '"', "'", ')',
    ':', ';', '。', '！', '？', '́', '̃', '्', 'ि',
    '👩', '👦', '👍', '🏽', '‍', '❤', '️', '🇦', '🇧', '🇨',
    '中', '文', 'カ', 'タ', 'あ', 'か', '한', '글', 'ᄒ', 'ᅡ', 'ᆫ',
    '\r', '\n', '\t', ' ', '\x00', 'क', 'ि', 'έ', 'é', 'ﬁ',
    '①', 'Ａ', '_', '3.5', "can't", 'Mr.', 'e.g.',
]

FIXED = [
    '',
    '👩‍👩‍👧‍👦 family 👍🏽 🇨🇳🇯🇵🇰🇷',
    'Mr. Smith paid 3.5 kg. Really? "Yes!"  (He did.)',
    'a' + '́' * 200 + 'b',
    'x. ' * 100,
    '한국어 한국어',
    'कषि क्‍ष',
    'trailing CR\r',
    'spaces   \r\n\r\nend.',
    'e.g. this. i.e. that. Wait! really. etc. (note).',
]


def random_text(rng, maxlen=120):
    return ''.join(rng.choice(ALPHABET) for _ in range(rng.randrange(maxlen)))


def random_chunks(rng, text):
    chunks = []
    i = 0
    while i < len(text):
        n = rng.randrange(1, max(2, len(text) - i + 1))
        chunks.append(text[i:i + n])
        i += n
    return chunks


def run_stream(cls, chunks):
    s = cls()
    out = []
    for c in chunks:
        out.extend(s.feed(c))
    out.extend(s.flush())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--iterations', type=int, default=300)
    ap.add_argument('--seed', type=int, default=20260923)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    failures = 0
    checks = 0

    texts = list(FIXED) + [random_text(rng) for _ in range(args.iterations)]

    for text in texts:
        for trial in range(4):
            chunks = random_chunks(rng, text)
            for cls, batch, name in ((GraphemeStream, graphemes, 'grapheme'),
                                     (WordStream, words, 'word'),
                                     (SentenceStream, sentences, 'sentence')):
                got = run_stream(cls, chunks)
                want = batch(text)
                checks += 1
                if got != want:
                    failures += 1
                    print('MISMATCH [%s] text=%r chunks=%r' % (name, text, chunks))
                    print('  stream: %r' % (got[:8],))
                    print('  batch : %r' % (want[:8],))
                if ''.join(got) != text:
                    failures += 1
                    print('LOSSY [%s] text=%r' % (name, text))

    # normalization oracle + invariance
    for text in texts:
        for form in ('NFC', 'NFD', 'NFKC', 'NFKD'):
            checks += 1
            if normalize(text, form) != unicodedata.normalize(form, text):
                failures += 1
                print('NORMALIZE MISMATCH [%s] text=%r' % (form, text))
        for form in ('NFC', 'NFD'):
            alt = normalize(text, form)
            for seg, name in ((graphemes, 'grapheme'), (words, 'word'),
                              (sentences, 'sentence')):
                checks += 1
                base, other = seg(text), seg(alt)
                if len(base) != len(other) or any(
                        normalize(a, 'NFC') != normalize(b, 'NFC')
                        for a, b in zip(base, other)):
                    failures += 1
                    print('INVARIANCE MISMATCH [%s/%s] text=%r' % (name, form, text))

    print('diff_stream: %d checks, %d failures (seed=%d, iterations=%d)'
          % (checks, failures, args.seed, args.iterations))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
