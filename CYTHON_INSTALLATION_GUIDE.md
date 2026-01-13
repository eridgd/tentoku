# Cython Installation and Verification Guide

This guide explains how to install and verify that the Cython-optimized version of Tentoku is properly configured.

## Quick Start

### Option 1: Install from Source with Cython

```bash
# Clone the repository
git clone https://github.com/eridgd/tentoku.git
cd tentoku

# Switch to cython-version branch
git checkout cython-version

# Install with Cython (recommended)
pip install .
```

This will automatically build the Cython extensions during installation.

### Option 2: Development Installation

```bash
# Install in editable mode with build
pip install -e .

# OR manually build Cython extensions
python setup.py build_ext --inplace
```

## Verification

### Quick Check

```python
import tentoku

# Check if Cython is being used
if tentoku.is_using_cython():
    print("✓ Cython optimization active!")
else:
    print("✗ Using Python fallback")
```

### Detailed Verification

```python
import tentoku

# Print detailed report
tentoku.verify_cython_status()
```

This will output:
```
======================================================================
CYTHON VERIFICATION REPORT
======================================================================

normalize:
  normalize_input                ✓ Cython
  kana_to_hiragana               ✓ Cython

deinflect:
  deinflect                      ✓ Cython

yoon:
  ends_in_yoon                   ✓ Cython

variations:
  expand_choon                   ✓ Cython
  kyuujitai_to_shinjitai         ✓ Cython

type_matching:
  entry_matches_type             ✓ Cython

sorting:
  sort_word_results              ✓ Cython

word_search:
  word_search                    ✓ Cython
  lookup_candidates              ✓ Cython
  is_only_digits                 ✓ Cython

======================================================================
✓ ALL MODULES USING CYTHON
======================================================================
```

### Command-Line Verification

```bash
# Run verification script directly
python -m tentoku.verify_cython

# Or using the standalone script
cd tentoku
python verify_cython.py
```

## How It Works

### Dynamic Fallback Loading

All performance-critical modules use a dynamic import pattern:

```python
# Try to import Cython version
try:
    from .module_cy import function as _function_cy
    _CYTHON_AVAILABLE = True
except ImportError:
    _CYTHON_AVAILABLE = False

def _function_py(...):
    # Python implementation
    ...

# Assign the appropriate version
if _CYTHON_AVAILABLE:
    function = _function_cy
else:
    function = _function_py
```

This means:
- ✓ **With Cython**: Uses compiled `.so` files for maximum performance
- ✓ **Without Cython**: Automatically falls back to pure Python (slower but functional)
- ✓ **No runtime errors**: Package works either way

### Modules with Cython Optimization

All of these modules have Cython versions:

| Module | Functions | Speedup |
|--------|-----------|---------|
| `normalize` | `normalize_input`, `kana_to_hiragana` | 4-8x |
| `deinflect` | `deinflect` | 1.2-1.4x |
| `yoon` | `ends_in_yoon` | 6-8x |
| `variations` | `expand_choon`, `kyuujitai_to_shinjitai` | 2-6x |
| `type_matching` | `entry_matches_type` | Varies |
| `sorting` | `sort_word_results` | Varies |
| `word_search` | `word_search`, `lookup_candidates`, `is_only_digits` | Varies |

## Troubleshooting

### Cython Not Being Used

If `is_using_cython()` returns `False`:

**1. Check if Cython is installed:**
```bash
python -c "import Cython; print(Cython.__version__)"
```

**2. Rebuild extensions:**
```bash
python setup.py build_ext --inplace
```

**3. Check for `.so` files:**
```bash
ls -la *.so
```

You should see files like:
- `deinflect_cy.cpython-312-x86_64-linux-gnu.so`
- `normalize_cy.cpython-312-x86_64-linux-gnu.so`
- etc.

**4. Verify import:**
```python
# This should work if Cython is available
from tentoku.normalize_cy import normalize_input
print("Cython import successful!")
```

### Installation Issues

**Problem: "Cython not found"**

Solution:
```bash
pip install Cython>=0.29.0
pip install .
```

**Problem: "error: command 'gcc' failed"**

Solution: Install build tools
```bash
# Ubuntu/Debian
sudo apt-get install build-essential python3-dev

# macOS
xcode-select --install

# Windows
# Install Visual Studio Build Tools
```

**Problem: "No module named 'tentoku.normalize_cy'"**

This is normal if Cython wasn't installed during build. The package will automatically fall back to Python versions.

## Performance Comparison

### With Cython (Recommended)

```python
import tentoku
import time

text = "私は毎日日本語を勉強しています。" * 50  # Long text
start = time.perf_counter()
tokens = tentoku.tokenize(text)
end = time.perf_counter()

print(f"Tokenized {len(tokens)} tokens in {(end-start)*1000:.2f}ms")
# Expected: ~10-20ms for 50x repetitions
```

### Without Cython (Python Fallback)

Same code will run 4-8x slower for normalization operations.

## Development Workflow

### For Contributors

```bash
# 1. Clone and checkout cython-version branch
git checkout cython-version

# 2. Install in development mode
pip install -e .

# 3. Make changes to .pyx files

# 4. Rebuild Cython extensions
python setup.py build_ext --inplace

# 5. Verify changes
python verify_cython.py

# 6. Run tests
python test_cython_correctness.py
python benchmark_cython.py
```

### Testing Both Versions

To test the Python fallback (without Cython):

```bash
# Temporarily rename .so files
mv *.so /tmp/

# Now imports will use Python versions
python -c "import tentoku; print('Using Cython:', tentoku.is_using_cython())"
# Output: Using Cython: False

# Restore .so files
mv /tmp/*.so .
```

## Integration with Your Project

### Basic Usage

```python
from tentoku import tokenize

# Works with or without Cython
tokens = tokenize("食べました")

for token in tokens:
    print(f"{token.text}: {token.dictionary_entry.ent_seq if token.dictionary_entry else 'N/A'}")
```

### Performance-Critical Applications

```python
import tentoku

# Check if Cython is available
if not tentoku.is_using_cython():
    print("WARNING: Cython not available, performance will be reduced")
    print("Install with: pip install Cython && pip install --force-reinstall .")

# Your code here
...
```

### Benchmarking Your Use Case

```python
import tentoku
import time

# Your test data
texts = [...]  # Your actual manga/subtitle texts

# Benchmark
start = time.perf_counter()
for text in texts:
    tokens = tentoku.tokenize(text)
end = time.perf_counter()

avg_time = (end - start) / len(texts) * 1000
print(f"Average: {avg_time:.2f}ms per text")
print(f"Throughput: {len(texts)/(end-start):.1f} texts/sec")
```

## FAQ

**Q: Do I need Cython installed to use the package?**

A: No. If Cython extensions are pre-built and included in the distribution, they'll work without Cython installed. However, to build from source, you need Cython.

**Q: What's the performance difference?**

A: 4-8x faster for normalization on long texts. See `CYTHON_OPTIMIZATION_SUMMARY.md` for detailed benchmarks.

**Q: Can I use this in production?**

A: Yes! The Cython extensions are thoroughly tested for correctness (100% match with Python versions) and are production-ready.

**Q: What if installation fails?**

A: The package will still work using pure Python fallback. Performance will be reduced but functionality is identical.

**Q: How do I force a rebuild?**

A:
```bash
# Clean previous build
python setup.py clean --all

# Force rebuild
pip install --force-reinstall --no-binary :all: .
```

## Support

For issues related to Cython optimization:
1. Check this guide
2. Run `tentoku.verify_cython_status()` for diagnostics
3. Report issues with the output of the verification report

## See Also

- `CYTHON_OPTIMIZATION_SUMMARY.md` - Detailed performance analysis
- `benchmark_cython.py` - Performance benchmarking suite
- `test_cython_correctness.py` - Correctness validation
- `verify_cython.py` - Verification utility
