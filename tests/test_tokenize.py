"""
Tests for full tokenization.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tentoku import SQLiteDictionary, tokenize


class TestTokenize(unittest.TestCase):
    """Test tokenization functions."""
    
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
    
    def test_tokenize_simple_sentence(self):
        """Test tokenization of simple sentence."""
        text = "私は学生です"
        tokens = tokenize(text, self.dictionary)
        
        self.assertGreater(len(tokens), 0)
        # Verify all characters are covered
        total_length = sum(len(token.text) for token in tokens)
        self.assertGreaterEqual(total_length, len(text))
    
    def test_tokenize_with_conjugation(self):
        """Test tokenization with conjugated verbs."""
        text = "食べています"
        tokens = tokenize(text, self.dictionary)
        
        self.assertGreater(len(tokens), 0)
        # Should find at least one token with dictionary entry
        has_dict_entry = any(token.dictionary_entry for token in tokens)
        self.assertTrue(has_dict_entry, "Should find at least one dictionary entry")
    
    def test_tokenize_deinflection_reasons(self):
        """Test that deinflection reasons are preserved in tokens."""
        from tentoku._types import Reason
        
        # Test with a conjugated verb that should have deinflection reasons
        text = "食べました"
        tokens = tokenize(text, self.dictionary)
        
        # Find tokens with deinflection reasons
        tokens_with_reasons = [t for t in tokens if t.deinflection_reasons]
        
        # CRITICAL: The full word should be found as a single token
        # This test would have caught the POS tag matching bug
        full_word_token = next((t for t in tokens if t.text == text), None)
        self.assertIsNotNone(
            full_word_token,
            f"Expected '{text}' to be tokenized as a single token, but got: {[t.text for t in tokens]}"
        )
        self.assertIsNotNone(
            full_word_token.deinflection_reasons,
            f"Token '{full_word_token.text}' should have deinflection_reasons"
        )
        self.assertGreater(
            len(full_word_token.deinflection_reasons), 0,
            f"Token '{full_word_token.text}' should have at least one reason chain"
        )
        
        # Verify reasons are valid Reason enum values
        for chain in full_word_token.deinflection_reasons:
            for reason in chain:
                self.assertIsInstance(reason, (Reason, int))
    
    def test_tokenize_verb_forms(self):
        """Test tokenization preserves verb form information."""
        from tentoku._types import Reason
        
        test_cases = [
            ("食べました", Reason.PolitePast),
            ("食べている", Reason.Continuous),
            ("食べない", Reason.Negative),
        ]
        
        for text, expected_reason in test_cases:
            tokens = tokenize(text, self.dictionary)
            
            # CRITICAL: The full word should be found as a single token with the expected reason
            # This test would have caught the POS tag matching bug
            full_word_token = next((t for t in tokens if t.text == text), None)
            self.assertIsNotNone(
                full_word_token,
                f"Expected '{text}' to be tokenized as a single token, but got: {[t.text for t in tokens]}"
            )
            
            self.assertIsNotNone(
                full_word_token.deinflection_reasons,
                f"Token '{text}' should have deinflection_reasons"
            )
            
            # Check if the token has the expected reason
            found_reason = False
            for chain in full_word_token.deinflection_reasons:
                if expected_reason in chain:
                    found_reason = True
                    break
            
            self.assertTrue(
                found_reason,
                f"Token '{text}' should have {expected_reason.name} in deinflection_reasons. "
                f"Found: {[[Reason(r).name for r in chain] for chain in full_word_token.deinflection_reasons]}"
            )
        text = "食べています"
        tokens = tokenize(text, self.dictionary)
        
        self.assertGreater(len(tokens), 0)
        # Should find tokens
        self.assertTrue(any(token.dictionary_entry is not None for token in tokens))
    
    def test_tokenize_mixed_scripts(self):
        """Test tokenization with mixed scripts."""
        text = "日本語を勉強しています"
        tokens = tokenize(text, self.dictionary)
        
        self.assertGreater(len(tokens), 0)
    
    def test_tokenize_with_punctuation(self):
        """Test tokenization with punctuation."""
        text = "こんにちは。元気ですか？"
        tokens = tokenize(text, self.dictionary)
        
        self.assertGreater(len(tokens), 0)
    
    def test_tokenize_token_positions(self):
        """Test that token positions are correct."""
        text = "私は学生です"
        tokens = tokenize(text, self.dictionary)
        
        # Tokens should not overlap and should cover the text
        for i, token in enumerate(tokens):
            if i < len(tokens) - 1:
                next_token = tokens[i + 1]
                self.assertEqual(token.end, next_token.start)
        
        # First token should start at 0
        if tokens:
            self.assertEqual(tokens[0].start, 0)
        
        # Last token should end at text length
        if tokens:
            self.assertLessEqual(tokens[-1].end, len(text))


if __name__ == '__main__':
    unittest.main()

