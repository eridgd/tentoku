#!/usr/bin/env python3
"""
Profile the optimized dictionary lookups.
"""

import sys
import time
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))

import tentoku
from tentoku.sqlite_dict_optimized import OptimizedSQLiteDictionary

# Track lookups
lookup_counter = Counter()
skipped_counter = Counter()
actual_db_lookups = 0
cache_hits_negative = 0
cache_hits_positive = 0

original_get_words = OptimizedSQLiteDictionary.get_words

def tracked_get_words(self, input_text, max_results, matching_text=None):
    global actual_db_lookups, cache_hits_negative, cache_hits_positive

    lookup_counter[len(input_text)] += 1

    # Track what happens
    if len(input_text) > self.max_lookup_length:
        skipped_counter['length_check'] += 1
    elif input_text in self._negative_cache:
        cache_hits_negative += 1
    else:
        cache_key = (input_text, max_results, matching_text)
        if cache_key in self._positive_cache:
            cache_hits_positive += 1
        else:
            actual_db_lookups += 1

    return original_get_words(self, input_text, max_results, matching_text)

OptimizedSQLiteDictionary.get_words = tracked_get_words

# Test with the long sentence
text = '''にこやかにうなずいている東京、秋葉原駅前にある、通称"ラジ館"。その8階は、イベントスペースになっている。【倫太郎「これからここで始まるのは、ドクター中鉢の記者会見だ」ドクター中鉢というのは発明家である。テレビなどにもよく登場する有名な人物で、特許数もそれなりに持っている。とはいえ世間一般の目からは所詮"色モノ"としか見られていないが。【【まゆり】「記者会見？」でもー、記者さんなんて見当たらない気がするよ？」まゆりの言う通りだった。'''

print(f'Text length: {len(text)} chars\n')

start = time.time()
tokens = tentoku.tokenize(text)
total_time = time.time() - start

print(f'Tokenized {len(tokens)} tokens in {total_time:.3f}s\n')

print('=== OPTIMIZATION STATISTICS ===')
total_calls = sum(lookup_counter.values())
print(f'Total get_words() calls: {total_calls:,}')
print(f'Skipped by length check (>{15} chars): {skipped_counter.get("length_check", 0):,} ({skipped_counter.get("length_check", 0)/total_calls*100:.1f}%)')
print(f'Negative cache hits: {cache_hits_negative:,} ({cache_hits_negative/total_calls*100:.1f}%)')
print(f'Positive cache hits: {cache_hits_positive:,} ({cache_hits_positive/total_calls*100:.1f}%)')
print(f'Actual database lookups: {actual_db_lookups:,} ({actual_db_lookups/total_calls*100:.1f}%)')

print('\n=== LENGTH DISTRIBUTION OF LOOKUPS ===')
length_buckets = {
    '1-5': 0,
    '6-10': 0,
    '11-15': 0,
    '16-20': 0,
    '21-50': 0,
    '51-100': 0,
    '100-200': 0,
    '200+': 0
}

for length, count in lookup_counter.items():
    if length <= 5:
        length_buckets['1-5'] += count
    elif length <= 10:
        length_buckets['6-10'] += count
    elif length <= 15:
        length_buckets['11-15'] += count
    elif length <= 20:
        length_buckets['16-20'] += count
    elif length <= 50:
        length_buckets['21-50'] += count
    elif length <= 100:
        length_buckets['51-100'] += count
    elif length <= 200:
        length_buckets['100-200'] += count
    else:
        length_buckets['200+'] += count

for bucket, count in length_buckets.items():
    pct = count / total_calls * 100
    print(f'  {bucket:10s}: {count:6,d} lookups ({pct:5.1f}%)')

print(f'\nReduction from baseline (~170k): {(1 - actual_db_lookups/170000)*100:.1f}%')
