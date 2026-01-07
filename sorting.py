"""
Result sorting utilities.

This module implements the sorting logic for word search results, prioritizing
results based on deinflection steps, match type, and priority.
"""

from typing import List, Dict, Optional
from ._types import WordEntry, WordResult, Reason


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


def get_priority_score(priority: str) -> int:
    """
    Get priority score for a priority string.
    
    Args:
        priority: Priority string (e.g., 'i1', 'n1', 'nf01')
        
    Returns:
        Priority score (0-50+)
    """
    if priority in PRIORITY_ASSIGNMENTS:
        return PRIORITY_ASSIGNMENTS[priority]
    
    if priority.startswith('nf'):
        # The wordfreq scores are groups of 500 words.
        # e.g. nf01 is the top 500 words, and nf48 is the 23,501 ~ 24,000
        # most popular words.
        try:
            wordfreq = int(priority[2:])
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


def get_priority(entry: WordEntry, matching_text: str) -> int:
    """
    Get priority score for an entry based on matching text.
    
    Args:
        entry: Dictionary entry
        matching_text: The text that was matched
        
    Returns:
        Priority score
    """
    scores = [0]
    
    # Scores from kanji readings
    for kanji in entry.kanji_readings:
        if kanji.text == matching_text and kanji.priority:
            # Priority can be comma-separated
            priorities = [p.strip() for p in kanji.priority.split(',')] if kanji.priority else []
            if priorities:
                scores.append(get_priority_sum(priorities))
    
    # Scores from kana readings
    for kana in entry.kana_readings:
        if kana.text == matching_text and kana.priority:
            # Priority can be comma-separated
            priorities = [p.strip() for p in kana.priority.split(',')] if kana.priority else []
            if priorities:
                scores.append(get_priority_sum(priorities))
    
    # Return top score
    return max(scores)


def get_kana_headword_type(entry: WordEntry, matching_text: str) -> int:
    """
    Determine the headword match type.
    
    1 = match on a kanji, or kana which is not just the reading for a kanji
    2 = match on a kana reading for a kanji
    
    Args:
        entry: Dictionary entry
        matching_text: The text that was matched
        
    Returns:
        1 or 2
    """
    # Check if we matched on a kana reading
    matching_kana = None
    for kana in entry.kana_readings:
        if kana.text == matching_text:
            matching_kana = kana
            break
    
    if not matching_kana:
        return 1  # Matched on kanji
    
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
    #     `misc` field
    # Note: We don't have a 'match' field like the TypeScript version, so we
    # check all senses. The TypeScript version filters for matched English senses.
    matched_en_senses = [
        sense for sense in entry.senses
        # Filter for English senses (default lang is 'eng')
        if not sense.glosses or any(g.lang in (None, 'eng', 'en') for g in sense.glosses)
    ]
    if matched_en_senses:
        uk_en_sense_count = sum(
            1 for sense in matched_en_senses
            if sense.misc and any('uk' in m for m in sense.misc)
        )
        if uk_en_sense_count >= len(matched_en_senses) / 2:
            return 1
    
    # (c) the headword is marked as `nokanji`
    if matching_kana.no_kanji:
        return 1
    
    return 2


def sort_word_results(results: List[WordResult], matching_text: str) -> List[WordResult]:
    """
    Sort word results by deinflection steps, match type, and priority.
    
    Sorting criteria (in order):
    1. Number of deinflection steps (fewer = better)
    2. Match type: kanji/kana primary headword (1) vs reading (2)
    3. Priority score (higher = better)
    
    Args:
        results: List of word results to sort
        matching_text: The text that was matched (for priority calculation)
        
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
        
        # Match type
        match_type = get_kana_headword_type(result.entry, matching_text)
        
        # Priority
        priority = get_priority(result.entry, matching_text)
        
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

