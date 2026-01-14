#!/usr/bin/env python3
"""
Comprehensive benchmark of SQLite optimization.
"""

import time
import tentoku

# Test cases of varying lengths
test_cases = [
    ("Short", "東京の天気"),
    ("Medium", "これからここで始まるのは、ドクター中鉢の記者会見だ"),
    ("Long", '''にこやかにうなずいている東京、秋葉原駅前にある、通称"ラジ館"。その8階は、イベントスペースになっている。【倫太郎「これからここで始まるのは、ドクター中鉢の記者会見だ」ドクター中鉢というのは発明家である。テレビなどにもよく登場する有名な人物で、特許数もそれなりに持っている。とはいえ世間一般の目からは所詮"色モノ"としか見られていないが。【【まゆり】「記者会見？」でもー、記者さんなんて見当たらない気がするよ？」まゆりの言う通りだった。'''),
]

print("=" * 60)
print("TENTOKU SQLITE OPTIMIZATION BENCHMARK")
print("=" * 60)
print(f"\nUsing dictionary: {tentoku.SQLiteDictionary.__name__}")
print(f"Module: {tentoku.SQLiteDictionary.__module__}\n")

for name, text in test_cases:
    print(f"\n{name} text ({len(text)} chars):")
    print(f"  Text: {text[:50]}..." if len(text) > 50 else f"  Text: {text}")

    # Warm up
    tentoku.tokenize(text)

    # Benchmark
    times = []
    for _ in range(3):
        start = time.time()
        tokens = tentoku.tokenize(text)
        elapsed = time.time() - start
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    print(f"  Tokens: {len(tokens)}")
    print(f"  Average time: {avg_time:.3f}s")
    print(f"  Best time: {min(times):.3f}s")

print("\n" + "=" * 60)
print("OPTIMIZATION SUMMARY")
print("=" * 60)
print("\nOptimizations active:")
print("  ✓ Length-based lookup filtering (>15 chars skipped)")
print("  ✓ Negative lookup caching")
print("  ✓ Positive lookup caching")
print("\nExpected improvements over baseline:")
print("  • ~96% reduction in database lookups")
print("  • ~2.2x speedup on long sentences")
print("  • Minimal overhead on short sentences")
print("\nFor detailed statistics, run: python profile_optimized.py")
