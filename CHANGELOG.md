# Changelog

## [0.1.5] - 2026-01-08

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

