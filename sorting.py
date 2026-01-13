"""
Result sorting utilities.

This module implements the sorting logic for word search results, prioritizing
results based on deinflection steps, match type, and priority.
"""

from typing import List, Dict, Optional
from ._types import WordEntry, WordResult, Reason

# Try to import Cython-optimized version, fall back to Python if not available
try:
    from .sorting_cy import sort_word_results as _sort_word_results_cy
    _CYTHON_AVAILABLE = True
except ImportError:
    _CYTHON_AVAILABLE = False


# Priority score assignments
PRIORITY_ASSIGNMENTS: Dict[str, int] = {
    'i1': 50,  # Top 10,000 words minus i2 (from 1998) (P)
    'i2': 20,
    'n1': 40,  # Top 12,000 words in newspapers (from 2003?) (P)
    'n2': 20,  # Next 12,000
    's1': 32,  # "Speculative" annotations? Seem pretty common to me. (P)
    's2': 20,  # (P)
    'g1': 30,  # (P)
    'g2': 15,
}


def normalize_priority(priority: str) -> str:
    """
    Normalize JMDict priority strings to short codes.
    
    JMDict uses full names like 'ichi1', 'news1', 'spec1', etc.
    but the priority assignments use short codes like 'i1', 'n1', 's1'.
    
    Args:
        priority: Priority string from JMDict (e.g., 'ichi1', 'news1')
        
    Returns:
        Normalized priority code (e.g., 'i1', 'n1')
    """
    # Map full JMDict priority names to short codes
    # Based on JMDict documentation and 10ten Reader's usage
    priority_map = {
        'ichi1': 'i1',
        'ichi2': 'i2',
        'news1': 'n1',
        'news2': 'n2',
        'spec1': 's1',
        'spec2': 's2',
        'gai1': 'g1',
        'gai2': 'g2',
    }
    
    # If it's already a short code, return as-is
    if priority in PRIORITY_ASSIGNMENTS:
        return priority
    
    # Try mapping from full name
    if priority in priority_map:
        return priority_map[priority]
    
    # For nf## (word frequency), return as-is
    if priority.startswith('nf'):
        return priority
    
    # Unknown priority, return as-is (will get score 0)
    return priority


def get_priority_score(priority: str) -> int:
    """
    Get priority score for a priority string.
    
    Args:
        priority: Priority string (e.g., 'i1', 'n1', 'nf01', or 'ichi1', 'news1')
        
    Returns:
        Priority score (0-50+)
    """
    # Normalize to short code
    normalized = normalize_priority(priority)
    
    if normalized in PRIORITY_ASSIGNMENTS:
        return PRIORITY_ASSIGNMENTS[normalized]
    
    if normalized.startswith('nf'):
        # The wordfreq scores are groups of 500 words.
        # e.g. nf01 is the top 500 words, and nf48 is the 23,501 ~ 24,000
        # most popular words.
        try:
            wordfreq = int(normalized[2:])
            if 0 < wordfreq < 48:
                return int(48 - wordfreq / 2)
        except ValueError:
            pass
    
    return 0


def get_priority_sum(priorities: List[str]) -> int:
    """
    Produce an overall priority from a series of priority strings.
    
    This should produce a value somewhere in the range 0~67.
    
    In general we report the highest priority, but if we have several priority
    scores we add a decreasing fraction (10%) of the lesser scores as an
    indication that several sources have attested to the priority.
    
    Args:
        priorities: List of priority strings
        
    Returns:
        Combined priority score
    """
    if not priorities:
        return 0
    
    scores = sorted([get_priority_score(p) for p in priorities], reverse=True)
    
    if not scores:
        return 0
    
    # Highest score plus decreasing fractions of lesser scores
    result = scores[0]
    for i, score in enumerate(scores[1:], 1):
        result += score / (10 ** i)
    
    return result


def get_priority(entry: WordEntry) -> int:
    """
    Get priority score for an entry based on matched readings.
    
    Only uses priority from readings that have matchRange (i.e., that matched the input).
    This matches 10ten Reader's behavior.
    
    Args:
        entry: Dictionary entry
        
    Returns:
        Priority score
    """
    scores = [0]
    
    # Scores from kanji readings (only those that matched)
    for kanji in entry.kanji_readings:
        if kanji.match_range and kanji.priority:
            # Priority can be comma-separated
            priorities = [p.strip() for p in kanji.priority.split(',')] if kanji.priority else []
            if priorities:
                scores.append(get_priority_sum(priorities))
    
    # Scores from kana readings (only those that matched)
    for kana in entry.kana_readings:
        if kana.match_range and kana.priority:
            # Priority can be comma-separated
            priorities = [p.strip() for p in kana.priority.split(',')] if kana.priority else []
            if priorities:
                scores.append(get_priority_sum(priorities))
    
    # Return top score
    return max(scores)


def get_kana_headword_type(entry: WordEntry) -> int:
    """
    Determine the headword match type.
    
    1 = match on a kanji, or kana which is not just the reading for a kanji
    2 = match on a kana reading for a kanji
    
    Uses matchRange to find which kana matched, matching 10ten Reader's behavior.
    
    Args:
        entry: Dictionary entry
        
    Returns:
        1 or 2
    """
    # Check if we matched on a kana reading (using matchRange like 10ten Reader)
    matching_kana = None
    for kana in entry.kana_readings:
        if kana.match_range:
            matching_kana = kana
            break
    
    if not matching_kana:
        return 1  # Matched on kanji (or no match)
    
    # Check if reading is marked as obscure
    is_reading_obscure = False
    if matching_kana.info:
        info_parts = matching_kana.info.split(',')
        is_reading_obscure = any(
            part.strip() in ['ok', 'rk', 'sk', 'ik'] for part in info_parts
        )
    
    if is_reading_obscure:
        return 2
    
    # Kana headwords are type 1 if:
    # (a) the entry has no kanji headwords or all the kanji headwords are marked
    #     as `rK`, `sK`, or `iK`.
    if not entry.kanji_readings:
        return 1
    
    # Check if all kanji headwords are marked as obscure (rK, sK, or iK)
    # If any kanji has no info or is not marked as obscure, this fails
    if entry.kanji_readings:
        all_kanji_obscure = all(
            kanji.info and any(
                part.strip() in ['rK', 'sK', 'iK']
                for part in kanji.info.split(',')
            )
            for kanji in entry.kanji_readings
        )
        
        if all_kanji_obscure:
            return 1
    
    # (b) most of the English senses for the entry have a `uk` (usually kana)
    #     `misc` field and the reading is not marked as `ok` (old kana usage).
    #
    # Note: 10ten Reader filters for s.match && (s.lang === undefined || s.lang === 'en')
    # In flat-file.ts, all senses get match: true, so we check all English senses.
    # Since tentoku uses SQLite (similar to flat file), we check all English senses.
    matched_en_senses = [
        sense for sense in entry.senses
        # Filter for English senses (default lang is 'eng' or 'en')
        if not sense.glosses or any(g.lang in (None, 'eng', 'en') for g in sense.glosses)
    ]
    if matched_en_senses:
        uk_en_sense_count = sum(
            1 for sense in matched_en_senses
            if sense.misc and any('uk' in m for m in sense.misc)
        )
        # Check if at least half of the English senses are marked as 'uk'
        if uk_en_sense_count >= len(matched_en_senses) / 2:
            return 1
    
    # (c) the headword is marked as `nokanji`
    if matching_kana.no_kanji:
        return 1
    
    return 2


def _sort_word_results_py(results: List[WordResult]) -> List[WordResult]:
    """
    Sort word results by deinflection steps, match type, and priority.
    
    Sorting criteria (in order):
    1. Number of deinflection steps (fewer = better)
    2. Match type: kanji/kana primary headword (1) vs reading (2)
    3. Priority score (higher = better)
    
    This matches 10ten Reader's sortWordResults function exactly.
    Uses matchRange to determine which reading matched, not matching_text.
    
    Args:
        results: List of word results to sort
        
    Returns:
        Sorted list of word results
    """
    # Calculate sort metadata for each result
    sort_meta: Dict[int, Dict[str, int]] = {}
    
    for result in results:
        # Number of deinflection steps
        reasons = 0
        if result.reason_chains:
            reasons = max(len(chain) for chain in result.reason_chains)
        
        # Match type (uses matchRange internally)
        match_type = get_kana_headword_type(result.entry)
        
        # Priority (uses matchRange internally)
        priority = get_priority(result.entry)
        
        sort_meta[result.entry.entry_id] = {
            'reasons': reasons,
            'type': match_type,
            'priority': priority
        }
    
    # Sort results
    def sort_key(result: WordResult) -> tuple:
        meta = sort_meta[result.entry.entry_id]
        return (
            meta['reasons'],      # Fewer deinflection steps = better
            meta['type'],         # Type 1 (primary) before type 2 (reading)
            -meta['priority']     # Higher priority = better (negate for ascending)
        )
    
    return sorted(results, key=sort_key)


# Use Cython version if available, otherwise use Python fallback
if _CYTHON_AVAILABLE:
    sort_word_results = _sort_word_results_cy
else:
    sort_word_results = _sort_word_results_py

