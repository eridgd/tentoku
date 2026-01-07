"""
Comprehensive tests for text variations.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tentoku.variations import expand_choon, kyuujitai_to_shinjitai


class TestVariations(unittest.TestCase):
    """Test text variation functions."""
    
    def test_expand_choon_basic(self):
        """Test basic choon expansion."""
        variations = expand_choon("コーヒー")
        self.assertGreater(len(variations), 0)
        # Should generate variations with different vowels
        self.assertTrue(any('あ' in v or 'い' in v or 'う' in v or 'え' in v or 'お' in v 
                          for v in variations))
    
    def test_expand_choon_no_choon(self):
        """Test choon expansion with no choon."""
        variations = expand_choon("コーヒ")
        # Should return empty list if no choon (ー is not in this string)
        # Note: コーヒ has ー, so let's use a string without it
        variations = expand_choon("コヒ")
        self.assertEqual(len(variations), 0)
    
    def test_expand_choon_multiple_choon(self):
        """Test choon expansion with multiple choon marks."""
        variations = expand_choon("コーヒー")
        # Should expand the first choon
        self.assertGreater(len(variations), 0)
    
    def test_kyuujitai_to_shinjitai_basic(self):
        """Test basic kyuujitai conversion."""
        self.assertEqual(kyuujitai_to_shinjitai("舊"), "旧")
        self.assertEqual(kyuujitai_to_shinjitai("體"), "体")
        self.assertEqual(kyuujitai_to_shinjitai("國"), "国")
        self.assertEqual(kyuujitai_to_shinjitai("學"), "学")
        self.assertEqual(kyuujitai_to_shinjitai("會"), "会")
    
    def test_kyuujitai_to_shinjitai_no_old_kanji(self):
        """Test kyuujitai conversion with no old kanji."""
        text = "日本語"
        result = kyuujitai_to_shinjitai(text)
        self.assertEqual(result, text)  # Should return unchanged
    
    def test_kyuujitai_to_shinjitai_mixed(self):
        """Test kyuujitai conversion with mixed content."""
        text = "舊體國"
        result = kyuujitai_to_shinjitai(text)
        self.assertEqual(result, "旧体国")
    
    def test_kyuujitai_to_shinjitai_with_hiragana(self):
        """Test kyuujitai conversion with hiragana."""
        text = "舊ひらがな"
        result = kyuujitai_to_shinjitai(text)
        self.assertEqual(result, "旧ひらがな")


if __name__ == '__main__':
    unittest.main()

