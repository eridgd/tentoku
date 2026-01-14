#!/usr/bin/env python3
"""
Profile dictionary lookups to see what's being queried.
"""

import sys
import time
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))

from tentoku.sqlite_dict import SQLiteDictionary

# Track lookups
lookup_counter = Counter()
lookup_times = []
original_get_words = SQLiteDictionary.get_words

def tracked_get_words(self, input_text, max_results, matching_text=None):
    lookup_counter[input_text] += 1
    start = time.time()
    result = original_get_words(self, input_text, max_results, matching_text)
    elapsed = time.time() - start
    lookup_times.append(elapsed)
    return result

SQLiteDictionary.get_words = tracked_get_words

# Now import tentoku which will use our patched version
import tentoku

# Test with the long sentence
text = '''にこやかにうなずいている東京、秋葉原駅前にある、通称"ラジ館"。その8階は、イベントスペースになっている。【倫太郎「これからここで始まるのは、ドクター中鉢の記者会見だ」ドクター中鉢というのは発明家である。テレビなどにもよく登場する有名な人物で、特許数もそれなりに持っている。とはいえ世間一般の目からは所詮"色モノ"としか見られていないが。【【まゆり】「記者会見？」でもー、記者さんなんて見当たらない気がするよ？」まゆりの言う通りだった。'''

print(f'Text length: {len(text)} chars\n')

start = time.time()
tokens = tentoku.tokenize(text)
total_time = time.time() - start

print(f'Tokenized {len(tokens)} tokens in {total_time:.3f}s\n')

if lookup_counter:
    print('=== LOOKUP STATISTICS ===')
    print(f'Total lookups: {sum(lookup_counter.values())}')
    print(f'Unique words looked up: {len(lookup_counter)}')
    print(f'Average lookups per unique word: {sum(lookup_counter.values()) / len(lookup_counter):.1f}')
    print(f'Total time in lookups: {sum(lookup_times):.3f}s ({sum(lookup_times)/total_time*100:.1f}% of total)')
    print(f'Average time per lookup: {sum(lookup_times)/len(lookup_times)*1000:.1f}ms')

    print('\n=== TOP 20 MOST LOOKED UP WORDS ===')
    for word, count in lookup_counter.most_common(20):
        print(f'  {word:20s} {count:3d} times')

    print('\n=== SLOWEST LOOKUPS ===')
    sorted_times = sorted(lookup_times, reverse=True)[:10]
    for i, t in enumerate(sorted_times, 1):
        print(f'  {i}. {t*1000:.1f}ms')
else:
    print('No lookups tracked!')
