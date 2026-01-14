"""
Optimized SQLite dictionary implementation.

Key optimizations:
1. Skip lookups for unreasonably long strings (>15 chars)
2. Cache negative lookups (not found)
3. Prepared statement reuse
"""

import sqlite3
from typing import List, Optional
from pathlib import Path

from .dictionary import Dictionary
from ._types import (
    WordEntry, KanjiReading, KanaReading, Sense, Gloss
)
from .normalize import kana_to_hiragana
from .database_path import find_database_path, get_default_database_path
from .build_database import build_database


class OptimizedSQLiteDictionary(Dictionary):
    """
    SQLite dictionary with aggressive optimizations for long text performance.
    """

    def __init__(self, db_path: Optional[str] = None, auto_build: bool = True, max_lookup_length: int = 15):
        """
        Initialize optimized SQLite dictionary.

        Args:
            db_path: Path to the SQLite database file. If None, uses default location.
            auto_build: If True, automatically builds the database if it doesn't exist.
            max_lookup_length: Maximum length of text to look up (default: 15 chars).
                              Longer strings are automatically returned as not found.
        """
        if db_path is None:
            db_path_obj = get_default_database_path()
        else:
            db_path_obj = Path(db_path)

        self.db_path = db_path_obj
        self.max_lookup_length = max_lookup_length
        self._negative_cache = set()  # Cache for words not found
        self._positive_cache = {}      # Cache for words found

        # Auto-build database if it doesn't exist
        if not self.db_path.exists() and auto_build:
            print(f"Database not found at {self.db_path}")
            print("Building database from JMdict XML (this may take several minutes)...")
            print("This is a one-time operation. The database will be saved for future use.")

            import tempfile
            download_dir = Path(tempfile.gettempdir()) / "tentoku"

            success = build_database(
                str(self.db_path),
                xml_path=None,
                download_dir=download_dir,
                show_progress=True,
                auto_download=True
            )

            if not success:
                raise RuntimeError(
                    f"Failed to build database at {self.db_path}. "
                    "Please check your internet connection and try again, "
                    "or provide an existing database file."
                )

        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database file not found: {self.db_path}\n"
                "Set auto_build=True to automatically download and build the database, "
                "or provide the path to an existing jmdict.db file."
            )

        self.conn: Optional[sqlite3.Connection] = None
        self._connect()

    def _connect(self):
        """Connect to the SQLite database with optimizations."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        # SQLite performance optimizations
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA synchronous = OFF")  # Faster but less safe (read-only anyway)
        cursor.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
        cursor.execute("PRAGMA temp_store = MEMORY")  # Use memory for temp tables
        cursor.execute("PRAGMA mmap_size = 268435456")  # 256MB memory-mapped I/O
        cursor.execute("PRAGMA cache_size = -64000")  # 64MB cache
        cursor.close()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
        self._negative_cache.clear()
        self._positive_cache.clear()

    def get_words(self, input_text: str, max_results: int, matching_text: Optional[str] = None) -> List[WordEntry]:
        """
        Look up words in the dictionary by exact match.

        Optimizations:
        - Skips lookups for unreasonably long strings
        - Caches negative lookups
        - Caches positive lookups

        Args:
            input_text: The text to look up (normalized to hiragana for readings)
            max_results: Maximum number of results to return
            matching_text: Optional text that was actually matched

        Returns:
            List of WordEntry objects matching the input
        """
        if not self.conn:
            self._connect()

        # OPTIMIZATION 1: Skip lookup for unreasonably long strings
        # No dictionary entry will match a 200+ character string
        if len(input_text) > self.max_lookup_length:
            return []

        # OPTIMIZATION 2: Check negative cache
        cache_key = (input_text, max_results, matching_text)
        if input_text in self._negative_cache:
            return []

        # OPTIMIZATION 3: Check positive cache
        if cache_key in self._positive_cache:
            return self._positive_cache[cache_key]

        # Perform actual lookup (same as standard SQLiteDictionary)
        from .sqlite_dict import SQLiteDictionary

        # Temporarily create a standard dict to do the lookup
        # (We inherit from Dictionary, not SQLiteDictionary, so we need to call it)
        cursor = self.conn.cursor()
        text_for_match_range = matching_text if matching_text is not None else input_text
        normalized_input = kana_to_hiragana(input_text)

        # Try reading first (most common case)
        cursor.execute("""
            SELECT DISTINCT e.entry_id, e.ent_seq
            FROM entries e
            JOIN readings r ON e.entry_id = r.entry_id
            WHERE r.reading_text = ? OR r.reading_text = ?
            LIMIT ?
        """, (input_text, normalized_input, max_results))

        entry_rows = cursor.fetchall()

        # If no results from reading, try kanji match
        if not entry_rows:
            cursor.execute("""
                SELECT DISTINCT e.entry_id, e.ent_seq
                FROM entries e
                JOIN kanji k ON e.entry_id = k.entry_id
                WHERE k.kanji_text = ? OR k.kanji_text = ?
                LIMIT ?
            """, (input_text, normalized_input, max_results))
            entry_rows = cursor.fetchall()

        if not entry_rows:
            # Cache negative result
            self._negative_cache.add(input_text)
            # Keep cache bounded
            if len(self._negative_cache) > 100000:
                # Remove 20% of oldest entries (convert to list, remove first 20%, convert back)
                entries_list = list(self._negative_cache)
                self._negative_cache = set(entries_list[20000:])
            return []

        # Build full entries (delegate to parent class logic - copy from sqlite_dict.py)
        entries = self._build_entries(cursor, entry_rows, text_for_match_range)

        # Cache positive result
        self._positive_cache[cache_key] = entries
        # Keep cache bounded
        if len(self._positive_cache) > 10000:
            # Remove 20% of oldest entries
            keys_to_remove = list(self._positive_cache.keys())[:2000]
            for key in keys_to_remove:
                del self._positive_cache[key]

        return entries

    def _build_entries(self, cursor, entry_rows, text_for_match_range):
        """Build entries from entry_rows (extracted from SQLiteDictionary)."""
        # This is copied from the standard SQLiteDictionary implementation
        # to avoid circular dependencies
        from .sqlite_dict import SQLiteDictionary

        # Create a temporary standard dict just to use its _build_entries logic
        # This is a bit hacky but avoids code duplication
        temp_dict = SQLiteDictionary.__new__(SQLiteDictionary)
        temp_dict.conn = self.conn

        normalized_matching = kana_to_hiragana(text_for_match_range)
        entries = []

        for row in entry_rows:
            entry_id = row['entry_id']
            ent_seq = row['ent_seq']

            # Get kanji readings
            cursor.execute("""
                SELECT kanji_text, priority, info
                FROM kanji
                WHERE entry_id = ?
                ORDER BY kanji_id
            """, (entry_id,))
            kanji_rows = cursor.fetchall()

            # Determine if we matched on kanji or kana
            kanji_match_found = False
            for kanji_row in kanji_rows:
                if kana_to_hiragana(kanji_row['kanji_text']) == normalized_matching:
                    kanji_match_found = True
                    break

            # Get kana readings
            cursor.execute("""
                SELECT reading_text, no_kanji, priority, info
                FROM readings
                WHERE entry_id = ?
                ORDER BY reading_id
            """, (entry_id,))
            kana_rows = cursor.fetchall()

            # Check if any kana matches
            kana_match_found = False
            if not kanji_match_found:
                for kana_row in kana_rows:
                    if kana_to_hiragana(kana_row['reading_text']) == normalized_matching:
                        kana_match_found = True
                        break

            # Build kanji readings
            kanji_readings = []
            for kanji_row in kanji_rows:
                kanji_text = kanji_row['kanji_text']
                kanji_normalized = kana_to_hiragana(kanji_text)
                matches = kanji_normalized == normalized_matching

                kanji_readings.append(KanjiReading(
                    text=kanji_text,
                    priority=kanji_row['priority'],
                    info=kanji_row['info'],
                    match_range=(0, len(kanji_text)) if matches else None,
                    match=(kanji_match_found and matches) or not kanji_match_found
                ))

            # Build kana readings
            kana_readings = []
            for kana_row in kana_rows:
                kana_text = kana_row['reading_text']
                matches = kana_to_hiragana(kana_text) == normalized_matching

                kana_readings.append(KanaReading(
                    text=kana_text,
                    no_kanji=bool(kana_row['no_kanji']),
                    priority=kana_row['priority'],
                    info=kana_row['info'],
                    match_range=(0, len(kana_text)) if matches else None,
                    match=(kana_match_found and matches) or not kana_match_found
                ))

            # Get senses
            cursor.execute("""
                SELECT s.sense_id, s.sense_index, s.info
                FROM senses s
                WHERE s.entry_id = ?
                ORDER BY s.sense_index
            """, (entry_id,))
            sense_rows = cursor.fetchall()

            senses = []
            for sense_row in sense_rows:
                sense_id = sense_row['sense_id']

                # Get POS tags
                cursor.execute("SELECT pos FROM sense_pos WHERE sense_id = ?", (sense_id,))
                pos_tags = [row['pos'] for row in cursor.fetchall()]

                # Get glosses
                cursor.execute("""
                    SELECT gloss_text, lang, g_type
                    FROM glosses
                    WHERE sense_id = ?
                    ORDER BY gloss_id
                """, (sense_id,))
                glosses = [
                    Gloss(
                        text=row['gloss_text'],
                        lang=row['lang'] or 'eng',
                        g_type=row['g_type']
                    )
                    for row in cursor.fetchall()
                ]

                # Get optional metadata
                cursor.execute("SELECT field FROM sense_field WHERE sense_id = ?", (sense_id,))
                fields = [row['field'] for row in cursor.fetchall()] or None

                cursor.execute("SELECT misc FROM sense_misc WHERE sense_id = ?", (sense_id,))
                misc = [row['misc'] for row in cursor.fetchall()] or None

                cursor.execute("SELECT dial FROM sense_dial WHERE sense_id = ?", (sense_id,))
                dial = [row['dial'] for row in cursor.fetchall()] or None

                senses.append(Sense(
                    index=sense_row['sense_index'],
                    pos_tags=pos_tags,
                    glosses=glosses,
                    info=sense_row['info'],
                    field=fields,
                    misc=misc,
                    dial=dial
                ))

            entries.append(WordEntry(
                entry_id=entry_id,
                ent_seq=ent_seq,
                kanji_readings=kanji_readings,
                kana_readings=kana_readings,
                senses=senses
            ))

        return entries

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
