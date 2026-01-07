"""
Core deinflection logic.

This module implements the deinflection algorithm that converts conjugated
Japanese words back to their dictionary forms.
"""

from typing import List, Dict
from ._types import CandidateWord, WordType, Reason
from .deinflect_rules import get_deinflect_rule_groups
from .normalize import kana_to_hiragana


def deinflect(word: str) -> List[CandidateWord]:
    """
    Returns an array of possible de-inflected versions of a word.
    
    This function applies deinflection rules iteratively to generate all
    possible dictionary forms that the input word could be derived from.
    
    Args:
        word: The word to deinflect
        
    Returns:
        List of CandidateWord objects, each representing a possible
        dictionary form with type constraints and reason chains
    """
    result: List[CandidateWord] = []
    result_index: Dict[str, int] = {}
    rule_groups = get_deinflect_rule_groups()
    
    # Start with the original word
    original = CandidateWord(
        word=word,
        # Initially, the type of word is unknown, so we set the type mask to
        # match all rules except stems, that don't make sense on their own.
        type=0xffff ^ (WordType.TaTeStem | WordType.DaDeStem | WordType.IrrealisStem),
        reason_chains=[]
    )
    result.append(original)
    result_index[word] = 0
    
    i = 0
    while i < len(result):
        this_candidate = result[i]
        
        # Don't deinflect masu-stem results of Ichidan verbs any further since
        # they should already be the plain form.
        #
        # Without this we would take something like 食べて, try deinflecting it as
        # a masu stem into 食べてる and then try de-inflecting it as a continuous
        # form. However, we should just stop immediately after de-inflecting to
        # the plain form.
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
        
        # Ichidan verbs have only one stem, which is the plain form minus the
        # final る. Since the stem is shorter than the plain form, to avoid
        # adding multiple entries for all possible stem variations to the rule
        # data array, we forward the stem to the plain form programmatically.
        if word_type & (WordType.MasuStem | WordType.TaTeStem | WordType.IrrealisStem):
            reason = []
            
            # Add the "masu" reason only if the word is solely the masu stem.
            if word_type & WordType.MasuStem and not this_candidate.reason_chains:
                reason.append([Reason.MasuStem])
            
            # Ichidan verbs attach the auxiliary verbs られる and させる instead of
            # れる and せる for the passive and causative forms to their stem. Since
            # られる and させる exist as separate rules that bypass the irrealis stem
            # type, we ignore the the rules with a to-type of IrrealisStem for the
            # passive and causative, i.e. the rules for れる and せる.
            # Similarly, we need to ignore the rule for the causative passive, as
            # the contraction of せられる to される is incorrect for Ichidan verbs.
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
                
                # Continue if the rule introduces a duplicate in the reason chain,
                # as it wouldn't make sense grammatically.
                rule_reasons_set = set(rule['reasons'])
                flat_reasons = [r for chain in this_candidate.reason_chains for r in chain]
                if any(r in rule_reasons_set for r in flat_reasons):
                    continue
                
                # If we already have a candidate for this word with the same
                # 'to' type(s), expand the possible reasons by starting a new
                # reason chain.
                if new_word in result_index:
                    existing_candidate = result[result_index[new_word]]
                    if existing_candidate.type == rule['toType']:
                        if rule['reasons']:
                            # Start a new reason chain
                            existing_candidate.reason_chains.insert(0, rule['reasons'].copy())
                        continue
                
                # Start a new candidate
                # Note: We set the index before appending so the index is correct
                new_index = len(result)
                result_index[new_word] = new_index
                
                # Deep clone reason chains
                reason_chains = [chain.copy() for chain in this_candidate.reason_chains]
                
                # We only need to add something to the reason chain if the rule is
                # not a pure forwarding rule, i.e. the reasons array is not empty.
                if rule['reasons']:
                    # Add our new reason in
                    #
                    # If we already have reason chains, prepend to the first chain
                    if reason_chains:
                        first_reason_chain = reason_chains[0]
                        
                        # Rather having causative + passive, combine the two rules into
                        # "causative passive":
                        if (
                            rule['reasons'] and
                            rule['reasons'][0] == Reason.Causative and
                            first_reason_chain and
                            first_reason_chain[0] == Reason.PotentialOrPassive
                        ):
                            first_reason_chain[0] = Reason.CausativePassive
                        elif (
                            # Add the "masu" reason only if the word is solely the masu stem.
                            rule['reasons'] and
                            rule['reasons'][0] == Reason.MasuStem and
                            first_reason_chain
                        ):
                            # Do nothing
                            pass
                        else:
                            first_reason_chain[:0] = rule['reasons']
                    else:
                        # Add new reason to the start of the chain
                        reason_chains.append(rule['reasons'].copy())
                
                new_candidate = CandidateWord(
                    word=new_word,
                    type=rule['toType'],
                    reason_chains=reason_chains
                )
                
                result.append(new_candidate)
        
        i += 1
    
    # Post-process to filter out any lingering intermediate forms
    result = [r for r in result if r.type & WordType.All]
    
    return result

