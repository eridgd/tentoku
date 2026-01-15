"""
Trie-accelerated dictionary that uses marisa-trie for fast lookups.

This module provides a dictionary implementation that uses a trie for O(key_length)
existence checks, dramatically reducing the number of SQLite queries needed during
tokenization.

The trie stores dictionary keys (kanji forms and readings) mapped to entry IDs.
Full entry data is still fetched from SQLite, but only for entries that actually match.
"""

import struct
from pathlib import Path
from typing import List, Optional, Dict, Set

from .dictionary import Dictionary
from ._types import WordEntry
from .normalize import kana_to_hiragana
from .database_path import find_database_path, get_default_database_path


def _should_normalize(text: str) -> bool:
    """
    Check if text should be normalized to hiragana for lookup.

    Only normalizes pure katakana strings to match SQLite behavior.
    Mixed hiragana+katakana strings should not be normalized.

    Optimized: checks first char to quickly reject mixed strings.
    """
    if not text:
        return False

    # Quick check: if first char isn't katakana, don't normalize
    first_code = ord(text[0])
    if not ((0x30A0 <= first_code <= 0x30FF) or (0xFF65 <= first_code <= 0xFF9F)):
        return False

    # Full check: all chars must be katakana
    for char in text:
        code = ord(char)
        if not ((0x30A0 <= code <= 0x30FF) or (0xFF65 <= code <= 0xFF9F)):
            return False
    return True

# Try to import marisa-trie
try:
    import marisa_trie
    MARISA_AVAILABLE = True
except ImportError:
    MARISA_AVAILABLE = False

# Try to import Cython-optimized functions
try:
    from .trie_dict_cy import (
        unpack_entry_ids as _unpack_entry_ids_cy,
        get_entry_ids_fast as _get_entry_ids_fast_cy,
        get_entry_ids_normalized_fast as _get_entry_ids_normalized_fast_cy,
        trie_exists as _trie_exists_cy,
    )
    _CYTHON_AVAILABLE = True
except ImportError:
    _CYTHON_AVAILABLE = False


def _unpack_entry_ids_py(packed: bytes) -> List[int]:
    """Unpack entry IDs from packed bytes (Python fallback)."""
    num_ids = len(packed) // 4
    return list(struct.unpack('<' + 'I' * num_ids, packed))


def _get_entry_ids_py(trie, text: str) -> List[int]:
    """Get entry IDs from trie for exact match (Python fallback)."""
    if text not in trie:
        return []
    packed = trie[text][0]
    return _unpack_entry_ids_py(packed)


def _get_entry_ids_normalized_py(trie, text: str) -> List[int]:
    """Get entry IDs, trying both original and hiragana-normalized forms (Python fallback)."""
    ids: Set[int] = set()

    # Try original
    if text in trie:
        ids.update(_unpack_entry_ids_py(trie[text][0]))

    # Try hiragana-normalized (for pure katakana input only)
    if _should_normalize(text):
        normalized = kana_to_hiragana(text)
        if normalized != text and normalized in trie:
            ids.update(_unpack_entry_ids_py(trie[normalized][0]))

    return sorted(ids)


# Use Cython versions if available
if _CYTHON_AVAILABLE:
    _unpack_entry_ids = _unpack_entry_ids_cy
    _get_entry_ids = _get_entry_ids_fast_cy
    _get_entry_ids_normalized = _get_entry_ids_normalized_fast_cy
else:
    _unpack_entry_ids = _unpack_entry_ids_py
    _get_entry_ids = _get_entry_ids_py
    _get_entry_ids_normalized = _get_entry_ids_normalized_py


class TrieAcceleratedDictionary(Dictionary):
    """
    Dictionary with trie-based fast path for existence checks.

    Uses marisa-trie for O(key_length) lookups to determine if a word exists
    in the dictionary. SQLite is only consulted for entries that actually match,
    dramatically reducing database queries during tokenization.
    """

    def __init__(self, db_path: Optional[str] = None, auto_build: bool = True):
        """
        Initialize trie-accelerated dictionary.

        Args:
            db_path: Path to the SQLite database file. If None, uses default location.
            auto_build: If True, automatically builds database/trie if they don't exist.

        Raises:
            ImportError: If marisa-trie is not installed
        """
        if not MARISA_AVAILABLE:
            raise ImportError(
                "marisa-trie is required for TrieAcceleratedDictionary. "
                "Install with: pip install marisa-trie"
            )

        # Import SQLite dictionary (lazy to avoid circular import)
        from .sqlite_dict_optimized import OptimizedSQLiteDictionary

        if db_path is None:
            db_path_obj = get_default_database_path()
        else:
            db_path_obj = Path(db_path)

        self.db_path = db_path_obj

        # Initialize SQLite backend first (may auto-build database)
        self._sqlite = OptimizedSQLiteDictionary(str(db_path_obj), auto_build=auto_build)

        # Load or build trie
        trie_path = self._ensure_trie_exists()
        self._trie = marisa_trie.BytesTrie().load(str(trie_path))
        self._trie_path = trie_path

    def _ensure_trie_exists(self) -> Path:
        """Ensure trie index exists, building if necessary."""
        from .build_trie import ensure_trie_exists
        return ensure_trie_exists(self.db_path, show_progress=True)

    def exists(self, text: str) -> bool:
        """
        Fast O(len) check if text exists in dictionary.

        Checks both the exact text and its hiragana-normalized form
        (only for pure katakana strings to match SQLite behavior).

        Args:
            text: Text to check

        Returns:
            True if text (or its normalized form) exists in dictionary
        """
        # Python implementation (Cython disabled until we fix it)
        if text in self._trie:
            return True

        # Only normalize pure katakana to match SQLite behavior
        if _should_normalize(text):
            normalized = kana_to_hiragana(text)
            if normalized != text and normalized in self._trie:
                return True

        return False

    def get_entry_ids(self, text: str) -> List[int]:
        """
        Get entry IDs for exact match.

        Args:
            text: Text to look up

        Returns:
            List of entry IDs, empty if not found
        """
        return _get_entry_ids(self._trie, text)

    def get_entry_ids_normalized(self, text: str) -> List[int]:
        """
        Get entry IDs, trying both original and hiragana-normalized forms.

        Args:
            text: Text to look up (may be katakana)

        Returns:
            Sorted list of entry IDs from both forms
        """
        return _get_entry_ids_normalized(self._trie, text)

    def get_words(self, input_text: str, max_results: int = 20,
                  matching_text: Optional[str] = None) -> List[WordEntry]:
        """
        Get dictionary entries for input text.

        This is the main API - compatible with existing Dictionary interface.
        Uses trie for fast existence check, then fetches from SQLite.

        Args:
            input_text: The text to look up
            max_results: Maximum number of results to return
            matching_text: Optional text that was actually matched (for match_range)

        Returns:
            List of WordEntry objects matching the input
        """
        # Fast path: check trie first
        entry_ids = self.get_entry_ids_normalized(input_text)

        if not entry_ids:
            return []

        # Limit entry_ids before fetching
        entry_ids = entry_ids[:max_results]

        # Fetch full entries from SQLite
        return self._sqlite.get_entries_by_ids(
            entry_ids,
            matching_text=matching_text or input_text
        )

    def get_words_batch(self, texts: List[str], max_results_per: int = 20) -> Dict[str, List[WordEntry]]:
        """
        Batch lookup for multiple texts at once.

        More efficient than individual lookups when processing many candidates.

        Args:
            texts: List of texts to look up
            max_results_per: Maximum results per text

        Returns:
            Dictionary mapping each text to its list of WordEntry objects
        """
        # Collect all entry_ids across all texts
        text_to_ids: Dict[str, List[int]] = {}
        all_ids: Set[int] = set()

        for text in texts:
            ids = self.get_entry_ids_normalized(text)
            limited_ids = ids[:max_results_per]
            text_to_ids[text] = limited_ids
            all_ids.update(limited_ids)

        if not all_ids:
            return {text: [] for text in texts}

        # Single batched fetch from SQLite
        entries_by_id = self._sqlite.get_entries_by_ids_map(list(all_ids))

        # Map back to texts
        result: Dict[str, List[WordEntry]] = {}
        for text, ids in text_to_ids.items():
            result[text] = [entries_by_id[id_] for id_ in ids if id_ in entries_by_id]

        return result

    def close(self):
        """Close database connection."""
        if self._sqlite:
            self._sqlite.close()
            self._sqlite = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
