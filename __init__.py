"""
Tentoku (天読) - Python module for Japanese word tokenization.

This module provides Japanese text tokenization with deinflection support,
dictionary lookup, and greedy longest-match algorithm. It reimplements the
tokenization algorithm from 10ten Reader.
"""

__version__ = "0.1.8"

# Import using relative imports to avoid conflicts with stdlib tokenize
from . import tokenizer as _tokenize_module
from .dictionary import Dictionary
from .sqlite_dict import SQLiteDictionary

# Note: FastSQLiteDictionary was removed as it was actually slower than the standard version
# The caching overhead and query complexity made it perform worse in practice
_FAST_SQLITE_AVAILABLE = False

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
    "SQLiteDictionary",
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

