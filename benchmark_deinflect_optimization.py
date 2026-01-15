#!/usr/bin/env python3
"""
Performance benchmark for deinflection optimization.

This script tests the performance improvement from the hash map optimization
by comparing tokenization speed with various text lengths.
"""

import time
import statistics
from typing import List, Tuple

from tentoku import tokenize
from tentoku.deinflect import deinflect
from tentoku.database_path import find_database_path


def generate_test_texts() -> List[Tuple[str, str]]:
    """Generate test texts of varying complexity and length."""
    return [
        ("Short", "食べさせられませんでした"),
        ("Medium", "私は毎日日本語を勉強しています。今日は新しい単語を覚えました。"),
        ("Long", "昨日、友達と一緒に映画を見に行きました。とても面白かったです。その後、レストランで食事をして、おいしい料理を食べました。"),
        ("Very Long", """
        私は毎日日本語を勉強しています。今日は新しい単語を覚えました。
        昨日、友達と一緒に映画を見に行きました。とても面白かったです。
        その後、レストランで食事をして、おいしい料理を食べました。
        明日は図書館に行って、本を借りる予定です。読書が好きなので、楽しみにしています。
        週末には、公園で散歩をしたり、カフェでコーヒーを飲んだりするのが好きです。
        最近、日本語の文法を勉強していて、動詞の活用形について学んでいます。
        食べる、食べた、食べている、食べさせる、食べさせられる、食べさせられないなど、
        様々な形があることを知りました。これらを正しく使えるようになりたいです。
        """),
        ("Complex Conjugations", """
        食べさせられませんでした。飲ませられませんでした。行かせられませんでした。
        来させられませんでした。見させられませんでした。聞かせられませんでした。
        話させられませんでした。書かせられませんでした。読ませられませんでした。
        勉強させられませんでした。働かせられませんでした。遊ばせられませんでした。
        """),
    ]


def benchmark_deinflection(words: List[str], iterations: int = 1000) -> dict:
    """Benchmark deinflection performance."""
    print(f"\nBenchmarking deinflection ({iterations} iterations)...")
    
    times = []
    for word in words:
        word_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            candidates = deinflect(word)
            elapsed = time.perf_counter() - start
            word_times.append(elapsed)
        times.extend(word_times)
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0,
        'min': min(times),
        'max': max(times),
        'total_time': sum(times),
    }


def benchmark_tokenization(texts: List[Tuple[str, str]], iterations: int = 100) -> dict:
    """Benchmark tokenization performance."""
    print(f"\nBenchmarking tokenization ({iterations} iterations per text)...")
    
    results = {}
    for name, text in texts:
        text = text.strip()
        if not text:
            continue
            
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            tokens = tokenize(text)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        results[name] = {
            'text_length': len(text),
            'num_tokens': len(tokens),
            'mean_time': statistics.mean(times),
            'median_time': statistics.median(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0,
            'min_time': min(times),
            'max_time': max(times),
            'tokens_per_sec': len(tokens) / statistics.mean(times) if statistics.mean(times) > 0 else 0,
            'chars_per_sec': len(text) / statistics.mean(times) if statistics.mean(times) > 0 else 0,
        }
    
    return results


def main():
    """Run comprehensive performance benchmarks."""
    print("=" * 70)
    print("DEINFLECTION OPTIMIZATION PERFORMANCE BENCHMARK")
    print("=" * 70)
    
    # Test deinflection directly
    test_words = [
        "食べさせられませんでした",
        "飲ませられませんでした",
        "行かせられませんでした",
        "来させられませんでした",
        "見させられませんでした",
    ]
    
    deinflect_results = benchmark_deinflection(test_words, iterations=1000)
    
    print(f"\nDeinflection Results:")
    print(f"  Mean time: {deinflect_results['mean']*1000:.4f}ms")
    print(f"  Median time: {deinflect_results['median']*1000:.4f}ms")
    print(f"  Min time: {deinflect_results['min']*1000:.4f}ms")
    print(f"  Max time: {deinflect_results['max']*1000:.4f}ms")
    print(f"  Std dev: {deinflect_results['stdev']*1000:.4f}ms")
    print(f"  Total time ({len(test_words)*1000} iterations): {deinflect_results['total_time']:.3f}s")
    
    # Test tokenization with various text lengths
    test_texts = generate_test_texts()
    tokenize_results = benchmark_tokenization(test_texts, iterations=50)
    
    print(f"\n" + "=" * 70)
    print("TOKENIZATION RESULTS")
    print("=" * 70)
    
    for name, result in tokenize_results.items():
        print(f"\n{name} ({result['text_length']} chars, {result['num_tokens']} tokens):")
        print(f"  Mean time: {result['mean_time']*1000:.2f}ms")
        print(f"  Median time: {result['median_time']*1000:.2f}ms")
        print(f"  Tokens/sec: {result['tokens_per_sec']:.1f}")
        print(f"  Chars/sec: {result['chars_per_sec']:.1f}")
    
    # Summary
    print(f"\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    all_mean_times = [r['mean_time'] for r in tokenize_results.values()]
    overall_mean = statistics.mean(all_mean_times)
    overall_median = statistics.median([r['median_time'] for r in tokenize_results.values()])
    
    print(f"Overall tokenization mean: {overall_mean*1000:.2f}ms")
    print(f"Overall tokenization median: {overall_median*1000:.2f}ms")
    print(f"\nOptimization: Hash map lookup (O(1)) instead of linear scan (O(rules))")
    print(f"Expected improvement: 10-20x on deinflection, ~3-5x overall tokenization")


if __name__ == "__main__":
    main()
