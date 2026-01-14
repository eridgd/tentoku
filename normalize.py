"""
Text normalization utilities.

Handles Unicode normalization, full-width number conversion, and ZWNJ stripping.
"""

import unicodedata
from typing import Tuple, List

# Try to import Cython-optimized versions, fall back to Python if not available
try:
    from .normalize_cy import (
        normalize_input as _normalize_input_cy,
        kana_to_hiragana as _kana_to_hiragana_cy,
        half_to_full_width_num as _half_to_full_width_num_cy,
        to_normalized as _to_normalized_cy,
        do_strip_zwnj as _do_strip_zwnj_cy,
    )
    _CYTHON_AVAILABLE = True
except ImportError:
    _CYTHON_AVAILABLE = False


ZWNJ = 0x200C  # Zero-width non-joiner


def _half_to_full_width_num_py(text: str) -> str:
    """
    Convert half-width numbers to full-width numbers.
    
    Args:
        text: Input text
        
    Returns:
        Text with half-width numbers converted to full-width
    """
    result = []
    for char in text:
        code = ord(char)
        # Half-width digits: 0-9 (0x0030-0x0039)
        if 0x0030 <= code <= 0x0039:
            # Convert to full-width: ０-９ (0xFF10-0xFF19)
            result.append(chr(code - 0x0030 + 0xFF10))
        else:
            result.append(char)
    return ''.join(result)


def _to_normalized_py(text: str) -> Tuple[str, List[int]]:
    """
    Normalize text and return input length mapping.
    
    This handles Unicode normalization (NFD/NFC), expands combined characters,
    and returns a mapping array that uses 16-bit character offsets as opposed
    to Unicode codepoints.
    
    Args:
        text: Input text
        
    Returns:
        Tuple of (normalized_text, input_lengths)
        where input_lengths[i] is the original input length up to position i
    """
    # Normalize to NFC (canonical composition)
    normalized = unicodedata.normalize('NFC', text)
    
    # Handle empty string
    if not normalized:
        return normalized, [0]
    
    # Build input lengths array
    # This maps each position in the normalized string to the original input length
    input_lengths = []
    original_pos = 0
    
    # Iterate through normalized string
    i = 0
    while i < len(normalized):
        char = normalized[i]
        char_len = len(char.encode('utf-16-le')) // 2  # UTF-16 code units
        
        # Handle surrogate pairs (non-BMP characters)
        if ord(char) > 0xFFFF:
            # Surrogate pair takes 2 UTF-16 code units
            char_len = 2
        
        # Add mapping for each UTF-16 code unit
        for _ in range(char_len):
            input_lengths.append(original_pos)
        
        # Advance original position by 1 (we count characters, not code units)
        original_pos += 1
        i += 1
    
    # Add final position
    input_lengths.append(original_pos)
    
    return normalized, input_lengths


def _do_strip_zwnj_py(normalized: str, input_lengths: List[int]) -> Tuple[str, List[int]]:
    """
    Strip zero-width non-joiners (ZWNJ) from text.
    
    Google Docs sometimes inserts ZWNJ between every character.
    
    Args:
        normalized: Normalized text
        input_lengths: Input length mapping array
        
    Returns:
        Tuple of (text_without_zwnj, adjusted_input_lengths)
    """
    result = []
    new_lengths = []
    last = 0
    
    for i, char in enumerate(normalized):
        code_point = ord(char) if len(char) == 1 else ord(char[0])
        if code_point != ZWNJ:
            result.append(char)
            if i < len(input_lengths):
                new_lengths.append(input_lengths[i])
            last = input_lengths[i + 1] if i + 1 < len(input_lengths) else input_lengths[-1]
    
    if last:
        new_lengths.append(last)
    
    return ''.join(result), new_lengths


# Use Cython versions if available, otherwise use Python fallback
if _CYTHON_AVAILABLE:
    half_to_full_width_num = _half_to_full_width_num_cy
    to_normalized = _to_normalized_cy
    do_strip_zwnj = _do_strip_zwnj_cy
else:
    half_to_full_width_num = _half_to_full_width_num_py
    to_normalized = _to_normalized_py
    do_strip_zwnj = _do_strip_zwnj_py


def _normalize_input_py(
    input_text: str,
    make_numbers_full_width: bool = True,
    strip_zwnj: bool = True
) -> Tuple[str, List[int]]:
    """
    Normalize input text for dictionary lookup (Python fallback implementation).
    
    This method returns an array of input lengths which use 16-bit character
    offsets as opposed to Unicode codepoints. This allows us to use .length,
    .substring etc. on the matched string.
    
    Args:
        input_text: Input text to normalize
        make_numbers_full_width: Convert half-width numbers to full-width
        strip_zwnj: Strip zero-width non-joiners
        
    Returns:
        Tuple of (normalized_text, input_lengths)
        where input_lengths[i] is the original input length up to position i
    """
    # Handle empty string early
    if not input_text:
        return "", [0]
    
    normalized = input_text
    
    # Convert to full-width numbers
    if make_numbers_full_width:
        normalized = half_to_full_width_num(normalized)
    
    # Unicode normalization and character expansion
    normalized, input_lengths = to_normalized(normalized)
    
    # Strip zero-width non-joiners
    if strip_zwnj:
        normalized, input_lengths = do_strip_zwnj(normalized, input_lengths)
    
    # Ensure we always have at least one element (for empty string case after stripping)
    if not input_lengths:
        input_lengths = [0]
    
    return normalized, input_lengths


# Use Cython version if available, otherwise use Python fallback
# Fixed: Replace function directly instead of wrapping to preserve Cython function type
if _CYTHON_AVAILABLE:
    normalize_input = _normalize_input_cy
else:
    normalize_input = _normalize_input_py


def _kana_to_hiragana_py(text: str) -> str:
    """
    Convert katakana to hiragana (Python fallback implementation).
    
    Args:
        text: Input text (may contain katakana)
        
    Returns:
        Text with katakana converted to hiragana
    """
    result = []
    for char in text:
        code = ord(char)
        # Katakana range: 0x30A0-0x30FF
        # Hiragana range: 0x3040-0x309F
        if 0x30A1 <= code <= 0x30F6:
            # Convert katakana to hiragana
            result.append(chr(code - 0x30A0 + 0x3040))
        elif code == 0x30F7:  # ヷ
            result.append('わ')
        elif code == 0x30F8:  # ヸ
            result.append('ゐ')
        elif code == 0x30F9:  # ヹ
            result.append('ゑ')
        elif code == 0x30FA:  # ヺ
            result.append('を')
        else:
            result.append(char)
    return ''.join(result)


# Use Cython version if available, otherwise use Python fallback
# Fixed: Replace function directly instead of wrapping to preserve Cython function type
if _CYTHON_AVAILABLE:
    kana_to_hiragana = _kana_to_hiragana_cy
else:
    kana_to_hiragana = _kana_to_hiragana_py

