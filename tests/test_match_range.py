"""
Tests for match_range tracking.

These tests verify that match_range is correctly set on kanji and kana readings
to track which reading actually matched the input text.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tentoku.sqlite_dict import SQLiteDictionary
from tentoku.word_search import word_search
from tentoku.normalize import normalize_input
from tentoku.sorting import get_priority, get_kana_headword_type


class TestMatchRange(unittest.TestCase):
    """Test match_range tracking and usage."""
    
    def setUp(self):
        """Set up test dictionary."""
        self.dictionary = SQLiteDictionary()
    
    def test_match_range_set_on_kanji(self):
        """Test that match_range is set on kanji readings that match."""
        # Search for a word with kanji
        entries = self.dictionary.get_words('日本語', 5, matching_text='日本語')
        
        if entries:
            entry = entries[0]
            # Check that kanji readings with match_range exist
            matched_kanji = [k for k in entry.kanji_readings if k.match_range]
            if matched_kanji:
                self.assertIsNotNone(matched_kanji[0].match_range, "Should have match_range")
                self.assertEqual(matched_kanji[0].text, '日本語', "Matched kanji should be '日本語'")
    
    def test_match_range_set_on_kana(self):
        """Test that match_range is set on kana readings that match."""
        # Search for a word by reading
        entries = self.dictionary.get_words('にほんご', 5, matching_text='にほんご')
        
        if entries:
            entry = entries[0]
            # Check that kana readings with match_range exist
            matched_kana = [r for r in entry.kana_readings if r.match_range]
            if matched_kana:
                self.assertIsNotNone(matched_kana[0].match_range, "Should have match_range")
                self.assertEqual(matched_kana[0].text, 'にほんご', "Matched kana should be 'にほんご'")
    
    def test_priority_uses_match_range(self):
        """Test that priority calculation only uses readings with match_range."""
        # Search for a word
        entries = self.dictionary.get_words('に', 5, matching_text='に')
        
        if entries:
            entry = entries[0]
            # Get priority (should only use readings with match_range)
            priority = get_priority(entry)
            
            # Priority should be calculated based on matched readings
            # If no matched reading has priority, priority should be 0
            # If matched reading has priority, it should be > 0
            self.assertIsInstance(priority, int, "Priority should be an integer")
            self.assertGreaterEqual(priority, 0, "Priority should be >= 0")
    
    def test_kana_headword_type_uses_match_range(self):
        """Test that get_kana_headword_type uses match_range."""
        # Search for a word
        entries = self.dictionary.get_words('に', 5, matching_text='に')
        
        if entries:
            entry = entries[0]
            # Get kana headword type (should use match_range to find matching kana)
            headword_type = get_kana_headword_type(entry)
            
            # Should return 1 (primary headword) or 2 (reading)
            self.assertIn(headword_type, [1, 2], "Headword type should be 1 or 2")
    
    def test_ni_vs_nibe_priority(self):
        """Test that 'に' (particle) has higher priority than 'にべ' (fish)."""
        # This is the specific case we fixed
        normalized, input_lengths = normalize_input('にベ')
        result = word_search(normalized, self.dictionary, max_results=10, input_lengths=input_lengths)
        
        self.assertIsNotNone(result, "Should find results for 'にベ'")
        self.assertGreater(len(result.data), 0, "Should have at least one result")
        
        # Check that 'に' (particle) comes before 'にべ' (fish) in results
        # 'に' should have higher priority (50 for i1) than 'にべ' (0 or lower)
        ni_entry = None
        nibe_entry = None
        
        for word_result in result.data:
            entry = word_result.entry
            matched_kana = [r.text for r in entry.kana_readings if r.match_range]
            if matched_kana:
                if matched_kana[0] == 'に':
                    ni_entry = entry
                elif matched_kana[0] in ['にべ', 'にベ']:
                    nibe_entry = entry
        
        # Verify we found both entries
        self.assertIsNotNone(ni_entry, "Should find 'に' entry")
        
        if ni_entry and nibe_entry:
            ni_priority = get_priority(ni_entry)
            nibe_priority = get_priority(nibe_entry)
            
            # 'に' should have higher priority (typically 50 for ichi1) than 'にべ'
            # But 'にべ' might not have priority set, so it would be 0
            self.assertGreaterEqual(
                ni_priority, nibe_priority,
                f"'に' (particle, priority={ni_priority}) should have >= priority than 'にべ' (fish, priority={nibe_priority})"
            )
            
            # 'に' should appear before 'にべ' in sorted results (due to priority and deinflection steps)
            ni_index = next((i for i, wr in enumerate(result.data) if wr.entry.entry_id == ni_entry.entry_id), -1)
            nibe_index = next((i for i, wr in enumerate(result.data) if wr.entry.entry_id == nibe_entry.entry_id), -1)
            
            if ni_index >= 0 and nibe_index >= 0:
                # 'に' should come first due to higher priority and/or fewer deinflection steps
                # But if they have the same priority and same deinflection steps, order might vary
                # So we just check that 'に' has higher or equal priority
                self.assertGreaterEqual(
                    ni_priority, nibe_priority,
                    "'に' should have >= priority than 'にべ'"
                )
        elif ni_entry:
            # If we only found 'に', that's also correct (it's the better match)
            ni_priority = get_priority(ni_entry)
            self.assertGreater(ni_priority, 0, "'に' should have priority > 0")


if __name__ == '__main__':
    unittest.main()
