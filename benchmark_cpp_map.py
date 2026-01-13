#!/usr/bin/env python3
"""
Benchmark the C++ unordered_map optimization in deinflect.

This compares the current C++ optimized version against the baseline Python version.
"""

import sys
import time
import statistics
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tentoku import deinflect as deinflect_module
from tentoku import deinflect_cy


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


def benchmark_cpp_map():
    """Benchmark C++ unordered_map optimization."""
    print("=" * 70)
    print("C++ UNORDERED_MAP OPTIMIZATION BENCHMARK")
    print("=" * 70)
    print("\nComparing: Python dict vs C++ std::unordered_map")
    print("Optimization: String-to-int lookups in deinflection rule index\n")

    test_cases = [
        ("Simple conjugation", "食べました", 500),
        ("Medium complexity", "読んでいます", 500),
        ("Complex conjugation", "食べさせられませんでした", 500),
        ("Respectful form", "いらっしゃいました", 500),
        ("Multiple deinflections", "書かされている", 500),
    ]

    total_py_time = 0
    total_cy_time = 0

    for name, word, iterations in test_cases:
        print(f"\n{name}: '{word}'")

        # Python version (uses Python dict)
        py_time = time_function(deinflect_module._deinflect_py, word, iterations=iterations)

        # C++ optimized version (uses C++ unordered_map)
        cy_time = time_function(deinflect_cy.deinflect, word, iterations=iterations)

        speedup = py_time['mean'] / cy_time['mean']

        print(f"  Python dict:        {py_time['mean']*1000:.3f} ms")
        print(f"  C++ unordered_map:  {cy_time['mean']*1000:.3f} ms")
        print(f"  Speedup:            {speedup:.2f}x")

        total_py_time += py_time['mean']
        total_cy_time += cy_time['mean']

    print("\n" + "=" * 70)
    overall_speedup = total_py_time / total_cy_time
    print(f"OVERALL SPEEDUP: {overall_speedup:.2f}x")
    print("=" * 70)

    return overall_speedup


if __name__ == '__main__':
    speedup = benchmark_cpp_map()

    print(f"\n✓ C++ unordered_map provides {speedup:.2f}x speedup for deinflection")
    print("\nTechnical details:")
    print("  - Replaced Python dict with C++ std::unordered_map")
    print("  - Faster string-to-int lookups (O(1) with lower overhead)")
    print("  - Reduced memory allocation overhead")
    print("  - Better cache locality with C++ implementation")
