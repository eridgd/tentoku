"""
Basic tests for the Japanese tokenizer.

These tests verify that the basic components work correctly.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tentoku.normalize import normalize_input, kana_to_hiragana
from tentoku.yoon import ends_in_yoon
from tentoku.variations import expand_choon, kyuujitai_to_shinjitai
from tentoku.deinflect import deinflect
from tentoku._types import WordType


class TestNormalize(unittest.TestCase):
    """Test normalization functions."""
    
    def test_normalize_input(self):
        """Test basic normalization."""
        text = "こんにちは"
        normalized, lengths = normalize_input(text)
        self.assertEqual(normalized, text)
        self.assertEqual(len(lengths), len(text) + 1)
    
    def test_kana_to_hiragana(self):
        """Test katakana to hiragana conversion."""
        self.assertEqual(kana_to_hiragana("カタカナ"), "かたかな")
        self.assertEqual(kana_to_hiragana("ひらがな"), "ひらがな")


class TestYoon(unittest.TestCase):
    """Test yoon detection."""
    
    def test_ends_in_yoon(self):
        """Test yoon detection."""
        self.assertTrue(ends_in_yoon("きゃ"))
        self.assertTrue(ends_in_yoon("しゅ"))
        self.assertTrue(ends_in_yoon("ちょ"))
        self.assertFalse(ends_in_yoon("か"))
        self.assertFalse(ends_in_yoon("き"))


class TestVariations(unittest.TestCase):
    """Test text variations."""
    
    def test_expand_choon(self):
        """Test choon expansion."""
        variations = expand_choon("コーヒー")
        self.assertGreater(len(variations), 0)
    
    def test_kyuujitai_to_shinjitai(self):
        """Test kyuujitai conversion."""
        self.assertEqual(kyuujitai_to_shinjitai("舊"), "旧")
        self.assertEqual(kyuujitai_to_shinjitai("體"), "体")
        self.assertEqual(kyuujitai_to_shinjitai("國"), "国")


class TestDeinflect(unittest.TestCase):
    """Test deinflection."""
    
    def test_deinflect_ichidan_verb(self):
        """Test deinflection of ichidan verb."""
        candidates = deinflect("食べて")
        self.assertGreater(len(candidates), 0)
        # Should find 食べる
        found_taberu = any(c.word == "食べる" for c in candidates)
        self.assertTrue(found_taberu)
    
    def test_deinflect_godan_verb(self):
        """Test deinflection of godan verb."""
        candidates = deinflect("読んで")
        self.assertGreater(len(candidates), 0)
        # Should find 読む
        found_yomu = any(c.word == "読む" for c in candidates)
        self.assertTrue(found_yomu)
    
    def test_deinflect_i_adj(self):
        """Test deinflection of i-adjective."""
        candidates = deinflect("高く")
        self.assertGreater(len(candidates), 0)
        # Should find 高い
        found_takai = any(c.word == "高い" for c in candidates)
        self.assertTrue(found_takai)


if __name__ == '__main__':
    unittest.main()

