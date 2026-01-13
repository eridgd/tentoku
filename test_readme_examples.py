#!/usr/bin/env python3
"""
Test script to run README examples and compare outputs with expected results.
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import tentoku as a package
# This script should be run from the tentoku directory
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import from tentoku module
from tentoku import tokenize
from tentoku.sqlite_dict import SQLiteDictionary
from tentoku.word_search import word_search
from tentoku.normalize import normalize_input
from tentoku.deinflect import deinflect

def test_basic_usage():
    """Test Basic Usage example from README."""
    print("=" * 80)
    print("TEST 1: Basic Usage - tokenize('私は学生です')")
    print("=" * 80)
    
    tokens = tokenize("私は学生です")
    
    actual_output = []
    for token in tokens:
        line = f"{token.text} ({token.start}-{token.end})"
        actual_output.append(line)
        
        if token.dictionary_entry:
            entry = token.dictionary_entry
            sense = entry.senses[0]
            meaning = sense.glosses[0].text
            
            actual_output.append(f"  Entry: {entry.ent_seq}")
            actual_output.append(f"  Meaning: {meaning}")
            
            if sense.pos_tags:
                actual_output.append(f"  POS: {', '.join(sense.pos_tags)}")
            
            if sense.misc:
                actual_output.append(f"  Usage: {', '.join(sense.misc)}")
            
            if sense.field:
                actual_output.append(f"  Field: {', '.join(sense.field)}")
            
            if sense.dial:
                actual_output.append(f"  Dialect: {', '.join(sense.dial)}")
            
            actual_output.append("")
    
    print("\nACTUAL OUTPUT:")
    print("\n".join(actual_output))
    
    expected_lines = [
        "私 (0-1)",
        "  Entry: 1311110",
        "  Meaning: I",
        "  POS: pronoun",
        "",
        "は (1-2)",
        "  Entry: 2028920",
        "  Meaning: indicates sentence topic",
        "  POS: particle",
        "",
        "学生 (2-4)",
        "  Entry: 1206900",
        "  Meaning: student (esp. a university student)",
        "  POS: noun (common) (futsuumeishi)",
        "",
        "です (4-6)",
        "  Entry: 1628500",
        "  Meaning: be",
        "  POS: copula, auxiliary verb",
        "  Usage: polite (teineigo) language",
    ]
    
    print("\nEXPECTED OUTPUT:")
    print("\n".join(expected_lines))
    
    # Compare key elements
    issues = []
    if len(tokens) != 4:
        issues.append(f"Expected 4 tokens, got {len(tokens)}")
    
    # Check first token
    if tokens[0].text != "私":
        issues.append(f"First token should be '私', got '{tokens[0].text}'")
    if tokens[0].dictionary_entry and tokens[0].dictionary_entry.ent_seq != "1311110":
        issues.append(f"First entry should be 1311110, got {tokens[0].dictionary_entry.ent_seq if tokens[0].dictionary_entry else 'None'}")
    
    # Check last token
    if tokens[-1].text != "です":
        issues.append(f"Last token should be 'です', got '{tokens[-1].text}'")
    
    if issues:
        print("\n⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ Output matches expected format")
    
    return issues


def test_verb_forms():
    """Test Verb Forms and Deinflection example from README."""
    print("\n" + "=" * 80)
    print("TEST 2: Verb Forms - tokenize('食べました')")
    print("=" * 80)
    
    tokens = tokenize("食べました")
    
    actual_output = []
    for token in tokens:
        if token.deinflection_reasons:
            for chain in token.deinflection_reasons:
                reasons = [r.name for r in chain]
                actual_output.append(f"{token.text} -> {', '.join(reasons)}")
    
    print("\nACTUAL OUTPUT:")
    print("\n".join(actual_output) if actual_output else "(no output)")
    
    expected = "食べました -> PolitePast"
    print(f"\nEXPECTED OUTPUT:")
    print(expected)
    
    issues = []
    if not actual_output:
        issues.append("No deinflection reasons found")
    elif actual_output[0] != expected:
        issues.append(f"Expected '{expected}', got '{actual_output[0]}'")
    
    if issues:
        print("\n⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ Output matches expected")
    
    return issues


def test_word_search():
    """Test Word Search example from README."""
    print("\n" + "=" * 80)
    print("TEST 3: Word Search - word_search('食べています')")
    print("=" * 80)
    
    dictionary = SQLiteDictionary()
    
    try:
        text = "食べています"
        normalized, input_lengths = normalize_input(text)
        
        result = word_search(normalized, dictionary, max_results=7, input_lengths=input_lengths)
        
        actual_output = []
        if result:
            for word_result in result.data:
                matched_text = text[:word_result.match_len]
                entry_word = word_result.entry.kana_readings[0].text if word_result.entry.kana_readings else "N/A"
                actual_output.append(f"'{matched_text}' -> {entry_word} (entry: {word_result.entry.ent_seq})")
                
                if word_result.reason_chains:
                    for chain in word_result.reason_chains:
                        reason_names = [r.name for r in chain]
                        actual_output.append(f"  Deinflected from: {' -> '.join(reason_names)}")
        
        print("\nACTUAL OUTPUT:")
        print("\n".join(actual_output) if actual_output else "(no results)")
        
        expected_lines = [
            "'食べています' -> たべる (entry: 1358280)",
            "  Deinflected from: Continuous -> Polite",
        ]
        
        print(f"\nEXPECTED OUTPUT:")
        print("\n".join(expected_lines))
        
        issues = []
        if not actual_output:
            issues.append("No results found")
        else:
            # Check that the expected result exists in the output
            # (word_search may return multiple results, including shorter matches)
            found_expected = False
            found_deinflection = False
            
            for line in actual_output:
                if "'食べています' ->" in line and "1358280" in line:
                    found_expected = True
                if "Continuous -> Polite" in line:
                    found_deinflection = True
            
            if not found_expected:
                issues.append("Expected result '食べています' -> たべる (entry: 1358280) not found in output")
            if not found_deinflection:
                issues.append("Expected deinflection chain 'Continuous -> Polite' not found in output")
        
        if issues:
            print("\n⚠️  ISSUES FOUND:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\n✅ Output matches expected format")
        
        return issues
    
    finally:
        dictionary.close()


def test_deinflect():
    """Test Deinflection example from README."""
    print("\n" + "=" * 80)
    print("TEST 4: Deinflection - deinflect('食べました')")
    print("=" * 80)
    
    candidates = deinflect("食べました")
    
    actual_output = []
    for candidate in candidates:
        if candidate.reason_chains and candidate.word == "食べる":
            for chain in candidate.reason_chains:
                reason_names = [r.name for r in chain]
                actual_output.append(f"{candidate.word} <- {' -> '.join(reason_names)}")
                break
    
    print("\nACTUAL OUTPUT:")
    print("\n".join(actual_output) if actual_output else "(no matching candidate found)")
    
    expected = "食べる <- PolitePast"
    print(f"\nEXPECTED OUTPUT:")
    print(expected)
    
    issues = []
    if not actual_output:
        issues.append("No matching candidate found for '食べる'")
    elif actual_output[0] != expected:
        issues.append(f"Expected '{expected}', got '{actual_output[0]}'")
    
    if issues:
        print("\n⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ Output matches expected")
    
    return issues


def main():
    """Run all README example tests."""
    print("\n" + "=" * 80)
    print("README EXAMPLES TEST SUITE")
    print("=" * 80)
    
    all_issues = []
    
    all_issues.extend(test_basic_usage())
    all_issues.extend(test_verb_forms())
    all_issues.extend(test_word_search())
    all_issues.extend(test_deinflect())
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if all_issues:
        print(f"\n⚠️  Found {len(all_issues)} issue(s):")
        for issue in all_issues:
            print(f"  - {issue}")
        return 1
    else:
        print("\n✅ All examples produce expected outputs!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
