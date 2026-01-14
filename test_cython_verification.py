#!/usr/bin/env python3
"""
Test script to verify Cython functions are being used and tokenization works.
"""

import tentoku

print("=" * 70)
print("CYTHON VERIFICATION & TOKENIZATION TEST")
print("=" * 70)
print()

# First, verify Cython status
print("1. Checking Cython status...")
print("-" * 70)
tentoku.verify_cython_status(verbose=True)
print()

# Test actual tokenization
print("2. Testing tokenization with Japanese text...")
print("-" * 70)

# Initialize dictionary
try:
    db_path = tentoku.find_database_path()
    print(f"Using database: {db_path}")
    dictionary = tentoku.SQLiteDictionary(db_path)  # SQLiteDictionary is actually OptimizedSQLiteDictionary
    print("Dictionary loaded successfully")
    print()
except Exception as e:
    print(f"Error loading dictionary: {e}")
    print("Skipping tokenization test")
    exit(1)

# Test sentences
test_sentences = [
    "今日は良い天気です",
    "食べました",
    "日本語を勉強しています",
]

for sentence in test_sentences:
    print(f"Tokenizing: {sentence}")
    try:
        tokens = tentoku.tokenize(sentence, dictionary)
        print(f"  Found {len(tokens)} tokens:")
        for token in tokens[:5]:  # Show first 5 tokens
            # Token has 'text' and 'match_len' attributes
            match_len = getattr(token, 'match_len', 'N/A')
            print(f"    - {token.text} (match_len: {match_len})")
        if len(tokens) > 5:
            print(f"    ... and {len(tokens) - 5} more")
        print()
    except Exception as e:
        print(f"  Error: {e}")
        print()

print("=" * 70)
print("Test completed!")
print("=" * 70)
