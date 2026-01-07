#!/usr/bin/env python3
"""
Performance benchmark suite for Tentoku.

This script measures the performance of various operations:
- Tokenization speed (tokens/sec, chars/sec)
- Deinflection performance
- Dictionary lookup performance
- Different text complexity scenarios

Usage:
    python benchmark.py
    python benchmark.py --iterations 1000
    python benchmark.py --warmup
"""

import sys
import os
import time
import statistics
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tentoku import tokenize, SQLiteDictionary
from tentoku.deinflect import deinflect
from tentoku.word_search import word_search
from tentoku.normalize import normalize_input
from tentoku.database_path import find_database_path


def percentile(xs: List[float], p: float) -> float:
    """
    Calculate percentile.
    
    Args:
        xs: List of values
        p: Percentile (0.0 to 1.0)
        
    Returns:
        Percentile value
    """
    if not xs:
        return 0.0
    xs_sorted = sorted(xs)
    k = (len(xs_sorted) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs_sorted) - 1)
    if f == c:
        return xs_sorted[f]
    return xs_sorted[f] + (xs_sorted[c] - xs_sorted[f]) * (k - f)


class Benchmark:
    """Performance benchmarking suite."""
    
    def __init__(self, warmup: bool = True, debug: bool = False):
        """Initialize benchmark suite."""
        self.warmup = warmup
        self.debug = debug
        self.dictionary = None
        self._setup_dictionary()
    
    def _setup_dictionary(self):
        """Set up dictionary connection."""
        db_path = find_database_path()
        if not db_path:
            print("ERROR: SQLite database not found. Please build the database first.")
            sys.exit(1)
        
        self.dictionary = SQLiteDictionary(db_path=str(db_path))
        print(f"✓ Dictionary loaded from: {db_path}")
    
    def close(self):
        """Close dictionary connection."""
        if self.dictionary:
            self.dictionary.close()
    
    def _warmup(self):
        """Warm up the system by running a few tokenizations."""
        if not self.warmup:
            return
        
        print("Warming up...")
        warmup_texts = [
            "私は学生です",
            "食べました",
            "読んでいます",
            "高かったです"
        ]
        for text in warmup_texts:
            tokenize(text, self.dictionary)
        print("✓ Warmup complete\n")
    
    def time_function(self, func, *args, iterations: int = 100, batch_size: int = 1) -> Tuple[float, List[float], Any]:
        """
        Time a function execution.
        
        Args:
            func: Function to time
            *args: Arguments to pass to function
            iterations: Number of iterations
            batch_size: Number of calls per iteration (for reducing overhead on fast functions)
        
        Returns:
            Tuple of (mean_time_per_call, list_of_times_per_call, last_result)
        """
        times = []
        last_result = None
        
        if batch_size > 1:
            # Batch timing for very fast functions
            for _ in range(iterations):
                start = time.perf_counter()
                for _ in range(batch_size):
                    last_result = func(*args)
                end = time.perf_counter()
                times.append((end - start) / batch_size)
        else:
            # Normal timing
            for _ in range(iterations):
                start = time.perf_counter()
                last_result = func(*args)
                end = time.perf_counter()
                times.append(end - start)
        
        return statistics.mean(times), times, last_result
    
    def benchmark_tokenization(self, text: str, iterations: int = 100) -> Dict:
        """Benchmark tokenization of a text."""
        def run_tokenize():
            return tokenize(text, self.dictionary)
        
        # Use batched timing for very short texts (likely fast-path)
        batch_size = 10 if len(text) < 10 else 1
        
        mean_time, all_times, tokens = self.time_function(
            run_tokenize, 
            iterations=iterations,
            batch_size=batch_size
        )
        
        # If we batched, get a fresh result for accurate token count
        if batch_size > 1:
            tokens = run_tokenize()
        
        num_tokens = len(tokens) if tokens else 0
        num_chars = len(text)
        
        return {
            'text': text,
            'text_length': num_chars,
            'num_tokens': num_tokens,
            'mean_time': mean_time,
            'median_time': statistics.median(all_times),
            'p90_time': percentile(all_times, 0.90),
            'p95_time': percentile(all_times, 0.95),
            'min_time': min(all_times),
            'max_time': max(all_times),
            'std_dev': statistics.stdev(all_times) if len(all_times) > 1 else 0,
            'tokens_per_sec': num_tokens / mean_time if mean_time > 0 else 0,
            'chars_per_sec': num_chars / mean_time if mean_time > 0 else 0,
            'time_per_token': mean_time / num_tokens if num_tokens > 0 else 0,
        }
    
    def benchmark_deinflection(self, word: str, iterations: int = 1000) -> Dict:
        """Benchmark deinflection of a word."""
        def run_deinflect():
            return deinflect(word)
        
        # Deinflection is typically very fast, use batching
        mean_time, all_times, candidates = self.time_function(
            run_deinflect, 
            iterations=iterations,
            batch_size=10
        )
        
        # Get fresh result if we batched
        if not candidates:
            candidates = run_deinflect()
        
        return {
            'word': word,
            'mean_time': mean_time,
            'median_time': statistics.median(all_times),
            'p90_time': percentile(all_times, 0.90),
            'p95_time': percentile(all_times, 0.95),
            'min_time': min(all_times),
            'max_time': max(all_times),
            'std_dev': statistics.stdev(all_times) if len(all_times) > 1 else 0,
            'candidates': len(candidates) if candidates else 0,
            'ops_per_sec': 1.0 / mean_time if mean_time > 0 else 0,
        }
    
    def benchmark_word_search(self, text: str, iterations: int = 100) -> Dict:
        """Benchmark word search operation."""
        normalized, input_lengths = normalize_input(text)
        
        def run_word_search():
            return word_search(normalized, self.dictionary, max_results=7, input_lengths=input_lengths)
        
        mean_time, all_times, result = self.time_function(
            run_word_search, 
            iterations=iterations
        )
        
        # Get fresh result if needed
        if result is None:
            result = run_word_search()
        
        # Robust check for actual matches
        # word_search returns Optional[WordSearchResult] where WordSearchResult.data is List[WordResult]
        found_match = False
        branch = "none"
        match_info = ""
        data = None
        
        if result is None:
            branch = "none"
            found_match = False
        else:
            data = getattr(result, "data", None)
            if isinstance(data, list):
                branch = "list"
                found_match = len(data) > 0
                match_info = f"len={len(data)}"
            elif isinstance(data, dict):
                # Check common keys that might contain matches
                branch = "dict:fallback"
                for key in ("matches", "results", "entries", "words", "items"):
                    if key in data:
                        branch = f"dict:{key}"
                        value = data[key]
                        if isinstance(value, list):
                            found_match = len(value) > 0
                            match_info = f"len={len(value)}"
                        else:
                            found_match = bool(value)
                            match_info = f"value={bool(value)}"
                        break
                if branch == "dict:fallback":
                    # No recognized key found
                    found_match = False
                    match_info = "no recognized keys"
            elif data is not None:
                # Fallback: if data exists and is truthy, assume match
                branch = "fallback"
                found_match = bool(data)
                match_info = f"type={type(data).__name__}"
        
        # Debug output for "Not in dict" case (or if debug flag is set)
        if self.debug or text == "あいうえおかきくけこ":
            print("DEBUG word_search type:", type(result))
            print("DEBUG repr:", repr(result))
            print("DEBUG data type:", type(data))
            print("DEBUG data repr:", repr(data))
            if data is not None:
                if hasattr(data, "__len__"):
                    print("DEBUG data length:", len(data))
                print("DEBUG bool(data):", bool(data))
            print(f"DEBUG found_match branch={branch} {match_info} -> {found_match}")
        
        return {
            'text': text,
            'mean_time': mean_time,
            'median_time': statistics.median(all_times),
            'p90_time': percentile(all_times, 0.90),
            'p95_time': percentile(all_times, 0.95),
            'min_time': min(all_times),
            'max_time': max(all_times),
            'std_dev': statistics.stdev(all_times) if len(all_times) > 1 else 0,
            'found_match': found_match,
            'ops_per_sec': 1.0 / mean_time if mean_time > 0 else 0,
        }
    
    def run_all_benchmarks(self, iterations: int = 100):
        """Run all benchmark tests."""
        print("=" * 70)
        print("TENTOKU PERFORMANCE BENCHMARK")
        print("=" * 70)
        print()
        
        self._warmup()
        
        # Test texts of varying complexity
        test_texts = [
            # Simple texts
            ("Simple - Basic sentence", "私は学生です"),
            ("Simple - Short", "こんにちは"),
            ("Simple - Numbers", "12345"),
            
            # Medium complexity
            ("Medium - With particles", "これは本です"),
            ("Medium - Multiple words", "今日は良い天気です"),
            ("Medium - Mixed script", "東京タワーに行きました"),
            
            # Complex - with deinflection
            ("Complex - Verb conjugation", "食べました"),
            ("Complex - Continuous form", "読んでいます"),
            ("Complex - Negative form", "行きませんでした"),
            ("Complex - Multiple conjugations", "食べさせられませんでした"),
            
            # Long texts
            ("Long - Paragraph", "私は毎日日本語を勉強しています。今日は新しい単語を覚えました。明日も続けます。"),
            ("Long - Multiple sentences", "これはテストです。あれもテストです。それもテストです。"),
        ]
        
        print("TOKENIZATION BENCHMARKS")
        print("-" * 70)
        tokenization_results = []
        
        for name, text in test_texts:
            print(f"\n{name}:")
            print(f"  Text: {text[:50]}{'...' if len(text) > 50 else ''}")
            result = self.benchmark_tokenization(text, iterations=iterations)
            tokenization_results.append((name, result))
            
            print(f"  Length: {result['text_length']} chars, {result['num_tokens']} tokens")
            print(f"  Mean time: {result['mean_time']*1000:.3f} ms")
            print(f"  Median time: {result['median_time']*1000:.3f} ms")
            print(f"  P95 time: {result['p95_time']*1000:.3f} ms")
            print(f"  Throughput: {result['tokens_per_sec']:.1f} tokens/sec, {result['chars_per_sec']:.1f} chars/sec")
            print(f"  Time per token: {result['time_per_token']*1000:.3f} ms")
            
            # Flag unusually slow cases
            if result['mean_time'] > 0.010:  # > 10ms
                print(f"  ⚠ Note: This case is slower than typical - may indicate complexity")
        
        # Summary statistics
        print("\n" + "=" * 70)
        print("TOKENIZATION SUMMARY")
        print("-" * 70)
        
        # Separate microbenchmarks (Numbers) from real cases
        microbench_names = {"Simple - Numbers"}
        real_results = [r for r in tokenization_results if r[0] not in microbench_names]
        microbench_results = [r for r in tokenization_results if r[0] in microbench_names]
        
        all_tokens_per_sec = [r[1]['tokens_per_sec'] for r in tokenization_results]
        all_chars_per_sec = [r[1]['chars_per_sec'] for r in tokenization_results]
        real_tokens_per_sec = [r[1]['tokens_per_sec'] for r in real_results]
        real_chars_per_sec = [r[1]['chars_per_sec'] for r in real_results]
        all_p95_times = [r[1]['p95_time'] for r in tokenization_results]
        real_p95_times = [r[1]['p95_time'] for r in real_results]
        
        print("Overall (including microbenchmarks):")
        print(f"  Median tokens/sec: {statistics.median(all_tokens_per_sec):.1f}")
        print(f"  Median chars/sec: {statistics.median(all_chars_per_sec):.1f}")
        print(f"  P95 time per call: {statistics.median(all_p95_times)*1000:.3f} ms")
        
        if real_results:
            print("\nReal-world cases (excluding microbenchmarks):")
            print(f"  Median tokens/sec: {statistics.median(real_tokens_per_sec):.1f}")
            print(f"  Median chars/sec: {statistics.median(real_chars_per_sec):.1f}")
            print(f"  P95 time per call: {statistics.median(real_p95_times)*1000:.3f} ms")
        
        # Deinflection benchmarks
        print("\n" + "=" * 70)
        print("DEINFLECTION BENCHMARKS")
        print("-" * 70)
        
        deinflect_words = [
            ("Simple - Past tense", "食べました"),
            ("Simple - Continuous", "読んで"),
            ("Simple - Negative", "行かない"),
            ("Complex - Multiple conjugations", "食べさせられませんでした"),
            ("Adjective - Past", "高かった"),
            ("Adjective - Negative", "高くない"),
        ]
        
        deinflect_results = []
        for name, word in deinflect_words:
            print(f"\n{name}:")
            print(f"  Word: {word}")
            result = self.benchmark_deinflection(word, iterations=iterations * 10)
            deinflect_results.append((name, result))
            
            print(f"  Mean time: {result['mean_time']*1000000:.3f} μs")
            print(f"  P95 time: {result['p95_time']*1000000:.3f} μs")
            print(f"  Candidates found: {result['candidates']}")
            print(f"  Throughput: {result['ops_per_sec']:.1f} ops/sec")
        
        # Word search benchmarks
        print("\n" + "=" * 70)
        print("WORD SEARCH BENCHMARKS")
        print("-" * 70)
        
        search_texts = [
            ("Simple lookup", "食べる"),
            ("Conjugated", "食べました"),
            ("Long word", "食べさせられませんでした"),
            ("Not in dict", "あいうえおかきくけこ"),
        ]
        
        search_results = []
        for name, text in search_texts:
            print(f"\n{name}:")
            print(f"  Text: {text}")
            result = self.benchmark_word_search(text, iterations=iterations)
            search_results.append((name, result))
            
            print(f"  Mean time: {result['mean_time']*1000:.3f} ms")
            print(f"  P95 time: {result['p95_time']*1000:.3f} ms")
            print(f"  Found match: {result['found_match']}")
            print(f"  Throughput: {result['ops_per_sec']:.1f} ops/sec")
        
        # Throughput test - tokenize many texts
        print("\n" + "=" * 70)
        print("THROUGHPUT TEST")
        print("-" * 70)
        
        throughput_texts = [
            "私は学生です",
            "食べました",
            "読んでいます",
            "今日は良い天気です",
            "東京タワーに行きました",
        ] * 20  # 100 texts total
        
        print(f"Tokenizing {len(throughput_texts)} texts...")
        start = time.perf_counter()
        total_tokens = 0
        total_chars = 0
        for text in throughput_texts:
            tokens = tokenize(text, self.dictionary)
            total_tokens += len(tokens)
            total_chars += len(text)
        end = time.perf_counter()
        
        total_time = end - start
        print(f"Total time: {total_time:.3f} s")
        print(f"Total texts: {len(throughput_texts)}")
        print(f"Total tokens: {total_tokens}")
        print(f"Total chars: {total_chars}")
        print(f"Throughput: {len(throughput_texts)/total_time:.1f} texts/sec")
        print(f"Throughput: {total_tokens/total_time:.1f} tokens/sec")
        print(f"Throughput: {total_chars/total_time:.1f} chars/sec")
        
        # Windowed throughput test (hover-like scenario)
        print("\n" + "=" * 70)
        print("WINDOWED THROUGHPUT TEST (hover-like)")
        print("-" * 70)
        
        # Simulate hovering over a longer text, tokenizing substrings
        long_text = "私は毎日日本語を勉強しています。今日は新しい単語を覚えました。明日も続けます。"
        window_size = 10  # Tokenize 10-char windows
        num_windows = max(1, len(long_text) - window_size + 1)
        
        print(f"Tokenizing {num_windows} overlapping windows of {window_size} chars from text:")
        print(f"  '{long_text[:50]}{'...' if len(long_text) > 50 else ''}'")
        
        start = time.perf_counter()
        total_window_tokens = 0
        total_window_chars = 0
        for i in range(num_windows):
            window_text = long_text[i:i + window_size]
            tokens = tokenize(window_text, self.dictionary)
            total_window_tokens += len(tokens)
            total_window_chars += len(window_text)
        end = time.perf_counter()
        
        window_total_time = end - start
        print(f"Total time: {window_total_time:.3f} s")
        print(f"Total windows: {num_windows}")
        print(f"Total tokens: {total_window_tokens}")
        print(f"Total chars: {total_window_chars}")
        print(f"Throughput: {num_windows/window_total_time:.1f} windows/sec")
        print(f"Throughput: {total_window_tokens/window_total_time:.1f} tokens/sec")
        print(f"Throughput: {total_window_chars/window_total_time:.1f} chars/sec")
        print(f"Time per window: {window_total_time/num_windows*1000:.3f} ms")
        
        print("\n" + "=" * 70)
        print("BENCHMARK COMPLETE")
        print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Benchmark Tentoku performance')
    parser.add_argument(
        '--iterations',
        type=int,
        default=100,
        help='Number of iterations per benchmark (default: 100)'
    )
    parser.add_argument(
        '--no-warmup',
        action='store_true',
        help='Skip warmup phase'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output (also enabled by TENTOKU_BENCH_DEBUG env var)'
    )
    
    args = parser.parse_args()
    
    # Check for debug flag from CLI or environment variable
    debug = args.debug or os.getenv('TENTOKU_BENCH_DEBUG') == '1'
    
    benchmark = Benchmark(warmup=not args.no_warmup, debug=debug)
    
    try:
        benchmark.run_all_benchmarks(iterations=args.iterations)
    finally:
        benchmark.close()


if __name__ == '__main__':
    main()

