#!/usr/bin/env python3
"""
Utility to verify that Cython modules are being used throughout the package.

This module checks all code paths to ensure Cython optimization is active.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def is_cython_function(func):
    """Check if a function is a Cython function."""
    func_type_str = str(type(func)).lower()
    return 'cython' in func_type_str


def verify_all_modules():
    """Verify that all modules are using Cython where available."""
    results = {}

    # Import all modules
    from tentoku import normalize, deinflect, yoon, variations, type_matching, sorting, word_search

    # Check each module's functions
    modules_to_check = {
        'normalize': [
            ('normalize_input', normalize.normalize_input),
            ('kana_to_hiragana', normalize.kana_to_hiragana),
        ],
        'deinflect': [
            ('deinflect', deinflect.deinflect),
        ],
        'yoon': [
            ('ends_in_yoon', yoon.ends_in_yoon),
        ],
        'variations': [
            ('expand_choon', variations.expand_choon),
            ('kyuujitai_to_shinjitai', variations.kyuujitai_to_shinjitai),
        ],
        'type_matching': [
            ('entry_matches_type', type_matching.entry_matches_type),
        ],
        'sorting': [
            ('sort_word_results', sorting.sort_word_results),
        ],
        'word_search': [
            ('word_search', word_search.word_search),
            ('lookup_candidates', word_search.lookup_candidates),
            ('is_only_digits', word_search.is_only_digits),
        ],
    }

    all_cython = True
    for module_name, functions in modules_to_check.items():
        module_results = {}
        for func_name, func in functions:
            is_cython = is_cython_function(func)
            module_results[func_name] = is_cython
            if not is_cython:
                all_cython = False
        results[module_name] = module_results

    return results, all_cython


def print_verification_report():
    """Print a detailed verification report."""
    print("=" * 70)
    print("CYTHON VERIFICATION REPORT")
    print("=" * 70)
    print()

    results, all_cython = verify_all_modules()

    for module_name, module_results in results.items():
        print(f"\n{module_name}:")
        for func_name, is_cython in module_results.items():
            status = "✓ Cython" if is_cython else "✗ Python"
            print(f"  {func_name:<30} {status}")

    print("\n" + "=" * 70)
    if all_cython:
        print("✓ ALL MODULES USING CYTHON")
    else:
        print("✗ SOME MODULES NOT USING CYTHON")
        print("\nThis is expected if:")
        print("  1. Cython extensions weren't built (run: python setup.py build_ext --inplace)")
        print("  2. Package was installed without build step")
    print("=" * 70)

    return all_cython


def get_cython_status():
    """Get a simple boolean indicating if Cython is being used."""
    _, all_cython = verify_all_modules()
    return all_cython


if __name__ == '__main__':
    success = print_verification_report()
    sys.exit(0 if success else 1)
