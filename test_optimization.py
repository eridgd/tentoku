#!/usr/bin/env python3
"""
Simple test to verify optimization is working.
"""

import time

# Test the long sentence
text = '''にこやかにうなずいている東京、秋葉原駅前にある、通称"ラジ館"。その8階は、イベントスペースになっている。【倫太郎「これからここで始まるのは、ドクター中鉢の記者会見だ」ドクター中鉢というのは発明家である。テレビなどにもよく登場する有名な人物で、特許数もそれなりに持っている。とはいえ世間一般の目からは所詮"色モノ"としか見られていないが。【【まゆり】「記者会見？」でもー、記者さんなんて見当たらない気がするよ？」まゆりの言う通りだった。'''

print(f'Text length: {len(text)} chars\n')

# Import tentoku - this should now use OptimizedSQLiteDictionary
import tentoku

# Check which dictionary class is being used
print(f'Dictionary class: {tentoku.SQLiteDictionary.__name__}')
print(f'Module: {tentoku.SQLiteDictionary.__module__}\n')

# Test the optimization
dict_instance = tentoku.SQLiteDictionary()
print(f'Dictionary instance type: {type(dict_instance).__name__}')
print(f'Has max_lookup_length: {hasattr(dict_instance, "max_lookup_length")}')
if hasattr(dict_instance, 'max_lookup_length'):
    print(f'max_lookup_length value: {dict_instance.max_lookup_length}\n')

# Test with a very long string (should be skipped)
long_string = "a" * 100
result = dict_instance.get_words(long_string, 10)
print(f'Lookup of 100-char string returned {len(result)} results (should be 0)')

# Test with a short string (should work)
short_string = "東京"
result = dict_instance.get_words(short_string, 10)
print(f'Lookup of "東京" returned {len(result)} results (should be > 0)\n')

# Now test tokenization
print('Running tokenization...')
start = time.time()
tokens = tentoku.tokenize(text)
elapsed = time.time() - start

print(f'Tokenized {len(tokens)} tokens in {elapsed:.3f}s')
