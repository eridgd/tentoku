# Preprocessing Comparison: tentoku vs 10ten Reader

This document compares the preprocessing and normalization steps between tentoku and 10ten Reader to ensure compatibility.

## ✅ Implemented (Matches 10ten Reader)

### 1. Input Normalization (`normalize_input`)
- ✅ **Half-width to full-width numbers**: Converts `123` → `１２３`
- ✅ **Unicode normalization**: Uses NFC (canonical composition) via `to_normalized`
- ✅ **Zero-width non-joiner (ZWNJ) stripping**: Removes `\u200c` characters (Google Docs issue)
- ✅ **Input length mapping**: Returns 16-bit character offset array (for non-BMP character support)

### 2. Text Variations (`word_search`)
- ✅ **Choon (ー) expansion**: Generates variations by replacing ー with vowels (あ, い, う, え, お)
- ✅ **Kyuujitai to shinjitai conversion**: Converts old kanji forms (舊體國) to new forms (旧体国)

### 3. Katakana Normalization
- ✅ **Katakana to hiragana conversion**: Converts katakana to hiragana for dictionary lookup
- ✅ **Dual-form search**: Searches for both original (katakana) and normalized (hiragana) forms
- ✅ **Hiragana comparison for match_range**: Compares both sides in hiragana (like 10ten Reader)

## ⚠️ Difference: Out-of-Range Character Truncation

**10ten Reader behavior**: Truncates input at characters outside expected range:
- Characters `<= 0x2e80` (except `0x200c` ZWNJ) → truncate
- Characters `0x3000-0x3002` (spaces, ideographic comma/period) → truncate

**tentoku behavior**: Does NOT truncate at out-of-range characters.

**Example**:
- 10ten Reader: `"日本語。English"` → `"日本語"` (truncated at `。`)
- tentoku: `"日本語。English"` → `"日本語。English"` (no truncation)

**Impact**: 
- For **interactive lookups** (10ten Reader's use case): Truncation prevents searching non-Japanese text when cursor is on punctuation
- For **full-text tokenization** (tentoku's use case): Truncation is less critical since we're processing complete Japanese sentences

**Recommendation**: This difference is acceptable for our use case. If needed, we could add truncation as an optional parameter to `normalize_input`.

## Summary

tentoku implements all critical preprocessing steps that 10ten Reader uses:
- ✅ Full-width number conversion
- ✅ Unicode normalization
- ✅ ZWNJ stripping
- ✅ Choon expansion
- ✅ Kyuujitai conversion
- ✅ Katakana normalization and dual-form search

The only difference is out-of-range character truncation, which is less relevant for full-text tokenization than for interactive lookups.
