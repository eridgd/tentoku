"""
Comprehensive tests for yoon detection.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tentoku.yoon import ends_in_yoon


class TestYoon(unittest.TestCase):
    """Test yoon detection."""
    
    def test_ends_in_yoon_valid(self):
        """Test valid yoon endings."""
        self.assertTrue(ends_in_yoon("きゃ"))
        self.assertTrue(ends_in_yoon("しゅ"))
        self.assertTrue(ends_in_yoon("ちょ"))
        self.assertTrue(ends_in_yoon("にゃ"))
        self.assertTrue(ends_in_yoon("ひゅ"))
        self.assertTrue(ends_in_yoon("みょ"))
        self.assertTrue(ends_in_yoon("りゃ"))
        self.assertTrue(ends_in_yoon("ぎゃ"))
        self.assertTrue(ends_in_yoon("じゅ"))
        self.assertTrue(ends_in_yoon("びょ"))
        self.assertTrue(ends_in_yoon("ぴゃ"))
    
    def test_ends_in_yoon_invalid(self):
        """Test invalid endings (not yoon)."""
        self.assertFalse(ends_in_yoon("か"))
        self.assertFalse(ends_in_yoon("き"))
        self.assertFalse(ends_in_yoon("し"))
        # Note: ちゃ is actually a valid yoon (ち is in yoon_start)
        self.assertFalse(ends_in_yoon("た"))  # た is not in yoon_start
        self.assertFalse(ends_in_yoon("や"))
    
    def test_ends_in_yoon_empty_string(self):
        """Test empty string."""
        self.assertFalse(ends_in_yoon(""))
    
    def test_ends_in_yoon_single_character(self):
        """Test single character."""
        self.assertFalse(ends_in_yoon("き"))
        self.assertFalse(ends_in_yoon("ゃ"))
    
    def test_ends_in_yoon_longer_text(self):
        """Test yoon at end of longer text."""
        self.assertTrue(ends_in_yoon("日本語きゃ"))
        self.assertFalse(ends_in_yoon("日本語か"))


if __name__ == '__main__':
    unittest.main()

