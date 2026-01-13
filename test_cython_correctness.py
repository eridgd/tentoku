#!/usr/bin/env python3
"""
Comprehensive correctness tests comparing Python and Cython implementations.

This test suite ensures that the Cython-optimized modules produce identical
results to the original Python implementations.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import Python versions
from tentoku import deinflect as deinflect_py
from tentoku import normalize as normalize_py
from tentoku import word_search as word_search_py
from tentoku import sorting as sorting_py
from tentoku import type_matching as type_matching_py
from tentoku import variations as variations_py
from tentoku import yoon as yoon_py

# Import Cython versions
from tentoku import deinflect_cy
from tentoku import normalize_cy
from tentoku import word_search_cy
from tentoku import sorting_cy
from tentoku import type_matching_cy
from tentoku import variations_cy
from tentoku import yoon_cy


def test_normalize():
    """Test normalize functions."""
    print("\n=== Testing normalize ===")
    test_cases = [
        "私は学生です",
        "食べました",
        "12345",
        "こんにちは、世界",
        "",
        "あいうえお",
    ]

    for text in test_cases:
        # Test normalize_input
        py_result = normalize_py.normalize_input(text)
        cy_result = normalize_cy.normalize_input(text)
        assert py_result == cy_result, f"normalize_input mismatch for '{text}'"

        # Test kana_to_hiragana
        py_kana = normalize_py.kana_to_hiragana(text)
        cy_kana = normalize_cy.kana_to_hiragana(text)
        assert py_kana == cy_kana, f"kana_to_hiragana mismatch for '{text}'"

        # Test half_to_full_width_num
        py_full = normalize_py.half_to_full_width_num(text)
        cy_full = normalize_cy.half_to_full_width_num(text)
        assert py_full == cy_full, f"half_to_full_width_num mismatch for '{text}'"

        print(f"  ✓ '{text}' matches")

    print("  ✓ All normalize tests passed!")


def test_variations():
    """Test variations functions."""
    print("\n=== Testing variations ===")
    test_cases = [
        "ラーメン",
        "コーヒー",
        "學校",
        "國語",
        "あいうえお",
    ]

    for text in test_cases:
        # Test expand_choon
        py_choon = variations_py.expand_choon(text)
        cy_choon = variations_cy.expand_choon(text)
        assert py_choon == cy_choon, f"expand_choon mismatch for '{text}'"

        # Test kyuujitai_to_shinjitai
        py_kyuu = variations_py.kyuujitai_to_shinjitai(text)
        cy_kyuu = variations_cy.kyuujitai_to_shinjitai(text)
        assert py_kyuu == cy_kyuu, f"kyuujitai_to_shinjitai mismatch for '{text}'"

        print(f"  ✓ '{text}' matches")

    print("  ✓ All variations tests passed!")


def test_yoon():
    """Test yoon functions."""
    print("\n=== Testing yoon ===")
    test_cases = [
        ("きゃ", True),
        ("しゅ", True),
        ("ちょ", True),
        ("あい", False),
        ("", False),
        ("き", False),
        ("きゃきゃ", True),
    ]

    for text, expected in test_cases:
        py_result = yoon_py.ends_in_yoon(text)
        cy_result = yoon_cy.ends_in_yoon(text)
        assert py_result == cy_result == expected, f"ends_in_yoon mismatch for '{text}'"
        print(f"  ✓ '{text}' -> {expected}")

    print("  ✓ All yoon tests passed!")


def test_deinflect():
    """Test deinflect functions."""
    print("\n=== Testing deinflect ===")
    test_cases = [
        "食べました",
        "読んでいます",
        "高かった",
        "行きません",
        "書く",
        "見る",
        "食べさせられませんでした",
    ]

    for word in test_cases:
        py_result = deinflect_py.deinflect(word)
        cy_result = deinflect_cy.deinflect(word)

        # Compare lengths
        assert len(py_result) == len(cy_result), \
            f"deinflect length mismatch for '{word}': Python={len(py_result)}, Cython={len(cy_result)}"

        # Compare each candidate
        for i, (py_cand, cy_cand) in enumerate(zip(py_result, cy_result)):
            assert py_cand.word == cy_cand.word, \
                f"Candidate {i} word mismatch: {py_cand.word} != {cy_cand.word}"
            assert py_cand.type == cy_cand.type, \
                f"Candidate {i} type mismatch"
            assert len(py_cand.reason_chains) == len(cy_cand.reason_chains), \
                f"Candidate {i} reason_chains length mismatch"

        print(f"  ✓ '{word}' -> {len(py_result)} candidates match")

    print("  ✓ All deinflect tests passed!")


def test_is_only_digits():
    """Test is_only_digits function."""
    print("\n=== Testing is_only_digits ===")
    test_cases = [
        ("12345", True),
        ("１２３４５", True),
        ("123.45", True),
        ("あいうえお", False),
        ("", False),
        ("123abc", False),
    ]

    for text, expected in test_cases:
        py_result = word_search_py.is_only_digits(text)
        cy_result = word_search_cy.is_only_digits(text)
        assert py_result == cy_result == expected, \
            f"is_only_digits mismatch for '{text}'"
        print(f"  ✓ '{text}' -> {expected}")

    print("  ✓ All is_only_digits tests passed!")


def run_all_tests():
    """Run all correctness tests."""
    print("=" * 70)
    print("CYTHON CORRECTNESS TESTS")
    print("=" * 70)

    test_normalize()
    test_variations()
    test_yoon()
    test_deinflect()
    test_is_only_digits()

    print("\n" + "=" * 70)
    print("ALL CORRECTNESS TESTS PASSED!")
    print("=" * 70)


if __name__ == '__main__':
    run_all_tests()
