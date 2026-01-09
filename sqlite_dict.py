"""
SQLite dictionary implementation.

This module provides a SQLite-based dictionary implementation using the
JMDict SQLite database.
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


class SQLiteDictionary(Dictionary):
    """SQLite-based dictionary implementation."""
    
    def __init__(self, db_path: Optional[str] = None, auto_build: bool = True):
        """
        Initialize SQLite dictionary.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses default location.
            auto_build: If True, automatically builds the database if it doesn't exist.
                       This will download and process the JMdict XML file if needed.
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
        
        self.conn: Optional[sqlite3.Connection] = None
        self._connect()
    
    def _connect(self):
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def get_words(self, input_text: str, max_results: int, matching_text: Optional[str] = None) -> List[WordEntry]:
        """
        Look up words in the dictionary by exact match.
        
        Args:
            input_text: The text to look up (normalized to hiragana for readings)
            max_results: Maximum number of results to return
            matching_text: Optional text that was actually matched (for setting matchRange).
                          If None, uses input_text. This is the original input before deinflection.
            
        Returns:
            List of WordEntry objects matching the input, with matchRange set on matching readings
        """
        if not self.conn:
            self._connect()
        
        cursor = self.conn.cursor()
        
        # Use matching_text if provided, otherwise use input_text
        # matching_text is what we're matching against (usually the deinflected candidate.word)
        # This matches 10ten Reader's behavior where matchingText is the input to getWords
        text_for_match_range = matching_text if matching_text is not None else input_text
        
        # Normalize input to hiragana for reading lookup (like 10ten Reader)
        # 10ten Reader normalizes katakana to hiragana before searching when using flat-file DB
        # The SQLite database stores readings in their original form (katakana for loanwords),
        # so we need to search for both original and normalized forms
        normalized_input = kana_to_hiragana(input_text)
        # Normalize matching text for matchRange calculation (like 10ten Reader's kanaToHiragana)
        normalized_matching = kana_to_hiragana(text_for_match_range)
        
        # First, try to find entries by reading (most common case)
        # Try both original input_text (for katakana like "ベッド") and normalized (for hiragana)
        # This matches 10ten Reader's behavior: it normalizes input to hiragana, but database
        # may store readings in original form (katakana), so we search both
        cursor.execute("""
            SELECT DISTINCT e.entry_id, e.ent_seq
            FROM entries e
            JOIN readings r ON e.entry_id = r.entry_id
            WHERE r.reading_text = ? OR r.reading_text = ?
            LIMIT ?
        """, (input_text, normalized_input, max_results))
        
        entry_rows = cursor.fetchall()
        
        # If no results from reading, try kanji match
        # Also try both original and normalized for kanji (some kanji entries may be katakana)
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
            return []
        
        # Fetch full entry data for each entry_id
        entries = []
        for row in entry_rows:
            entry_id = row['entry_id']
            ent_seq = row['ent_seq']
            
            # Get kanji readings first to check for kanji match
            cursor.execute("""
                SELECT kanji_text, priority, info
                FROM kanji
                WHERE entry_id = ?
                ORDER BY kanji_id
            """, (entry_id,))
            kanji_rows = cursor.fetchall()
            
            # Determine if we matched on kanji or kana (like 10ten Reader)
            # Check if any kanji matches the matching_text (normalized)
            kanji_match_found = False
            for kanji_row in kanji_rows:
                if kana_to_hiragana(kanji_row['kanji_text']) == normalized_matching:
                    kanji_match_found = True
                    break
            
            # Get kana readings to check for kana match
            cursor.execute("""
                SELECT reading_text, no_kanji, priority, info
                FROM readings
                WHERE entry_id = ?
                ORDER BY reading_id
            """, (entry_id,))
            kana_rows = cursor.fetchall()
            
            # Check if any kana matches (only if no kanji match, like 10ten Reader)
            # 10ten Reader compares kanaToHiragana(entry_reading) === matchingText (which is already hiragana)
            # So we normalize both sides to hiragana for comparison
            kana_match_found = False
            if not kanji_match_found:
                for kana_row in kana_rows:
                    kana_text = kana_row['reading_text']
                    # Normalize entry reading to hiragana and compare with normalized_matching (already hiragana)
                    if kana_to_hiragana(kana_text) == normalized_matching:
                        kana_match_found = True
                        break
            
            # Build kanji readings with matchRange (like 10ten Reader)
            kanji_readings = []
            for kanji_row in kanji_rows:
                kanji_text = kanji_row['kanji_text']
                kanji_normalized = kana_to_hiragana(kanji_text)
                # Check if this kanji matches the matching_text (normalized)
                matches = kanji_normalized == normalized_matching
                
                kanji_readings.append(KanjiReading(
                    text=kanji_text,
                    priority=kanji_row['priority'],
                    info=kanji_row['info'],
                    match_range=(0, len(kanji_text)) if matches else None,
                    match=(kanji_match_found and matches) or not kanji_match_found
                ))
            
            # Build kana readings with matchRange (like 10ten Reader)
            # 10ten Reader compares: kanaToHiragana(key) === matchingText (both normalized to hiragana)
            kana_readings = []
            for kana_row in kana_rows:
                kana_text = kana_row['reading_text']
                # Normalize entry reading to hiragana and compare with normalized_matching (already hiragana)
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
            
            senses = []
            for sense_row in sense_rows:
                sense_id = sense_row['sense_id']
                
                # Get POS tags for this sense
                cursor.execute("""
                    SELECT pos
                    FROM sense_pos
                    WHERE sense_id = ?
                """, (sense_id,))
                pos_tags = [row['pos'] for row in cursor.fetchall()]
                
                # Get glosses for this sense
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
                
                # Get optional metadata (if available)
                cursor.execute("""
                    SELECT field
                    FROM sense_field
                    WHERE sense_id = ?
                """, (sense_id,))
                fields = [row['field'] for row in cursor.fetchall()] or None
                
                cursor.execute("""
                    SELECT misc
                    FROM sense_misc
                    WHERE sense_id = ?
                """, (sense_id,))
                misc = [row['misc'] for row in cursor.fetchall()] or None
                
                cursor.execute("""
                    SELECT dial
                    FROM sense_dial
                    WHERE sense_id = ?
                """, (sense_id,))
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

