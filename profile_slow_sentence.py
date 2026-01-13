#!/usr/bin/env python3
"""
Profile slow sentence to identify performance bottleneck.
"""

import sys
import time
import cProfile
import pstats
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import tentoku

# The slow sentence (removing spaces between chars as user suggested)
text = """にこやかにうなずいている東京、秋葉原駅前にある、通称"ラジ館"。その8階は、イベントスペースになっている。【倫太郎「これからここで始まるのは、ドクター中鉢の記者会見だ」ドクター中鉢というのは発明家である。テレビなどにもよく登場する有名な人物で、特許数もそれなりに持っている。とはいえ世間一般の目からは所詮"色モノ"としか見られていないが。【【まゆり】「記者会見？」でもー、記者さんなんて見当たらない気がするよ？」まゆりの言う通りだった。"""

print(f"Text length: {len(text)} characters")
print(f"Text preview: {text[:100]}...")

# Warm up
print("\nWarming up...")
dict_obj = tentoku.SQLiteDictionary()
_ = tentoku.tokenize("テスト", dictionary=dict_obj)

# Time the slow sentence
print("\nTiming full tokenization...")
start = time.time()
tokens = tentoku.tokenize(text, dictionary=dict_obj)
end = time.time()

print(f"Tokenized into {len(tokens)} tokens")
print(f"Time: {end - start:.2f} seconds")

if end - start > 5:
    print("\n⚠️  SLOW! Running detailed profiler...")

    # Profile it
    profiler = cProfile.Profile()
    profiler.enable()
    tokens = tentoku.tokenize(text, dictionary=dict_obj)
    profiler.disable()

    # Print stats
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(30)
    print("\nTop 30 functions by cumulative time:")
    print(s.getvalue())

    # Also sort by time
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('time')
    ps.print_stats(30)
    print("\nTop 30 functions by total time:")
    print(s.getvalue())

# Show some tokens
print("\nFirst 10 tokens:")
for i, token in enumerate(tokens[:10]):
    entry = token.dictionary_entry
    if entry:
        reading = entry.kana_readings[0].text if entry.kana_readings else '?'
        print(f"  {i+1}. {token.text} [{reading}]")
    else:
        print(f"  {i+1}. {token.text} [no entry]")

dict_obj.close()
