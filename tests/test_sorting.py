"""
Tests for result sorting.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tentoku.sorting import sort_word_results, get_priority_score, get_priority_sum
from tentoku._types import WordResult, WordEntry, KanjiReading, KanaReading, Sense, Gloss


class TestSorting(unittest.TestCase):
    """Test sorting functions."""
    
    def create_entry(self, entry_id, kanji_priority=None, kana_priority=None):
        """Helper to create a test entry."""
        kanji_readings = []
        if kanji_priority:
            kanji_readings.append(KanjiReading(text="test", priority=kanji_priority))
        else:
            kanji_readings.append(KanjiReading(text="test"))
        
        kana_readings = []
        if kana_priority:
            kana_readings.append(KanaReading(text="test", priority=kana_priority))
        else:
            kana_readings.append(KanaReading(text="test"))
        
        return WordEntry(
            entry_id=entry_id,
            ent_seq=str(entry_id),
            kanji_readings=kanji_readings,
            kana_readings=kana_readings,
            senses=[Sense(index=0, pos_tags=[], glosses=[Gloss(text="test")])]
        )
    
    def test_get_priority_score(self):
        """Test priority score calculation."""
        self.assertEqual(get_priority_score("i1"), 50)
        self.assertEqual(get_priority_score("n1"), 40)
        self.assertEqual(get_priority_score("s1"), 32)
        self.assertEqual(get_priority_score("g1"), 30)
        self.assertEqual(get_priority_score("i2"), 20)
        self.assertEqual(get_priority_score("nf01"), 47)  # 48 - 1/2
        self.assertEqual(get_priority_score("unknown"), 0)
    
    def test_get_priority_sum(self):
        """Test priority sum calculation."""
        # Single priority
        self.assertEqual(get_priority_sum(["i1"]), 50)
        
        # Multiple priorities (highest + fractions of others)
        result = get_priority_sum(["i1", "n1"])
        self.assertGreater(result, 50)
        # 50 + 40/10 = 54
        self.assertEqual(result, 54.0)
    
    def test_sort_by_deinflection_steps(self):
        """Test sorting by deinflection steps."""
        from tentoku._types import Reason
        
        entry1 = self.create_entry(1)
        entry2 = self.create_entry(2)
        
        result1 = WordResult(entry=entry1, match_len=5, reason_chains=[[Reason.Past]])
        result2 = WordResult(entry=entry2, match_len=5, reason_chains=[[Reason.Past, Reason.Negative]])
        
        results = [result2, result1]  # More steps first
        sorted_results = sort_word_results(results, "test")
        
        # Fewer steps should come first
        self.assertEqual(sorted_results[0].entry.entry_id, 1)
    
    def test_sort_by_priority(self):
        """Test sorting by priority."""
        entry1 = self.create_entry(1, kana_priority="i1")
        entry2 = self.create_entry(2, kana_priority="n1")
        
        result1 = WordResult(entry=entry1, match_len=5)
        result2 = WordResult(entry=entry2, match_len=5)
        
        results = [result2, result1]  # Lower priority first
        sorted_results = sort_word_results(results, "test")
        
        # Higher priority should come first
        self.assertEqual(sorted_results[0].entry.entry_id, 1)
    
    def test_sort_combined_criteria(self):
        """Test sorting with combined criteria."""
        from tentoku._types import Reason
        
        # Entry 1: fewer steps, lower priority
        entry1 = self.create_entry(1, kana_priority="n1")
        result1 = WordResult(entry=entry1, match_len=5, reason_chains=[[Reason.Past]])
        
        # Entry 2: more steps, higher priority
        entry2 = self.create_entry(2, kana_priority="i1")
        result2 = WordResult(entry=entry2, match_len=5, reason_chains=[[Reason.Past, Reason.Negative]])
        
        results = [result2, result1]
        sorted_results = sort_word_results(results, "test")
        
        # Fewer steps should win over priority
        self.assertEqual(sorted_results[0].entry.entry_id, 1)


if __name__ == '__main__':
    unittest.main()

