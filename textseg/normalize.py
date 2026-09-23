"""Unicode normalization: canonical (NFC/NFD) and compatibility (NFKC/NFKD)
equivalence, built on the standard library's normalization tables.

Note: the project constraint forbids using the runtime's *segmentation*
facilities; normalization tables in unicodedata are not segmentation and
are used here as the canonical data source.
"""
import unicodedata

FORMS = ("NFC", "NFD", "NFKC", "NFKD")
CANONICAL_FORMS = ("NFC", "NFD")
COMPATIBILITY_FORMS = ("NFKC", "NFKD")


def _check(form):
    if form not in FORMS:
        raise ValueError(f"unknown normalization form {form!r}; expected one of {FORMS}")


def normalize(text, form="NFC"):
    """Normalize text to the given form (NFC/NFD/NFKC/NFKD)."""
    _check(form)
    return unicodedata.normalize(form, text)


def is_normalized(text, form="NFC"):
    _check(form)
    return unicodedata.is_normalized(form, text)


def canonical_equal(a, b):
    """True iff a and b are canonically equivalent (NFD-identical)."""
    return unicodedata.normalize("NFD", a) == unicodedata.normalize("NFD", b)


def compatibility_equal(a, b):
    """True iff a and b are compatibility equivalent (NFKC-identical)."""
    return unicodedata.normalize("NFKC", a) == unicodedata.normalize("NFKC", b)
