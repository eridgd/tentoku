"""
Word search algorithm.

This module implements the backtracking word search algorithm that finds
the longest matching words in text, handling deinflection and variations.
"""

from typing import List, Optional, Set
from .dictionary import Dictionary
from ._types import WordResult, WordEntry, Reason
from .deinflect import deinflect
from .type_matching import entry_matches_type
from .sorting import sort_word_results
from .variations import expand_choon, kyuujitai_to_shinjitai
from .yoon import ends_in_yoon
from .normalize import normalize_input

# Try to import Cython-optimized versions, fall back to Python if not available
try:
    from .word_search_cy import (
        word_search as _word_search_cy,
        lookup_candidates as _lookup_candidates_cy,
        is_only_digits as _is_only_digits_cy,
        WordSearchResult as _WordSearchResult_cy,
    )
    _CYTHON_AVAILABLE = True
except ImportError:
    _CYTHON_AVAILABLE = False


class WordSearchResult:
    """Result from word search."""
    
    def __init__(self, data: List[WordResult], match_len: int, more: bool = False):
        self.data = data
        self.match_len = match_len
        self.more = more


def _is_only_digits_py(text: str) -> bool:
    """
    Check if text contains only digits, commas, and periods.
    
    Args:
        text: Text to check
        
    Returns:
        True if text contains only digits (half-width or full-width),
        commas, and periods
    """
    if not text:
        return False
    
    # Check for full-width and half-width digits, commas, periods
    for char in text:
        code = ord(char)
        # Half-width digits: 0x0030-0x0039
        # Full-width digits: 0xFF10-0xFF19
        # Half-width comma: 0x002C, period: 0x002E
        # Full-width comma: 0xFF0C, period: 0xFF0E
        # Ideographic comma: 0x3001, period: 0x3002
        if not (
            (0x0030 <= code <= 0x0039) or  # Half-width digits
            (0xFF10 <= code <= 0xFF19) or  # Full-width digits
            code == 0x002C or code == 0xFF0C or code == 0x3001 or  # Commas
            code == 0x002E or code == 0xFF0E or code == 0x3002     # Periods
        ):
            return False
    
    return True


def _word_search_py(
    input_text: str,
    dictionary: Dictionary,
    max_results: int = 7,
    input_lengths: Optional[List[int]] = None
) -> Optional[WordSearchResult]:
    """
    Search for words in input text using backtracking algorithm.
    
    This function implements a backtracking approach:
    1. Start with full input string
    2. Generate variations (choon expansion, kyuujitai conversion)
    3. Deinflect each variation to get candidate dictionary forms
    4. Look up candidates in dictionary
    5. Track longest successful match
    6. Shorten input and repeat
    
    Args:
        input_text: Input text to search (should be normalized)
        dictionary: Dictionary to search in
        max_results: Maximum number of results to return
        input_lengths: Input length mapping array (for tracking original positions)
        
    Returns:
        WordSearchResult with matched words, or None if no matches
    """
    longest_match = 0
    have: Set[int] = set()
    results: List[WordResult] = []
    include_variants = True
    
    # Normalize input if not already normalized
    if input_lengths is None:
        normalized, input_lengths = normalize_input(input_text)
    else:
        normalized = input_text
    
    current_input = normalized
    
    while current_input:
        # If we only have digits left, don't bother looking them up
        if _is_only_digits_py(current_input):
            break
        
        variations = [current_input]
        
        # Generate variations on this substring
        if include_variants:
            # Expand ー to its various possibilities
            variations.extend(expand_choon(current_input))
            
            # See if there are any 旧字体 we can convert to 新字体
            to_new = kyuujitai_to_shinjitai(current_input)
            if to_new != current_input:
                variations.append(to_new)
        
        current_input_length = input_lengths[len(current_input)] if len(current_input) < len(input_lengths) else input_lengths[-1]
        
        found_match = False
        for variant in variations:
            # Pass current_input (the shortened input we're trying) as matching_text
            # This ensures matchRange is set correctly for the current search length
            word_results = _lookup_candidates_py(
                variant,
                dictionary,
                have,
                max_results,
                current_input_length,
                current_input  # Pass current shortened input for matchRange setting
            )
            
            if not word_results:
                continue
            
            found_match = True
            
            # Update duplicates set
            have.update(word.entry.entry_id for word in word_results)
            
            # Update longest match length
            longest_match = max(longest_match, current_input_length)
            
            # Add results (but don't limit yet - continue to try shorter matches)
            # This ensures we collect results from all match lengths before sorting
            # We'll limit to max_results after sorting all results together
            results.extend(word_results)
            
            # Mark that we found a match, but continue to try shorter matches
            found_match = True

            # Continue refining this variant excluding all others
            current_input = variant
            include_variants = False
            break

        # Don't break early - continue trying shorter matches to find all possible results
        # Only break if we have collected way too many results
        if len(results) >= max_results * 5:
            break
        
        # Shorten input to try shorter matches, but don't split a ようおん (e.g. きゃ)
        length_to_shorten = 2 if ends_in_yoon(current_input) else 1
        current_input = current_input[:len(current_input) - length_to_shorten]
    
    if not results:
        return None
    
    # Sort all results together (results from different iterations may have been
    # sorted separately, but we want them sorted as a whole)
    # Note: sort_word_results now uses matchRange from entries, not matching_text
    results = sort_word_results(results)
    
    # Now limit to max_results AFTER sorting
    # This ensures we get the best results by priority, not just the longest matches
    results = results[:max_results]
    
    return WordSearchResult(
        data=results,
        match_len=longest_match,
        more=len(results) >= max_results
    )


def _lookup_candidates_py(
    input_text: str,
    dictionary: Dictionary,
    existing_entries: Set[int],
    max_results: int,
    input_length: int,
    original_search_text: Optional[str] = None
) -> List[WordResult]:
    """
    Look up candidates for a given input, handling deinflection.
    
    Args:
        input_text: Input text to look up
        dictionary: Dictionary to search
        existing_entries: Set of entry IDs we already have
        max_results: Maximum number of results
        input_length: Original input length for this match
        
    Returns:
        List of WordResult objects
    """
    candidate_results: List[WordResult] = []
    
    # Deinflect the input to get candidate dictionary forms
    candidates = deinflect(input_text)
    
    for candidate_index, candidate in enumerate(candidates):
        # Look up this candidate in the dictionary
        # Get more results than max_results so we can sort and pick the best ones
        # Changed from max(max_results * 3, 20) to max_results * 2 to reduce excessive lookups
        lookup_max = max_results * 2
        # Pass original_search_text (or input_text if not provided) as matching_text
        # matchRange should be based on the original input text, not the deinflected form
        # This matches 10ten Reader's behavior where matchingText is the original input
        matching_text = original_search_text if original_search_text is not None else input_text
        word_entries = dictionary.get_words(candidate.word, lookup_max, matching_text=matching_text)
        
        # Filter by word type if this is a deinflection (not the original)
        is_deinflection = candidate_index != 0
        if is_deinflection:
            word_entries = [
                entry for entry in word_entries
                if entry_matches_type(entry, candidate.type)
            ]
        
        # Drop redundant results
        word_entries = [
            entry for entry in word_entries
            if entry.entry_id not in existing_entries
        ]
        
        # Convert to WordResult
        for entry in word_entries:
            candidate_results.append(WordResult(
                entry=entry,
                match_len=input_length,
                reason_chains=candidate.reason_chains if candidate.reason_chains else None
            ))
    
    # Sort results across all candidate lookups
    # Note: sort_word_results now uses matchRange from entries, not matching_text
    if candidate_results:
        candidate_results = sort_word_results(candidate_results)
    
    return candidate_results[:max_results]


# Use Cython versions if available, otherwise use Python fallback
if _CYTHON_AVAILABLE:
    is_only_digits = _is_only_digits_cy
    word_search = _word_search_cy
    lookup_candidates = _lookup_candidates_cy
    # Use Cython's WordSearchResult if available
    WordSearchResult = _WordSearchResult_cy
else:
    is_only_digits = _is_only_digits_py
    word_search = _word_search_py
    lookup_candidates = _lookup_candidates_py
    # Python WordSearchResult is already defined above

