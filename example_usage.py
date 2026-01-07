#!/usr/bin/env python3
"""
Example usage of the Japanese tokenizer module.

This demonstrates how to use the tokenizer in your own Python programs.
"""

from tentoku import tokenize

def main():
    # Example sentences to tokenize
    # The dictionary will be automatically created and built if needed
    sentences = [
        "私は学生です",
        "食べています",
        "日本語を勉強しています",
    ]
    
    print("Japanese Tokenizer Example\n" + "="*50)
    
    for sentence in sentences:
        print(f"\nInput: {sentence}")
        print("-" * 50)
        
        tokens = tokenize(sentence)
        
        for i, token in enumerate(tokens, 1):
            print(f"{i}. '{token.text}' ({token.start}-{token.end})")
            
            if token.dictionary_entry:
                entry = token.dictionary_entry
                print(f"   Entry ID: {entry.ent_seq}")
                
                # Show first sense
                if entry.senses:
                    sense = entry.senses[0]
                    if sense.glosses:
                        gloss_texts = [g.text for g in sense.glosses[:3]]  # First 3 glosses
                        print(f"   Meaning: {', '.join(gloss_texts)}")
                
                if token.deinflection_reasons:
                    from tentoku import Reason
                    print("   Deinflected from:")
                    for chain in token.deinflection_reasons:
                        reason_names = [Reason(r).name for r in chain]
                        print(f"     {' → '.join(reason_names)}")
            else:
                print("   (No dictionary match)")
    
    print("\n" + "="*50)

if __name__ == '__main__':
    main()

