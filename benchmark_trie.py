#!/usr/bin/env python3
"""
Benchmark trie vs SQLite dictionary performance.

This script compares tokenization performance between the SQLite-only
dictionary and the trie-accelerated dictionary.

Usage:
    python -m tentoku.benchmark_trie
"""

import time
from statistics import mean, stdev

from tentoku import tokenize
from tentoku.database_path import find_database_path


def benchmark_tokenization():
    """Compare tokenization speed between SQLite and Trie dictionaries."""
    from tentoku.sqlite_dict_optimized import OptimizedSQLiteDictionary
    from tentoku.trie_dict import TrieAcceleratedDictionary

    db_path = find_database_path()
    if not db_path:
        print("Error: Database not found")
        return

    test_texts = [
        "私は学生です",
        "東京に行きました",
        "食べさせられませんでした",
        "彼女は美しい花を見ている",
        "私は毎日日本語を勉強しています。今日は新しい単語を覚えました。",
        "昨日、友達と一緒に映画を見に行きました。とても面白かったです。",
    ]

    print("Loading dictionaries...")
    sqlite_dict = OptimizedSQLiteDictionary(str(db_path))
    trie_dict = TrieAcceleratedDictionary(str(db_path))

    # Warmup
    print("Warming up...")
    for text in test_texts[:2]:
        tokenize(text, sqlite_dict)
        tokenize(text, trie_dict)

    # Benchmark SQLite
    print("\nBenchmarking SQLite dictionary...")
    sqlite_times = []
    for text in test_texts:
        start = time.perf_counter()
        tokens = tokenize(text, sqlite_dict)
        elapsed = time.perf_counter() - start
        sqlite_times.append(elapsed)
        print(f"  {text[:20]:20s} -> {elapsed*1000:7.2f}ms ({len(tokens)} tokens)")

    # Benchmark Trie
    print("\nBenchmarking Trie dictionary...")
    trie_times = []
    for text in test_texts:
        start = time.perf_counter()
        tokens = tokenize(text, trie_dict)
        elapsed = time.perf_counter() - start
        trie_times.append(elapsed)
        print(f"  {text[:20]:20s} -> {elapsed*1000:7.2f}ms ({len(tokens)} tokens)")

    sqlite_dict.close()
    trie_dict.close()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"SQLite: mean={mean(sqlite_times)*1000:.2f}ms, stdev={stdev(sqlite_times)*1000:.2f}ms")
    print(f"Trie:   mean={mean(trie_times)*1000:.2f}ms, stdev={stdev(trie_times)*1000:.2f}ms")

    if mean(trie_times) < mean(sqlite_times):
        speedup = mean(sqlite_times) / mean(trie_times)
        print(f"Speedup: {speedup:.1f}x faster")
    else:
        slowdown = mean(trie_times) / mean(sqlite_times)
        print(f"Slowdown: {slowdown:.1f}x slower")


def benchmark_lookups():
    """Compare raw lookup speed."""
    from tentoku.sqlite_dict_optimized import OptimizedSQLiteDictionary
    from tentoku.trie_dict import TrieAcceleratedDictionary

    db_path = find_database_path()
    if not db_path:
        print("Error: Database not found")
        return

    test_words = ["食べる", "見る", "東京", "日本語", "学生"] * 100

    sqlite_dict = OptimizedSQLiteDictionary(str(db_path))
    trie_dict = TrieAcceleratedDictionary(str(db_path))

    # Warmup
    for word in test_words[:10]:
        sqlite_dict.get_words(word, max_results=10)
        trie_dict.get_words(word, max_results=10)

    # Benchmark SQLite
    start = time.perf_counter()
    for word in test_words:
        sqlite_dict.get_words(word, max_results=10)
    sqlite_time = time.perf_counter() - start

    # Benchmark Trie
    start = time.perf_counter()
    for word in test_words:
        trie_dict.get_words(word, max_results=10)
    trie_time = time.perf_counter() - start

    # Benchmark Trie existence check only
    start = time.perf_counter()
    for word in test_words:
        trie_dict.exists(word)
    exists_time = time.perf_counter() - start

    sqlite_dict.close()
    trie_dict.close()

    print(f"\nRaw lookups ({len(test_words)} words):")
    print(f"SQLite:       {sqlite_time*1000:.2f}ms ({sqlite_time/len(test_words)*1000000:.1f}us/lookup)")
    print(f"Trie:         {trie_time*1000:.2f}ms ({trie_time/len(test_words)*1000000:.1f}us/lookup)")
    print(f"Trie exists:  {exists_time*1000:.2f}ms ({exists_time/len(test_words)*1000000:.1f}us/check)")


if __name__ == "__main__":
    benchmark_lookups()
    print()
    benchmark_tokenization()
