#!/usr/bin/env python3
"""
Benchmark parallel batch processing.

This compares sequential vs parallel processing of multiple texts.
"""

import sys
import time
import statistics
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

import parallel_tokenize
from parallel_tokenize import parallel_normalize_batch, parallel_deinflect_batch, get_num_cpus
from normalize_cy import normalize_input
from deinflect_cy import deinflect


def time_function(func, *args, iterations=10):
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


def benchmark_parallel_normalize():
    """Benchmark parallel normalization."""
    print("\n" + "=" * 70)
    print("PARALLEL NORMALIZE BENCHMARK")
    print("=" * 70)
    print(f"\nCPU cores available: {get_num_cpus()}")

    # Create test data - simulate processing multiple manga pages
    base_text = "私は毎日日本語を勉強しています。今日は新しい単語を覚えました。明日も続けます。日本語はとても難しいですが、楽しいです。頑張ります。"

    test_cases = [
        ("Small batch (10 texts)", [base_text * 5] * 10, 10),
        ("Medium batch (50 texts)", [base_text * 5] * 50, 5),
        ("Large batch (100 texts)", [base_text * 5] * 100, 3),
    ]

    for name, texts, iterations in test_cases:
        print(f"\n{name}:")
        print(f"  {len(texts)} texts, {len(texts[0])} chars each")

        # Sequential processing
        def sequential_process():
            return [normalize_input(text) for text in texts]

        seq_time = time_function(sequential_process, iterations=iterations)

        # Parallel processing
        def parallel_process():
            return parallel_normalize_batch(texts)

        par_time = time_function(parallel_process, iterations=iterations)

        speedup = seq_time['mean'] / par_time['mean']

        print(f"  Sequential:  {seq_time['mean']:.3f} s")
        print(f"  Parallel:    {par_time['mean']:.3f} s")
        print(f"  Speedup:     {speedup:.2f}x")


def benchmark_parallel_deinflect():
    """Benchmark parallel deinflection."""
    print("\n" + "=" * 70)
    print("PARALLEL DEINFLECT BENCHMARK")
    print("=" * 70)
    print(f"\nCPU cores available: {get_num_cpus()}")

    # Create test data
    test_words = [
        "食べました", "読んでいます", "書かれた", "見させられる",
        "歩いている", "飲みたい", "話してください", "聞こえる",
        "考えさせられる", "教えられました", "走っている", "笑わせる",
    ]

    test_cases = [
        ("Small batch (50 words)", test_words * 4, 10),
        ("Medium batch (100 words)", test_words * 8, 5),
        ("Large batch (200 words)", test_words * 16, 3),
    ]

    for name, words, iterations in test_cases:
        print(f"\n{name}:")
        print(f"  {len(words)} words")

        # Sequential processing
        def sequential_process():
            return [deinflect(word) for word in words]

        seq_time = time_function(sequential_process, iterations=iterations)

        # Parallel processing
        def parallel_process():
            return parallel_deinflect_batch(words)

        par_time = time_function(parallel_process, iterations=iterations)

        speedup = seq_time['mean'] / par_time['mean']

        print(f"  Sequential:  {seq_time['mean']:.3f} s")
        print(f"  Parallel:    {par_time['mean']:.3f} s")
        print(f"  Speedup:     {speedup:.2f}x")


def run_all_benchmarks():
    """Run all parallel processing benchmarks."""
    print("=" * 70)
    print("PARALLEL PROCESSING BENCHMARKS")
    print("=" * 70)

    benchmark_parallel_normalize()
    benchmark_parallel_deinflect()

    print("\n" + "=" * 70)
    print("ALL BENCHMARKS COMPLETED!")
    print("=" * 70)

    print("\nNote: Parallel processing is most beneficial for:")
    print("  - Processing many texts/words at once (batch processing)")
    print("  - Multi-core systems (current: {} cores)".format(get_num_cpus()))
    print("  - IO-heavy operations with multiple API calls")


if __name__ == '__main__':
    run_all_benchmarks()
