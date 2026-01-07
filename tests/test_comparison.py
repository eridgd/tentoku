"""
Automated comparison tests with baseline tokenization results.

These tests compare the Python tokenizer output against baseline results
generated from the 10ten Reader algorithm (for validation purposes).
"""

import unittest
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tentoku import SQLiteDictionary, tokenize


class TestComparison(unittest.TestCase):
    """Comparison tests with baseline."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database connection."""
        from tentoku.database_path import find_database_path
        
        db_path = find_database_path()
        if not db_path:
            raise unittest.SkipTest("SQLite database not found")
        
        cls.db_path = str(db_path)
