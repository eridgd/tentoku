# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: initializedcheck=False
"""
Word type matching for deinflection validation - Cython optimized version.
"""

from tentoku._types import WordEntry, WordType


cpdef bint entry_matches_type(WordEntry entry, int word_type):
    """
    Tests if a given entry matches the type of a generated deinflection.

    Args:
        entry: Dictionary entry to check
        word_type: WordType bitmask from deinflection

    Returns:
        True if the entry's POS tags match the word type
    """
    cdef list all_pos_tags = []
    cdef str pos
    cdef object sense

    # Get all POS tags from all senses
    for sense in entry.senses:
        all_pos_tags.extend(sense.pos_tags)

    if not all_pos_tags:
        return False

    # Check each POS tag against the word type
    if word_type & WordType.IchidanVerb:
        for pos in all_pos_tags:
            if pos.startswith('v1') or 'Ichidan verb' in pos or pos == 'v1':
                return True

    if word_type & WordType.GodanVerb:
        for pos in all_pos_tags:
            if pos.startswith('v5') or pos.startswith('v4') or 'Godan verb' in pos:
                return True

    if word_type & WordType.IAdj:
        for pos in all_pos_tags:
            if pos.startswith('adj-i') or 'adjective' in pos.lower():
                return True

    if word_type & WordType.KuruVerb:
        for pos in all_pos_tags:
            if pos == 'vk' or 'kuru verb' in pos.lower():
                return True

    if word_type & WordType.SuruVerb:
        for pos in all_pos_tags:
            if pos == 'vs-i' or pos == 'vs-s' or 'suru verb' in pos.lower():
                return True

    if word_type & WordType.SpecialSuruVerb:
        for pos in all_pos_tags:
            if pos == 'vs-s' or pos == 'vz' or 'suru verb' in pos.lower():
                return True

    if word_type & WordType.NounVS:
        for pos in all_pos_tags:
            if pos == 'vs' or ('noun or participle' in pos.lower() and 'suru' in pos.lower()):
                return True

    return False
