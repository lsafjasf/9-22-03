"""Demo CLI: python3 -m textseg [TEXT]"""
import sys

from . import graphemes, words, split_sentences, normalize, UNICODE_VERSION


def main(argv):
    text = " ".join(argv[1:]) if len(argv) > 1 else (
        "Sóme 👨‍👩‍👧‍👦 text, isn't it? 3.14 rocks! 🇨🇳🇺🇸 yes."
    )
    print(f"textseg demo (Unicode {UNICODE_VERSION})")
    print(f"input    : {text!r}")
    print(f"graphemes: {graphemes(text)}")
    print(f"words    : {words(text)}")
    print(f"sentences: {split_sentences(text)}")
    print(f"NFC/NFD  : {normalize(text, 'NFC')!r} / {normalize(text, 'NFD')!r}")


if __name__ == "__main__":
    main(sys.argv)
