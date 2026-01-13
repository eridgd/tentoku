# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: initializedcheck=False
"""
Word search algorithm - Cython optimized version.
"""

from typing import List, Optional, Set
from tentoku.dictionary import Dictionary
from tentoku._types import WordResult, WordEntry, Reason
from tentoku.deinflect_cy import deinflect
from tentoku.type_matching_cy import entry_matches_type
from tentoku.sorting_cy import sort_word_results
from tentoku.variations_cy import expand_choon, kyuujitai_to_shinjitai
from tentoku.yoon_cy import ends_in_yoon
from tentoku.normalize_cy import normalize_input


class WordSearchResult:
    """Result from word search."""

    def __init__(self, data: List[WordResult], match_len: int, more: bool = False):
        self.data = data
        self.match_len = match_len
        self.more = more


cpdef bint is_only_digits(str text):
    """
    Check if text contains only digits, commas, and periods.
    """
    cdef int code
    cdef str char

    if not text:
        return False

    for char in text:
        code = ord(char)
        if not (
            (0x0030 <= code <= 0x0039) or  # Half-width digits
            (0xFF10 <= code <= 0xFF19) or  # Full-width digits
            code == 0x002C or code == 0xFF0C or code == 0x3001 or  # Commas
            code == 0x002E or code == 0xFF0E or code == 0x3002     # Periods
        ):
            return False

    return True


def word_search(
    str input_text,
    object dictionary,
    int max_results=7,
    object input_lengths=None
):
    """
    Search for words in input text using backtracking algorithm.

    Args:
        input_text: Input text to search
        dictionary: Dictionary to search in
        max_results: Maximum number of results to return
        input_lengths: Input length mapping array

    Returns:
        WordSearchResult with matched words, or None if no matches
    """
    cdef int longest_match = 0
    cdef set have = set()
    cdef list results = []
    cdef bint include_variants = True
    cdef str normalized, current_input
    cdef list variations
    cdef int current_input_length
    cdef bint found_match
    cdef str variant
    cdef list word_results
    cdef int length_to_shorten
    cdef object word

    # Normalize input if not already normalized
    if input_lengths is None:
        normalized, input_lengths = normalize_input(input_text)
    else:
        normalized = input_text

    current_input = normalized

    while current_input:
        # Skip if only digits left
        if is_only_digits(current_input):
            break

        variations = [current_input]

        # Generate variations
        if include_variants:
            variations.extend(expand_choon(current_input))

            to_new = kyuujitai_to_shinjitai(current_input)
            if to_new != current_input:
                variations.append(to_new)

        current_input_length = input_lengths[len(current_input)] if len(current_input) < len(input_lengths) else input_lengths[-1]

        found_match = False
        for variant in variations:
            word_results = lookup_candidates(
                variant,
                dictionary,
                have,
                max_results,
                current_input_length,
                current_input
            )

            if not word_results:
                continue

            found_match = True

            # Update duplicates set
            have.update(word.entry.entry_id for word in word_results)

            # Update longest match length
            longest_match = max(longest_match, current_input_length)

            # Add results
            results.extend(word_results)

            found_match = True

            # Continue refining this variant
            current_input = variant
            include_variants = False
            break

        # Don't break early - continue trying shorter matches to find all possible results
        # Only break if we have collected way too many results
        if len(results) >= max_results * 5:
            break

        # Shorten input
        length_to_shorten = 2 if ends_in_yoon(current_input) else 1
        current_input = current_input[:len(current_input) - length_to_shorten]

    if not results:
        return None

    # Sort all results
    results = sort_word_results(results)

    # Limit to max_results
    results = results[:max_results]

    return WordSearchResult(
        data=results,
        match_len=longest_match,
        more=len(results) >= max_results
    )


def lookup_candidates(
    str input_text,
    object dictionary,
    set existing_entries,
    int max_results,
    int input_length,
    object original_search_text=None
):
    """
    Look up candidates for a given input, handling deinflection.

    Args:
        input_text: Input text to look up
        dictionary: Dictionary to search
        existing_entries: Set of entry IDs we already have
        max_results: Maximum number of results
        input_length: Original input length for this match
        original_search_text: Original search text for matchRange

    Returns:
        List of WordResult objects
    """
    cdef list candidate_results = []
    cdef list candidates
    cdef int candidate_index
    cdef object candidate
    cdef int lookup_max
    cdef str matching_text
    cdef list word_entries
    cdef bint is_deinflection
    cdef object entry

    # Deinflect the input
    candidates = deinflect(input_text)

    for candidate_index, candidate in enumerate(candidates):
        # Look up in dictionary
        # Changed from max(max_results * 3, 20) to max_results * 2 to reduce excessive lookups
        lookup_max = max_results * 2
        matching_text = original_search_text if original_search_text is not None else input_text
        word_entries = dictionary.get_words(candidate.word, lookup_max, matching_text=matching_text)

        # Filter by word type if this is a deinflection
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

    # Sort results
    if candidate_results:
        candidate_results = sort_word_results(candidate_results)

    return candidate_results[:max_results]
