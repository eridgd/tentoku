"""
Comprehensive tests for text normalization.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tentoku.normalize import (
    normalize_input, kana_to_hiragana, half_to_full_width_num
)


class TestNormalize(unittest.TestCase):
    """Test normalization functions."""
    
    def test_normalize_input_basic(self):
        """Test basic normalization."""
        text = "こんにちは"
        normalized, lengths = normalize_input(text)
        self.assertEqual(normalized, text)
        self.assertEqual(len(lengths), len(text) + 1)
    
    def test_normalize_input_fullwidth_numbers(self):
        """Test full-width number conversion."""
        text = "123"
        normalized, _ = normalize_input(text, make_numbers_full_width=True)
        # Should convert to full-width
        self.assertNotEqual(normalized, text)
        self.assertTrue(all(ord(c) >= 0xFF10 for c in normalized if c.isdigit()))
    
    def test_normalize_input_zwnj_stripping(self):
        """Test ZWNJ stripping."""
        # ZWNJ is 0x200C
        text_with_zwnj = "こ\u200cん\u200cに\u200cち\u200cは"
        normalized, lengths = normalize_input(text_with_zwnj, strip_zwnj=True)
        self.assertNotIn('\u200c', normalized)
        self.assertEqual(normalized, "こんにちは")
    
    def test_normalize_input_empty_string(self):
        """Test empty string normalization."""
        normalized, lengths = normalize_input("")
        self.assertEqual(normalized, "")
        # Should have at least one element (final position at 0)
        self.assertGreaterEqual(len(lengths), 1)
    
    def test_normalize_input_surrogate_pairs(self):
        """Test normalization with surrogate pairs (non-BMP characters)."""
        # U+20B9F (𠏹) is a non-BMP character
        text = "𠏹沢"
        normalized, lengths = normalize_input(text)
        self.assertEqual(normalized, text)
        # Lengths should account for surrogate pairs (𠏹 takes 2 UTF-16 code units)
        # So we should have at least len(text) + 1 elements
        self.assertGreaterEqual(len(lengths), len(text) + 1)
    
    def test_kana_to_hiragana_katakana(self):
        """Test katakana to hiragana conversion."""
        self.assertEqual(kana_to_hiragana("カタカナ"), "かたかな")
        self.assertEqual(kana_to_hiragana("アイウエオ"), "あいうえお")
        self.assertEqual(kana_to_hiragana("コンピュータ"), "こんぴゅーた")
    
    def test_kana_to_hiragana_hiragana(self):
        """Test that hiragana remains unchanged."""
        self.assertEqual(kana_to_hiragana("ひらがな"), "ひらがな")
        self.assertEqual(kana_to_hiragana("あいうえお"), "あいうえお")
    
    def test_kana_to_hiragana_mixed(self):
        """Test mixed kana conversion."""
        self.assertEqual(kana_to_hiragana("カタカナとひらがな"), "かたかなとひらがな")
    
    def test_kana_to_hiragana_special_katakana(self):
        """Test special katakana characters."""
        # ヷ, ヸ, ヹ, ヺ
        self.assertEqual(kana_to_hiragana("ヷ"), "わ")
        self.assertEqual(kana_to_hiragana("ヸ"), "ゐ")
        self.assertEqual(kana_to_hiragana("ヹ"), "ゑ")
        self.assertEqual(kana_to_hiragana("ヺ"), "を")
    
    def test_half_to_full_width_num(self):
        """Test half-width to full-width number conversion."""
        self.assertEqual(half_to_full_width_num("123"), "１２３")
        self.assertEqual(half_to_full_width_num("0"), "０")
        self.assertEqual(half_to_full_width_num("9"), "９")
        # Non-digits should remain unchanged
        self.assertEqual(half_to_full_width_num("abc"), "abc")
        self.assertEqual(half_to_full_width_num("日本語"), "日本語")


if __name__ == '__main__':
    unittest.main()

