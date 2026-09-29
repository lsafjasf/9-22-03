"""Multilingual gold samples for boundary-accuracy evaluation and
normalization-order invariance checks.

Each sample carries hand-annotated expectations:
  graphemes : extended grapheme clusters
  words     : word-like segments (textseg.words semantics)
  sentences : sentence segments (textseg.split_sentences semantics)

SAMPLES are stable under all four normalization forms (boundaries are
invariant under NFC/NFD/NFKC/NFKD on them).  COMPAT_SAMPLES contain
compatibility characters whose NFKC/NFKD mapping legitimately changes
boundaries (e.g. U+FB01 -> "fi"); they document where compatibility
normalization is expected to differ.
"""

_FR = "Café crème brûlée, s'il vous plaît."
_FR_NFD = "Café crème brûlée, s'il vous plaît."
_KO = "한글은 과학적이다."
_KO_JAMO = "한글은 과학적이다."
_AR = "\u0623\u064e\u0647\u0652\u0644\u0627\u064b \u0628\u0650\u0643\u064f\u0645\u0652."
_HI = "क्षत्रिय हिंदी बोलता है।"
_TH = "ภาษาไทยสนุกมาก"
_EMOJI = "👨‍👩‍👧‍👦 family 🇨🇳👍🏽!"

SAMPLES = [
    {
        "id": "fr-nfc",
        "lang": "French",
        "note": "composed accents (NFC)",
        "text": _FR,
        "graphemes": list(_FR),
        "words": ["Café", "crème", "brûlée", "s'il", "vous", "plaît"],
        "sentences": [_FR],
    },
    {
        "id": "fr-nfd",
        "lang": "French",
        "note": "decomposed accents (NFD), canonically equal to fr-nfc",
        "text": _FR_NFD,
        "graphemes": [
            "C", "a", "f", "é", " ",
            "c", "r", "è", "m", "e", " ",
            "b", "r", "û", "l", "é", "e", ",", " ",
            "s", "'", "i", "l", " ",
            "v", "o", "u", "s", " ",
            "p", "l", "a", "î", "t", ".",
        ],
        "words": ["Café", "crème", "brûlée", "s'il", "vous", "plaît"],
        "sentences": [_FR_NFD],
    },
    {
        "id": "de",
        "lang": "German",
        "note": "eszett, umlauts, two sentences",
        "text": "Straße, Müller! Grüße dich.",
        "graphemes": list("Straße, Müller! Grüße dich."),
        "words": ["Straße", "Müller", "Grüße", "dich"],
        "sentences": ["Straße, Müller! ", "Grüße dich."],
    },
    {
        "id": "el",
        "lang": "Greek",
        "note": "monotonic Greek with tonos",
        "text": "Σίσυφος ήταν εκεί.",
        "graphemes": list("Σίσυφος ήταν εκεί."),
        "words": ["Σίσυφος", "ήταν", "εκεί"],
        "sentences": ["Σίσυφος ήταν εκεί."],
    },
    {
        "id": "ru",
        "lang": "Russian",
        "note": "Cyrillic, two sentences",
        "text": "Привет, мир! Как дела?",
        "graphemes": list("Привет, мир! Как дела?"),
        "words": ["Привет", "мир", "Как", "дела"],
        "sentences": ["Привет, мир! ", "Как дела?"],
    },
    {
        "id": "ar",
        "lang": "Arabic",
        "note": "combining harakat (fatha/sukun/tanwin)",
        "text": _AR,
        "graphemes": ["\u0623\u064e", "\u0647\u0652", "\u0644", "\u0627\u064b", " ", "\u0628\u0650", "\u0643\u064f", "\u0645\u0652", "."],
        "words": ["\u0623\u064e\u0647\u0652\u0644\u0627\u064b", "\u0628\u0650\u0643\u064f\u0645\u0652"],
        "sentences": [_AR],
    },
    {
        "id": "he",
        "lang": "Hebrew",
        "note": "Hebrew letters",
        "text": "שלום עולם.",
        "graphemes": list("שלום עולם."),
        "words": ["שלום", "עולם"],
        "sentences": ["שלום עולם."],
    },
    {
        "id": "hi",
        "lang": "Hindi",
        "note": "Devanagari conjunct क्ष, spacing marks, danda",
        "text": _HI,
        "graphemes": [
            "क्ष", "त्रि", "य", " ",
            "हिं", "दी", " ",
            "बो", "ल", "ता", " ",
            "है", "।",
        ],
        "words": ["क्षत्रिय", "हिंदी", "बोलता", "है"],
        "sentences": [_HI],
    },
    {
        "id": "ko",
        "lang": "Korean",
        "note": "precomposed Hangul syllables (NFC)",
        "text": _KO,
        "graphemes": list(_KO),
        "words": ["한글은", "과학적이다"],
        "sentences": [_KO],
    },
    {
        "id": "ko-jamo",
        "lang": "Korean",
        "note": "conjoining jamo (NFD), canonically equal to ko",
        "text": _KO_JAMO,
        "graphemes": ["한", "글", "은", " ", "과", "학", "적", "이", "다", "."],
        "words": ["한글은", "과학적이다"],
        "sentences": [_KO_JAMO],
    },
    {
        "id": "ja",
        "lang": "Japanese",
        "note": "hiragana/katakana, composed ガ (U+30AC)",
        "text": "これはペンです。ガムです。",
        "graphemes": list("これはペンです。ガムです。"),
        "words": ["ペン", "ガム"],
        "sentences": ["これはペンです。", "ガムです。"],
    },
    {
        "id": "ja-nfd",
        "lang": "Japanese",
        "note": "decomposed カ+゙(U+3099), canonically equal to ja",
        "text": "これはペンです。ガムです。",
        "graphemes": ["こ", "れ", "は", "ペ", "ン", "で", "す", "。", "ガ", "ム", "で", "す", "。"],
        "words": ["ペン", "ガム"],
        "sentences": ["これはペンです。", "ガムです。"],
    },
    {
        "id": "zh",
        "lang": "Chinese",
        "note": "Han ideographs, ideographic full stop",
        "text": "这是中文句子。还有一句。",
        "graphemes": list("这是中文句子。还有一句。"),
        "words": [],
        "sentences": ["这是中文句子。", "还有一句。"],
    },
    {
        "id": "th",
        "lang": "Thai",
        "note": "below-base vowel sign (U+0E38) joins its base",
        "text": _TH,
        "graphemes": ["ภ", "า", "ษ", "า", "ไ", "ท", "ย", "ส", "นุ", "ก", "ม", "า", "ก"],
        "words": [],
        "sentences": [_TH],
    },
    {
        "id": "emoji",
        "lang": "Emoji/mixed",
        "note": "ZWJ family, RI flag, skin-tone modifier",
        "text": _EMOJI,
        "graphemes": [
            "👨‍👩‍👧‍👦", " ",
            "f", "a", "m", "i", "l", "y", " ",
            "🇨🇳", "👍🏽", "!",
        ],
        "words": ["family"],
        "sentences": [_EMOJI],
    },
    {
        "id": "mixed-num",
        "lang": "Mixed/numbers",
        "note": "decimal/group separators, apostrophe, Greek letter",
        "text": "3.14 is π, isn't it? 1,000.5 ok.",
        "graphemes": list("3.14 is π, isn't it? 1,000.5 ok."),
        "words": ["3.14", "is", "π", "isn't", "it", "1,000.5", "ok"],
        "sentences": ["3.14 is π, isn't it? ", "1,000.5 ok."],
    },
]

# Compatibility-sensitive samples: NFKC/NFKD legitimately change boundaries
# (ligature expansion, fullwidth folding, superscripts).  No gold here;
# they are used to demonstrate/report expected order-of-operation diffs.
COMPAT_SAMPLES = [
    {"id": "compat-ligature", "text": "ﬁle ①②", "why": "U+FB01 -> 'fi', circled digits -> '1','2'"},
    {"id": "compat-fullwidth", "text": "Ｗｉｄｅ ｔｅｘｔ", "why": "fullwidth -> ASCII"},
    {"id": "compat-superscript", "text": "x²+y²", "why": "superscript two -> '2'"},
]

__all__ = ["SAMPLES", "COMPAT_SAMPLES"]
