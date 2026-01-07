"""
Word type matching for deinflection validation.

This module validates that deinflected words match the expected word types
based on their part-of-speech tags.
"""

from ._types import WordEntry, WordType


def entry_matches_type(entry: WordEntry, word_type: int) -> bool:
    """
    Tests if a given entry matches the type of a generated deinflection.
    
    The deinflection code doesn't know anything about the actual words. It just
    produces possible deinflections along with a type that says what kind of a
    word (e.g. godan verb, i-adjective etc.) it must be in order for that
    deinflection to be valid.
    
    So, if we have a possible deinflection, we need to check that it matches
    the kind of word we looked up.
    
    Args:
        entry: Dictionary entry to check
        word_type: WordType bitmask from deinflection
        
    Returns:
        True if the entry's POS tags match the word type
    """
    # Get all POS tags from all senses
    all_pos_tags = []
    for sense in entry.senses:
        all_pos_tags.extend(sense.pos_tags)
    
    if not all_pos_tags:
        return False
    
    # Check each POS tag against the word type
    has_matching_sense = lambda test: any(test(pos) for pos in all_pos_tags)
    
    if word_type & WordType.IchidanVerb:
        if has_matching_sense(lambda pos: pos.startswith('v1') or 'Ichidan verb' in pos or pos == 'v1'):
            return True
    
    if word_type & WordType.GodanVerb:
        if has_matching_sense(lambda pos: pos.startswith('v5') or pos.startswith('v4') or 'Godan verb' in pos):
            return True
    
    if word_type & WordType.IAdj:
        if has_matching_sense(lambda pos: pos.startswith('adj-i') or 'adjective' in pos.lower()):
            return True
    
    if word_type & WordType.KuruVerb:
        if has_matching_sense(lambda pos: pos == 'vk' or 'kuru verb' in pos.lower()):
            return True
    
    if word_type & WordType.SuruVerb:
        if has_matching_sense(lambda pos: pos == 'vs-i' or pos == 'vs-s' or 'suru verb' in pos.lower()):
            return True
    
    if word_type & WordType.SpecialSuruVerb:
        if has_matching_sense(lambda pos: pos == 'vs-s' or pos == 'vz' or 'suru verb' in pos.lower()):
            return True
    
    if word_type & WordType.NounVS:
        if has_matching_sense(lambda pos: pos == 'vs' or ('noun or participle' in pos.lower() and 'suru' in pos.lower())):
            return True
    
    return False

