"""
Tentoku (天読) - Python module for Japanese word tokenization.

This module provides Japanese text tokenization with deinflection support,
dictionary lookup, and greedy longest-match algorithm. It reimplements the
tokenization algorithm from 10ten Reader.
"""

__version__ = "0.2.0"

# Import using relative imports to avoid conflicts with stdlib tokenize
from . import tokenizer as _tokenize_module
from .dictionary import Dictionary
from .sqlite_dict import SQLiteDictionary as _SQLiteDictionary_Standard
from .sqlite_dict_optimized import OptimizedSQLiteDictionary as SQLiteDictionary

# Use OptimizedSQLiteDictionary which has:
# 1. Length-based lookup skipping (>15 chars)
# 2. Negative lookup caching (words not found)
# 3. Positive lookup caching (words found)
# This reduces database lookups dramatically for long text
_FAST_SQLITE_AVAILABLE = False

# Try to import trie-accelerated dictionary (optional, requires marisa-trie)
try:
    from .trie_dict import TrieAcceleratedDictionary
    _TRIE_AVAILABLE = True
except ImportError:
    TrieAcceleratedDictionary = None
    _TRIE_AVAILABLE = False

from ._types import (
    WordEntry, WordResult, Token, WordType, Reason
)
from .database_path import get_default_database_path, find_database_path
from .build_database import build_database

# Re-export the tokenize function
tokenize = _tokenize_module.tokenize

__all__ = [
    "tokenize",
    "Dictionary",
    "SQLiteDictionary",  # Now points to OptimizedSQLiteDictionary
    "TrieAcceleratedDictionary",  # Fast trie-based dictionary (requires marisa-trie)
    "WordEntry",
    "WordResult",
    "Token",
    "WordType",
    "Reason",
    "get_default_database_path",
    "find_database_path",
    "build_database",
    "is_using_cython",
    "verify_cython_status",
    "is_using_trie",
]


def is_using_cython():
    """
    Check if Cython optimizations are active.

    Returns:
        bool: True if all modules are using Cython, False otherwise
    """
    try:
        from .verify_cython import get_cython_status
        return get_cython_status() and _FAST_SQLITE_AVAILABLE
    except ImportError:
        return False


def verify_cython_status(verbose=True):
    """
    Verify and optionally print the status of Cython optimizations.

    Args:
        verbose: If True, print detailed report. If False, just return status.

    Returns:
        bool: True if all modules are using Cython, False otherwise
    """
    try:
        from .verify_cython import print_verification_report, verify_all_modules
        if verbose:
            print_verification_report()
        else:
            _, all_cython = verify_all_modules()
            return all_cython
        return is_using_cython()
    except ImportError:
        if verbose:
            print("Warning: verify_cython module not available")
        return False


def is_using_trie():
    """
    Check if trie-accelerated dictionary is available and being used.

    Returns:
        bool: True if marisa-trie is installed and trie dictionary is available
    """
    return _TRIE_AVAILABLE

