# SQLite Dictionary Optimization

## Summary

Implemented aggressive SQLite dictionary optimizations that reduce database lookups by **96.6%** and improve performance by **2.2x** on long sentences.

## The Problem

Profiling revealed that for a 218-character sentence:
- **169,898 total dictionary lookups** were made
- **142,368 unique words** were looked up
- Most lookups were for impossibly long strings (100-200+ characters)
- These long strings came from `expand_choon()` creating variations of the full remaining text
- No dictionary entry is longer than ~15 characters, so these lookups always fail

## The Solution

Created `OptimizedSQLiteDictionary` with three key optimizations:

### 1. Length-Based Lookup Skipping
```python
if len(input_text) > self.max_lookup_length:  # default: 15 chars
    return []
```
- Skips database lookups for strings longer than 15 characters
- Eliminates 95.6% of wasteful lookups
- No dictionary word is that long anyway

### 2. Negative Lookup Caching
```python
self._negative_cache = set()  # Cache words not found
```
- Remembers words that weren't found in the dictionary
- Avoids repeated failed lookups
- Bounded to 100,000 entries with LRU-like eviction

### 3. Positive Lookup Caching
```python
self._positive_cache = {}  # Cache words found
```
- Caches successful dictionary lookups
- Instant retrieval for repeated words
- Bounded to 10,000 entries with LRU-like eviction

## Results

### Performance on 218-char Sentence

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Database lookups | 169,898 | 5,834 | **96.6% reduction** |
| Lookups skipped by length | 0 | 156,930 (95.6%) | N/A |
| Time (cold start) | 14.0s | 6.3s | **2.2x faster** |
| Time (warm cache) | 14.0s | 5.8s | **2.4x faster** |

### Lookup Distribution

After optimization, for 164,071 total `get_words()` calls:
- **95.6%** skipped by length check (>15 chars)
- **0.7%** served from negative cache
- **0.0%** served from positive cache
- **3.6%** actual database lookups (5,834)

### Length Distribution of Attempted Lookups

| Length Range | Lookups | Percentage |
|--------------|---------|------------|
| 1-5 chars | 1,437 | 0.9% |
| 6-10 chars | 2,323 | 1.4% |
| 11-15 chars | 3,381 | 2.1% |
| 16-20 chars | 3,982 | 2.4% |
| 21-50 chars | 31,667 | 19.3% |
| 51-100 chars | 53,571 | 32.7% |
| 100-200 chars | 66,096 | 40.3% |
| 200+ chars | 1,614 | 1.0% |

**Key insight**: 92.3% of lookups are for strings >15 chars, which are now skipped instantly.

## Implementation

The optimization is enabled by default:

```python
# In __init__.py
from .sqlite_dict_optimized import OptimizedSQLiteDictionary as SQLiteDictionary

# In tokenizer.py
from .sqlite_dict_optimized import OptimizedSQLiteDictionary
_default_dictionary = OptimizedSQLiteDictionary()
```

Users automatically get the optimization when they:
```python
import tentoku
tokens = tentoku.tokenize(text)  # Uses OptimizedSQLiteDictionary
```

## Benchmarks

Run the benchmarks yourself:
```bash
python profile_optimized.py      # Detailed optimization statistics
python benchmark_optimization.py # Performance across different text lengths
```

## Why This Works

The core issue was that `expand_choon()` in `word_search.py` creates variations of the current search substring, including very long ones:

```python
current_input = "にこやかにうなずいている東京、秋葉原駅前にある..." (200+ chars)
variations = [current_input]
variations.extend(expand_choon(current_input))  # Creates 5+ variations
```

Each variation gets deinflected, which can produce 20+ candidates, each of which gets looked up in the database. For a 200-char string, this is completely wasteful since no dictionary entry is that long.

The length check eliminates these lookups at the source, before hitting SQLite.

## Trade-offs

- **Max lookup length**: Set to 15 chars by default. Can be adjusted if needed:
  ```python
  dict = OptimizedSQLiteDictionary(max_lookup_length=20)
  ```

- **Cache memory**: Negative cache bounded to 100k entries, positive cache to 10k entries. This is ~1-2 MB of memory, negligible compared to the 45 MB database.

- **Cache eviction**: Simple truncation (remove oldest 20%) when bounds exceeded. Could use LRU but overhead not worth it for this use case.

## Comparison to Previous Attempts

### FastSQLiteDictionary (Removed)
- Tried to optimize with LEFT JOIN queries and eager loading
- Actually 166x SLOWER than standard version (0.17s vs 0.000s per lookup)
- Complex queries don't help when you're making 170k of them

### This Optimization (Kept)
- Simple length check eliminates 95%+ of lookups before they happen
- Standard queries remain fast (0.000s)
- Total time reduced by 2.2x

**Lesson**: Sometimes the best optimization is to not do the work at all.
