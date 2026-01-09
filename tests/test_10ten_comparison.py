#!/usr/bin/env python3
"""
Comprehensive test to compare tentoku behavior with 10ten Reader.

This test verifies that tentoku's word_search and sorting match 10ten Reader's behavior.
"""

import sys
from pathlib import Path
# Add parent directory to path to use local tentoku as a package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tentoku.word_search import word_search
from tentoku.sqlite_dict import SQLiteDictionary
from tentoku.sorting import sort_word_results, get_priority, get_kana_headword_type
from tentoku.normalize import normalize_input

def test_word_search_behavior():
    """Test word_search behavior matches 10ten Reader."""
    
    print("=" * 80)
    print("Testing word_search behavior")
    print("=" * 80)
    
    dictionary = SQLiteDictionary()
    
    # Test cases that should prioritize shorter, higher-priority matches
    test_cases = [
        ("にベッドリングを", "Should find 'に' (particle) before 'にベ' (鮸)"),
        ("この", "Should find 'この' (this) correctly"),
        ("一般的", "Should find '一般的' correctly"),
        ("食べました", "Should find '食べる' (to eat) via deinflection"),
        ("機関", "Should find '機関' (mechanism) correctly"),
    ]
    
    for input_text, description in test_cases:
        print(f"\n{'-'*80}")
        print(f"Input: {input_text}")
        print(f"Expected: {description}")
        print(f"{'-'*80}")
        
        normalized, input_lengths = normalize_input(input_text)
        
        # Get multiple results to see sorting
        result = word_search(
            normalized,
            dictionary,
            max_results=10,  # Get more results to see sorting
            input_lengths=input_lengths
        )
        
        if not result:
            print(f"  ✗ No results found")
            continue
        
        print(f"  Found {len(result.data)} results (match_len={result.match_len}):")
        
        for i, word_result in enumerate(result.data[:5], 1):  # Show top 5
            entry = word_result.entry
            
            # Get matched readings
            matched_kanji = [k.text for k in entry.kanji_readings if k.match_range]
            matched_kana = [r.text for r in entry.kana_readings if r.match_range]
            
            # Get priority and type
            priority = get_priority(entry)
            match_type = get_kana_headword_type(entry)
            reasons = max(len(chain) for chain in word_result.reason_chains) if word_result.reason_chains else 0
            
            print(f"\n    Result {i}:")
            print(f"      Entry ID: {entry.entry_id}")
            if matched_kanji:
                print(f"      Matched kanji: {matched_kanji[0]}")
            if matched_kana:
                print(f"      Matched kana: {matched_kana[0]}")
            print(f"      Priority: {priority}")
            print(f"      Match type: {match_type} ({'primary' if match_type == 1 else 'reading'})")
            print(f"      Deinflection steps: {reasons}")
            
            # Show first sense
            if entry.senses:
                first_gloss = entry.senses[0].glosses[0].text if entry.senses[0].glosses else "N/A"
                print(f"      First gloss: {first_gloss[:50]}...")
        
        # Check if first result makes sense
        first_result = result.data[0]
        first_matched = (
            [k.text for k in first_result.entry.kanji_readings if k.match_range] +
            [r.text for r in first_result.entry.kana_readings if r.match_range]
        )
        
        if first_matched:
            print(f"\n  ✓ First result matches: {first_matched[0]}")
        else:
            print(f"\n  ✗ First result has no matchRange!")


def test_sorting_priority():
    """Test that sorting prioritizes correctly."""
    
    print("\n" + "=" * 80)
    print("Testing sorting priority")
    print("=" * 80)
    
    dictionary = SQLiteDictionary()
    
    # Test: "にベ" should NOT be preferred over "に"
    # "に" is a common particle (priority spec1 = 32)
    # "にベ" (鮸) is a fish name (likely lower priority)
    
    print("\nTest: 'にベ' should NOT be preferred over 'に'")
    print("-" * 80)
    
    normalized, input_lengths = normalize_input("にベ")
    result = word_search(normalized, dictionary, max_results=10, input_lengths=input_lengths)
    
    if result:
        print(f"Found {len(result.data)} results:")
        
        # Find "に" in results
        ni_result = None
        nibe_result = None
        
        for word_result in result.data:
            matched = (
                [k.text for k in word_result.entry.kanji_readings if k.match_range] +
                [r.text for r in word_result.entry.kana_readings if r.match_range]
            )
            if matched:
                if matched[0] == "に":
                    ni_result = word_result
                elif matched[0] in ["にべ", "にベ"]:
                    nibe_result = word_result
        
        if ni_result and nibe_result:
            ni_priority = get_priority(ni_result.entry)
            nibe_priority = get_priority(nibe_result.entry)
            
            print(f"  'に' priority: {ni_priority}")
            print(f"  'にベ' priority: {nibe_priority}")
            
            ni_index = result.data.index(ni_result)
            nibe_index = result.data.index(nibe_result)
            
            print(f"  'に' position: {ni_index + 1}")
            print(f"  'にベ' position: {nibe_index + 1}")
            
            if ni_index < nibe_index:
                print(f"  ✓ 'に' correctly comes before 'にベ'")
            else:
                print(f"  ✗ 'にベ' comes before 'に' (WRONG!)")
        else:
            print(f"  Could not find both results in top 10")


def test_match_range_setting():
    """Test that matchRange is set correctly."""
    
    print("\n" + "=" * 80)
    print("Testing matchRange setting")
    print("=" * 80)
    
    dictionary = SQLiteDictionary()
    
    test_cases = [
        "この",
        "食べる",
        "機関",
    ]
    
    for input_text in test_cases:
        print(f"\nInput: {input_text}")
        
        # Get words directly
        entries = dictionary.get_words(input_text, max_results=3, matching_text=input_text)
        
        if not entries:
            print(f"  ✗ No entries found")
            continue
        
        for entry in entries:
            print(f"\n  Entry {entry.entry_id}:")
            
            # Check kanji readings
            matched_kanji = [k for k in entry.kanji_readings if k.match_range]
            if matched_kanji:
                print(f"    Matched kanji: {[k.text for k in matched_kanji]}")
                for k in matched_kanji:
                    print(f"      '{k.text}': match_range={k.match_range}, priority={k.priority}")
            
            # Check kana readings
            matched_kana = [r for r in entry.kana_readings if r.match_range]
            if matched_kana:
                print(f"    Matched kana: {[r.text for r in matched_kana]}")
                for r in matched_kana:
                    print(f"      '{r.text}': match_range={r.match_range}, priority={r.priority}")
            
            # Verify at least one reading has matchRange
            if not matched_kanji and not matched_kana:
                print(f"    ✗ No readings have matchRange!")


if __name__ == "__main__":
    try:
        test_match_range_setting()
        test_word_search_behavior()
        test_sorting_priority()
    except Exception as e:
        import traceback
        print(f"\n✗ Error: {e}")
        traceback.print_exc()
