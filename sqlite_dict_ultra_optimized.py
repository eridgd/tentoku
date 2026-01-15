"""
Ultra-optimized SQLite dictionary implementation.

Key optimizations:
1. Batch all queries using IN clauses instead of per-entry queries
2. Prepared statement reuse
3. Aggressive caching (entry-level, not just word-level)
4. Skip lookups for unreasonably long strings
5. SQLite performance pragmas
"""

import sqlite3
from typing import List, Optional, Dict, Set
from pathlib import Path
from collections import defaultdict

from .dictionary import Dictionary
from ._types import (
    WordEntry, KanjiReading, KanaReading, Sense, Gloss
)
from .normalize import kana_to_hiragana
from .database_path import get_default_database_path
from .build_database import build_database


class UltraOptimizedSQLiteDictionary(Dictionary):
    """
    Ultra-optimized SQLite dictionary with batched queries.
    
    This version batches all database queries to minimize round-trips.
    Instead of querying each entry separately, it fetches all data in bulk.
    """

    def __init__(self, db_path: Optional[str] = None, auto_build: bool = True, max_lookup_length: int = 15):
        """
        Initialize ultra-optimized SQLite dictionary.

        Args:
            db_path: Path to the SQLite database file. If None, uses default location.
            auto_build: If True, automatically builds the database if it doesn't exist.
            max_lookup_length: Maximum length of text to look up (default: 15 chars).
        """
        if db_path is None:
            db_path_obj = get_default_database_path()
        else:
            db_path_obj = Path(db_path)

        self.db_path = db_path_obj
        self.max_lookup_length = max_lookup_length
        self._negative_cache = set()  # Cache for words not found
        self._positive_cache = {}      # Cache for words found
        self._entry_cache = {}         # Cache for full entry data by entry_id

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
        """Connect to the SQLite database with aggressive optimizations."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        # Aggressive SQLite performance optimizations
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA synchronous = OFF")  # Faster but less safe (read-only anyway)
        cursor.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
        cursor.execute("PRAGMA temp_store = MEMORY")  # Use memory for temp tables
        cursor.execute("PRAGMA mmap_size = 268435456")  # 256MB memory-mapped I/O
        cursor.execute("PRAGMA cache_size = -128000")  # 128MB cache (doubled)
        cursor.execute("PRAGMA page_size = 4096")  # Standard page size
        cursor.execute("PRAGMA optimize")  # Optimize query planner
        cursor.close()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
        self._negative_cache.clear()
        self._positive_cache.clear()
        self._entry_cache.clear()

    def get_words(self, input_text: str, max_results: int, matching_text: Optional[str] = None) -> List[WordEntry]:
        """
        Look up words in the dictionary by exact match.

        Optimizations:
        - Skips lookups for unreasonably long strings
        - Caches negative and positive lookups
        - Uses batched queries to minimize database round-trips

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
        if len(input_text) > self.max_lookup_length:
            return []

        # OPTIMIZATION 2: Check negative cache
        cache_key = (input_text, max_results, matching_text)
        if input_text in self._negative_cache:
            return []

        # OPTIMIZATION 3: Check positive cache
        if cache_key in self._positive_cache:
            return self._positive_cache[cache_key]

        text_for_match_range = matching_text if matching_text is not None else input_text
        normalized_input = kana_to_hiragana(input_text)
        normalized_matching = kana_to_hiragana(text_for_match_range)

        cursor = self.conn.cursor()

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
                entries_list = list(self._negative_cache)
                self._negative_cache = set(entries_list[20000:])
            return []

        # OPTIMIZATION 4: Batch fetch ALL entry data in one go instead of per-entry queries
        entry_ids = [row['entry_id'] for row in entry_rows]
        entries = self._build_entries_batched(cursor, entry_ids, entry_rows, normalized_matching)

        # Cache positive result
        self._positive_cache[cache_key] = entries
        # Keep cache bounded
        if len(self._positive_cache) > 10000:
            keys_to_remove = list(self._positive_cache.keys())[:2000]
            for key in keys_to_remove:
                del self._positive_cache[key]

        return entries

    def _build_entries_batched(self, cursor, entry_ids: List[int], entry_rows: List, normalized_matching: str) -> List[WordEntry]:
        """
        Build entries using batched queries - MUCH faster than per-entry queries.
        
        This is the key optimization: instead of querying each entry separately,
        we fetch all data for all entries in bulk using IN clauses.
        """
        # Check entry cache first
        cached_entries = {}
        uncached_entry_ids = []
        for entry_id in entry_ids:
            if entry_id in self._entry_cache:
                cached_entries[entry_id] = self._entry_cache[entry_id]
            else:
                uncached_entry_ids.append(entry_id)
        
        # If all entries are cached, return them (but still need to set match_range)
        if not uncached_entry_ids:
            # Still need to set match_range based on normalized_matching
            entries = []
            for row in entry_rows:
                entry_id = row['entry_id']
                cached_entry = cached_entries[entry_id]
                # Create new entry with match_range set
                entries.append(self._set_match_range(cached_entry, normalized_matching))
            return entries
        
        # Batch fetch all kanji readings for all entries at once
        placeholders = ','.join('?' * len(uncached_entry_ids))
        cursor.execute(f"""
            SELECT kanji_id, entry_id, kanji_text, priority, info
            FROM kanji
            WHERE entry_id IN ({placeholders})
            ORDER BY entry_id, kanji_id
        """, uncached_entry_ids)
        kanji_rows = cursor.fetchall()
        
        # Batch fetch all kana readings for all entries at once
        cursor.execute(f"""
            SELECT reading_id, entry_id, reading_text, no_kanji, priority, info
            FROM readings
            WHERE entry_id IN ({placeholders})
            ORDER BY entry_id, reading_id
        """, uncached_entry_ids)
        kana_rows = cursor.fetchall()
        
        # Batch fetch all senses for all entries at once
        cursor.execute(f"""
            SELECT sense_id, entry_id, sense_index, info
            FROM senses
            WHERE entry_id IN ({placeholders})
            ORDER BY entry_id, sense_index
        """, uncached_entry_ids)
        sense_rows = cursor.fetchall()
        
        # Get all sense_ids for batch fetching sense data
        sense_ids = [row['sense_id'] for row in sense_rows]
        
        # Batch fetch all POS tags for all senses at once
        sense_pos_map = defaultdict(list)
        if sense_ids:
            placeholders_sense = ','.join('?' * len(sense_ids))
            cursor.execute(f"""
                SELECT sense_id, pos
                FROM sense_pos
                WHERE sense_id IN ({placeholders_sense})
                ORDER BY sense_id
            """, sense_ids)
            for row in cursor.fetchall():
                sense_pos_map[row['sense_id']].append(row['pos'])
        
        # Batch fetch all glosses for all senses at once
        sense_glosses_map = defaultdict(list)
        if sense_ids:
            cursor.execute(f"""
                SELECT sense_id, gloss_text, lang, g_type, gloss_id
                FROM glosses
                WHERE sense_id IN ({placeholders_sense})
                ORDER BY sense_id, gloss_id
            """, sense_ids)
            for row in cursor.fetchall():
                sense_glosses_map[row['sense_id']].append(Gloss(
                    text=row['gloss_text'],
                    lang=row['lang'] or 'eng',
                    g_type=row['g_type']
                ))
        
        # Batch fetch all sense fields
        sense_fields_map = defaultdict(list)
        if sense_ids:
            cursor.execute(f"""
                SELECT sense_id, field
                FROM sense_field
                WHERE sense_id IN ({placeholders_sense})
            """, sense_ids)
            for row in cursor.fetchall():
                sense_fields_map[row['sense_id']].append(row['field'])
        
        # Batch fetch all sense misc
        sense_misc_map = defaultdict(list)
        if sense_ids:
            cursor.execute(f"""
                SELECT sense_id, misc
                FROM sense_misc
                WHERE sense_id IN ({placeholders_sense})
            """, sense_ids)
            for row in cursor.fetchall():
                sense_misc_map[row['sense_id']].append(row['misc'])
        
        # Batch fetch all sense dial
        sense_dial_map = defaultdict(list)
        if sense_ids:
            cursor.execute(f"""
                SELECT sense_id, dial
                FROM sense_dial
                WHERE sense_id IN ({placeholders_sense})
            """, sense_ids)
            for row in cursor.fetchall():
                sense_dial_map[row['sense_id']].append(row['dial'])
        
        # Group data by entry_id
        kanji_by_entry = defaultdict(list)
        for row in kanji_rows:
            kanji_by_entry[row['entry_id']].append(row)
        
        kana_by_entry = defaultdict(list)
        for row in kana_rows:
            kana_by_entry[row['entry_id']].append(row)
        
        senses_by_entry = defaultdict(list)
        for row in sense_rows:
            senses_by_entry[row['entry_id']].append(row)
        
        # Build entries from batched data
        entries = []
        entry_id_to_row = {row['entry_id']: row for row in entry_rows}
        
        for entry_id in entry_ids:
            if entry_id in cached_entries:
                # Use cached entry but set match_range
                entry = self._set_match_range(cached_entries[entry_id], normalized_matching)
                entries.append(entry)
                continue
            
            row = entry_id_to_row[entry_id]
            ent_seq = row['ent_seq']
            
            # Build kanji readings
            kanji_readings = []
            kanji_match_found = False
            for kanji_row in kanji_by_entry[entry_id]:
                kanji_text = kanji_row['kanji_text']
                kanji_normalized = kana_to_hiragana(kanji_text)
                matches = kanji_normalized == normalized_matching
                if matches:
                    kanji_match_found = True
                
                kanji_readings.append(KanjiReading(
                    text=kanji_text,
                    priority=kanji_row['priority'],
                    info=kanji_row['info'],
                    match_range=(0, len(kanji_text)) if matches else None,
                    match=(kanji_match_found and matches) or not kanji_match_found
                ))
            
            # Build kana readings
            kana_readings = []
            kana_match_found = False
            if not kanji_match_found:
                for kana_row in kana_by_entry[entry_id]:
                    kana_text = kana_row['reading_text']
                    matches = kana_to_hiragana(kana_text) == normalized_matching
                    if matches:
                        kana_match_found = True
                    
                    kana_readings.append(KanaReading(
                        text=kana_text,
                        no_kanji=bool(kana_row['no_kanji']),
                        priority=kana_row['priority'],
                        info=kana_row['info'],
                        match_range=(0, len(kana_text)) if matches else None,
                        match=(kana_match_found and matches) or not kana_match_found
                    ))
            else:
                # Still build kana readings even if kanji matched
                for kana_row in kana_by_entry[entry_id]:
                    kana_text = kana_row['reading_text']
                    matches = kana_to_hiragana(kana_text) == normalized_matching
                    
                    kana_readings.append(KanaReading(
                        text=kana_text,
                        no_kanji=bool(kana_row['no_kanji']),
                        priority=kana_row['priority'],
                        info=kana_row['info'],
                        match_range=(0, len(kana_text)) if matches else None,
                        match=False  # Kanji matched, so kana doesn't match
                    ))
            
            # Build senses
            senses = []
            for sense_row in senses_by_entry[entry_id]:
                sense_id = sense_row['sense_id']
                
                pos_tags = sense_pos_map.get(sense_id, [])
                glosses = sense_glosses_map.get(sense_id, [])
                fields = sense_fields_map.get(sense_id) or None
                misc = sense_misc_map.get(sense_id) or None
                dial = sense_dial_map.get(sense_id) or None
                
                senses.append(Sense(
                    index=sense_row['sense_index'],
                    pos_tags=pos_tags,
                    glosses=glosses,
                    info=sense_row['info'],
                    field=fields,
                    misc=misc,
                    dial=dial
                ))
            
            entry = WordEntry(
                entry_id=entry_id,
                ent_seq=ent_seq,
                kanji_readings=kanji_readings,
                kana_readings=kana_readings,
                senses=senses
            )
            
            # Cache the entry (without match_range, which is query-specific)
            self._entry_cache[entry_id] = entry
            
            # Set match_range for this query
            entry = self._set_match_range(entry, normalized_matching)
            entries.append(entry)
        
        return entries
    
    def _set_match_range(self, entry: WordEntry, normalized_matching: str) -> WordEntry:
        """Set match_range on an entry based on normalized_matching."""
        # Check kanji match
        kanji_match_found = False
        for kanji_reading in entry.kanji_readings:
            if kana_to_hiragana(kanji_reading.text) == normalized_matching:
                kanji_match_found = True
                break
        
        # Update kanji readings with match_range
        new_kanji_readings = []
        for kanji_reading in entry.kanji_readings:
            matches = kana_to_hiragana(kanji_reading.text) == normalized_matching
            new_kanji_readings.append(KanjiReading(
                text=kanji_reading.text,
                priority=kanji_reading.priority,
                info=kanji_reading.info,
                match_range=(0, len(kanji_reading.text)) if matches else None,
                match=(kanji_match_found and matches) or not kanji_match_found
            ))
        
        # Update kana readings with match_range
        new_kana_readings = []
        kana_match_found = False
        if not kanji_match_found:
            for kana_reading in entry.kana_readings:
                matches = kana_to_hiragana(kana_reading.text) == normalized_matching
                if matches:
                    kana_match_found = True
                new_kana_readings.append(KanaReading(
                    text=kana_reading.text,
                    no_kanji=kana_reading.no_kanji,
                    priority=kana_reading.priority,
                    info=kana_reading.info,
                    match_range=(0, len(kana_reading.text)) if matches else None,
                    match=(kana_match_found and matches) or not kana_match_found
                ))
        else:
            for kana_reading in entry.kana_readings:
                matches = kana_to_hiragana(kana_reading.text) == normalized_matching
                new_kana_readings.append(KanaReading(
                    text=kana_reading.text,
                    no_kanji=kana_reading.no_kanji,
                    priority=kana_reading.priority,
                    info=kana_reading.info,
                    match_range=(0, len(kana_reading.text)) if matches else None,
                    match=False
                ))
        
        return WordEntry(
            entry_id=entry.entry_id,
            ent_seq=entry.ent_seq,
            kanji_readings=new_kanji_readings,
            kana_readings=new_kana_readings,
            senses=entry.senses
        )
