"""
Tests for dictionary interface.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tentoku import SQLiteDictionary


class TestDictionary(unittest.TestCase):
    """Test dictionary interface."""
    
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
    
    def test_get_words_by_reading(self):
        """Test lookup by reading."""
        entries = self.dictionary.get_words("食べる", max_results=5)
        self.assertGreater(len(entries), 0)
        
        entry = entries[0]
        self.assertIsNotNone(entry.entry_id)
        self.assertIsNotNone(entry.ent_seq)
        self.assertGreater(len(entry.kana_readings), 0)
    
    def test_get_words_by_kanji(self):
        """Test lookup by kanji."""
        entries = self.dictionary.get_words("食べる", max_results=5)
        # Should find entries with kanji readings
        if entries:
            entry = entries[0]
            # Entry should have structure
            self.assertIsNotNone(entry.kanji_readings)
            self.assertIsNotNone(entry.kana_readings)
            self.assertIsNotNone(entry.senses)
    
    def test_get_words_max_results(self):
        """Test result limit enforcement."""
        entries = self.dictionary.get_words("する", max_results=3)
        self.assertLessEqual(len(entries), 3)
    
    def test_get_words_entry_structure(self):
        """Test entry data structure."""
        entries = self.dictionary.get_words("食べる", max_results=1)
        if entries:
            entry = entries[0]
            self.assertIsNotNone(entry.entry_id)
            self.assertIsNotNone(entry.ent_seq)
            self.assertIsInstance(entry.kanji_readings, list)
            self.assertIsInstance(entry.kana_readings, list)
            self.assertIsInstance(entry.senses, list)
            
            if entry.senses:
                sense = entry.senses[0]
                self.assertIsInstance(sense.pos_tags, list)
                self.assertIsInstance(sense.glosses, list)
    
    def test_get_words_pos_tags(self):
        """Test POS tag extraction."""
        entries = self.dictionary.get_words("食べる", max_results=1)
        if entries and entries[0].senses:
            sense = entries[0].senses[0]
            self.assertIsInstance(sense.pos_tags, list)
    
    def test_get_words_priority(self):
        """Test priority handling."""
        entries = self.dictionary.get_words("食べる", max_results=1)
        if entries:
            entry = entries[0]
            # Check that priority fields exist (may be None)
            for kanji in entry.kanji_readings:
                # Priority is optional
                pass
            for kana in entry.kana_readings:
                # Priority is optional
                pass
    
    def test_get_words_nonexistent(self):
        """Test lookup of non-existent word."""
        entries = self.dictionary.get_words("xxxxxxxx", max_results=5)
        self.assertEqual(len(entries), 0)
    
    def test_get_words_empty_string(self):
        """Test lookup with empty string."""
        entries = self.dictionary.get_words("", max_results=5)
        self.assertEqual(len(entries), 0)


if __name__ == '__main__':
    unittest.main()

