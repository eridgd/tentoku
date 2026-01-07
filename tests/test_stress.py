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
        cls.dictionary = SQLiteDictionary(db_path=cls.db_path)
    
    @classmethod
    def tearDownClass(cls):
        """Close database connection."""
        if hasattr(cls, 'dictionary'):
            cls.dictionary.close()
    
    def test_tokenize_performance_simple(self):
        """Test that simple tokenization completes in reasonable time."""
        text = "こんにちは"
        start = time.perf_counter()
        tokens = tokenize(text, self.dictionary)
        elapsed = time.perf_counter() - start
        self.assertIsInstance(tokens, list)
        # Should complete in under 100ms for simple text
        self.assertLess(elapsed, 0.1, f"Tokenization took {elapsed*1000:.2f}ms, expected < 100ms")
    
    def test_tokenize_performance_complex(self):
        """Test that complex tokenization completes in reasonable time."""
        text = "食べさせられませんでした"
        start = time.perf_counter()
        tokens = tokenize(text, self.dictionary)
        elapsed = time.perf_counter() - start
        self.assertIsInstance(tokens, list)
        # Should complete in under 500ms for complex text
        self.assertLess(elapsed, 0.5, f"Tokenization took {elapsed*1000:.2f}ms, expected < 500ms")
    
    def test_tokenize_throughput(self):
        """Test tokenization throughput with multiple texts."""
        texts = [
            "私は学生です",
            "食べました",
            "読んでいます",
            "今日は良い天気です",
            "東京タワーに行きました",
        ] * 10  # 50 texts total
        
        start = time.perf_counter()
        total_tokens = 0
        for text in texts:
            tokens = tokenize(text, self.dictionary)
            total_tokens += len(tokens)
        elapsed = time.perf_counter() - start
        
        # Should process at least 10 texts per second
        texts_per_sec = len(texts) / elapsed
        self.assertGreater(texts_per_sec, 10, 
                          f"Throughput: {texts_per_sec:.1f} texts/sec, expected > 10")
    
    def test_tokenize_performance_long_text(self):
        """Test that long text tokenization completes in reasonable time."""
        text = "私は毎日日本語を勉強しています。今日は新しい単語を覚えました。明日も続けます。" * 5
        start = time.perf_counter()
        tokens = tokenize(text, self.dictionary)
        elapsed = time.perf_counter() - start
        self.assertIsInstance(tokens, list)
        # Should complete in under 2 seconds for long text
        self.assertLess(elapsed, 2.0, f"Tokenization took {elapsed*1000:.2f}ms, expected < 2000ms")
    
    def test_tokenize_stress_many_operations(self):
        """Stress test: tokenize many different texts in sequence."""
        texts = [
            "私は学生です",
            "食べました",
            "読んでいます",
            "今日は良い天気です",
            "東京タワーに行きました",
            "食べさせられませんでした",
            "これは本です",
            "あれも本です",
            "それも本です",
        ] * 20  # 180 texts total
        
        start = time.perf_counter()
        for text in texts:
            tokens = tokenize(text, self.dictionary)
            # Verify we got results (basic sanity check)
            self.assertIsInstance(tokens, list)
        elapsed = time.perf_counter() - start
        
        # Should process at least 50 texts per second
        texts_per_sec = len(texts) / elapsed
        self.assertGreater(texts_per_sec, 50, 
                          f"Throughput: {texts_per_sec:.1f} texts/sec, expected > 50")
    
    def test_tokenize_stress_windowed(self):
        """Stress test: simulate hover-like scenario with overlapping windows."""
        long_text = "私は毎日日本語を勉強しています。今日は新しい単語を覚えました。明日も続けます。"
        window_size = 10
        num_windows = max(1, len(long_text) - window_size + 1)
        
        start = time.perf_counter()
        for i in range(num_windows):
            window_text = long_text[i:i + window_size]
            tokens = tokenize(window_text, self.dictionary)
            self.assertIsInstance(tokens, list)
        elapsed = time.perf_counter() - start
        
        # Should process at least 20 windows per second
        windows_per_sec = num_windows / elapsed
        self.assertGreater(windows_per_sec, 20,
                          f"Throughput: {windows_per_sec:.1f} windows/sec, expected > 20")
