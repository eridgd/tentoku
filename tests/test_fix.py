#!/usr/bin/env python3
"""
Test script to verify matchRange and sorting fixes match 10ten Reader behavior.
"""

import sys
from pathlib import Path
# Add parent directory to path to use local tentoku as a package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tentoku import tokenize

def test_problematic_texts():
    """Test with the problematic texts from the user's API response."""
    
    test_cases = [
        "この時期は、一時間の時、一般的にベッドリングを",
        "機関",
        "この",
        "一般的",
    ]
    
    print("=" * 80)
    print("Testing matchRange and Sorting Fixes")
    print("=" * 80)
    
    for text in test_cases:
        print(f"\n{'='*80}")
        print(f"Text: {text}")
        print(f"{'='*80}")
        
        tokens = tokenize(text)
        print(f"\nTokens ({len(tokens)}):")
        
        for i, token in enumerate(tokens):
            print(f"\n  Token {i}: \"{token.text}\" (start={token.start}, end={token.end})")
            
            if token.dictionary_entry:
                print(f"    Dictionary entry found (ent_seq={token.dictionary_entry.ent_seq})")
                
                # Check kanji readings with matchRange
                matching_kanji = [k for k in token.dictionary_entry.kanji_readings if k.match_range]
                if matching_kanji:
                    print(f"    ✓ Matched kanji: {[k.text for k in matching_kanji]}")
                    for k in matching_kanji:
                        if k.priority:
                            print(f"      Priority: {k.priority}")
                else:
                    print(f"    Kanji readings: {[k.text for k in token.dictionary_entry.kanji_readings[:3]]}")
                
                # Check kana readings with matchRange
                matching_kana = [r for r in token.dictionary_entry.kana_readings if r.match_range]
                if matching_kana:
                    print(f"    ✓ Matched kana: {[r.text for r in matching_kana]}")
                    for r in matching_kana:
                        if r.priority:
                            print(f"      Priority: {r.priority}")
                else:
                    print(f"    Kana readings: {[r.text for r in token.dictionary_entry.kana_readings[:3]]}")
                
                # Check if original text matches any reading
                matches_kanji = [k.text for k in token.dictionary_entry.kanji_readings 
                                if k.match_range and k.text == token.text]
                matches_kana = [r.text for r in token.dictionary_entry.kana_readings 
                               if r.match_range and r.text == token.text]
                if matches_kanji:
                    print(f"    ✓ Original text matches kanji reading: {matches_kanji[0]}")
                elif matches_kana:
                    print(f"    ✓ Original text matches kana reading: {matches_kana[0]}")
                else:
                    print(f"    ✗ Original text does NOT match any reading with matchRange!")
            else:
                print(f"    No dictionary entry")

if __name__ == "__main__":
    test_problematic_texts()
