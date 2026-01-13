#!/usr/bin/env python3
"""
Interactive JMDict SQLite database explorer.

Usage:
    python3 explore_db.py [jmdict.db]

Features:
    - Interactive REPL-style interface
    - Lookup by kanji, reading, or English search
    - Browse results with pagination
    - View detailed entry information
    - Command history (up/down arrows)
"""

import sys
import sqlite3
import argparse
from pathlib import Path
from typing import List, Tuple, Optional
import readline  # For command history and editing


class JMDictExplorer:
    """Interactive explorer for JMDict SQLite database."""
    
    def __init__(self, db_path: str):
        """Initialize explorer with database path."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.last_results = []
        self.current_page = 0
        self.page_size = 5
        
    def connect(self):
        """Connect to SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        # Enable row factory for dict-like access (must be set before creating cursor)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def lookup_kanji(self, kanji: str, limit: int = 10) -> List[dict]:
        """Lookup entries by kanji."""
        query = """
            SELECT 
                e.ent_seq,
                k.kanji_text,
                r.reading_text,
                (SELECT GROUP_CONCAT(gloss_text, '; ')
                 FROM (
                     SELECT DISTINCT g2.gloss_text
                     FROM senses s2
                     JOIN glosses g2 ON s2.sense_id = g2.sense_id
                     WHERE s2.entry_id = e.entry_id
                     ORDER BY g2.gloss_id
                 )) as glosses,
                (SELECT COUNT(DISTINCT s3.sense_id)
                 FROM senses s3
                 WHERE s3.entry_id = e.entry_id) as sense_count,
                (SELECT GROUP_CONCAT(pos, '; ')
                 FROM (
                     SELECT DISTINCT pos
                     FROM sense_pos sp2
                     JOIN senses s4 ON sp2.sense_id = s4.sense_id
                     WHERE s4.entry_id = e.entry_id
                     ORDER BY pos
                 )) as pos_sample
            FROM entries e
            JOIN kanji k ON e.entry_id = k.entry_id
            JOIN readings r ON e.entry_id = r.entry_id
            WHERE k.kanji_text = ?
            GROUP BY e.ent_seq, k.kanji_text, r.reading_text
            ORDER BY e.ent_seq
            LIMIT ?
        """
        
        self.cursor.execute(query, (kanji, limit))
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'ent_seq': row['ent_seq'],
                'kanji': row['kanji_text'],
                'reading': row['reading_text'],
                'glosses': row['glosses'],
                'sense_count': row['sense_count'],
                'pos_sample': row['pos_sample'] if row['pos_sample'] else None
            })
        return results
    
    def lookup_reading(self, reading: str, limit: int = 10) -> List[dict]:
        """Lookup entries by reading."""
        query = """
            SELECT 
                e.ent_seq,
                COALESCE(k.kanji_text, '') as kanji_text,
                r.reading_text,
                (SELECT GROUP_CONCAT(gloss_text, '; ')
                 FROM (
                     SELECT DISTINCT g2.gloss_text
                     FROM senses s2
                     JOIN glosses g2 ON s2.sense_id = g2.sense_id
                     WHERE s2.entry_id = e.entry_id
                     ORDER BY g2.gloss_id
                 )) as glosses,
                (SELECT COUNT(DISTINCT s3.sense_id)
                 FROM senses s3
                 WHERE s3.entry_id = e.entry_id) as sense_count,
                (SELECT GROUP_CONCAT(pos, '; ')
                 FROM (
                     SELECT DISTINCT pos
                     FROM sense_pos sp2
                     JOIN senses s4 ON sp2.sense_id = s4.sense_id
                     WHERE s4.entry_id = e.entry_id
                     ORDER BY pos
                 )) as pos_sample
            FROM entries e
            LEFT JOIN kanji k ON e.entry_id = k.entry_id
            JOIN readings r ON e.entry_id = r.entry_id
            WHERE r.reading_text = ?
            GROUP BY e.ent_seq, k.kanji_text, r.reading_text
            ORDER BY e.ent_seq
            LIMIT ?
        """
        
        self.cursor.execute(query, (reading, limit))
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'ent_seq': row['ent_seq'],
                'kanji': row['kanji_text'] if row['kanji_text'] else None,
                'reading': row['reading_text'],
                'glosses': row['glosses'],
                'sense_count': row['sense_count'],
                'pos_sample': row['pos_sample'] if row['pos_sample'] else None
            })
        return results
    
    def search_english(self, search_term: str, limit: int = 10) -> List[dict]:
        """Full-text search by English gloss."""
        query = """
            SELECT DISTINCT 
                e.ent_seq,
                COALESCE(k.kanji_text, '') as kanji_text,
                r.reading_text,
                g.gloss_text,
                s.sense_id
            FROM entries e
            LEFT JOIN kanji k ON e.entry_id = k.entry_id
            JOIN readings r ON e.entry_id = r.entry_id
            JOIN senses s ON e.entry_id = s.entry_id
            JOIN glosses_fts fts ON s.sense_id = fts.sense_id
            JOIN glosses g ON fts.rowid = g.gloss_id
            WHERE glosses_fts MATCH ?
            ORDER BY e.ent_seq
            LIMIT ?
        """
        
        self.cursor.execute(query, (search_term, limit))
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'ent_seq': row['ent_seq'],
                'kanji': row['kanji_text'] if row['kanji_text'] else None,
                'reading': row['reading_text'],
                'gloss': row['gloss_text'],
                'sense_id': row['sense_id']
            })
        return results
    
    def lookup_kanji_character(self, kanji_char: str, limit: int = 50) -> dict:
        """Lookup all words containing a specific kanji character.
        
        Returns comprehensive information about all words that use this kanji,
        similar to Yomitan/10ten Reader kanji lookup.
        """
        # Find all entries containing this kanji character
        query = """
            SELECT DISTINCT
                e.ent_seq,
                k.kanji_text,
                (SELECT GROUP_CONCAT(reading_text, ' / ')
                 FROM (
                     SELECT DISTINCT reading_text
                     FROM readings r2
                     WHERE r2.entry_id = e.entry_id
                 )) as readings,
                (SELECT GROUP_CONCAT(gloss_text, '; ')
                 FROM (
                     SELECT DISTINCT g2.gloss_text
                     FROM senses s2
                     JOIN glosses g2 ON s2.sense_id = g2.sense_id
                     WHERE s2.entry_id = e.entry_id
                     LIMIT 3
                 )) as meanings,
                (SELECT COUNT(DISTINCT sense_id)
                 FROM senses s3
                 WHERE s3.entry_id = e.entry_id) as sense_count,
                MAX(k.priority) as priority
            FROM entries e
            JOIN kanji k ON e.entry_id = k.entry_id
            WHERE k.kanji_text LIKE ?
            GROUP BY e.ent_seq, k.kanji_text
            ORDER BY 
                CASE WHEN k.priority IS NOT NULL THEN 0 ELSE 1 END,
                e.ent_seq
            LIMIT ?
        """
        
        # Search for kanji containing the character
        pattern = f'%{kanji_char}%'
        self.cursor.execute(query, (pattern, limit))
        
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'ent_seq': row['ent_seq'],
                'kanji': row['kanji_text'],
                'readings': row['readings'],
                'meanings': row['meanings'],
                'sense_count': row['sense_count'],
                'priority': row['priority']
            })
        
        # Get statistics
        stats_query = """
            SELECT 
                COUNT(DISTINCT e.entry_id) as word_count,
                COUNT(DISTINCT k.kanji_text) as kanji_variant_count,
                COUNT(DISTINCT r.reading_text) as reading_count
            FROM entries e
            JOIN kanji k ON e.entry_id = k.entry_id
            JOIN readings r ON e.entry_id = r.entry_id
            WHERE k.kanji_text LIKE ?
        """
        self.cursor.execute(stats_query, (pattern,))
        stats_row = self.cursor.fetchone()
        
        # Get all unique readings for this kanji across all words
        # Also get the kanji text to analyze if reading is on-yomi or kun-yomi
        readings_query = """
            SELECT 
                r.reading_text, 
                COUNT(DISTINCT e.entry_id) as word_count,
                k.kanji_text,
                (SELECT GROUP_CONCAT(ent_seq, ', ')
                 FROM (
                     SELECT DISTINCT ent_seq
                     FROM entries e2
                     JOIN kanji k2 ON e2.entry_id = k2.entry_id
                     JOIN readings r2 ON e2.entry_id = r2.entry_id
                     WHERE k2.kanji_text = k.kanji_text
                     AND r2.reading_text = r.reading_text
                     LIMIT 5
                 )) as entry_ids
            FROM entries e
            JOIN kanji k ON e.entry_id = k.entry_id
            JOIN readings r ON e.entry_id = r.entry_id
            WHERE k.kanji_text LIKE ?
            GROUP BY r.reading_text, k.kanji_text
            ORDER BY word_count DESC, r.reading_text
            LIMIT 50
        """
        self.cursor.execute(readings_query, (pattern,))
        all_readings_raw = []
        for row in self.cursor.fetchall():
            all_readings_raw.append({
                'reading': row[0],
                'word_count': row[1],
                'kanji': row[2],
                'entry_ids': row[3]
            })
        
        # Categorize readings as on-yomi or kun-yomi
        # Heuristics based on Japanese linguistics:
        # - On-yomi: Short readings (1-3 morae), appear in compound words, no okurigana
        # - Kun-yomi: Can be longer, often have okurigana, native Japanese readings
        # - For single kanji: if reading matches kanji position exactly, likely on-yomi
        # - If reading has extra hiragana after kanji position, likely kun-yomi
        on_yomi = []
        kun_yomi = []
        other = []
        
        for reading_info in all_readings_raw:
            reading = reading_info['reading']
            kanji_text = reading_info['kanji']
            
            # Find position of target kanji in the compound
            kanji_pos = kanji_text.find(kanji_char)
            if kanji_pos < 0:
                other.append(reading_info)
                continue
            
            # Extract the reading portion that corresponds to this kanji
            # This is approximate - we try to match the kanji position in reading
            reading_length = len(reading)
            kanji_length = len(kanji_text)
            
            # Estimate reading portion for this kanji
            # If kanji is at start, reading portion is likely at start too
            if kanji_pos == 0:
                # Kanji at start - reading portion likely starts at beginning
                # Check if there's okurigana (hiragana after the kanji)
                # For on-yomi, reading should be short and match kanji position
                # For kun-yomi, there's often okurigana
                
                # Simple heuristic: if reading is much longer than kanji, likely has okurigana (kun-yomi)
                # If reading length is close to kanji length, likely on-yomi
                ratio = reading_length / kanji_length if kanji_length > 0 else 1
                
                # On-yomi are typically 1-3 morae per kanji
                # Kun-yomi can be longer and often have okurigana
                if ratio <= 1.5 and reading_length <= 4:
                    # Short reading, likely on-yomi
                    on_yomi.append(reading_info)
                elif ratio > 2.0 or reading_length > 6:
                    # Long reading or high ratio, likely kun-yomi with okurigana
                    kun_yomi.append(reading_info)
                else:
                    # Ambiguous - check if it appears in single-kanji words (kun-yomi)
                    if kanji_length == 1:
                        kun_yomi.append(reading_info)
                    else:
                        on_yomi.append(reading_info)
            else:
                # Kanji in middle or end of compound
                # On-yomi are more common in compounds
                # Check reading length - on-yomi are typically shorter
                if reading_length <= 6 and kanji_length > 1:
                    on_yomi.append(reading_info)
                else:
                    kun_yomi.append(reading_info)
        
        # Sort by word count
        on_yomi.sort(key=lambda x: x['word_count'], reverse=True)
        kun_yomi.sort(key=lambda x: x['word_count'], reverse=True)
        other.sort(key=lambda x: x['word_count'], reverse=True)
        
        all_readings = {
            'on_yomi': on_yomi[:15],  # Top 15
            'kun_yomi': kun_yomi[:15],  # Top 15
            'other': other[:10]  # Top 10
        }
        
        return {
            'kanji_char': kanji_char,
            'words': results,
            'stats': {
                'total_words': stats_row[0] if stats_row else 0,
                'kanji_variants': stats_row[1] if stats_row else 0,
                'unique_readings': stats_row[2] if stats_row else 0
            },
            'all_readings': all_readings
        }
    
    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        self.cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        return self.cursor.fetchone() is not None
    
    def get_entry_details(self, ent_seq: str) -> Optional[dict]:
        """Get detailed information for a specific entry."""
        # Check if enhanced schema is available
        has_enhanced = self._table_exists('sense_misc')
        
        # Get all kanji for this entry
        if has_enhanced:
            kanji_query = """
                SELECT kanji_text, priority, info
                FROM entries e
                JOIN kanji k ON e.entry_id = k.entry_id
                WHERE e.ent_seq = ?
                ORDER BY k.kanji_id
            """
        else:
            kanji_query = """
                SELECT kanji_text, priority, NULL as info
                FROM entries e
                JOIN kanji k ON e.entry_id = k.entry_id
                WHERE e.ent_seq = ?
                ORDER BY k.kanji_id
            """
        self.cursor.execute(kanji_query, (ent_seq,))
        kanji_list = [{'text': row[0], 'priority': row[1], 'info': row[2]} 
                     for row in self.cursor.fetchall()]
        
        # Get all readings for this entry
        if has_enhanced:
            reading_query = """
                SELECT reading_text, no_kanji, priority, info
                FROM entries e
                JOIN readings r ON e.entry_id = r.entry_id
                WHERE e.ent_seq = ?
                ORDER BY r.reading_id
            """
        else:
            reading_query = """
                SELECT reading_text, no_kanji, priority, NULL as info
                FROM entries e
                JOIN readings r ON e.entry_id = r.entry_id
                WHERE e.ent_seq = ?
                ORDER BY r.reading_id
            """
        self.cursor.execute(reading_query, (ent_seq,))
        reading_list = [{'text': row[0], 'no_kanji': row[1], 'priority': row[2], 'info': row[3]} 
                       for row in self.cursor.fetchall()]
        
        # Get all senses with detailed information
        if has_enhanced:
            sense_query = """
                SELECT 
                    s.sense_id,
                    s.sense_index,
                    s.info,
                    (SELECT GROUP_CONCAT(pos, '; ')
                     FROM (
                         SELECT DISTINCT pos
                         FROM sense_pos sp2
                         WHERE sp2.sense_id = s.sense_id
                     )) as pos,
                    (SELECT GROUP_CONCAT(field, ', ')
                     FROM sense_field sf
                     WHERE sf.sense_id = s.sense_id) as fields,
                    (SELECT GROUP_CONCAT(misc, ', ')
                     FROM sense_misc sm
                     WHERE sm.sense_id = s.sense_id) as misc,
                    (SELECT GROUP_CONCAT(dial, ', ')
                     FROM sense_dial sd
                     WHERE sd.sense_id = s.sense_id) as dial
                FROM entries e
                JOIN senses s ON e.entry_id = s.entry_id
                WHERE e.ent_seq = ?
                ORDER BY s.sense_index
            """
        else:
            sense_query = """
                SELECT 
                    s.sense_id,
                    s.sense_index,
                    NULL as info,
                    (SELECT GROUP_CONCAT(pos, '; ')
                     FROM (
                         SELECT DISTINCT pos
                         FROM sense_pos sp2
                         WHERE sp2.sense_id = s.sense_id
                     )) as pos,
                    NULL as fields,
                    NULL as misc,
                    NULL as dial
                FROM entries e
                JOIN senses s ON e.entry_id = s.entry_id
                WHERE e.ent_seq = ?
                ORDER BY s.sense_index
            """
        self.cursor.execute(sense_query, (ent_seq,))
        sense_ids = []
        for row in self.cursor.fetchall():
            sense_ids.append({
                'sense_id': row[0],
                'index': row[1],
                'info': row[2],
                'pos': row[3] if row[3] else 'N/A',
                'fields': row[4] if row[4] else None,
                'misc': row[5] if row[5] else None,
                'dial': row[6] if row[6] else None
            })
        
        # Get glosses for each sense with type and language
        senses = []
        for sense_info in sense_ids:
            gloss_query = """
                SELECT gloss_text, lang, g_type
                FROM glosses
                WHERE sense_id = ?
                ORDER BY gloss_id
            """
            self.cursor.execute(gloss_query, (sense_info['sense_id'],))
            glosses = []
            for gloss_row in self.cursor.fetchall():
                glosses.append({
                    'text': gloss_row[0],
                    'lang': gloss_row[1] if gloss_row[1] else 'eng',
                    'type': gloss_row[2] if gloss_row[2] else None
                })
            
            senses.append({
                'index': sense_info['index'],
                'pos': sense_info['pos'],
                'info': sense_info.get('info'),
                'fields': sense_info.get('fields'),
                'misc': sense_info.get('misc'),
                'dial': sense_info.get('dial'),
                'glosses': glosses
            })
        
        if not kanji_list and not reading_list:
            return None
        
        return {
            'ent_seq': ent_seq,
            'kanji': kanji_list,
            'readings': reading_list,
            'senses': senses,
            'enhanced': has_enhanced
        }
    
    def _format_priority(self, priority: str) -> str:
        """Convert priority code to star marker (☆ or ★)."""
        if not priority:
            return ""
        # Higher priority = solid star, lower = hollow star
        # ichi1, news1, spec1, gai1 = ★ (more common)
        # ichi2, news2, spec2, gai2 = ☆ (less common)
        if priority.endswith('1'):
            return "★"
        elif priority.endswith('2'):
            return "☆"
        else:
            return "★"  # Default to solid star for other priorities
    
    def _format_tags(self, pos: str, misc: str = None, field: str = None, dial: str = None) -> str:
        """Format tags in Yomitan style [tag] format."""
        tags = []
        if pos:
            # Split multiple POS tags
            for p in pos.split('; '):
                p = p.strip()
                if p and p != 'N/A':
                    # First, try to extract short code if it's in parentheses
                    original_p = p
                    if '(' in p:
                        # Extract code from parentheses like "interjection (kandoushi)" -> "kandoushi"
                        paren_match = p[p.find('(')+1:p.find(')')]
                        if paren_match:
                            p = paren_match
                    
                    # Map common POS codes to short readable names (Yomitan style)
                    pos_map = {
                        'n': 'noun', 'v1': 'verb', 'v5': 'verb', 'adj-i': 'i-adj',
                        'adj-na': 'na-adj', 'adv': 'adverb', 'int': 'int.',
                        'pref': 'prefix', 'suf': 'suffix', 'conj': 'conjunction',
                        'kandoushi': 'int.', 'futsuumeishi': 'noun', 'keiyodoshi': 'na-adj',
                        'fukushi': 'adverb', 'joshi': 'particle', 'jodoushi': 'auxiliary verb',
                        'meishi': 'noun', 'doushi': 'verb'
                    }
                    
                    # Try mapping
                    tag = pos_map.get(p.lower(), None)
                    if not tag:
                        # If no direct match, try to infer from description
                        p_lower = original_p.lower()
                        if 'interjection' in p_lower or 'int' in p_lower:
                            tag = 'int.'
                        elif 'noun' in p_lower or 'meishi' in p_lower:
                            tag = 'noun'
                        elif 'adjective' in p_lower or 'adj' in p_lower:
                            if 'na' in p_lower or 'keiyodoshi' in p_lower:
                                tag = 'na-adj'
                            else:
                                tag = 'i-adj'
                        elif 'adverb' in p_lower or 'fukushi' in p_lower:
                            tag = 'adverb'
                        elif 'prefix' in p_lower or 'pref' in p_lower:
                            tag = 'prefix'
                        elif 'verb' in p_lower or 'doushi' in p_lower:
                            tag = 'verb'
                        else:
                            # Fallback: use first word or code
                            tag = p.split()[0] if ' ' in p else p
                            if len(tag) > 10:
                                tag = tag[:10]
                    
                    tags.append(tag)
        if misc:
            for m in misc.split(', '):
                m = m.strip()
                if m:
                    # Map misc codes to readable names
                    misc_map = {
                        'uk': 'usually kana', 'col': 'colloquial', 'sl': 'slang',
                        'arch': 'archaic', 'obs': 'obsolete', 'rare': 'rare',
                        'fam': 'familiar', 'hon': 'honorific', 'hum': 'humorous',
                        'derog': 'derogatory', 'vulg': 'vulgar', 'poet': 'poetic'
                    }
                    # Handle full descriptions like "word usually written using kana alone"
                    if 'kana' in m.lower() and 'usually' in m.lower():
                        tag = 'usually kana'
                    else:
                        tag = misc_map.get(m.lower(), m.lower())
                    tags.append(tag)
        if field:
            for f in field.split(', '):
                f = f.strip()
                if f:
                    field_map = {
                        'comp': 'computing', 'med': 'medicine', 'ling': 'linguistics',
                        'law': 'law', 'mil': 'military', 'sports': 'sports'
                    }
                    tag = field_map.get(f.lower(), f.lower())
                    tags.append(tag)
        if dial:
            for d in dial.split(', '):
                d = d.strip()
                if d:
                    dial_map = {
                        'ksb': 'Kansai', 'ktb': 'Kantou', 'kyb': 'Kyoto',
                        'osb': 'Osaka', 'tsb': 'Tosa', 'thb': 'Touhoku'
                    }
                    tag = dial_map.get(d.lower(), d.lower())
                    if 'dialect' not in tag.lower():
                        tag = f"{tag} dialect"
                    tags.append(tag)
        return ' '.join(f"[{tag}]" for tag in tags) if tags else ""
    
    def print_results(self, results: List[dict], query_type: str = "search"):
        """Print search results in Yomitan-style format."""
        if not results:
            print("  No results found.")
            return
        
        print(f"\n  Found {len(results)} result(s):\n")
        
        for i, result in enumerate(results, 1):
            if query_type == "kanji" or query_type == "reading":
                # For quick lookup, fetch full entry details to show per-sense format
                ent_seq = result.get('ent_seq')
                if ent_seq:
                    entry = self.get_entry_details(ent_seq)
                    if entry:
                        # Format header with kanji and reading
                        kanji_list = entry.get('kanji', [])
                        reading_list = entry.get('readings', [])
                        
                        kanji_parts = []
                        for k in kanji_list:
                            kanji_text = k['text']
                            priority_marker = self._format_priority(k.get('priority'))
                            kanji_parts.append(kanji_text + priority_marker)
                        
                        reading_parts = []
                        for r in reading_list:
                            reading_text = r['text']
                            priority_marker = self._format_priority(r.get('priority'))
                            reading_parts.append(reading_text + priority_marker)
                        
                        kanji_display = '、'.join(kanji_parts) if kanji_parts else ""
                        reading_display = ' '.join(reading_parts) if reading_parts else ""
                        
                        print(f"  [{i}] {kanji_display} {reading_display}".strip())
                        
                        # Show senses with tags inline
                        senses = entry.get('senses', [])
                        has_enhanced = entry.get('enhanced', False)
                        
                        for sense_idx, sense in enumerate(senses, 1):
                            pos = sense.get('pos', '')
                            misc = sense.get('misc', '') if has_enhanced else None
                            field = sense.get('field', '') if has_enhanced else None
                            dial = sense.get('dial', '') if has_enhanced else None
                            
                            tags = self._format_tags(pos, misc, field, dial)
                            
                            glosses = sense.get('glosses', [])
                            if glosses:
                                def_texts = [g['text'] for g in glosses]
                                line_parts = [f"      {sense_idx}."]
                                
                                if tags:
                                    line_parts.append(tags)
                                
                                line_parts.append('; '.join(def_texts))
                                print(' '.join(line_parts))
                        
                        print()
                        continue
                
                # Fallback if entry details not available
                kanji = result.get('kanji', '')
                reading = result.get('reading', '')
                print(f"  [{i}] {kanji} {reading}")
                print(f"      Use 'd {result.get('ent_seq')}' for detailed view")
                
            elif query_type == "english":
                kanji = result.get('kanji', '')
                reading = result.get('reading', '')
                gloss = result.get('gloss', '')
                
                header_parts = []
                if kanji:
                    header_parts.append(kanji)
                if reading:
                    header_parts.append(reading)
                
                print(f"  [{i}] {' '.join(header_parts)}")
                print(f"      {gloss}")
            
            print()
    
    def print_kanji_character_info(self, kanji_info: dict):
        """Print comprehensive kanji character information."""
        kanji_char = kanji_info['kanji_char']
        words = kanji_info['words']
        stats = kanji_info['stats']
        all_readings = kanji_info['all_readings']
        
        print(f"\n{'='*70}")
        print(f"Kanji Character: {kanji_char}")
        print(f"{'='*70}")
        
        print(f"\nStatistics:")
        print(f"  Total words containing this kanji: {stats['total_words']:,}")
        print(f"  Kanji variants (compounds): {stats['kanji_variants']:,}")
        print(f"  Unique readings: {stats['unique_readings']:,}")
        
        if kanji_info['all_readings']['on_yomi'] or kanji_info['all_readings']['kun_yomi']:
            print(f"\nReadings for '{kanji_char}':")
            
            if kanji_info['all_readings']['on_yomi']:
                print(f"\n  On-yomi (音読み) - Chinese-derived readings:")
                on_yomi_list = kanji_info['all_readings']['on_yomi']
                for reading_info in on_yomi_list:
                    print(f"    • {reading_info['reading']} ({reading_info['word_count']} words)")
                if kanji_info.get('on_yomi_count', len(on_yomi_list)) > len(on_yomi_list):
                    print(f"    ... and {kanji_info.get('on_yomi_count', len(on_yomi_list)) - len(on_yomi_list)} more on-yomi")
            
            if kanji_info['all_readings']['kun_yomi']:
                print(f"\n  Kun-yomi (訓読み) - Japanese native readings:")
                kun_yomi_list = kanji_info['all_readings']['kun_yomi']
                for reading_info in kun_yomi_list:
                    print(f"    • {reading_info['reading']} ({reading_info['word_count']} words)")
                if kanji_info.get('kun_yomi_count', len(kun_yomi_list)) > len(kun_yomi_list):
                    print(f"    ... and {kanji_info.get('kun_yomi_count', len(kun_yomi_list)) - len(kun_yomi_list)} more kun-yomi")
            
            if kanji_info['all_readings']['other']:
                print(f"\n  Other readings:")
                for reading_info in kanji_info['all_readings']['other'][:5]:
                    print(f"    • {reading_info['reading']} ({reading_info['word_count']} words)")
            
            print(f"\n  ⚠️  Note: On-yomi/kun-yomi categorization is approximate and")
            print(f"        inferred from word readings. JMDict is a word dictionary,")
            print(f"        not a kanji dictionary, so it doesn't contain kanji-specific")
            print(f"        reading information. For accurate on-yomi/kun-yomi data,")
            print(f"        KANJIDIC2 dictionary would be needed.")
            print(f"\n  Common readings shown above are the most frequent readings")
            print(f"        that appear in words containing this kanji character.")
        
        if words:
            print(f"\nWords Containing '{kanji_char}' (showing {len(words)} of {stats['total_words']}):")
            print(f"{'='*70}")
            
            for i, word in enumerate(words, 1):
                priority_marker = f" [{word['priority']}]" if word['priority'] else ""
                print(f"\n[{i}] {word['kanji']}{priority_marker}")
                print(f"    Readings: {word['readings']}")
                print(f"    Meanings: {word['meanings']}")
                print(f"    Entry: {word['ent_seq']} | Senses: {word['sense_count']}")
            
            if stats['total_words'] > len(words):
                print(f"\n... and {stats['total_words'] - len(words)} more words")
                print(f"Use 'd <entry_id>' to see detailed information for any entry")
        
        print(f"\n{'='*70}\n")
    
    def print_entry_details(self, entry: dict):
        """Print detailed entry information in Yomitan-style format."""
        # Group by kanji-reading combinations (like Yomitan shows separate blocks)
        kanji_list = entry.get('kanji', [])
        reading_list = entry.get('readings', [])
        senses = entry.get('senses', [])
        
        # Get enhanced fields if available
        has_enhanced = entry.get('enhanced', False)
        
        # For each kanji-reading combination, show all senses
        # Yomitan groups by: kanji + reading(s) → all senses for that combination
        
        print()  # Blank line before entry
        
        # Build kanji string with priority markers
        # Format: 糞★、屎(rare) for alternative kanji
        kanji_parts = []
        for k in kanji_list:
            kanji_text = k['text']
            priority_marker = self._format_priority(k.get('priority'))
            info = k.get('info', '')
            
            kanji_str = kanji_text + priority_marker
            # Note: Alternative kanji would be in separate entries in JMdict
            # So we just show the kanji with priority marker
            kanji_parts.append(kanji_str)
        
        kanji_display = '、'.join(kanji_parts) if kanji_parts else ""
        
        # Build reading string with priority markers
        reading_parts = []
        for r in reading_list:
            reading_text = r['text']
            priority_marker = self._format_priority(r.get('priority'))
            reading_parts.append(reading_text + priority_marker)
        
        reading_display = ' '.join(reading_parts) if reading_parts else ""
        
        # Print header: Kanji Reading
        if kanji_display and reading_display:
            print(f"{kanji_display} {reading_display}")
        elif kanji_display:
            print(kanji_display)
        elif reading_display:
            print(reading_display)
        
        # Print senses with Yomitan-style formatting
        for sense_idx, sense in enumerate(senses, 1):
            # Get tags for this sense
            pos = sense.get('pos', '')
            misc = sense.get('misc', '') if has_enhanced else None
            field = sense.get('field', '') if has_enhanced else None
            dial = sense.get('dial', '') if has_enhanced else None
            sense_info = sense.get('info', '') if has_enhanced else None
            
            # Format tags
            tags = self._format_tags(pos, misc, field, dial)
            
            # Get glosses (definitions)
            glosses = sense.get('glosses', [])
            if glosses:
                # Group by language (usually just English)
                glosses_by_lang = {}
                for gloss in glosses:
                    lang = gloss.get('lang', 'eng')
                    if lang not in glosses_by_lang:
                        glosses_by_lang[lang] = []
                    glosses_by_lang[lang].append(gloss)
                
                # Print definitions with tags inline
                for lang, gloss_list in sorted(glosses_by_lang.items()):
                    # Build the definition line: number, tags, definitions
                    line_parts = [f"{sense_idx}."]
                    
                    # Add tags inline
                    if tags:
                        line_parts.append(tags)
                    
                    # Add definitions (semicolon-separated)
                    def_texts = [g['text'] for g in gloss_list]
                    line_parts.append('; '.join(def_texts))
                    
                    # Print the complete line
                    print(f"  {' '.join(line_parts)}")
            
            # Show sense info/notes if available (on separate line in parentheses)
            if sense_info:
                print(f"  ({sense_info})")
            
            # Add spacing between senses (except last one)
            if sense_idx < len(senses):
                print()
        
        print()  # Blank line after entry
    
    def show_help(self):
        """Display help information."""
        help_text = """
Commands:
  k <kanji>          - Lookup by exact kanji word (e.g., k 日本語)
  kanji <char>       - Lookup all words containing a kanji character (e.g., kanji 日)
  r <reading>        - Lookup by reading (e.g., r にほんご)
  e <english>        - Search English definitions (e.g., e japanese)
  d <entry_id>       - Show detailed entry with all info (e.g., d 1464530)
  stats              - Show database statistics
  help               - Show this help message
  quit / exit / q    - Exit the explorer
  
Note: Use 'd <entry_id>' to see full details including:
  - All kanji variants with priority markers
  - All readings with flags (no-kanji, priority)
  - All senses with parts of speech
  - All glosses with types (lit, fig, expl) and languages
  
Examples:
  k 日本語           - Find exact word "日本語"
  kanji 日           - Find all words containing 日 (like 日本語, 日本, 今日, etc.)
  r たべる           - Find words with reading "たべる"
  e language         - Search English definitions
  d 1464530          - Show detailed entry
        """
        print(help_text)
    
    def show_stats(self):
        """Show database statistics."""
        stats = {}
        self.cursor.execute("SELECT COUNT(*) FROM entries")
        stats['entries'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM kanji")
        stats['kanji'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM readings")
        stats['readings'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM glosses")
        stats['glosses'] = self.cursor.fetchone()[0]
        
        db_size = Path(self.db_path).stat().st_size
        stats['size_mb'] = db_size / (1024 * 1024)
        
        print(f"\n{'='*70}")
        print("Database Statistics")
        print(f"{'='*70}")
        print(f"  Entries:        {stats['entries']:,}")
        print(f"  Kanji elements: {stats['kanji']:,}")
        print(f"  Reading elements: {stats['readings']:,}")
        print(f"  Glosses:        {stats['glosses']:,}")
        print(f"  Database size:  {stats['size_mb']:.2f} MB")
        print(f"{'='*70}\n")
    
    def run(self):
        """Run interactive explorer."""
        print("\n" + "="*70)
        print("JMDict SQLite Database Explorer")
        print("="*70)
        print(f"Database: {self.db_path}")
        print("Type 'help' for commands, 'quit' to exit")
        print("="*70 + "\n")
        
        while True:
            try:
                # Get user input
                line = input("jmdict> ").strip()
                
                if not line:
                    continue
                
                # Parse command
                parts = line.split(None, 1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""
                
                # Handle commands
                if cmd in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                elif cmd == 'help' or cmd == 'h':
                    self.show_help()
                
                elif cmd == 'stats':
                    self.show_stats()
                
                elif cmd == 'k':
                    if not arg:
                        print("  Error: Please provide kanji (e.g., k 日本語)")
                        continue
                    results = self.lookup_kanji(arg, limit=20)
                    self.last_results = results
                    self.print_results(results, "kanji")
                
                elif cmd == 'kanji':
                    if not arg:
                        print("  Error: Please provide a kanji character (e.g., kanji 日)")
                        continue
                    if len(arg) > 1:
                        print(f"  Note: '{arg}' contains multiple characters. Showing words containing any of them.")
                    kanji_info = self.lookup_kanji_character(arg, limit=30)
                    self.print_kanji_character_info(kanji_info)
                
                elif cmd == 'r' or cmd == 'reading':
                    if not arg:
                        print("  Error: Please provide reading (e.g., r にほんご)")
                        continue
                    results = self.lookup_reading(arg, limit=20)
                    self.last_results = results
                    self.print_results(results, "reading")
                
                elif cmd == 'e' or cmd == 'english' or cmd == 'search':
                    if not arg:
                        print("  Error: Please provide search term (e.g., e japanese)")
                        continue
                    results = self.search_english(arg, limit=20)
                    self.last_results = results
                    self.print_results(results, "english")
                
                elif cmd == 'd' or cmd == 'detail' or cmd == 'detail':
                    if not arg:
                        print("  Error: Please provide entry ID (e.g., d 1464530)")
                        continue
                    entry = self.get_entry_details(arg)
                    if entry:
                        self.print_entry_details(entry)
                    else:
                        print(f"  Entry {arg} not found.")
                
                else:
                    print(f"  Unknown command: {cmd}")
                    print("  Type 'help' for available commands")
            
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except EOFError:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        description='Interactive JMDict SQLite database explorer'
    )
    parser.add_argument(
        'db_file',
        nargs='?',
        default='jmdict.db',
        help='Path to JMDict SQLite database (default: jmdict.db)'
    )
    
    args = parser.parse_args()
    
    # Validate database file
    db_path = Path(args.db_file)
    if not db_path.exists():
        print(f"Error: Database file not found: {args.db_file}", file=sys.stderr)
        print(f"Looking for: {db_path.absolute()}", file=sys.stderr)
        sys.exit(1)
    
    # Create and run explorer
    explorer = JMDictExplorer(str(db_path))
    
    try:
        explorer.connect()
        explorer.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        explorer.close()


if __name__ == '__main__':
    main()

