"""
Tests for trie-accelerated dictionary.

Verifies that the trie dictionary produces identical results to SQLite-only
and tests performance improvements.
"""

import time
import unittest
from pathlib import Path

from tentoku.database_path import find_database_path
from tentoku.normalize import kana_to_hiragana


class TestTrieCorrectness(unittest.TestCase):
    """Verify trie produces identical results to SQLite-only."""

    @classmethod
    def setUpClass(cls):
        """Set up test database connections."""
        db_path = find_database_path()
        if not db_path:
            raise unittest.SkipTest("Database not found")

        cls.db_path = str(db_path)

        # Check if marisa-trie is available
        try:
            import marisa_trie
        except ImportError:
            raise unittest.SkipTest("marisa-trie not installed")

        from tentoku.sqlite_dict_optimized import OptimizedSQLiteDictionary
        from tentoku.trie_dict import TrieAcceleratedDictionary

        cls.sqlite_dict = OptimizedSQLiteDictionary(cls.db_path)
        cls.trie_dict = TrieAcceleratedDictionary(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        """Close database connections."""
        if hasattr(cls, 'sqlite_dict'):
            cls.sqlite_dict.close()
        if hasattr(cls, 'trie_dict'):
            cls.trie_dict.close()

    def test_identical_results_common_words(self):
        """Test common words return identical or superset results.

        The trie may return more results than SQLite because it indexes all forms
        (kanji and readings) and combines them, while SQLite queries one path first.
        """
        test_words = [
            "食べる", "見る", "東京", "日本語", "学生",
            "たべる", "みる", "がくせい",  # hiragana
            "タベル", "ミル",  # katakana
        ]

        for word in test_words:
            with self.subTest(word=word):
                trie_results = self.trie_dict.get_words(word, max_results=20)
                sqlite_results = self.sqlite_dict.get_words(word, max_results=20)

                trie_ids = set(e.entry_id for e in trie_results)
                sqlite_ids = set(e.entry_id for e in sqlite_results)

                # Trie should contain at least all SQLite results
                # (may contain more due to indexing both kanji and readings)
                self.assertTrue(sqlite_ids.issubset(trie_ids),
                    f"Trie missing entries for '{word}': missing={sqlite_ids - trie_ids}")

    def test_exists_function(self):
        """Test exists() function returns correct results."""
        # Words that should exist
        existing_words = ["食べる", "見る", "東京", "日本語"]
        for word in existing_words:
            with self.subTest(word=word):
                self.assertTrue(self.trie_dict.exists(word),
                    f"'{word}' should exist in dictionary")

        # Words that should not exist
        nonexistent_words = ["xxxx", "qqqqq", "あああああ123"]
        for word in nonexistent_words:
            with self.subTest(word=word):
                self.assertFalse(self.trie_dict.exists(word),
                    f"'{word}' should not exist in dictionary")

    def test_katakana_normalization(self):
        """Test katakana words are found via normalization."""
        # タベル should find same entry as たべる
        trie_katakana = self.trie_dict.get_words("タベル", max_results=5)
        trie_hiragana = self.trie_dict.get_words("たべる", max_results=5)

        katakana_ids = sorted(e.entry_id for e in trie_katakana)
        hiragana_ids = sorted(e.entry_id for e in trie_hiragana)

        self.assertEqual(katakana_ids, hiragana_ids,
            "Katakana and hiragana should return same entries")

    def test_nonexistent_words(self):
        """Test nonexistent words return empty results."""
        fake_words = ["あああああ", "xyz123", "qqqqq"]

        for word in fake_words:
            with self.subTest(word=word):
                self.assertEqual(self.trie_dict.get_words(word), [])
                self.assertFalse(self.trie_dict.exists(word))

    def test_homographs(self):
        """Test words with multiple entries (homographs)."""
        # 生 has many entries
        results = self.trie_dict.get_words("生", max_results=50)
        self.assertGreater(len(results), 1,
            "'生' should have multiple entries")

    def test_entry_structure(self):
        """Test that returned entries have correct structure."""
        entries = self.trie_dict.get_words("食べる", max_results=1)
        self.assertEqual(len(entries), 1)

        entry = entries[0]
        # Check entry has required fields
        self.assertIsNotNone(entry.entry_id)
        self.assertIsNotNone(entry.ent_seq)
        self.assertGreater(len(entry.kana_readings), 0)
        self.assertGreater(len(entry.senses), 0)
        self.assertGreater(len(entry.senses[0].glosses), 0)

    def test_batch_lookup(self):
        """Test batch lookup returns correct results."""
        texts = ["食べる", "見る", "東京"]
        results = self.trie_dict.get_words_batch(texts, max_results_per=5)

        self.assertEqual(len(results), 3)
        for text in texts:
            self.assertIn(text, results)
            self.assertGreater(len(results[text]), 0,
                f"'{text}' should have results in batch lookup")


class TestTrieTokenizationEquivalence(unittest.TestCase):
    """Verify full tokenization produces identical results."""

    @classmethod
    def setUpClass(cls):
        """Set up test database connections."""
        db_path = find_database_path()
        if not db_path:
            raise unittest.SkipTest("Database not found")

        cls.db_path = str(db_path)

        try:
            import marisa_trie
        except ImportError:
            raise unittest.SkipTest("marisa-trie not installed")

    def test_tokenization_identical(self):
        """Full tokenization should produce identical tokens."""
        from tentoku import tokenize
        from tentoku.sqlite_dict_optimized import OptimizedSQLiteDictionary
        from tentoku.trie_dict import TrieAcceleratedDictionary

        test_texts = [
            "私は学生です",
            "東京に行きました",
            "食べさせられませんでした",
            "彼女は美しい花を見ている",
        ]

        sqlite_dict = OptimizedSQLiteDictionary(self.db_path)
        trie_dict = TrieAcceleratedDictionary(self.db_path)

        try:
            for text in test_texts:
                with self.subTest(text=text):
                    sqlite_tokens = tokenize(text, sqlite_dict)
                    trie_tokens = tokenize(text, trie_dict)

                    # Compare token texts
                    sqlite_texts = [t.text for t in sqlite_tokens]
                    trie_texts = [t.text for t in trie_tokens]
                    self.assertEqual(sqlite_texts, trie_texts,
                        f"Token texts differ for '{text}'")

                    # Compare entry IDs
                    sqlite_ids = [t.dictionary_entry.entry_id if t.dictionary_entry else None
                                  for t in sqlite_tokens]
                    trie_ids = [t.dictionary_entry.entry_id if t.dictionary_entry else None
                                for t in trie_tokens]
                    self.assertEqual(sqlite_ids, trie_ids,
                        f"Entry IDs differ for '{text}'")
        finally:
            sqlite_dict.close()
            trie_dict.close()


class TestTrieCompleteness(unittest.TestCase):
    """Verify trie contains all dictionary entries."""

    @classmethod
    def setUpClass(cls):
        """Set up test connections."""
        db_path = find_database_path()
        if not db_path:
            raise unittest.SkipTest("Database not found")

        cls.db_path = str(db_path)

        try:
            import marisa_trie
        except ImportError:
            raise unittest.SkipTest("marisa-trie not installed")

        from tentoku.trie_dict import TrieAcceleratedDictionary
        cls.trie_dict = TrieAcceleratedDictionary(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        """Close connections."""
        if hasattr(cls, 'trie_dict'):
            cls.trie_dict.close()

    def test_sample_kanji_indexed(self):
        """Sample of kanji forms should be in trie."""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT DISTINCT kanji_text FROM kanji LIMIT 100")

        missing = []
        for (kanji_text,) in cursor:
            if not self.trie_dict.exists(kanji_text):
                missing.append(kanji_text)

        conn.close()
        self.assertEqual(missing, [], f"Missing kanji forms: {missing[:10]}")

    def test_sample_readings_indexed(self):
        """Sample of readings should be in trie."""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT DISTINCT reading_text FROM readings LIMIT 100")

        missing = []
        for (reading_text,) in cursor:
            if not self.trie_dict.exists(reading_text):
                # Also check normalized form
                normalized = kana_to_hiragana(reading_text)
                if not self.trie_dict.exists(normalized):
                    missing.append(reading_text)

        conn.close()
        self.assertEqual(missing, [], f"Missing readings: {missing[:10]}")


class TestTriePerformance(unittest.TestCase):
    """Test trie performance improvements."""

    @classmethod
    def setUpClass(cls):
        """Set up test connections."""
        db_path = find_database_path()
        if not db_path:
            raise unittest.SkipTest("Database not found")

        cls.db_path = str(db_path)

        try:
            import marisa_trie
        except ImportError:
            raise unittest.SkipTest("marisa-trie not installed")

        from tentoku.trie_dict import TrieAcceleratedDictionary
        cls.trie_dict = TrieAcceleratedDictionary(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        """Close connections."""
        if hasattr(cls, 'trie_dict'):
            cls.trie_dict.close()

    def test_exists_performance(self):
        """Test exists() is fast."""
        test_words = ["食べる", "見る", "東京", "日本語", "学生"] * 100

        start = time.perf_counter()
        for word in test_words:
            self.trie_dict.exists(word)
        elapsed = time.perf_counter() - start

        # 500 existence checks should complete in < 10ms
        self.assertLess(elapsed, 0.01,
            f"500 exists() checks took {elapsed*1000:.2f}ms, expected < 10ms")

    def test_lookup_performance(self):
        """Test get_words() is reasonably fast."""
        test_words = ["食べる", "見る", "東京", "日本語", "学生"]

        start = time.perf_counter()
        for word in test_words:
            self.trie_dict.get_words(word, max_results=10)
        elapsed = time.perf_counter() - start

        # 5 lookups should complete in < 50ms
        self.assertLess(elapsed, 0.05,
            f"5 get_words() calls took {elapsed*1000:.2f}ms, expected < 50ms")

    def test_tokenization_performance(self):
        """Test tokenization with trie dictionary meets performance target."""
        from tentoku import tokenize

        text = "私は毎日日本語を勉強しています"

        start = time.perf_counter()
        tokens = tokenize(text, self.trie_dict)
        elapsed = time.perf_counter() - start

        # Target: < 100ms for medium text
        self.assertLess(elapsed, 0.1,
            f"Tokenization took {elapsed*1000:.2f}ms, expected < 100ms")


if __name__ == '__main__':
    unittest.main()
