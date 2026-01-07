"""
Stress and performance tests.
"""

import unittest
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tentoku import SQLiteDictionary, tokenize


class TestStress(unittest.TestCase):
    """Stress and performance tests."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database connection."""
        from tentoku.database_path import find_database_path
        
        db_path = find_database_path()
        if not db_path:
            raise unittest.SkipTest("SQLite database not found")
        
        cls.db_path = str(db_path)
