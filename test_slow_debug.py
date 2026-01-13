#!/usr/bin/env python3
"""
Debug the slow tokenization issue.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import tentoku

# Short test first
text = "にこやかにうなずいている"

print(f'Text: {text}')
print(f'Length: {len(text)} chars')

dict_obj = tentoku.SQLiteDictionary()

# Patch word_search to add logging
original_word_search = tentoku.word_search.word_search

call_count = [0]
total_time = [0]

def logged_word_search(*args, **kwargs):
    call_count[0] += 1
    start = time.time()
    result = original_word_search(*args, **kwargs)
    elapsed = time.time() - start
    total_time[0] += elapsed

    text_arg = args[0] if args else kwargs.get('input_text', '')
    print(f"  Call {call_count[0]}: text='{text_arg[:20]}...' ({len(text_arg)} chars), time={elapsed:.3f}s, results={len(result.data) if result else 0}")

    return result

# Replace with logged version
tentoku.word_search.word_search = logged_word_search
import tentoku.tokenizer
tentoku.tokenizer.word_search = logged_word_search

print('\nTokenizing...')
start = time.time()
tokens = tentoku.tokenize(text, dictionary=dict_obj)
end = time.time()

print(f'\nTotal: {len(tokens)} tokens in {end-start:.2f}s')
print(f'word_search called {call_count[0]} times, total time in word_search: {total_time[0]:.2f}s')

dict_obj.close()
