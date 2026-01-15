# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: initializedcheck=False
"""
Core deinflection logic - Cython optimized version with C++ unordered_map.
"""

from typing import List, Dict
from tentoku._types import CandidateWord, WordType, Reason
from tentoku.deinflect_rules import get_rules_by_ending
from tentoku.normalize_cy import kana_to_hiragana

# Import C++ unordered_map for faster lookups
from libcpp.unordered_map cimport unordered_map
from libcpp.string cimport string
from libcpp.pair cimport pair


cpdef list deinflect(str word):
    """
    Returns an array of possible de-inflected versions of a word.

    Optimized with C++ unordered_map for faster string lookups.

    Args:
        word: The word to deinflect

    Returns:
        List of CandidateWord objects
    """
    cdef list result = []
    # Use C++ unordered_map instead of Python dict for faster lookups
    cdef unordered_map[string, int] result_index
    # Get the rules index (cached) for O(1) lookup instead of O(rules) linear scan
    cdef dict rules_by_ending = get_rules_by_ending()
    cdef int i = 0
    cdef object this_candidate
    cdef str word_text, ending, hiragana_ending, new_word
    cdef int word_type
    cdef object rule_group, rule
    cdef list reason_chains, first_reason_chain
    cdef set rule_reasons_set
    cdef list flat_reasons
    cdef object existing_candidate
    cdef int new_index
    cdef bint inapplicable_form
    cdef bytes word_bytes, new_word_bytes
    cdef string word_str, new_word_str
    cdef unordered_map[string, int].iterator it
    cdef pair[unordered_map[string, int].iterator, bint] insert_result
    cdef int from_len
    cdef list matching_rules
    cdef int word_text_len

    # Start with the original word
    original = CandidateWord(
        word=word,
        type=0xffff ^ (WordType.TaTeStem | WordType.DaDeStem | WordType.IrrealisStem),
        reason_chains=[]
    )
    result.append(original)
    # Convert string to C++ string and insert into map
    word_bytes = word.encode('utf-8')
    word_str = word_bytes
    result_index[word_str] = 0

    while i < len(result):
        this_candidate = result[i]

        # Don't deinflect masu-stem results of Ichidan verbs any further
        if (
            this_candidate.type & WordType.IchidanVerb and
            len(this_candidate.reason_chains) == 1 and
            len(this_candidate.reason_chains[0]) == 1 and
            this_candidate.reason_chains[0][0] == Reason.MasuStem
        ):
            i += 1
            continue

        word_text = this_candidate.word
        word_type = this_candidate.type

        # Ichidan verbs stem forwarding
        if word_type & (WordType.MasuStem | WordType.TaTeStem | WordType.IrrealisStem):
            reason = []

            if word_type & WordType.MasuStem and not this_candidate.reason_chains:
                reason.append([Reason.MasuStem])

            inapplicable_form = (
                word_type & WordType.IrrealisStem and
                this_candidate.reason_chains and
                len(this_candidate.reason_chains) > 0 and
                len(this_candidate.reason_chains[0]) > 0 and
                this_candidate.reason_chains[0][0] in [Reason.Passive, Reason.Causative, Reason.CausativePassive]
            )

            if not inapplicable_form:
                new_word = word_text + 'る'
                new_candidate = CandidateWord(
                    word=new_word,
                    type=WordType.IchidanVerb | WordType.KuruVerb,
                    reason_chains=this_candidate.reason_chains + reason
                )
                result.append(new_candidate)
                # Use C++ map find() method for faster lookup
                new_word_bytes = new_word.encode('utf-8')
                new_word_str = new_word_bytes
                it = result_index.find(new_word_str)
                if it == result_index.end():
                    result_index[new_word_str] = len(result) - 1

        # Try to apply deinflection rules
        # Check endings from longest to shortest (max 7 chars in current rules)
        # Optimization: Use hash map lookup (O(1)) instead of linear scan (O(rules))
        word_text_len = len(word_text)
        
        for from_len in range(min(7, word_text_len), 0, -1):
            ending = word_text[-from_len:]
            hiragana_ending = kana_to_hiragana(ending)

            # Look up rules by ending (O(1) instead of O(rules))
            matching_rules = []
            if ending in rules_by_ending:
                matching_rules.extend(rules_by_ending[ending])
            if hiragana_ending != ending and hiragana_ending in rules_by_ending:
                matching_rules.extend(rules_by_ending[hiragana_ending])

            for rule in matching_rules:
                if not (word_type & rule['fromType']):
                    continue

                new_word = word_text[:-len(rule['from'])] + rule['to']
                if not new_word:
                    continue

                # Check for duplicate reasons
                rule_reasons_set = set(rule['reasons'])
                flat_reasons = []
                for chain in this_candidate.reason_chains:
                    for r in chain:
                        flat_reasons.append(r)

                has_duplicate = False
                for r in flat_reasons:
                    if r in rule_reasons_set:
                        has_duplicate = True
                        break

                if has_duplicate:
                    continue

                # Check if we already have this candidate using C++ map
                new_word_bytes = new_word.encode('utf-8')
                new_word_str = new_word_bytes
                it = result_index.find(new_word_str)
                if it != result_index.end():
                    # Found existing candidate
                    existing_index = result_index[new_word_str]
                    existing_candidate = result[existing_index]
                    if existing_candidate.type == rule['toType']:
                        if rule['reasons']:
                            existing_candidate.reason_chains.insert(0, rule['reasons'].copy())
                        continue

                # Create new candidate
                new_index = len(result)
                result_index[new_word_str] = new_index

                reason_chains = []
                for chain in this_candidate.reason_chains:
                    reason_chains.append(chain.copy())

                if rule['reasons']:
                    if reason_chains:
                        first_reason_chain = reason_chains[0]

                        # Combine causative + passive into causative passive
                        if (
                            rule['reasons'] and
                            rule['reasons'][0] == Reason.Causative and
                            first_reason_chain and
                            first_reason_chain[0] == Reason.PotentialOrPassive
                        ):
                            first_reason_chain[0] = Reason.CausativePassive
                        elif (
                            rule['reasons'] and
                            rule['reasons'][0] == Reason.MasuStem and
                            first_reason_chain
                        ):
                            pass
                        else:
                            first_reason_chain[:0] = rule['reasons']
                    else:
                        reason_chains.append(rule['reasons'].copy())

                new_candidate = CandidateWord(
                    word=new_word,
                    type=rule['toType'],
                    reason_chains=reason_chains
                )

                result.append(new_candidate)

        i += 1

    # Filter out intermediate forms
    filtered_result = []
    for r in result:
        if r.type & WordType.All:
            filtered_result.append(r)

    return filtered_result
