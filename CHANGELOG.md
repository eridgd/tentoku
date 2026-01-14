# Changelog

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

