# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: initializedcheck=False
"""
Result sorting utilities - Cython optimized version.
"""

from typing import List, Dict
from tentoku._types import WordEntry, WordResult, Reason

# Priority score assignments
cdef dict PRIORITY_ASSIGNMENTS = {
    'i1': 50,
    'i2': 20,
    'n1': 40,
    'n2': 20,
    's1': 32,
    's2': 20,
    'g1': 30,
    'g2': 15,
}

cdef dict PRIORITY_MAP = {
    'ichi1': 'i1',
    'ichi2': 'i2',
    'news1': 'n1',
    'news2': 'n2',
    'spec1': 's1',
    'spec2': 's2',
    'gai1': 'g1',
    'gai2': 'g2',
}


cpdef str normalize_priority(str priority):
    """
    Normalize JMDict priority strings to short codes.
    """
    # If it's already a short code, return as-is
    if priority in PRIORITY_ASSIGNMENTS:
        return priority

    # Try mapping from full name
    if priority in PRIORITY_MAP:
        return PRIORITY_MAP[priority]

    # For nf## (word frequency), return as-is
    if priority.startswith('nf'):
        return priority

    return priority


cpdef int get_priority_score(str priority):
    """
    Get priority score for a priority string.
    """
    cdef str normalized
    cdef int wordfreq

    normalized = normalize_priority(priority)

    if normalized in PRIORITY_ASSIGNMENTS:
        return PRIORITY_ASSIGNMENTS[normalized]

    if normalized.startswith('nf'):
        try:
            wordfreq = int(normalized[2:])
            if 0 < wordfreq < 48:
                return int(48 - wordfreq / 2)
        except ValueError:
            pass

    return 0


cpdef double get_priority_sum(list priorities):
    """
    Produce an overall priority from a series of priority strings.
    """
    cdef list scores
    cdef double result
    cdef int i
    cdef int score

    if not priorities:
        return 0.0

    scores = []
    for p in priorities:
        scores.append(get_priority_score(p))
    scores = sorted(scores, reverse=True)

    if not scores:
        return 0.0

    result = <double>scores[0]
    for i in range(1, len(scores)):
        score = scores[i]
        result += <double>score / (10.0 ** i)

    return result


cpdef int get_priority(object entry):
    """
    Get priority score for an entry based on matched readings.
    """
    cdef list scores = [0]
    cdef list priorities
    cdef str priority
    cdef object kanji, kana

    # Scores from kanji readings (only those that matched)
    for kanji in entry.kanji_readings:
        if kanji.match_range and kanji.priority:
            priorities = []
            for p in kanji.priority.split(','):
                priorities.append(p.strip())
            if priorities:
                scores.append(int(get_priority_sum(priorities)))

    # Scores from kana readings (only those that matched)
    for kana in entry.kana_readings:
        if kana.match_range and kana.priority:
            priorities = []
            for p in kana.priority.split(','):
                priorities.append(p.strip())
            if priorities:
                scores.append(int(get_priority_sum(priorities)))

    return max(scores)


cpdef int get_kana_headword_type(object entry):
    """
    Determine the headword match type.

    1 = match on a kanji, or kana which is not just the reading for a kanji
    2 = match on a kana reading for a kanji
    """
    cdef object matching_kana = None
    cdef object kana, kanji, sense
    cdef bint is_reading_obscure = False
    cdef bint all_kanji_obscure
    cdef list matched_en_senses
    cdef int uk_en_sense_count
    cdef list info_parts

    # Check if we matched on a kana reading
    for kana in entry.kana_readings:
        if kana.match_range:
            matching_kana = kana
            break

    if not matching_kana:
        return 1

    # Check if reading is marked as obscure
    if matching_kana.info:
        info_parts = matching_kana.info.split(',')
        is_reading_obscure = False
        for part in info_parts:
            if part.strip() in ['ok', 'rk', 'sk', 'ik']:
                is_reading_obscure = True
                break

    if is_reading_obscure:
        return 2

    # Kana headwords are type 1 if entry has no kanji headwords
    if not entry.kanji_readings:
        return 1

    # Check if all kanji headwords are marked as obscure
    if entry.kanji_readings:
        all_kanji_obscure = True
        for kanji in entry.kanji_readings:
            if not kanji.info:
                all_kanji_obscure = False
                break
            has_obscure_tag = False
            for part in kanji.info.split(','):
                if part.strip() in ['rK', 'sK', 'iK']:
                    has_obscure_tag = True
                    break
            if not has_obscure_tag:
                all_kanji_obscure = False
                break

        if all_kanji_obscure:
            return 1

    # Check if most English senses have 'uk' misc field
    matched_en_senses = []
    for sense in entry.senses:
        if not sense.glosses:
            matched_en_senses.append(sense)
        else:
            has_en_gloss = False
            for g in sense.glosses:
                if g.lang in (None, 'eng', 'en'):
                    has_en_gloss = True
                    break
            if has_en_gloss:
                matched_en_senses.append(sense)

    if matched_en_senses:
        uk_en_sense_count = 0
        for sense in matched_en_senses:
            if sense.misc:
                has_uk = False
                for m in sense.misc:
                    if 'uk' in m:
                        has_uk = True
                        break
                if has_uk:
                    uk_en_sense_count += 1

        if uk_en_sense_count >= len(matched_en_senses) / 2:
            return 1

    # Check if headword is marked as nokanji
    if matching_kana.no_kanji:
        return 1

    return 2


def sort_word_results(list results):
    """
    Sort word results by deinflection steps, match type, and priority.
    """
    cdef dict sort_meta = {}
    cdef int reasons, match_type, priority
    cdef object result

    # Calculate sort metadata for each result
    for result in results:
        # Number of deinflection steps
        reasons = 0
        if result.reason_chains:
            reasons = max(len(chain) for chain in result.reason_chains)

        # Match type
        match_type = get_kana_headword_type(result.entry)

        # Priority
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
            meta['reasons'],
            meta['type'],
            -meta['priority']
        )

    return sorted(results, key=sort_key)
