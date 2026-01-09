# Changelog

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

