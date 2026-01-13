# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: initializedcheck=False
"""
Text normalization utilities - Cython optimized version.

Handles Unicode normalization, full-width number conversion, and ZWNJ stripping.
"""

import unicodedata
from typing import Tuple, List

cdef int ZWNJ = 0x200C  # Zero-width non-joiner


cpdef str half_to_full_width_num(str text):
    """
    Convert half-width numbers to full-width numbers.

    Args:
        text: Input text

    Returns:
        Text with half-width numbers converted to full-width
    """
    cdef list result = []
    cdef int code
    cdef str char

    for char in text:
        code = ord(char)
        # Half-width digits: 0-9 (0x0030-0x0039)
        if 0x0030 <= code <= 0x0039:
            # Convert to full-width: ０-９ (0xFF10-0xFF19)
            result.append(chr(code - 0x0030 + 0xFF10))
        else:
            result.append(char)

    return ''.join(result)


cpdef tuple to_normalized(str text):
    """
    Normalize text and return input length mapping.

    Args:
        text: Input text

    Returns:
        Tuple of (normalized_text, input_lengths)
    """
    cdef str normalized
    cdef list input_lengths = []
    cdef int original_pos = 0
    cdef int i = 0
    cdef int char_len
    cdef str char
    cdef int char_code

    # Normalize to NFC (canonical composition)
    normalized = unicodedata.normalize('NFC', text)

    # Handle empty string
    if not normalized:
        return (normalized, [0])

    # Build input lengths array
    while i < len(normalized):
        char = normalized[i]
        char_code = ord(char)

        # Handle surrogate pairs (non-BMP characters)
        if char_code > 0xFFFF:
            # Surrogate pair takes 2 UTF-16 code units
            char_len = 2
        else:
            char_len = 1

        # Add mapping for each UTF-16 code unit
        for _ in range(char_len):
            input_lengths.append(original_pos)

        original_pos += 1
        i += 1

    # Add final position
    input_lengths.append(original_pos)

    return (normalized, input_lengths)


cpdef tuple do_strip_zwnj(str normalized, list input_lengths):
    """
    Strip zero-width non-joiners (ZWNJ) from text.

    Args:
        normalized: Normalized text
        input_lengths: Input length mapping array

    Returns:
        Tuple of (text_without_zwnj, adjusted_input_lengths)
    """
    cdef list result = []
    cdef list new_lengths = []
    cdef int last = 0
    cdef int i
    cdef str char
    cdef int code_point

    for i, char in enumerate(normalized):
        code_point = ord(char)
        if code_point != ZWNJ:
            result.append(char)
            if i < len(input_lengths):
                new_lengths.append(input_lengths[i])
            last = input_lengths[i + 1] if i + 1 < len(input_lengths) else input_lengths[-1]

    if last:
        new_lengths.append(last)

    return (''.join(result), new_lengths)


cpdef tuple normalize_input(str input_text, bint make_numbers_full_width=True, bint strip_zwnj=True):
    """
    Normalize input text for dictionary lookup.

    Args:
        input_text: Input text to normalize
        make_numbers_full_width: Convert half-width numbers to full-width
        strip_zwnj: Strip zero-width non-joiners

    Returns:
        Tuple of (normalized_text, input_lengths)
    """
    cdef str normalized
    cdef list input_lengths

    # Handle empty string early
    if not input_text:
        return ("", [0])

    normalized = input_text

    # Convert to full-width numbers
    if make_numbers_full_width:
        normalized = half_to_full_width_num(normalized)

    # Unicode normalization and character expansion
    normalized, input_lengths = to_normalized(normalized)

    # Strip zero-width non-joiners
    if strip_zwnj:
        normalized, input_lengths = do_strip_zwnj(normalized, input_lengths)

    # Ensure we always have at least one element
    if not input_lengths:
        input_lengths = [0]

    return (normalized, input_lengths)


cpdef str kana_to_hiragana(str text):
    """
    Convert katakana to hiragana.

    Args:
        text: Input text (may contain katakana)

    Returns:
        Text with katakana converted to hiragana
    """
    cdef list result = []
    cdef str char
    cdef int code

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
