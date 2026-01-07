"""
JMDict to SQLite converter with full field support.

This module provides functionality to build the JMDict SQLite database
from the XML source file, including automatic downloading if needed.
"""

import sys
import sqlite3
import gzip
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Set, Union
import argparse
from urllib.request import urlretrieve
from urllib.error import URLError

# Try to use lxml for better performance, fall back to standard library
try:
    from lxml import etree as ET
    HAS_LXML = True
except ImportError:
    import xml.etree.ElementTree as ET
    HAS_LXML = False

# Try to import tqdm for progress bars
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


# Official JMDict download URLs
# Source: https://www.edrdg.org/jmdict/j_jmdict.html
JMDICT_XML_URL = "https://www.edrdg.org/pub/Nihongo/JMdict_e.gz"
JMDICT_XML_FILENAME = "JMdict_e.xml.gz"


class JMDictConverter:
    """JMDict converter with full field support for Yomitan-style popups."""
    
    def __init__(self, db_path: str, show_progress: bool = True):
        """Initialize converter with database path."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.entry_count = 0
        self.show_progress = show_progress
        
    def connect(self):
        """Connect to SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        # Enable WAL mode for better concurrency
        self.cursor.execute("PRAGMA journal_mode=WAL")
        # Optimize for bulk inserts
        self.cursor.execute("PRAGMA synchronous=OFF")
        self.cursor.execute("PRAGMA cache_size=10000")
        self.cursor.execute("PRAGMA temp_store=MEMORY")
        
    def create_schema(self):
        """Create database schema with all Yomitan-style fields."""
        if self.show_progress:
            print("Creating database schema...")
        
        # Main entries table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                entry_id INTEGER PRIMARY KEY,
                ent_seq TEXT UNIQUE NOT NULL
            )
        """)
        
        # Kanji elements (written forms)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS kanji (
                kanji_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                kanji_text TEXT NOT NULL,
                priority TEXT,
                info TEXT,
                FOREIGN KEY (entry_id) REFERENCES entries(entry_id) ON DELETE CASCADE
            )
        """)
        
        # Reading elements (pronunciations)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                reading_text TEXT NOT NULL,
                no_kanji INTEGER DEFAULT 0,
                priority TEXT,
                info TEXT,
                FOREIGN KEY (entry_id) REFERENCES entries(entry_id) ON DELETE CASCADE
            )
        """)
        
        # Reading restrictions (which kanji this reading applies to)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS reading_restrictions (
                restriction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                reading_id INTEGER NOT NULL,
                kanji_text TEXT NOT NULL,
                FOREIGN KEY (reading_id) REFERENCES readings(reading_id) ON DELETE CASCADE
            )
        """)
        
        # Senses (meanings)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS senses (
                sense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                sense_index INTEGER NOT NULL,
                info TEXT,
                FOREIGN KEY (entry_id) REFERENCES entries(entry_id) ON DELETE CASCADE
            )
        """)
        
        # Parts of speech
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sense_pos (
                sense_pos_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sense_id INTEGER NOT NULL,
                pos TEXT NOT NULL,
                FOREIGN KEY (sense_id) REFERENCES senses(sense_id) ON DELETE CASCADE
            )
        """)
        
        # Field of application (computing, medicine, etc.)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sense_field (
                sense_field_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sense_id INTEGER NOT NULL,
                field TEXT NOT NULL,
                FOREIGN KEY (sense_id) REFERENCES senses(sense_id) ON DELETE CASCADE
            )
        """)
        
        # Miscellaneous info (archaic, colloquial, slang, etc.)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sense_misc (
                sense_misc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sense_id INTEGER NOT NULL,
                misc TEXT NOT NULL,
                FOREIGN KEY (sense_id) REFERENCES senses(sense_id) ON DELETE CASCADE
            )
        """)
        
        # Dialect information
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sense_dial (
                sense_dial_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sense_id INTEGER NOT NULL,
                dial TEXT NOT NULL,
                FOREIGN KEY (sense_id) REFERENCES senses(sense_id) ON DELETE CASCADE
            )
        """)
        
        # Sense applies to specific kanji (stagk)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sense_stagk (
                sense_stagk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sense_id INTEGER NOT NULL,
                kanji_text TEXT NOT NULL,
                FOREIGN KEY (sense_id) REFERENCES senses(sense_id) ON DELETE CASCADE
            )
        """)
        
        # Sense applies to specific readings (stagr)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sense_stagr (
                sense_stagr_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sense_id INTEGER NOT NULL,
                reading_text TEXT NOT NULL,
                FOREIGN KEY (sense_id) REFERENCES senses(sense_id) ON DELETE CASCADE
            )
        """)
        
        # Glosses (English definitions)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS glosses (
                gloss_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sense_id INTEGER NOT NULL,
                gloss_text TEXT NOT NULL,
                lang TEXT DEFAULT 'eng',
                g_type TEXT,
                FOREIGN KEY (sense_id) REFERENCES senses(sense_id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for fast lookups
        if self.show_progress:
            print("Creating indexes...")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_kanji_text ON kanji(kanji_text)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_kanji_entry ON kanji(entry_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_reading_text ON readings(reading_text)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_reading_entry ON readings(entry_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_gloss_text ON glosses(gloss_text)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_gloss_sense ON glosses(sense_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_sense_entry ON senses(entry_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_sense_pos_sense ON sense_pos(sense_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_sense_field_sense ON sense_field(sense_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_sense_misc_sense ON sense_misc(sense_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_sense_dial_sense ON sense_dial(sense_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_sense_stagk_sense ON sense_stagk(sense_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_sense_stagr_sense ON sense_stagr(sense_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_reading_restrictions_reading ON reading_restrictions(reading_id)")
        
        # Full-text search index for glosses (SQLite FTS5)
        self.cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS glosses_fts USING fts5(
                gloss_text,
                sense_id UNINDEXED,
                content='glosses',
                content_rowid='gloss_id'
            )
        """)
        
        self.conn.commit()
        
    def parse_entry(self, entry_elem) -> Optional[Dict]:
        """Parse a single JMDict entry element with all fields."""
        try:
            # Get entry sequence number
            ent_seq = entry_elem.findtext('ent_seq')
            if not ent_seq:
                return None
            
            # Parse kanji elements
            kanji_list = []
            for k_ele in entry_elem.findall('k_ele'):
                keb = k_ele.findtext('keb')  # kanji element body
                if keb:
                    ke_pri = k_ele.findtext('ke_pri')  # priority
                    # Collect all ke_inf (kanji information)
                    ke_inf_list = []
                    for ke_inf in k_ele.findall('ke_inf'):
                        if ke_inf.text:
                            ke_inf_list.append(ke_inf.text)
                    ke_inf_str = ','.join(ke_inf_list) if ke_inf_list else None
                    
                    kanji_list.append({
                        'text': keb,
                        'priority': ke_pri,
                        'info': ke_inf_str
                    })
            
            # Parse reading elements
            reading_list = []
            for r_ele in entry_elem.findall('r_ele'):
                reb = r_ele.findtext('reb')  # reading element body
                if reb:
                    re_pri = r_ele.findtext('re_pri')  # priority
                    re_nokanji = 1 if r_ele.find('re_nokanji') is not None else 0
                    
                    # Collect all re_inf (reading information)
                    re_inf_list = []
                    for re_inf in r_ele.findall('re_inf'):
                        if re_inf.text:
                            re_inf_list.append(re_inf.text)
                    re_inf_str = ','.join(re_inf_list) if re_inf_list else None
                    
                    # Collect re_restr (restrictions - which kanji this reading applies to)
                    re_restr_list = []
                    for re_restr in r_ele.findall('re_restr'):
                        if re_restr.text:
                            re_restr_list.append(re_restr.text)
                    
                    reading_list.append({
                        'text': reb,
                        'priority': re_pri,
                        'no_kanji': re_nokanji,
                        'info': re_inf_str,
                        'restrictions': re_restr_list
                    })
            
            # Parse senses (meanings)
            senses_list = []
            for sense_idx, sense in enumerate(entry_elem.findall('sense')):
                sense_data = {
                    'index': sense_idx,
                    'pos': [],
                    'field': [],
                    'misc': [],
                    'dial': [],
                    'stagk': [],
                    'stagr': [],
                    'glosses': []
                }
                
                # Parts of speech
                for pos in sense.findall('pos'):
                    pos_text = pos.text
                    if pos_text:
                        sense_data['pos'].append(pos_text)
                
                # Field of application
                for field in sense.findall('field'):
                    field_text = field.text
                    if field_text:
                        sense_data['field'].append(field_text)
                
                # Miscellaneous info
                for misc in sense.findall('misc'):
                    misc_text = misc.text
                    if misc_text:
                        sense_data['misc'].append(misc_text)
                
                # Dialect information
                for dial in sense.findall('dial'):
                    dial_text = dial.text
                    if dial_text:
                        sense_data['dial'].append(dial_text)
                
                # Sense applies to specific kanji (stagk)
                for stagk in sense.findall('stagk'):
                    stagk_text = stagk.text
                    if stagk_text:
                        sense_data['stagk'].append(stagk_text)
                
                # Sense applies to specific readings (stagr)
                for stagr in sense.findall('stagr'):
                    stagr_text = stagr.text
                    if stagr_text:
                        sense_data['stagr'].append(stagr_text)
                
                # Sense information (s_inf)
                s_inf_list = []
                for s_inf in sense.findall('s_inf'):
                    if s_inf.text:
                        s_inf_list.append(s_inf.text)
                sense_data['info'] = '; '.join(s_inf_list) if s_inf_list else None
                
                # Glosses (definitions)
                for gloss in sense.findall('gloss'):
                    gloss_text = gloss.text
                    if gloss_text:
                        g_type = gloss.get('g_type', '')
                        lang = gloss.get('{http://www.w3.org/XML/1998/namespace}lang', 'eng')
                        sense_data['glosses'].append({
                            'text': gloss_text,
                            'type': g_type,
                            'lang': lang
                        })
                
                if sense_data['glosses']:  # Only add sense if it has glosses
                    senses_list.append(sense_data)
            
            # Only return entry if it has at least kanji/reading and senses
            if (kanji_list or reading_list) and senses_list:
                return {
                    'ent_seq': ent_seq,
                    'kanji': kanji_list,
                    'readings': reading_list,
                    'senses': senses_list
                }
            
            return None
            
        except Exception as e:
            if self.show_progress:
                print(f"Error parsing entry: {e}", file=sys.stderr)
            return None
    
    def insert_entry(self, entry_data: Dict):
        """Insert a parsed entry into the database with all fields."""
        ent_seq = entry_data['ent_seq']
        
        # Insert main entry
        self.cursor.execute(
            "INSERT OR IGNORE INTO entries (ent_seq) VALUES (?)",
            (ent_seq,)
        )
        
        # Get entry_id
        self.cursor.execute(
            "SELECT entry_id FROM entries WHERE ent_seq = ?",
            (ent_seq,)
        )
        row = self.cursor.fetchone()
        if not row:
            return  # Entry already exists or failed to insert
        entry_id = row[0]
        
        # Check if entry already has data (prevent duplicates on re-run)
        self.cursor.execute(
            "SELECT COUNT(*) FROM kanji WHERE entry_id = ?",
            (entry_id,)
        )
        if self.cursor.fetchone()[0] > 0:
            return  # Entry already processed, skip to prevent duplicates
        
        # Track kanji/reading IDs for restrictions
        kanji_ids = {}
        reading_ids = {}
        
        # Insert kanji elements
        for kanji in entry_data['kanji']:
            self.cursor.execute(
                """INSERT INTO kanji (entry_id, kanji_text, priority, info)
                   VALUES (?, ?, ?, ?)""",
                (entry_id, kanji['text'], kanji.get('priority'), kanji.get('info'))
            )
            kanji_ids[kanji['text']] = self.cursor.lastrowid
        
        # Insert reading elements
        for reading in entry_data['readings']:
            self.cursor.execute(
                """INSERT INTO readings (entry_id, reading_text, no_kanji, priority, info)
                   VALUES (?, ?, ?, ?, ?)""",
                (entry_id, reading['text'], reading['no_kanji'], 
                 reading.get('priority'), reading.get('info'))
            )
            reading_id = self.cursor.lastrowid
            reading_ids[reading['text']] = reading_id
            
            # Insert reading restrictions
            for kanji_text in reading.get('restrictions', []):
                # Find the kanji_id for this kanji text
                kanji_id = kanji_ids.get(kanji_text)
                if kanji_id:
                    self.cursor.execute(
                        """INSERT INTO reading_restrictions (reading_id, kanji_text)
                           VALUES (?, ?)""",
                        (reading_id, kanji_text)
                    )
        
        # Insert senses
        for sense in entry_data['senses']:
            self.cursor.execute(
                """INSERT INTO senses (entry_id, sense_index, info)
                   VALUES (?, ?, ?)""",
                (entry_id, sense['index'], sense.get('info'))
            )
            sense_id = self.cursor.lastrowid
            
            # Insert parts of speech
            for pos in sense['pos']:
                self.cursor.execute(
                    "INSERT INTO sense_pos (sense_id, pos) VALUES (?, ?)",
                    (sense_id, pos)
                )
            
            # Insert field of application
            for field in sense['field']:
                self.cursor.execute(
                    "INSERT INTO sense_field (sense_id, field) VALUES (?, ?)",
                    (sense_id, field)
                )
            
            # Insert miscellaneous info
            for misc in sense['misc']:
                self.cursor.execute(
                    "INSERT INTO sense_misc (sense_id, misc) VALUES (?, ?)",
                    (sense_id, misc)
                )
            
            # Insert dialect information
            for dial in sense['dial']:
                self.cursor.execute(
                    "INSERT INTO sense_dial (sense_id, dial) VALUES (?, ?)",
                    (sense_id, dial)
                )
            
            # Insert sense applies to kanji (stagk)
            for stagk in sense['stagk']:
                self.cursor.execute(
                    "INSERT INTO sense_stagk (sense_id, kanji_text) VALUES (?, ?)",
                    (sense_id, stagk)
                )
            
            # Insert sense applies to readings (stagr)
            for stagr in sense['stagr']:
                self.cursor.execute(
                    "INSERT INTO sense_stagr (sense_id, reading_text) VALUES (?, ?)",
                    (sense_id, stagr)
                )
            
            # Insert glosses
            for gloss in sense['glosses']:
                self.cursor.execute(
                    """INSERT INTO glosses (sense_id, gloss_text, lang, g_type)
                       VALUES (?, ?, ?, ?)""",
                    (sense_id, gloss['text'], gloss['lang'], gloss['type'])
                )
                gloss_id = self.cursor.lastrowid
                
                # Insert into FTS index
                self.cursor.execute(
                    """INSERT INTO glosses_fts (rowid, gloss_text, sense_id)
                       VALUES (?, ?, ?)""",
                    (gloss_id, gloss['text'], sense_id)
                )
        
        self.entry_count += 1
        
    def convert(self, xml_path: str, batch_size: int = 1000):
        """Convert JMDict XML file to SQLite database."""
        if self.show_progress:
            print(f"Parsing JMDict XML: {xml_path}")
            if HAS_LXML:
                print("Using lxml for faster parsing")
            else:
                print("Using standard library ElementTree (install lxml for better performance)")
        
        # Use iterparse for memory-efficient parsing of large XML files
        if HAS_LXML:
            context = ET.iterparse(xml_path, events=('start', 'end'), huge_tree=True)
        else:
            context = ET.iterparse(xml_path, events=('start', 'end'))
        context = iter(context)
        event, root = next(context)
        
        batch_count = 0
        
        # Set up progress bar (without total count for now, as counting is expensive)
        if self.show_progress and HAS_TQDM:
            pbar = tqdm(unit="entries", desc="Processing entries", total=None)
        else:
            pbar = None
        
        try:
            for event, elem in context:
                if event == 'end' and elem.tag == 'entry':
                    entry_data = self.parse_entry(elem)
                    if entry_data:
                        self.insert_entry(entry_data)
                        batch_count += 1
                        
                        # Commit in batches for performance
                        if batch_count >= batch_size:
                            self.conn.commit()
                            batch_count = 0
                    
                    if pbar is not None:
                        pbar.update(1)
                        # Update description with count
                        pbar.set_description(f"Processed {self.entry_count:,} entries")
                    
                    # Clear element to free memory
                    elem.clear()
                    root.clear()
        finally:
            if pbar is not None:
                pbar.close()
        
        # Final commit
        self.conn.commit()
        if self.show_progress:
            print(f"\nCompleted: {self.entry_count:,} entries processed")
        
    def optimize(self, vita_mode: bool = False):
        """Optimize database after conversion."""
        if self.show_progress:
            print("Optimizing database...")
        
        if vita_mode:
            if self.show_progress:
                print("  Setting memory-efficient settings...")
            self.cursor.execute("PRAGMA cache_size = 200")
            self.cursor.execute("PRAGMA journal_mode = DELETE")
            self.cursor.execute("PRAGMA mmap_size = 0")
            self.cursor.execute("PRAGMA temp_store = 2")
            self.cursor.execute("PRAGMA page_size = 4096")
        
        if self.show_progress:
            print("  Analyzing database for query optimization...")
        self.cursor.execute("ANALYZE")
        
        if self.show_progress:
            print("  Vacuuming database to reclaim space...")
        self.cursor.execute("VACUUM")
        
        if self.show_progress:
            print("  Rebuilding indexes...")
        self.cursor.execute("REINDEX")
        
        self.conn.commit()
        if self.show_progress:
            print("Database optimization complete")
        
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            
    def get_stats(self):
        """Print database statistics."""
        if not self.conn:
            return
            
        stats = {}
        self.cursor.execute("SELECT COUNT(*) FROM entries")
        stats['entries'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM kanji")
        stats['kanji'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM readings")
        stats['readings'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM glosses")
        stats['glosses'] = self.cursor.fetchone()[0]
        
        # Get database file size
        db_size = Path(self.db_path).stat().st_size
        stats['db_size_mb'] = db_size / (1024 * 1024)
        
        if self.show_progress:
            print("\nDatabase Statistics:")
            print(f"  Entries: {stats['entries']:,}")
            print(f"  Kanji elements: {stats['kanji']:,}")
            print(f"  Reading elements: {stats['readings']:,}")
            print(f"  Glosses: {stats['glosses']:,}")
            print(f"  Database size: {stats['db_size_mb']:.2f} MB")
        
        return stats


def download_jmdict_xml(download_dir: Path, show_progress: bool = True) -> Path:
    """
    Download JMdict_e.xml.gz from the official source.
    
    Args:
        download_dir: Directory to save the downloaded file
        show_progress: Whether to show download progress
        
    Returns:
        Path to the downloaded XML file (uncompressed)
    """
    download_dir.mkdir(parents=True, exist_ok=True)
    
    gz_path = download_dir / JMDICT_XML_FILENAME
    xml_path = download_dir / "JMdict_e.xml"
    
    # Check if XML already exists
    if xml_path.exists():
        if show_progress:
            print(f"JMdict XML file already exists: {xml_path}")
        return xml_path
    
    # Download the gzipped file
    if show_progress:
        print(f"Downloading JMdict from {JMDICT_XML_URL}...")
        print(f"This may take a few minutes (file is ~50MB compressed)...")
    
    try:
        if HAS_TQDM and show_progress:
            # Use tqdm for download progress
            from tqdm import tqdm
            
            class TqdmUpTo(tqdm):
                def update_to(self, b=1, bsize=1, tsize=None):
                    if tsize is not None:
                        self.total = tsize
                    self.update(b * bsize - self.n)
            
            with TqdmUpTo(unit='B', unit_scale=True, unit_divisor=1024, miniters=1) as t:
                urlretrieve(JMDICT_XML_URL, gz_path, reporthook=t.update_to)
        else:
            # Simple download without progress bar
            urlretrieve(JMDICT_XML_URL, gz_path)
        
        if show_progress:
            print(f"Download complete: {gz_path}")
    except URLError as e:
        raise RuntimeError(f"Failed to download JMdict: {e}") from e
    
    # Uncompress the file
    if show_progress:
        print(f"Extracting {gz_path}...")
    
    with gzip.open(gz_path, 'rb') as f_in:
        with open(xml_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Remove the gzipped file to save space
    gz_path.unlink()
    
    if show_progress:
        print(f"Extraction complete: {xml_path}")
    
    return xml_path


def build_database(
    db_path: str,
    xml_path: Optional[str] = None,
    download_dir: Optional[Path] = None,
    show_progress: bool = True,
    auto_download: bool = True
) -> bool:
    """
    Build the JMDict SQLite database.
    
    Args:
        db_path: Path where the database should be created
        xml_path: Path to JMdict_e.xml file (if None, will download)
        download_dir: Directory for downloaded files (default: module data dir)
        show_progress: Whether to show progress messages
        auto_download: Whether to automatically download XML if not found
        
    Returns:
        True if database was built successfully, False otherwise
    """
    db_path_obj = Path(db_path)
    
    # Check if database already exists
    if db_path_obj.exists():
        if show_progress:
            print(f"Database already exists: {db_path}")
        return True
    
    # Determine XML file path
    if xml_path is None:
        if download_dir is None:
            # Use a temporary directory for downloads (will be cleaned up after build)
            import tempfile
            download_dir = Path(tempfile.gettempdir()) / "tentoku"
        else:
            download_dir = Path(download_dir)
        
        if auto_download:
            try:
                xml_path = download_jmdict_xml(download_dir, show_progress=show_progress)
            except Exception as e:
                if show_progress:
                    print(f"Error downloading JMdict: {e}", file=sys.stderr)
                return False
        else:
            # Look for existing XML file
            xml_path = download_dir / "JMdict_e.xml"
            if not xml_path.exists():
                if show_progress:
                    print(f"JMdict XML file not found: {xml_path}")
                    print("Set auto_download=True to automatically download it")
                return False
    else:
        xml_path = Path(xml_path)
        if not xml_path.exists():
            if show_progress:
                print(f"XML file not found: {xml_path}", file=sys.stderr)
            return False
    
    # Ensure database directory exists
    db_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Create converter and build database
    converter = JMDictConverter(str(db_path), show_progress=show_progress)
    
    try:
        converter.connect()
        converter.create_schema()
        converter.convert(str(xml_path), batch_size=1000)
        converter.optimize(vita_mode=False)
        converter.get_stats()
        
        if show_progress:
            print(f"\n✓ Database built successfully: {db_path}")
        
        # Clean up downloaded XML files after successful build
        xml_path_obj = Path(xml_path)
        if xml_path_obj.exists():
            if show_progress:
                print(f"Cleaning up temporary files...")
            try:
                xml_path_obj.unlink()
                if show_progress:
                    print(f"Removed {xml_path_obj}")
            except Exception as e:
                if show_progress:
                    print(f"Note: Could not remove {xml_path_obj}: {e}")
        
        # Also clean up any .gz file in the same directory
        gz_path = xml_path_obj.parent / JMDICT_XML_FILENAME
        if gz_path.exists():
            try:
                gz_path.unlink()
                if show_progress:
                    print(f"Removed {gz_path}")
            except Exception as e:
                if show_progress:
                    print(f"Note: Could not remove {gz_path}: {e}")
        
        return True
        
    except KeyboardInterrupt:
        if show_progress:
            print("\n\nDatabase build interrupted by user")
        return False
    except Exception as e:
        if show_progress:
            print(f"\n\nError building database: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
        return False
    finally:
        converter.close()


def main():
    """Command-line interface for building the database."""
    parser = argparse.ArgumentParser(
        description='Build JMDict SQLite database from XML'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default=None,
        help='Path to output SQLite database file (default: tentoku/data/jmdict.db)'
    )
    parser.add_argument(
        '--xml-path',
        type=str,
        default=None,
        help='Path to JMdict_e.xml file (if not provided, will download)'
    )
    parser.add_argument(
        '--download-dir',
        type=str,
        default=None,
        help='Directory for downloaded files (default: tentoku/data)'
    )
    parser.add_argument(
        '--no-download',
        action='store_true',
        help='Do not automatically download XML file'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages'
    )
    
    args = parser.parse_args()
    
    # Determine database path
    if args.db_path is None:
        module_dir = Path(__file__).parent
        db_path = str(module_dir / "data" / "jmdict.db")
    else:
        db_path = args.db_path
    
    # Build database
    success = build_database(
        db_path=db_path,
        xml_path=args.xml_path,
        download_dir=Path(args.download_dir) if args.download_dir else None,
        show_progress=not args.quiet,
        auto_download=not args.no_download
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

