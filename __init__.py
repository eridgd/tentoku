"""
Tentoku (天読) - Python module for Japanese word tokenization.

This module provides Japanese text tokenization with deinflection support,
dictionary lookup, and greedy longest-match algorithm. It reimplements the
tokenization algorithm from 10ten Reader.
"""

__version__ = "0.1.7"

# Import using relative imports to avoid conflicts with stdlib tokenize
from . import tokenizer as _tokenize_module
from .dictionary import Dictionary
from .sqlite_dict import SQLiteDictionary
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
]

