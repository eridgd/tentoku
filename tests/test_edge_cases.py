"""
Edge case tests for tokenization.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tentoku import SQLiteDictionary, tokenize
from tentoku.deinflect import deinflect


class TestEdgeCases(unittest.TestCase):
    """Test edge cases."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database connection."""
        from tentoku.database_path import find_database_path
        
        db_path = find_database_path()
        if not db_path:
            raise unittest.SkipTest("SQLite database not found")
        
        cls.db_path = str(db_path)
    
    def setUp(self):
        """Set up test."""
        if not self.db_path:
            self.skipTest("Database not available")
        self.dictionary = SQLiteDictionary(self.db_path)
    
    def tearDown(self):
        """Clean up."""
        if hasattr(self, 'dictionary'):
            self.dictionary.close()
    
    def test_empty_string(self):
        """Test empty string."""
        tokens = tokenize("", self.dictionary)
        self.assertEqual(len(tokens), 0)
    
    def test_single_character_hiragana(self):
        """Test single hiragana character."""
        tokens = tokenize("あ", self.dictionary)
        self.assertGreater(len(tokens), 0)
    
    def test_single_character_katakana(self):
        """Test single katakana character."""
        tokens = tokenize("ア", self.dictionary)
        self.assertGreater(len(tokens), 0)
    
    def test_single_character_kanji(self):
        """Test single kanji character."""
        tokens = tokenize("日", self.dictionary)
        self.assertGreater(len(tokens), 0)
    
    def test_mixed_japanese_english(self):
        """Test mixed Japanese and English."""
        text = "Hello こんにちは"
        tokens = tokenize(text, self.dictionary)
        self.assertGreater(len(tokens), 0)
    
    def test_numbers(self):
        """Test numbers."""
        text = "2024年"
        tokens = tokenize(text, self.dictionary)
        self.assertGreater(len(tokens), 0)
    
    def test_irregular_verbs(self):
        """Test irregular verbs."""
        # する
        candidates = deinflect("して")
        found_suru = any(c.word == "する" for c in candidates)
        self.assertTrue(found_suru)
        
        # 来る
        candidates = deinflect("来て")
        found_kuru = any(c.word == "来る" or c.word == "くる" for c in candidates)
        self.assertTrue(found_kuru)
    
    def test_multiple_conjugations(self):
        """Test multiple consecutive conjugations."""
        # 食べていません → 食べる
        candidates = deinflect("食べていません")
        found_taberu = any(c.word == "食べる" for c in candidates)
        self.assertTrue(found_taberu)
    
    def test_long_sentence(self):
        """Test long sentence."""
        text = "私は日本語を勉強しています。" * 10
        tokens = tokenize(text, self.dictionary)
        self.assertGreater(len(tokens), 0)


if __name__ == '__main__':
    unittest.main()

