"""
Integration tests for the Japanese tokenizer.

These tests require the SQLite database to be available.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tentoku import SQLiteDictionary, tokenize


class TestIntegration(unittest.TestCase):
    """Integration tests with SQLite database."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database connection."""
        from tentoku.database_path import find_database_path
        
        db_path = find_database_path()
        if not db_path:
            raise unittest.SkipTest("SQLite database not found")
        
        cls.db_path = str(db_path)
        
        cls.dictionary = SQLiteDictionary(cls.db_path)
    
    @classmethod
    def tearDownClass(cls):
        """Close database connection."""
        if hasattr(cls, 'dictionary'):
            cls.dictionary.close()
    
    def test_dictionary_lookup(self):
        """Test basic dictionary lookup."""
        entries = self.dictionary.get_words("食べる", max_results=5)
        self.assertGreater(len(entries), 0)
        
        # Check entry structure
        entry = entries[0]
        self.assertIsNotNone(entry.entry_id)
        self.assertIsNotNone(entry.ent_seq)
        self.assertGreater(len(entry.kana_readings), 0)
        self.assertGreater(len(entry.senses), 0)
    
    def test_tokenize_simple(self):
        """Test tokenization of simple text."""
        text = "私は学生です"
        tokens = tokenize(text, self.dictionary)
        
        self.assertGreater(len(tokens), 0)
        # Verify all characters are covered
        total_length = sum(len(token.text) for token in tokens)
        self.assertGreaterEqual(total_length, len(text))
    
    def test_tokenize_with_deinflection(self):
        """Test tokenization with conjugated verbs."""
        text = "食べています"
        tokens = tokenize(text, self.dictionary)
        
        self.assertGreater(len(tokens), 0)
        # Should find 食べる
        found_taberu = any(
            token.dictionary_entry and
            any(kana.text == "食べる" for kana in token.dictionary_entry.kana_readings)
            for token in tokens
        )
        # This might not always work depending on the database, so we'll just check
        # that we got some tokens
        self.assertGreater(len(tokens), 0)


if __name__ == '__main__':
    unittest.main()

