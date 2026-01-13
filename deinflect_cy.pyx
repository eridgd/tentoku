# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: initializedcheck=False
"""
Core deinflection logic - Cython optimized version.
"""

from typing import List, Dict
from tentoku._types import CandidateWord, WordType, Reason
from tentoku.deinflect_rules import get_deinflect_rule_groups
from tentoku.normalize_cy import kana_to_hiragana


cpdef list deinflect(str word):
    """
    Returns an array of possible de-inflected versions of a word.

    Args:
        word: The word to deinflect

    Returns:
        List of CandidateWord objects
    """
    cdef list result = []
    cdef dict result_index = {}
    cdef list rule_groups = get_deinflect_rule_groups()
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

    # Start with the original word
    original = CandidateWord(
        word=word,
        type=0xffff ^ (WordType.TaTeStem | WordType.DaDeStem | WordType.IrrealisStem),
        reason_chains=[]
    )
    result.append(original)
    result_index[word] = 0

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
                if new_word not in result_index:
                    result_index[new_word] = len(result) - 1

        # Try to apply deinflection rules
        for rule_group in rule_groups:
            if rule_group['fromLen'] > len(word_text):
                continue

            ending = word_text[-rule_group['fromLen']:]
            hiragana_ending = kana_to_hiragana(ending)

            for rule in rule_group['rules']:
                if not (word_type & rule['fromType']):
                    continue

                if ending != rule['from'] and hiragana_ending != rule['from']:
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

                # Check if we already have this candidate
                if new_word in result_index:
                    existing_candidate = result[result_index[new_word]]
                    if existing_candidate.type == rule['toType']:
                        if rule['reasons']:
                            existing_candidate.reason_chains.insert(0, rule['reasons'].copy())
                        continue

                # Create new candidate
                new_index = len(result)
                result_index[new_word] = new_index

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
