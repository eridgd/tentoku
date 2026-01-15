"""
Build marisa-trie index from SQLite dictionary.

This module creates a trie index that maps dictionary keys (kanji and readings)
to entry IDs for fast O(key_length) lookups.

Usage:
    python -m tentoku.build_trie [--db-path PATH] [--output PATH]

Or called automatically on first use if trie doesn't exist.
"""

import struct
import sqlite3
from pathlib import Path
from collections import defaultdict
from typing import Optional

try:
    import marisa_trie
    MARISA_AVAILABLE = True
except ImportError:
    MARISA_AVAILABLE = False

from .normalize import kana_to_hiragana


def get_trie_path(db_path: Path) -> Path:
    """Get trie path corresponding to database path."""
    return db_path.with_suffix('.trie')


def build_trie_index(db_path: Path, output_path: Optional[Path] = None, show_progress: bool = True) -> Path:
    """
    Build trie index from SQLite dictionary.

    Args:
        db_path: Path to SQLite database
        output_path: Path for output trie file (defaults to db_path with .trie extension)
        show_progress: Whether to print progress messages

    Returns:
        Path to the created trie file

    Raises:
        ImportError: If marisa-trie is not installed
        FileNotFoundError: If database doesn't exist
    """
    if not MARISA_AVAILABLE:
        raise ImportError(
            "marisa-trie is required for trie index. "
            "Install with: pip install marisa-trie"
        )

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    if output_path is None:
        output_path = get_trie_path(db_path)

    if show_progress:
        print(f"Building trie index from {db_path}...")

    conn = sqlite3.connect(str(db_path))

    # Step 1: Collect all keys -> entry_ids
    key_to_ids: dict[str, list[int]] = defaultdict(list)

    # Index kanji forms
    if show_progress:
        print("  Indexing kanji forms...")
    cursor = conn.execute("SELECT kanji_text, entry_id FROM kanji")
    kanji_count = 0
    for kanji_text, entry_id in cursor:
        key_to_ids[kanji_text].append(entry_id)
        kanji_count += 1

    if show_progress:
        print(f"    Found {kanji_count} kanji forms")

    # Index reading forms (both original and hiragana-normalized)
    if show_progress:
        print("  Indexing reading forms...")
    cursor = conn.execute("SELECT reading_text, entry_id FROM readings")
    reading_count = 0
    normalized_count = 0
    for reading_text, entry_id in cursor:
        key_to_ids[reading_text].append(entry_id)
        reading_count += 1

        # Also index hiragana-normalized form for katakana lookups
        normalized = kana_to_hiragana(reading_text)
        if normalized != reading_text:
            key_to_ids[normalized].append(entry_id)
            normalized_count += 1

    if show_progress:
        print(f"    Found {reading_count} readings, {normalized_count} normalized variants")

    conn.close()

    # Step 2: Deduplicate entry_ids per key
    if show_progress:
        print("  Deduplicating entry IDs...")
    for key in key_to_ids:
        key_to_ids[key] = sorted(set(key_to_ids[key]))

    # Step 3: Pack into marisa-trie format
    if show_progress:
        print(f"  Building trie with {len(key_to_ids)} unique keys...")

    items = []
    for key, ids in key_to_ids.items():
        # Pack entry_ids as 4-byte little-endian unsigned integers
        packed = struct.pack('<' + 'I' * len(ids), *ids)
        items.append((key, packed))

    # Step 4: Build and save trie
    trie = marisa_trie.BytesTrie(items)
    trie.save(str(output_path))

    # Get file size
    file_size_mb = output_path.stat().st_size / (1024 * 1024)

    if show_progress:
        print(f"  Trie saved to {output_path} ({file_size_mb:.1f} MB)")

    return output_path


def is_trie_stale(db_path: Path, trie_path: Path) -> bool:
    """
    Check if trie is stale (database is newer than trie).

    Args:
        db_path: Path to SQLite database
        trie_path: Path to trie file

    Returns:
        True if trie needs to be rebuilt
    """
    if not trie_path.exists():
        return True

    if not db_path.exists():
        return False  # Can't rebuild without database

    db_mtime = db_path.stat().st_mtime
    trie_mtime = trie_path.stat().st_mtime

    return db_mtime > trie_mtime


def ensure_trie_exists(db_path: Path, show_progress: bool = True) -> Path:
    """
    Ensure trie index exists, building if necessary.

    Args:
        db_path: Path to SQLite database
        show_progress: Whether to print progress messages

    Returns:
        Path to the trie file
    """
    trie_path = get_trie_path(db_path)

    if is_trie_stale(db_path, trie_path):
        if show_progress:
            print("Building trie index (one-time operation)...")
        build_trie_index(db_path, trie_path, show_progress=show_progress)

    return trie_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build marisa-trie index from SQLite dictionary")
    parser.add_argument("--db-path", type=Path, help="Path to SQLite database")
    parser.add_argument("--output", type=Path, help="Output path for trie file")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress messages")
    args = parser.parse_args()

    # Find database path
    if args.db_path:
        db_path = args.db_path
    else:
        from .database_path import find_database_path
        db_path = find_database_path()
        if not db_path:
            print("Error: Could not find database. Specify --db-path")
            exit(1)

    output_path = args.output or get_trie_path(db_path)

    build_trie_index(db_path, output_path, show_progress=not args.quiet)
