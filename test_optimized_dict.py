#!/usr/bin/env python3
"""
Test the optimized SQLite dictionary implementation.
"""

import sys
import time
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))

# Import directly from files
from sqlite_dict import SQLiteDictionary
from sqlite_dict_optimized import OptimizedSQLiteDictionary

# Track lookups for both versions
lookup_counter_standard = Counter()
lookup_counter_optimized = Counter()

original_get_words_standard = SQLiteDictionary.get_words
original_get_words_optimized = OptimizedSQLiteDictionary.get_words

def tracked_get_words_standard(self, input_text, max_results, matching_text=None):
    lookup_counter_standard[input_text] += 1
    return original_get_words_standard(self, input_text, max_results, matching_text)

def tracked_get_words_optimized(self, input_text, max_results, matching_text=None):
    lookup_counter_optimized[input_text] += 1
    return original_get_words_optimized(self, input_text, max_results, matching_text)

SQLiteDictionary.get_words = tracked_get_words_standard
OptimizedSQLiteDictionary.get_words = tracked_get_words_optimized

# Test with the long sentence
text = '''にこやかにうなずいている東京、秋葉原駅前にある、通称"ラジ館"。その8階は、イベントスペースになっている。【倫太郎「これからここで始まるのは、ドクター中鉢の記者会見だ」ドクター中鉢というのは発明家である。テレビなどにもよく登場する有名な人物で、特許数もそれなりに持っている。とはいえ世間一般の目からは所詮"色モノ"としか見られていないが。【【まゆり】「記者会見？」でもー、記者さんなんて見当たらない気がするよ？」まゆりの言う通りだった。'''

print(f'Text length: {len(text)} chars\n')

# Test standard version
print('=== TESTING STANDARD SQLiteDictionary ===')
import tentoku
lookup_counter_standard.clear()
start = time.time()
tokens_standard = tentoku.tokenize(text)
time_standard = time.time() - start
print(f'Tokenized {len(tokens_standard)} tokens in {time_standard:.3f}s')
print(f'Total lookups: {sum(lookup_counter_standard.values())}')
print(f'Unique words looked up: {len(lookup_counter_standard)}')

# Test optimized version
print('\n=== TESTING OPTIMIZED SQLiteDictionary ===')
# Replace the dictionary in tentoku module
from tentoku import tokenizer as tokenizer_module
tokenizer_module._dict = OptimizedSQLiteDictionary()
lookup_counter_optimized.clear()
start = time.time()
tokens_optimized = tentoku.tokenize(text)
time_optimized = time.time() - start
print(f'Tokenized {len(tokens_optimized)} tokens in {time_optimized:.3f}s')
print(f'Total lookups: {sum(lookup_counter_optimized.values())}')
print(f'Unique words looked up: {len(lookup_counter_optimized)}')

# Verify results are the same
print('\n=== VERIFICATION ===')
if len(tokens_standard) == len(tokens_optimized):
    print('✓ Same number of tokens')
else:
    print(f'✗ Different token counts: {len(tokens_standard)} vs {len(tokens_optimized)}')

# Check if tokens match
all_match = True
for i, (t1, t2) in enumerate(zip(tokens_standard, tokens_optimized)):
    if t1.text != t2.text:
        print(f'✗ Token {i} mismatch: "{t1.text}" vs "{t2.text}"')
        all_match = False
        break

if all_match:
    print('✓ All tokens match')

# Performance comparison
print('\n=== PERFORMANCE COMPARISON ===')
speedup = time_standard / time_optimized
lookup_reduction = (1 - sum(lookup_counter_optimized.values()) / sum(lookup_counter_standard.values())) * 100
print(f'Standard version: {time_standard:.3f}s')
print(f'Optimized version: {time_optimized:.3f}s')
print(f'Speedup: {speedup:.2f}x')
print(f'Lookup reduction: {lookup_reduction:.1f}%')

# Show distribution of lookup lengths
print('\n=== LOOKUP LENGTH DISTRIBUTION (Standard) ===')
length_buckets = {
    '1-5': 0,
    '6-10': 0,
    '11-15': 0,
    '16-20': 0,
    '21-50': 0,
    '51-100': 0,
    '100+': 0
}

for word in lookup_counter_standard.keys():
    length = len(word)
    if length <= 5:
        length_buckets['1-5'] += lookup_counter_standard[word]
    elif length <= 10:
        length_buckets['6-10'] += lookup_counter_standard[word]
    elif length <= 15:
        length_buckets['11-15'] += lookup_counter_standard[word]
    elif length <= 20:
        length_buckets['16-20'] += lookup_counter_standard[word]
    elif length <= 50:
        length_buckets['21-50'] += lookup_counter_standard[word]
    elif length <= 100:
        length_buckets['51-100'] += lookup_counter_standard[word]
    else:
        length_buckets['100+'] += lookup_counter_standard[word]

for bucket, count in length_buckets.items():
    pct = count / sum(lookup_counter_standard.values()) * 100
    print(f'  {bucket:10s}: {count:6d} lookups ({pct:5.1f}%)')
