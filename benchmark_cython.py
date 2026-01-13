#!/usr/bin/env python3
"""
Performance benchmark comparing Python and Cython implementations.

This benchmark suite measures the performance gains from Cython optimization,
especially focusing on long texts where the speed difference is most apparent.
"""

import sys
import time
import statistics
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import Python versions
from tentoku import deinflect as deinflect_py
from tentoku import normalize as normalize_py
from tentoku import variations as variations_py
from tentoku import yoon as yoon_py

# Import Cython versions
from tentoku import deinflect_cy
from tentoku import normalize_cy
from tentoku import variations_cy
from tentoku import yoon_cy


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


def benchmark_normalize(iterations=1000):
    """Benchmark normalize functions."""
    print("\n" + "=" * 70)
    print("NORMALIZE BENCHMARK")
    print("=" * 70)

    test_cases = [
        ("Short", "私は学生です"),
        ("Medium", "今日は良い天気ですね。明日も晴れるといいですね。"),
        ("Long", "私は毎日日本語を勉強しています。今日は新しい単語を覚えました。明日も続けます。日本語はとても難しいですが、楽しいです。頑張ります。" * 5),
        ("Very Long", "これはテストです。あれもテストです。それもテストです。どれもテストです。" * 20),
    ]

    for name, text in test_cases:
        print(f"\n{name} text ({len(text)} chars):")

        # normalize_input
        py_time = time_function(normalize_py.normalize_input, text, iterations=iterations)
        cy_time = time_function(normalize_cy.normalize_input, text, iterations=iterations)
        speedup = py_time['mean'] / cy_time['mean']
        print(f"  normalize_input:")
        print(f"    Python:  {py_time['mean']*1000:.3f} ms")
        print(f"    Cython:  {cy_time['mean']*1000:.3f} ms")
        print(f"    Speedup: {speedup:.2f}x")

        # kana_to_hiragana
        py_time = time_function(normalize_py.kana_to_hiragana, text, iterations=iterations)
        cy_time = time_function(normalize_cy.kana_to_hiragana, text, iterations=iterations)
        speedup = py_time['mean'] / cy_time['mean']
        print(f"  kana_to_hiragana:")
        print(f"    Python:  {py_time['mean']*1000:.3f} ms")
        print(f"    Cython:  {cy_time['mean']*1000:.3f} ms")
        print(f"    Speedup: {speedup:.2f}x")


def benchmark_deinflect(iterations=500):
    """Benchmark deinflect function."""
    print("\n" + "=" * 70)
    print("DEINFLECT BENCHMARK")
    print("=" * 70)

    test_cases = [
        ("Simple", "食べました"),
        ("Medium", "読んでいます"),
        ("Complex", "食べさせられませんでした"),
    ]

    for name, word in test_cases:
        print(f"\n{name}: '{word}'")
        py_time = time_function(deinflect_py.deinflect, word, iterations=iterations)
        cy_time = time_function(deinflect_cy.deinflect, word, iterations=iterations)
        speedup = py_time['mean'] / cy_time['mean']

        print(f"  Python:  {py_time['mean']*1000:.3f} ms")
        print(f"  Cython:  {cy_time['mean']*1000:.3f} ms")
        print(f"  Speedup: {speedup:.2f}x")


def benchmark_variations(iterations=1000):
    """Benchmark variations functions."""
    print("\n" + "=" * 70)
    print("VARIATIONS BENCHMARK")
    print("=" * 70)

    test_cases = [
        ("Short", "ラーメン"),
        ("Medium", "コーヒーとケーキ"),
        ("Long", "ラーメンとコーヒーとケーキとビール" * 5),
    ]

    for name, text in test_cases:
        print(f"\n{name} ({len(text)} chars):")

        # expand_choon
        py_time = time_function(variations_py.expand_choon, text, iterations=iterations)
        cy_time = time_function(variations_cy.expand_choon, text, iterations=iterations)
        speedup = py_time['mean'] / cy_time['mean']
        print(f"  expand_choon:")
        print(f"    Python:  {py_time['mean']*1000:.3f} ms")
        print(f"    Cython:  {cy_time['mean']*1000:.3f} ms")
        print(f"    Speedup: {speedup:.2f}x")


def benchmark_yoon(iterations=10000):
    """Benchmark yoon function."""
    print("\n" + "=" * 70)
    print("YOON BENCHMARK")
    print("=" * 70)

    test_cases = [
        ("With yoon", "きゃ"),
        ("Without yoon", "あいうえお"),
        ("Long with yoon", "あいうえおかきくけこきゃ"),
    ]

    for name, text in test_cases:
        print(f"\n{name}:")
        py_time = time_function(yoon_py.ends_in_yoon, text, iterations=iterations)
        cy_time = time_function(yoon_cy.ends_in_yoon, text, iterations=iterations)
        speedup = py_time['mean'] / cy_time['mean']

        print(f"  Python:  {py_time['mean']*1000000:.3f} μs")
        print(f"  Cython:  {cy_time['mean']*1000000:.3f} μs")
        print(f"  Speedup: {speedup:.2f}x")


def benchmark_long_text_processing(iterations=100):
    """Benchmark processing of very long texts."""
    print("\n" + "=" * 70)
    print("LONG TEXT PROCESSING BENCHMARK")
    print("=" * 70)

    # Create increasingly long texts
    base_text = "私は毎日日本語を勉強しています。今日は新しい単語を覚えました。明日も続けます。"

    for multiplier in [1, 5, 10, 20, 50]:
        long_text = base_text * multiplier
        print(f"\nText length: {len(long_text)} chars ({multiplier}x base)")

        # Test normalize_input (most likely to show speedup)
        py_time = time_function(normalize_py.normalize_input, long_text, iterations=iterations)
        cy_time = time_function(normalize_cy.normalize_input, long_text, iterations=iterations)
        speedup = py_time['mean'] / cy_time['mean']

        print(f"  normalize_input:")
        print(f"    Python:  {py_time['mean']*1000:.3f} ms")
        print(f"    Cython:  {cy_time['mean']*1000:.3f} ms")
        print(f"    Speedup: {speedup:.2f}x")


def run_all_benchmarks():
    """Run all performance benchmarks."""
    print("=" * 70)
    print("CYTHON PERFORMANCE BENCHMARKS")
    print("=" * 70)
    print("\nWarmup...")
    # Warmup
    for _ in range(10):
        normalize_py.normalize_input("私は学生です")
        normalize_cy.normalize_input("私は学生です")
        deinflect_py.deinflect("食べました")
        deinflect_cy.deinflect("食べました")

    benchmark_normalize()
    benchmark_deinflect()
    benchmark_variations()
    benchmark_yoon()
    benchmark_long_text_processing()

    print("\n" + "=" * 70)
    print("ALL BENCHMARKS COMPLETED!")
    print("=" * 70)


if __name__ == '__main__':
    run_all_benchmarks()
