"""
Main tokenization interface.

This module provides the main tokenize function that implements the
greedy longest-match tokenization algorithm.
"""

from typing import List, Optional
from .dictionary import Dictionary
from ._types import Token
from .word_search import word_search
from .normalize import normalize_input

# Module-level cache for default dictionary
_default_dictionary: Optional[Dictionary] = None


def tokenize(
    text: str,
    dictionary: Optional[Dictionary] = None,
    include_romaji: bool = False
) -> List[Token]:
    """
    Tokenize Japanese text using greedy longest-match algorithm.
    
    This function implements the same greedy longest-match algorithm as used in 10ten Reader
    function:
    1. Start at position 0
    2. Find longest matching word
    3. Advance by match length
    4. If no match, advance by 1 character
    5. Repeat until end of text
    
    Args:
        text: Input text to tokenize
        dictionary: Dictionary to use for lookups. If None, uses a default SQLiteDictionary
                   (will auto-build database if needed on first use).
        include_romaji: Whether to include romaji (not yet implemented)
        
    Returns:
        List of Token objects
    """
    global _default_dictionary
    
    # Create default dictionary if not provided
    if dictionary is None:
        if _default_dictionary is None:
            from .sqlite_dict import SQLiteDictionary
            _default_dictionary = SQLiteDictionary()
        dictionary = _default_dictionary
    
    tokens: List[Token] = []
    offset = 0
    
    # Normalize the input text
    normalized, input_lengths = normalize_input(text)
    
    while offset < len(normalized):
        # Search for words starting at current offset
        remaining_text = normalized[offset:]
        
        # Create adjusted input_lengths for the remaining text
        # The lengths should be relative to the start of the remaining text
        if offset < len(input_lengths):
            base_length = input_lengths[offset]
            remaining_lengths = [
                l - base_length for l in input_lengths[offset:offset + len(remaining_text) + 1]
            ]
        else:
            remaining_lengths = None
        
        search_result = word_search(
            remaining_text,
            dictionary,
            max_results=1,
            input_lengths=remaining_lengths
        )
        
        if search_result and search_result.data:
            # Found a match
            word_result = search_result.data[0]
            match_len = search_result.match_len
            
            # Calculate actual text positions
            # match_len is in terms of the normalized input_lengths array
            # We need to find the corresponding character positions
            if offset + match_len < len(input_lengths):
                end_pos = input_lengths[offset + match_len]
            else:
                end_pos = len(text)
            
            token_text = text[offset:end_pos]
            
            tokens.append(Token(
                text=token_text,
                start=offset,
                end=end_pos,
                dictionary_entry=word_result.entry,
                deinflection_reasons=word_result.reason_chains
            ))
            
            # Advance by match length (in original text)
            offset = end_pos
        else:
            # No match found, advance by 1 character
            # Find the next character boundary in the original text
            if offset < len(input_lengths) - 1:
                next_offset = input_lengths[offset + 1] if offset + 1 < len(input_lengths) else offset + 1
            else:
                next_offset = offset + 1
            
            # Create a token for the single character
            char_text = text[offset:next_offset] if next_offset <= len(text) else text[offset:]
            tokens.append(Token(
                text=char_text,
                start=offset,
                end=next_offset if next_offset <= len(text) else len(text),
                dictionary_entry=None,
                deinflection_reasons=None
            ))
            
            offset = next_offset if next_offset <= len(text) else len(text)
    
    return tokens

