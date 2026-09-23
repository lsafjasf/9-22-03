# -*- coding: utf-8 -*-
"""Rule-by-rule tests for grapheme / word / sentence boundaries."""
import unittest

from textseg import graphemes, words, sentences, count_graphemes


EP = '\U0001F600'      # 😀 extended pictographic
MOD = '\U0001F3FD'     # 🏽 emoji modifier (GCB=Extend)
RI_A, RI_B, RI_C, RI_D = '\U0001F1E6', '\U0001F1E7', '\U0001F1E8', '\U0001F1E9'
ZWJ = '‍'
VS16 = '️'
KEYCAP = '⃣'
TAG_G = '\U000E0067'
TAG_END = '\U000E007F'


def g(text):
    return graphemes(text)


class GraphemeRules(unittest.TestCase):
    def test_GB1_GB2_sot_eot(self):
        self.assertEqual(g(''), [])
        self.assertEqual(g('a'), ['a'])

    def test_GB3_cr_lf(self):
        self.assertEqual(g('\r\n'), ['\r\n'])
        self.assertEqual(g('a\r\nb'), ['a', '\r\n', 'b'])

    def test_GB4_GB5_controls(self):
        self.assertEqual(g('a\x00b'), ['a', '\x00', 'b'])
        self.assertEqual(g('a\rb'), ['a', '\r', 'b'])
        self.assertEqual(g('a\nb'), ['a', '\n', 'b'])
        self.assertEqual(g('\x00\x01\x02'), ['\x00', '\x01', '\x02'])
        # controls break even around combining marks
        self.assertEqual(g('a\x00\u0301'), ['a', '\x00', '\u0301'])

    def test_GB6_hangul_L(self):
        self.assertEqual(g('\u1100\u1100\u1161'), ['\u1100\u1100\u1161'])
        self.assertEqual(g('\u1100\uAC00'), ['\u1100\uAC00'])
        self.assertEqual(g('\u1100\uAC01'), ['\u1100\uAC01'])

    def test_GB7_hangul_V(self):
        self.assertEqual(g('\u1161\u1161'), ['\u1161\u1161'])
        self.assertEqual(g('\uAC00\u1161'), ['\uAC00\u1161'])
        self.assertEqual(g('\u1161\u11A8'), ['\u1161\u11A8'])

    def test_GB8_hangul_T(self):
        self.assertEqual(g('\uAC01\u11A8'), ['\uAC01\u11A8'])
        self.assertEqual(g('\u11A8\u11A8'), ['\u11A8\u11A8'])

    def test_GB9_extend_zwj(self):
        self.assertEqual(g('a\u0301\u0302'), ['a\u0301\u0302'])
        self.assertEqual(g('a' + ZWJ), ['a' + ZWJ])
        self.assertEqual(g(ZWJ), [ZWJ])          # lone ZWJ
        self.assertEqual(g('\u0301'), ['\u0301'])  # lone combining mark

    def test_GB9_emoji_modifier(self):
        self.assertEqual(g('👍' + MOD), ['👍' + MOD])
        self.assertEqual(g(MOD), [MOD])          # lone modifier

    def test_GB9_tag_characters(self):
        flag = '\U0001F3F4' + TAG_G + '\U000E0062\U000E0065\U000E006E' + TAG_G + TAG_END
        self.assertEqual(g(flag), [flag])

    def test_GB9a_spacing_mark(self):
        self.assertEqual(g('க\u0BBE'), ['க\u0BBE'])   # ta + Mc vowel sign
        self.assertEqual(g('a\u0903'), ['a\u0903'])

    def test_GB9b_prepend(self):
        self.assertEqual(g('\u0600a'), ['\u0600a'])
        self.assertEqual(g('\u0600\u0601a'), ['\u0600\u0601a'])

    def test_GB11_zwj_sequence(self):
        family = '👨' + ZWJ + '👩' + ZWJ + '👧' + ZWJ + '👦'
        self.assertEqual(g(family), [family])
        kiss = '👩' + ZWJ + '❤' + VS16 + ZWJ + '💋' + ZWJ + '👩'
        self.assertEqual(g(kiss), [kiss])
        # ZWJ not preceded by ExtPict: no glue
        self.assertEqual(g('a' + ZWJ + '👩'), ['a' + ZWJ, '👩'])
        self.assertEqual(g('👩' + ZWJ + 'x'), ['👩' + ZWJ, 'x'])

    def test_GB12_GB13_regional_indicators(self):
        self.assertEqual(g(RI_A + RI_B), [RI_A + RI_B])
        self.assertEqual(g(RI_A + RI_B + RI_C), [RI_A + RI_B, RI_C])
        self.assertEqual(g(RI_A + RI_B + RI_C + RI_D), [RI_A + RI_B, RI_C + RI_D])
        self.assertEqual(g(RI_A), [RI_A])
        self.assertEqual(g('x' + RI_A + RI_B), ['x', RI_A + RI_B])

    def test_GB999_default_break(self):
        self.assertEqual(g('ab'), ['a', 'b'])
        self.assertEqual(g('中文字'), ['中', '文', '字'])

    def test_keycap_sequence(self):
        self.assertEqual(g('1' + VS16 + KEYCAP), ['1' + VS16 + KEYCAP])

    def test_long_combining_run(self):
        text = 'a' + '\u0301' * 5000
        self.assertEqual(g(text), [text])
        self.assertEqual(count_graphemes(text), 1)

    def test_incomplete_sequences(self):
        self.assertEqual(g('👩' + ZWJ), ['👩' + ZWJ])           # dangling ZWJ
        self.assertEqual(g(RI_A + RI_B + RI_C), [RI_A + RI_B, RI_C])
        self.assertEqual(g('a\r'), ['a', '\r'])                # trailing CR
        self.assertEqual(g('\u1100'), ['\u1100'])              # lone jamo


class WordRules(unittest.TestCase):
    def w(self, text):
        return words(text)

    def test_WB1_WB2(self):
        self.assertEqual(self.w(''), [])
        self.assertEqual(self.w('a'), ['a'])

    def test_WB3_crlf(self):
        self.assertEqual(self.w('a\r\nb'), ['a', '\r\n', 'b'])

    def test_WB3a_WB3b_newlines(self):
        self.assertEqual(self.w('a\nb'), ['a', '\n', 'b'])
        self.assertEqual(self.w('a\x85b'), ['a', '\x85', 'b'])
        self.assertEqual(self.w('a\u2029b'), ['a', '\u2029', 'b'])

    def test_WB3c_zwj_emoji(self):
        self.assertEqual(self.w('👩‍👩'), ['👩‍👩'])
        # after WB3c, ZWJ is ignored like Extend (WB4) -> single token
        self.assertEqual(self.w('a‍b'), ['a‍b'])

    def test_WB3d_spaces(self):
        self.assertEqual(self.w('a  b'), ['a', '  ', 'b'])

    def test_WB4_ignore_extend_format(self):
        self.assertEqual(self.w('ab\u0301c'), ['ab\u0301c'])
        self.assertEqual(self.w('a\u200bb'), ['a\u200bb'])  # ZWSP is Format

    def test_WB5_letters(self):
        self.assertEqual(self.w('hello'), ['hello'])
        self.assertEqual(self.w('héllo'), ['héllo'])

    def test_WB6_WB7_midletter(self):
        self.assertEqual(self.w("can't"), ["can't"])
        self.assertEqual(self.w('a.b'), ['a.b'])
        self.assertEqual(self.w('a:b'), ['a:b'])
        self.assertEqual(self.w('a.'), ['a', '.'])       # no letter after
        self.assertEqual(self.w('.a'), ['.', 'a'])

    def test_WB7a_WB7b_WB7c_hebrew(self):
        self.assertEqual(self.w('א\'ב'), ['א\'ב'])
        self.assertEqual(self.w('א"ב'), ['א"ב'])
        self.assertEqual(self.w('א\''), ['א\''])  # WB7a: Hebrew x Single_Quote

    def test_WB8_WB9_WB10_numeric(self):
        self.assertEqual(self.w('123'), ['123'])
        self.assertEqual(self.w('a1'), ['a1'])
        self.assertEqual(self.w('1a'), ['1a'])

    def test_WB11_WB12_midnum(self):
        self.assertEqual(self.w('3.5'), ['3.5'])
        self.assertEqual(self.w('1,000'), ['1,000'])
        self.assertEqual(self.w('3.'), ['3', '.'])
        self.assertEqual(self.w('.5'), ['.', '5'])

    def test_WB13_katakana(self):
        self.assertEqual(self.w('カタカナ'), ['カタカナ'])
        # WB13 glues Katakana only to Katakana
        self.assertEqual(self.w('カタカナa'), ['カタカナ', 'a'])

    def test_WB13a_WB13b_extendnumlet(self):
        self.assertEqual(self.w('a_b'), ['a_b'])
        self.assertEqual(self.w('a_1'), ['a_1'])
        self.assertEqual(self.w('_a'), ['_a'])

    def test_WB15_WB16_ri_pairs(self):
        self.assertEqual(self.w(RI_A + RI_B), [RI_A + RI_B])
        self.assertEqual(self.w(RI_A + RI_B + RI_C), [RI_A + RI_B, RI_C])

    def test_WB999_default(self):
        self.assertEqual(self.w('a,b'), ['a', ',', 'b'])
        self.assertEqual(self.w('中文'), ['中', '文'])  # ideographs: per-char


class SentenceRules(unittest.TestCase):
    def s(self, text):
        return sentences(text)

    def test_SB1_SB2(self):
        self.assertEqual(self.s(''), [])
        self.assertEqual(self.s('Hi'), ['Hi'])

    def test_SB3_SB4_crlf_sep(self):
        self.assertEqual(self.s('a.\r\nb.'), ['a.', '\r\n', 'b.'])
        self.assertEqual(self.s('a.\nb.'), ['a.', '\n', 'b.'])
        self.assertEqual(self.s('a.\u2029b.'), ['a.', '\u2029', 'b.'])

    def test_SB5_extend_transparent(self):
        self.assertEqual(self.s('Hi\u0301. There.'), ['Hi\u0301. ', 'There.'])

    def test_SB6_aterm_numeric(self):
        self.assertEqual(self.s('It is 3.5 kg.'), ['It is 3.5 kg.'])

    def test_SB7_upper_aterm_upper(self):
        self.assertEqual(self.s('A.B test.'), ['A.B test.'])
        # preceding char must be Upper: 'hi. Really' does break
        self.assertEqual(self.s('hi. Really.'), ['hi. ', 'Really.'])

    def test_SB8_aterm_lower(self):
        # SB8: ATerm Sp* x Lower -> no break, whole text is one sentence
        self.assertEqual(self.s('e.g. eggs.'), ['e.g. eggs.'])
        self.assertEqual(self.s('Mr. smith.'), ['Mr. smith.'])
        # ...but a break happens before a non-letter
        self.assertEqual(self.s('etc. (note).'), ['etc. ', '(note).'])

    def test_SB8a_scontinue(self):
        self.assertEqual(self.s('Wow!, he said.'), ['Wow!, he said.'])
        self.assertEqual(self.s('a?! b.'), ['a?! ', 'b.'])  # 'b' is not SContinue

    def test_SB9_SB10_close_sp_absorbed(self):
        self.assertEqual(self.s('He said "hi."  Next.'), ['He said "hi."  ', 'Next.'])
        self.assertEqual(self.s('Really?) Yes.'), ['Really?) ', 'Yes.'])

    def test_SB11_break_after_terminator(self):
        self.assertEqual(self.s('One. Two! Three?'), ['One. ', 'Two! ', 'Three?'])
        self.assertEqual(self.s('One。Two。'), ['One。', 'Two。'])

    def test_SB999_no_break(self):
        self.assertEqual(self.s('no terminator here'), ['no terminator here'])
        self.assertEqual(self.s('a,b;c:d'), ['a,b;c:d'])

    def test_sterm_vs_aterm(self):
        # STerm (!?) breaks before lower case, ATerm (.) does not
        self.assertEqual(self.s('Wait! really.'), ['Wait! ', 'really.'])
        self.assertEqual(self.s('e.g. really.'), ['e.g. really.'])  # SB8


class EdgeCases(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(graphemes(''), [])
        self.assertEqual(words(''), [])
        self.assertEqual(sentences(''), [])
        self.assertEqual(count_graphemes(''), 0)

    def test_pure_controls(self):
        text = '\x00\x01\x02\x7f'
        self.assertEqual(graphemes(text), list(text))
        self.assertEqual(count_graphemes(text), 4)

    def test_only_combining_marks(self):
        text = '\u0301\u0302\u0303'
        self.assertEqual(graphemes(text), [text])

    def test_lone_surrogate(self):
        text = 'a\ud800b'
        self.assertEqual(graphemes(text), ['a', '\ud800', 'b'])

    def test_mixed_stress(self):
        text = 'a\u0301👩‍👧🇦🇧क\r\n汉'
        self.assertEqual(graphemes(text),
                         ['a\u0301', '👩‍👧', '🇦🇧', 'क', '\r\n', '汉'])


if __name__ == '__main__':
    unittest.main()
