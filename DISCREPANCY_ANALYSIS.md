# Discrepancy Analysis: tentoku vs 10ten Reader

## Summary

After thorough comparison with 10ten Reader's TypeScript source code, the following discrepancies were identified and addressed:

## ✅ Fixed Discrepancies

### 1. Missing `matchRange` Tracking
- **Issue**: tentoku didn't track which readings matched the input
- **10ten Reader**: Sets `matchRange` on kanji/kana readings that match
- **Fix**: Added `match_range` and `match` fields to `KanjiReading` and `KanaReading`, and set them in `sqlite_dict.py`

### 2. Priority Calculation Using Wrong Readings
- **Issue**: `get_priority()` was checking all readings, not just matched ones
- **10ten Reader**: Only uses priority from readings with `matchRange`
- **Fix**: Updated `get_priority()` to only check readings with `match_range`

### 3. Priority String Normalization
- **Issue**: JMDict stores priorities as "ichi1", "spec1" but code expected "i1", "s1"
- **10ten Reader**: Uses short codes "i1", "s1", etc.
- **Fix**: Added `normalize_priority()` function to map full names to short codes

### 4. Sorting Using Wrong Matching Text
- **Issue**: `sort_word_results()` used `matching_text` parameter instead of `matchRange`
- **10ten Reader**: Uses `matchRange` to determine which reading matched
- **Fix**: Updated sorting to use `matchRange` from entries

## ⚠️ Potential Discrepancies (Verified as Equivalent)

### 1. `r.app === 0` vs `no_kanji`
- **10ten Reader**: Checks `r.app === 0` for nokanji readings
- **tentoku**: Checks `matching_kana.no_kanji`
- **Status**: Equivalent - both indicate readings with no kanji
- **Note**: `app` in jpdict-idb indicates which kanji the reading applies to. `app === 0` means applies to no kanji, same as `no_kanji === true`

### 2. `mostMatchedEnSensesAreUk` - Sense Match Field
- **10ten Reader**: Filters for `s.match && (s.lang === undefined || s.lang === 'en')`
- **tentoku**: Checks all English senses (no `match` field)
- **Status**: Equivalent for SQLite/flat-file - In 10ten Reader's flat-file.ts, all senses get `match: true`, so filtering by `match` is effectively checking all senses
- **Note**: This might matter for IndexedDB, but tentoku uses SQLite (similar to flat file)

### 3. LongestMatch Calculation
- **10ten Reader**: Uses `inputLengths[input.length]` where `input` is the current input (before variant)
- **tentoku**: Uses `input_lengths[len(current_input)]` where `current_input` is before variant
- **Status**: Equivalent - both use the current input length (before variations), not the variant length

## 🔍 Remaining Considerations

### 1. Sense Match Field
- **Current**: tentoku doesn't track `match` on senses
- **Impact**: Low - only affects `mostMatchedEnSensesAreUk`, which in flat-file mode checks all senses anyway
- **Action**: Monitor if this causes issues, but likely not needed for SQLite

### 2. Reading Restrictions (app field)
- **Current**: tentoku uses `no_kanji` flag
- **Impact**: None - `no_kanji` is equivalent to `app === 0`
- **Action**: None needed

### 3. Input Length Calculation
- **Current**: Uses `input_lengths[len(current_input)]`
- **Impact**: None - equivalent to 10ten Reader's `inputLengths[input.length]`
- **Action**: None needed

## Test Results

All critical tests pass:
- ✅ "に" (priority 50) correctly comes before "にべ" (priority 0) when searching "にベ"
- ✅ Priority calculation works: `ichi1` → 50, `spec1` → 32, `news1` → 40
- ✅ `matchRange` is set correctly on matching readings
- ✅ Sorting matches 10ten Reader's behavior (reasons → type → priority)

## Conclusion

The implementation now matches 10ten Reader's behavior for dictionary lookup. All critical discrepancies have been fixed, and remaining differences are either equivalent implementations or don't affect the SQLite-based workflow.
