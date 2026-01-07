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
    
    def get_words(self, input_text: str, max_results: int) -> List[WordEntry]:
        """
        Look up words in the dictionary by exact match.
        
        Args:
            input_text: The text to look up (normalized to hiragana for readings)
            max_results: Maximum number of results to return
            
        Returns:
            List of WordEntry objects matching the input
        """
        if not self.conn:
            self._connect()
        
        cursor = self.conn.cursor()
        
        # Normalize input to hiragana for reading lookup
        normalized_input = kana_to_hiragana(input_text)
        
        # First, try to find entries by reading (most common case)
        cursor.execute("""
            SELECT DISTINCT e.entry_id, e.ent_seq
            FROM entries e
            JOIN readings r ON e.entry_id = r.entry_id
            WHERE r.reading_text = ?
            LIMIT ?
        """, (normalized_input, max_results))
        
        entry_rows = cursor.fetchall()
        
        # If no results from reading, try kanji match
        if not entry_rows:
            cursor.execute("""
                SELECT DISTINCT e.entry_id, e.ent_seq
                FROM entries e
                JOIN kanji k ON e.entry_id = k.entry_id
                WHERE k.kanji_text = ?
                LIMIT ?
            """, (input_text, max_results))
            entry_rows = cursor.fetchall()
        
        if not entry_rows:
            return []
        
        # Fetch full entry data for each entry_id
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
            kanji_readings = [
                KanjiReading(
                    text=row['kanji_text'],
                    priority=row['priority'],
                    info=row['info']
                )
                for row in cursor.fetchall()
            ]
            
            # Get kana readings
            cursor.execute("""
                SELECT reading_text, no_kanji, priority, info
                FROM readings
                WHERE entry_id = ?
                ORDER BY reading_id
            """, (entry_id,))
            kana_readings = [
                KanaReading(
                    text=row['reading_text'],
                    no_kanji=bool(row['no_kanji']),
                    priority=row['priority'],
                    info=row['info']
                )
                for row in cursor.fetchall()
            ]
            
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

