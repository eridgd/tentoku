#!/usr/bin/env python3
"""
Benchmark SQLite dictionary optimizations.

This compares the standard SQLiteDictionary vs FastSQLiteDictionary (Cython-optimized).
"""

import sys
import time
import statistics
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tentoku.sqlite_dict import SQLiteDictionary
from sqlite_dict_cy import FastSQLiteDictionary


def time_function(func, *args, iterations=100):
    """Time a function execution."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func(*args)
        end = time.perf_counter()
        times.append(end - start)
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'min': min(times),
        'max': max(times),
        'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
    }


def benchmark_sqlite_lookups():
    """Benchmark SQLite dictionary lookups."""
    print("=" * 70)
    print("SQLITE DICTIONARY OPTIMIZATION BENCHMARK")
    print("=" * 70)
    print("\nComparing: Standard SQLiteDictionary vs FastSQLiteDictionary (Cython)")

    # Initialize both dictionaries
    print("\nInitializing dictionaries...")
    std_dict = SQLiteDictionary()
    fast_dict = FastSQLiteDictionary()

    test_cases = [
        ("Common word", "食べる", 500),
        ("Kanji word", "日本語", 500),
        ("Hiragana", "たべる", 500),
        ("Katakana", "コーヒー", 500),
        ("Complex kanji", "勉強する", 500),
    ]

    total_std_time = 0
    total_fast_time = 0

    for name, word, iterations in test_cases:
        print(f"\n{name}: '{word}'")

        # Standard version
        std_time = time_function(std_dict.get_words, word, 7, iterations=iterations)

        # Fast Cython version
        fast_time = time_function(fast_dict.get_words, word, 7, iterations=iterations)

        speedup = std_time['mean'] / fast_time['mean']

        print(f"  Standard:    {std_time['mean']*1000:.3f} ms")
        print(f"  Fast (Cython): {fast_time['mean']*1000:.3f} ms")
        print(f"  Speedup:     {speedup:.2f}x")

        total_std_time += std_time['mean']
        total_fast_time += fast_time['mean']

    print("\n" + "=" * 70)
    overall_speedup = total_std_time / total_fast_time
    print(f"OVERALL SPEEDUP: {overall_speedup:.2f}x")
    print("=" * 70)

    # Close connections
    std_dict.close()
    fast_dict.close()

    return overall_speedup


def benchmark_cache_performance():
    """Benchmark cache performance."""
    print("\n" + "=" * 70)
    print("CACHE PERFORMANCE BENCHMARK")
    print("=" * 70)

    print("\nTesting repeated lookups (cache effectiveness)...")

    # Test with cache
    fast_dict = FastSQLiteDictionary(cache_size=1000)

    # Warm up cache
    test_words = ["食べる", "日本語", "たべる", "コーヒー", "勉強する"]
    for word in test_words:
        fast_dict.get_words(word, 7)

    # Benchmark cached lookups
    def cached_lookups():
        for word in test_words:
            fast_dict.get_words(word, 7)

    cached_time = time_function(cached_lookups, iterations=1000)

    # Test without cache
    fast_dict_no_cache = FastSQLiteDictionary(cache_size=0)

    def uncached_lookups():
        for word in test_words:
            fast_dict_no_cache.get_words(word, 7)

    uncached_time = time_function(uncached_lookups, iterations=1000)

    speedup = uncached_time['mean'] / cached_time['mean']

    print(f"\n  Uncached: {uncached_time['mean']*1000:.3f} ms")
    print(f"  Cached:   {cached_time['mean']*1000:.3f} ms")
    print(f"  Cache speedup: {speedup:.2f}x")

    fast_dict.close()
    fast_dict_no_cache.close()


if __name__ == '__main__':
    speedup = benchmark_sqlite_lookups()
    benchmark_cache_performance()

    print(f"\n✓ FastSQLiteDictionary provides {speedup:.2f}x speedup overall")
    print("\nOptimizations:")
    print("  - Cython-compiled lookups with reduced Python overhead")
    print("  - Result caching for repeated lookups")
    print("  - SQLite pragma optimizations (WAL mode, memory-mapped I/O)")
    print("  - Reduced object allocations in hot paths")
