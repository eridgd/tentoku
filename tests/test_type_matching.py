"""
Tests for word type matching.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tentoku.type_matching import entry_matches_type
from tentoku._types import WordEntry, KanjiReading, KanaReading, Sense, Gloss, WordType


class TestTypeMatching(unittest.TestCase):
    """Test word type matching."""
    
    def create_entry(self, pos_tags):
        """Helper to create a test entry with POS tags."""
        sense = Sense(
            index=0,
            pos_tags=pos_tags,
            glosses=[Gloss(text="test", lang="eng")]
        )
        return WordEntry(
            entry_id=1,
            ent_seq="1",
            kanji_readings=[],
            kana_readings=[KanaReading(text="test")],
            senses=[sense]
        )
    
    def test_match_ichidan_verb(self):
        """Test matching ichidan verb."""
        entry = self.create_entry(["v1"])
        self.assertTrue(entry_matches_type(entry, WordType.IchidanVerb))
        
        entry = self.create_entry(["v1-s"])
        self.assertTrue(entry_matches_type(entry, WordType.IchidanVerb))
    
    def test_match_godan_verb(self):
        """Test matching godan verb."""
        entry = self.create_entry(["v5u"])
        self.assertTrue(entry_matches_type(entry, WordType.GodanVerb))
        
        entry = self.create_entry(["v4k"])
        self.assertTrue(entry_matches_type(entry, WordType.GodanVerb))
    
    def test_match_i_adj(self):
        """Test matching i-adjective."""
        entry = self.create_entry(["adj-i"])
        self.assertTrue(entry_matches_type(entry, WordType.IAdj))
    
    def test_match_kuru_verb(self):
        """Test matching kuru verb."""
        entry = self.create_entry(["vk"])
        self.assertTrue(entry_matches_type(entry, WordType.KuruVerb))
    
    def test_match_suru_verb(self):
        """Test matching suru verb."""
        entry = self.create_entry(["vs-i"])
        self.assertTrue(entry_matches_type(entry, WordType.SuruVerb))
        
        entry = self.create_entry(["vs-s"])
        self.assertTrue(entry_matches_type(entry, WordType.SuruVerb))
    
    def test_match_noun_vs(self):
        """Test matching noun or participle which takes suru."""
        # Code format (for compatibility)
        entry = self.create_entry(["vs"])
        self.assertTrue(entry_matches_type(entry, WordType.NounVS))
        
        # English format (as stored in actual database)
        entry = self.create_entry(["noun or participle which takes the aux. verb suru"])
        self.assertTrue(entry_matches_type(entry, WordType.NounVS))
        
        # Should not match other suru verb types
        entry = self.create_entry(["suru verb - included"])
        self.assertFalse(entry_matches_type(entry, WordType.NounVS))
    
    def test_no_match(self):
        """Test non-matching types."""
        entry = self.create_entry(["n"])
        self.assertFalse(entry_matches_type(entry, WordType.IchidanVerb))
        self.assertFalse(entry_matches_type(entry, WordType.GodanVerb))
        self.assertFalse(entry_matches_type(entry, WordType.IAdj))
        self.assertFalse(entry_matches_type(entry, WordType.NounVS))
    
    def test_multiple_pos_tags(self):
        """Test entry with multiple POS tags."""
        entry = self.create_entry(["v1", "n"])
        self.assertTrue(entry_matches_type(entry, WordType.IchidanVerb))
    
    def test_no_pos_tags(self):
        """Test entry with no POS tags."""
        entry = self.create_entry([])
        self.assertFalse(entry_matches_type(entry, WordType.IchidanVerb))
    
    def test_english_pos_tags(self):
        """Test matching with English POS tags (as stored in actual database)."""
        # Real database entries use English POS tags like "Ichidan verb"
        entry = self.create_entry(["Ichidan verb", "transitive verb"])
        self.assertTrue(entry_matches_type(entry, WordType.IchidanVerb))
        
        entry = self.create_entry(["Godan verb"])
        self.assertTrue(entry_matches_type(entry, WordType.GodanVerb))
        
        entry = self.create_entry(["adjective (keiyoushi)"])
        self.assertTrue(entry_matches_type(entry, WordType.IAdj))
        
        entry = self.create_entry(["Kuru verb - special class"])
        self.assertTrue(entry_matches_type(entry, WordType.KuruVerb))
        
        entry = self.create_entry(["suru verb - included"])
        self.assertTrue(entry_matches_type(entry, WordType.SuruVerb))
        
        entry = self.create_entry(["noun or participle which takes the aux. verb suru"])
        self.assertTrue(entry_matches_type(entry, WordType.NounVS))
    
    def test_real_database_entry(self):
        """Test type matching with a real database entry."""
        import unittest
        from tentoku.database_path import find_database_path
        from tentoku import SQLiteDictionary
        
        db_path = find_database_path()
        if not db_path:
            raise unittest.SkipTest("SQLite database not found")
        
        dictionary = SQLiteDictionary(str(db_path))
        try:
            # Get a real entry for 食べる
            entries = dictionary.get_words("食べる", max_results=1)
            if entries:
                entry = entries[0]
                # Should match IchidanVerb type
                self.assertTrue(
                    entry_matches_type(entry, WordType.IchidanVerb),
                    f"Real database entry should match IchidanVerb. POS tags: {[pos for sense in entry.senses for pos in sense.pos_tags]}"
                )
            
            # Test NounVS with a real entry that has the tag
            # Search for entries with NounVS tag
            entries = dictionary.get_words("する", max_results=10)
            if entries:
                # Find an entry with NounVS tag
                nounvs_entry = None
                for entry in entries:
                    all_pos = [pos for sense in entry.senses for pos in sense.pos_tags]
                    if any('noun or participle' in pos.lower() and 'suru' in pos.lower() for pos in all_pos):
                        nounvs_entry = entry
                        break
                
                if nounvs_entry:
                    self.assertTrue(
                        entry_matches_type(nounvs_entry, WordType.NounVS),
                        f"Real database entry should match NounVS. POS tags: {[pos for sense in nounvs_entry.senses for pos in sense.pos_tags]}"
                    )
        finally:
            dictionary.close()


if __name__ == '__main__':
    unittest.main()

