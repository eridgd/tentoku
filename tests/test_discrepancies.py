#!/usr/bin/env python3
"""
Test to identify discrepancies between tentoku and 10ten Reader.
"""

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from tentoku.word_search import word_search
from tentoku.sqlite_dict import SQLiteDictionary
from tentoku.normalize import normalize_input

def test_longest_match_calculation():
    """Test that longestMatch uses original input length, not variant length."""
    
    print("=" * 80)
    print("Testing longestMatch calculation")
    print("=" * 80)
    
    dictionary = SQLiteDictionary()
    
    # Test with text that has variations (choon, kyuujitai)
    # The longestMatch should be based on the ORIGINAL input length, not variant
    test_cases = [
        "おはよう",  # Simple case
        "おはよー",  # Has choon (ー) which can expand
    ]
    
    for input_text in test_cases:
        print(f"\nInput: {input_text}")
        normalized, input_lengths = normalize_input(input_text)
        print(f"  Normalized: {normalized}")
        print(f"  Input lengths: {input_lengths[:10]}...")  # Show first 10
        
        result = word_search(normalized, dictionary, max_results=5, input_lengths=input_lengths)
        
        if result:
            print(f"  match_len: {result.match_len}")
            print(f"  Original input length: {len(input_text)}")
            print(f"  Normalized length: {len(normalized)}")
            print(f"  input_lengths[{len(normalized)}]: {input_lengths[len(normalized)] if len(normalized) < len(input_lengths) else 'N/A'}")
            
            # The match_len should correspond to the original input length
            if result.match_len <= len(input_text):
                print(f"  ✓ match_len ({result.match_len}) <= original length ({len(input_text)})")
            else:
                print(f"  ✗ match_len ({result.match_len}) > original length ({len(input_text)})")
        else:
            print(f"  No results")

def test_sense_match_field():
    """Test if we need to track sense.match field."""
    
    print("\n" + "=" * 80)
    print("Testing sense.match field requirement")
    print("=" * 80)
    
    # In 10ten Reader, mostMatchedEnSensesAreUk filters for s.match
    # But in flat-file.ts, all senses get match: true
    # So this might only matter for IndexedDB, not flat file
    # Since tentoku uses SQLite (similar to flat file), we might not need this
    
    print("\nNote: 10ten Reader's mostMatchedEnSensesAreUk filters for s.match")
    print("But in flat-file.ts, all senses get match: true")
    print("Since tentoku uses SQLite (similar to flat file), this might not matter")
    print("However, we should verify the logic still works correctly")

def test_app_field():
    """Test if r.app === 0 is equivalent to no_kanji."""
    
    print("\n" + "=" * 80)
    print("Testing r.app field vs no_kanji")
    print("=" * 80)
    
    dictionary = SQLiteDictionary()
    
    # Find entries with no_kanji readings
    # In JMDict, readings with no_kanji=1 should be equivalent to app === 0
    print("\nChecking entries with no_kanji readings...")
    
    # Test with a common no_kanji word
    test_words = ["する", "ある", "いる"]  # Common verbs that might have no_kanji readings
    
    for word in test_words:
        entries = dictionary.get_words(word, max_results=3, matching_text=word)
        for entry in entries:
            for kana in entry.kana_readings:
                if kana.no_kanji:
                    print(f"  {word}: Found no_kanji reading '{kana.text}'")
                    break

if __name__ == "__main__":
    test_longest_match_calculation()
    test_sense_match_field()
    test_app_field()
