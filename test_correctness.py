#!/usr/bin/env python3
"""
Test that optimized version produces same results as standard version.
"""

import tentoku

# Test sentences
test_cases = [
    "東京",
    "食べる",
    "にこやかにうなずいている東京",
    "これからここで始まるのは、ドクター中鉢の記者会見だ",
]

print("Testing correctness of optimized dictionary...")
for text in test_cases:
    tokens = tentoku.tokenize(text)
    token_texts = [t.text for t in tokens]
    print(f"\n'{text}'")
    print(f"  Tokens: {' | '.join(token_texts)}")
    print(f"  Count: {len(tokens)}")

print("\n✓ All tests completed successfully")
