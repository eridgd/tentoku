# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: initializedcheck=False
"""
Cython-optimized SQLite dictionary implementation.

This module provides a faster SQLite-based dictionary using Cython
wrappers around the SQLite C API for reduced overhead.
"""

import sqlite3
from typing import List, Optional
from pathlib import Path

from tentoku.dictionary import Dictionary
from tentoku._types import (
    WordEntry, KanjiReading, KanaReading, Sense, Gloss
)
from tentoku.normalize_cy import kana_to_hiragana
from tentoku.database_path import find_database_path, get_default_database_path
from tentoku.build_database import build_database


class FastSQLiteDictionary(Dictionary):
    """
    Fast SQLite-based dictionary implementation with Cython optimizations.

    This version uses optimized SQL queries and reduces Python object overhead.
    """

    def __init__(self, db_path: Optional[str] = None, auto_build: bool = True, cache_size: int = 1000):
        """
        Initialize fast SQLite dictionary.

        Args:
            db_path: Path to the SQLite database file. If None, uses default location.
            auto_build: If True, automatically builds the database if it doesn't exist.
            cache_size: Number of entries to cache (default: 1000, 0 to disable)
        """
        if db_path is None:
            db_path_obj = get_default_database_path()
        else:
            db_path_obj = Path(db_path)

        self.db_path = db_path_obj

        # Auto-build database if it doesn't exist
        if not self.db_path.exists() and auto_build:
            print(f"Database not found at {self.db_path}")
            print("Building database from JMdict XML (this may take several minutes)...")
            print("This is a one-time operation. The database will be saved for future use.")

            # Use temporary directory for downloads (will be cleaned up)
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

        self.conn = None
        self._cache = {} if cache_size > 0 else None
        self._connect()

    def _connect(self):
        """Connect to the SQLite database with optimizations."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        # SQLite performance optimizations
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA synchronous = OFF")  # Faster but less safe (read-only anyway)
        cursor.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging for better concurrency
        cursor.execute("PRAGMA temp_store = MEMORY")  # Use memory for temp tables
        cursor.execute("PRAGMA mmap_size = 268435456")  # 256MB memory-mapped I/O
        cursor.execute("PRAGMA cache_size = -64000")  # 64MB cache
        cursor.close()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
        if self._cache is not None:
            self._cache.clear()

    def get_words(self, str input_text, int max_results, str matching_text=None):
        """
        Look up words in the dictionary by exact match.

        Optimized with:
        - Result caching
        - Reduced object allocations
        - Optimized SQL queries

        Args:
            input_text: The text to look up (normalized to hiragana for readings)
            max_results: Maximum number of results to return
            matching_text: Optional text that was actually matched (for setting matchRange).

        Returns:
            List of WordEntry objects matching the input, with matchRange set on matching readings
        """
        if not self.conn:
            self._connect()

        # Check cache first
        cdef str cache_key
        if self._cache is not None:
            cache_key = f"{input_text}:{max_results}:{matching_text}"
            if cache_key in self._cache:
                return self._cache[cache_key]

        cdef object cursor = self.conn.cursor()
        cdef str text_for_match_range = matching_text if matching_text is not None else input_text
        cdef str normalized_input = kana_to_hiragana(input_text)
        cdef str normalized_matching = kana_to_hiragana(text_for_match_range)

        # Optimized query - fetch entry_ids first
        cursor.execute("""
            SELECT DISTINCT e.entry_id, e.ent_seq
            FROM entries e
            LEFT JOIN readings r ON e.entry_id = r.entry_id
            LEFT JOIN kanji k ON e.entry_id = k.entry_id
            WHERE r.reading_text = ? OR r.reading_text = ?
               OR k.kanji_text = ? OR k.kanji_text = ?
            LIMIT ?
        """, (input_text, normalized_input, input_text, normalized_input, max_results))

        cdef list entry_rows = cursor.fetchall()

        if not entry_rows:
            return []

        # Build entries list
        cdef list entries = []
        cdef object row, entry_id, ent_seq
        cdef list kanji_rows, kana_rows, sense_rows
        cdef list kanji_readings, kana_readings, senses
        cdef bint kanji_match_found, kana_match_found
        cdef object kanji_row, kana_row, sense_row
        cdef str kanji_text, kanji_normalized, kana_text
        cdef bint matches

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

            # Build kanji readings with matchRange
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

            # Build kana readings with matchRange
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

            # Get senses with POS tags
            cursor.execute("""
                SELECT s.sense_id, s.sense_index, s.info
                FROM senses s
                WHERE s.entry_id = ?
                ORDER BY s.sense_index
            """, (entry_id,))
            sense_rows = cursor.fetchall()

            senses = self._build_senses(cursor, sense_rows)

            entries.append(WordEntry(
                entry_id=entry_id,
                ent_seq=ent_seq,
                kanji_readings=kanji_readings,
                kana_readings=kana_readings,
                senses=senses
            ))

        # Cache the result
        if self._cache is not None:
            # Keep cache size bounded
            if len(self._cache) > 10000:
                # Remove 20% of oldest entries (simple FIFO)
                keys_to_remove = list(self._cache.keys())[:2000]
                for key in keys_to_remove:
                    del self._cache[key]
            self._cache[cache_key] = entries

        return entries

    def _build_senses(self, object cursor, list sense_rows):
        """Build senses list from rows (optimized helper)."""
        cdef list senses = []
        cdef object sense_row, sense_id
        cdef list pos_tags, glosses, fields, misc, dial

        for sense_row in sense_rows:
            sense_id = sense_row['sense_id']

            # Get POS tags
            cursor.execute("""
                SELECT pos FROM sense_pos WHERE sense_id = ?
            """, (sense_id,))
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

            # Get optional metadata (only if needed)
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

        return senses

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
