# Changelog

## [0.2.1] - 2026-01-15

### Added
- **Trie-accelerated dictionary** for faster tokenization:
  - `TrieAcceleratedDictionary` using marisa-trie for O(key_length) existence checks
  - `build_trie.py` to create trie indexes from SQLite dictionaries
  - Trie dictionary automatically used as default when marisa-trie is available
  - `is_using_trie()` function to check if trie acceleration is active
  - Comprehensive tests and benchmark script (`benchmark_trie.py`) for trie performance
- **Deinflection optimization benchmark** (`benchmark_deinflect_optimization.py`) for performance testing

### Changed
- **Deinflection performance optimization**:
  - Replaced O(rules) linear scan with O(1) hash map lookup using `get_rules_by_ending()`
  - Applied to both Python (`deinflect.py`) and Cython (`deinflect_cy.pyx`) versions
  - **2.89x faster deinflection** (0.1538ms → 0.0532ms per deinflection)
  - **1.49x faster tokenization** average across text lengths
- **SQLite dictionary optimization**:
  - Replaced per-entry queries with batched IN clause queries
  - Reduced from hundreds/thousands of queries to 8-10 per lookup
  - Applied to both Python (`sqlite_dict_optimized.py`) and Cython (`sqlite_dict_cy.pyx`) versions
  - Increased SQLite cache size to 128MB
  - Added query planner optimization pragmas
  - **1.4-2.7x faster** (8-16s → 5.8s for 134 tokens)
- **Tokenization improvements**:
  - Fixed tokenization of grammatical patterns like `ようにする`
  - Added `match_len` as first sorting criterion to prioritize longer matches
  - Increased `max_results` from 5 to 12 to prevent short high-priority words from crowding out longer matches
  - Updated Cython sorting (`sorting_cy.pyx`) to match Python version with `match_len` prioritization
  - Allow expressions to match verb types in `type_matching.py` for better deinflection support

### Fixed
- Fixed issue where `ようにした` was incorrectly split into `よ` + `うに` + `した` instead of being tokenized as one token with dict_form `ようにする`
- Fixed Cython sorting to match Python version's `match_len` prioritization

## [0.2.0] - 2026-01-14

### Added
- **Cython optimizations** for performance-critical modules, providing significant speedups:
  - `deinflect_cy.pyx`: Cython-optimized deinflection with C++ `std::unordered_map` for faster lookups (1.2-1.4x speedup)
  - `normalize_cy.pyx`: Optimized text normalization (4-7x speedup for long texts)
  - `word_search_cy.pyx`: Fast word search and candidate lookup
  - `sorting_cy.pyx`: Optimized result sorting
  - `type_matching_cy.pyx`: Fast type matching for dictionary entries
  - `variations_cy.pyx`: Optimized text variation handling (1.6-1.9x speedup)
  - `yoon_cy.pyx`: Fast yoon character detection
  - `sqlite_dict_cy.pyx`: Fast SQLite dictionary with caching optimizations
  - `parallel_tokenize.pyx`: Parallel tokenization support for batch processing
- **Parallel processing** support via `parallel_tokenize` module:
  - `parallel_tokenize_batch()`: Tokenize multiple texts in parallel using multiprocessing
  - `parallel_normalize_batch()`: Normalize multiple texts in parallel
  - `parallel_deinflect_batch()`: Deinflect multiple words in parallel
- **Cython verification utilities**:
  - `verify_cython.py`: Module to verify Cython optimizations are active
  - `is_using_cython()`: Check if Cython optimizations are enabled
  - `verify_cython_status()`: Detailed verification report
- **Comprehensive benchmark suite** for Cython performance:
  - `benchmark_cython.py`: Compare Python vs Cython implementations
  - `benchmark_cpp_map.py`: Benchmark C++ unordered_map optimization
  - `benchmark_sqlite.py`: SQLite dictionary performance tests
  - `benchmark_optimization.py`: Overall optimization benchmarks
- **Build system** updated for Cython compilation:
  - Updated `setup.py` with Cython build configuration
  - Compiler directives for maximum performance (bounds checking disabled, type inference enabled)
  - C++ compilation support for `deinflect_cy` module
  - HTML annotation file generation for performance analysis

### Changed
- **Performance improvements**:
  - Normalization: 4-7x faster for long texts (up to 7.58x speedup observed)
  - Deinflection: 1.2-1.4x faster with C++ unordered_map optimization
  - Text variations: 1.6-1.9x faster
  - Overall tokenization significantly faster, especially for long texts
- **Dictionary optimizations**:
  - `SQLiteDictionary` now defaults to `OptimizedSQLiteDictionary` with caching
  - Fast SQLite dictionary with negative and positive lookup caching
  - Length-based lookup skipping for words >15 characters
- **Build artifacts**:
  - Updated `.gitignore` to exclude Cython-generated files (`.c`, `.cpp`, `.html`, `.pyd`)
  - Removed generated Cython files from version control

### Technical Details
- All Cython modules compiled with `-O3` optimization
- C++11 support for `deinflect_cy` module using `std::unordered_map`
- Type inference and automatic optimization enabled via Cython compiler directives
- Backward compatible: Python fallback versions remain available if Cython extensions aren't built

## [0.1.8] - 2026-01-09

### Fixed
- Fixed matchRange tracking to correctly identify which kanji/kana readings matched the input text
- Fixed priority calculation to only use priorities from readings that actually matched (matching 10ten Reader behavior)
- Fixed katakana normalization to properly handle katakana loanwords (e.g., 'ベッド')
- Fixed tokenization to continue trying shorter matches even after finding longer matches, ensuring best match selection
- Fixed sorting to use matchRange instead of matching_text parameter

### Changed
- Improved tokenization match selection: now considers multiple candidates and prefers longest matches while maintaining priority
- Updated sorting algorithm to match 10ten Reader's behavior more closely

### Added
- Comprehensive test coverage for match_range tracking (`tests/test_match_range.py`)
- Test suite for katakana normalization (`tests/test_katakana_normalization.py`)
- Additional tests for sorting and priority calculation

## [0.1.7] - 2026-01-07

### Added
- Japanese README (`README.ja.md`) for Japanese-speaking users

## [0.1.6] - 2026-01-07

### Fixed
- Fixed broken logo image on PyPI by using absolute GitHub URL

## [0.1.5] - 2026-01-07

### Added
- Comprehensive benchmark suite (`benchmark.py`) for performance testing
  - Tokenization speed metrics (tokens/sec, chars/sec)
  - Deinflection and dictionary lookup performance benchmarks
  - Percentile reporting (p90, p95) for performance analysis
  - Windowed throughput tests for hover-like scenarios
- Stress and performance tests in test suite
  - Performance benchmarks for simple, complex, and long text tokenization
  - Throughput tests for multiple texts
  - Stress tests for many operations and windowed scenarios

### Changed
- Improved README with badges and logo

## [0.1.4] - 2026-01-07

### Added
- Python 3.12, 3.13, and 3.14 support
- Enhanced README example showcasing dictionary metadata fields (POS tags, usage, field, dialect)

## [0.1.3] - 2026-01-07

### Added
- Japanese text tokenization with deinflection support
- Reimplementation of 10ten Reader tokenization algorithm
- JMDict SQLite dictionary integration with auto-download
- Comprehensive test suite (141 tests, 98% coverage of original)
- Support for ~400 deinflection rules
- Greedy longest-match tokenization
- Text variations (choon expansion, kyuujitai conversion)

### Acknowledgments
- Algorithm based on [10ten Reader](https://github.com/birchill/10ten-ja-reader)
- Dictionary data from [JMDict](https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project)

