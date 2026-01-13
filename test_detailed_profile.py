#!/usr/bin/env python3
import time
import tentoku

text = "にこやか"  # Even shorter test

print(f'Text: {text} ({len(text)} chars)\n')

# Monkey-patch to add timing
original_deinflect = tentoku.deinflect.deinflect
original_get_words = None

deinflect_time = [0]
deinflect_calls = [0]
dict_time = [0]
dict_calls = [0]

def timed_deinflect(*args, **kwargs):
    deinflect_calls[0] += 1
    start = time.time()
    result = original_deinflect(*args, **kwargs)
    deinflect_time[0] += time.time() - start
    return result

def timed_get_words(self, *args, **kwargs):
    dict_calls[0] += 1
    start = time.time()
    result = original_get_words(self, *args, **kwargs)
    dict_time[0] += time.time() - start
    return result

tentoku.deinflect.deinflect = timed_deinflect
import tentoku.deinflect_cy
tentoku.deinflect_cy.deinflect = timed_deinflect

dict_obj = tentoku.SQLiteDictionary()
original_get_words = dict_obj.get_words.__func__
dict_obj.__class__.get_words = timed_get_words

print('Tokenizing...')
start = time.time()
tokens = tentoku.tokenize(text, dictionary=dict_obj)
total_time = time.time() - start

print(f'\nResults:')
print(f'  Total time: {total_time:.3f}s')
print(f'  Deinflect: {deinflect_calls[0]} calls, {deinflect_time[0]:.3f}s total')
print(f'  Dict lookups: {dict_calls[0]} calls, {dict_time[0]:.3f}s total')
print(f'  Other: {total_time - deinflect_time[0] - dict_time[0]:.3f}s')

dict_obj.close()
