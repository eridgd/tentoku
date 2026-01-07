# Tentoku (天読) - Japanese Tokenizer

A Python module for Japanese word tokenization with deinflection support.

This module reimplements the tokenization algorithm used in [10ten Japanese Reader](https://github.com/birchill/10ten-ja-reader), a browser extension for interactive Japanese reading and instant dictionary lookup. It provides the same greedy longest-match tokenization and deinflection capabilities as a Python package.

**What to expect**: This is a dictionary-based tokenizer, not a statistical segmenter. It prioritizes lookup accuracy over speed, making it ideal for reading aids, lookup tools, and annotation tasks. It is not designed for corpus-scale segmentation where speed is the primary concern.

## Features

- **Greedy longest-match tokenization**: Finds the longest possible words in text
- **Deinflection support**: Handles ~400 conjugation rules to resolve verbs and adjectives back to dictionary forms
- **Tense and form detection**: Identifies verb forms like "polite past", "continuous", "negative", etc.
- **Automatic database setup**: Downloads and builds the JMDict database automatically on first use
- **Dictionary lookup**: Uses JMDict SQLite database for word lookups
- **Text variations**: Handles choon (ー) expansion and kyuujitai (旧字体) to shinjitai (新字体) conversion
- **Type validation**: Validates deinflected forms against part-of-speech tags

## Installation

The tokenizer requires Python 3.8+ and uses only standard library modules (sqlite3, unicodedata, dataclasses, typing).

### From PyPI

```bash
pip install tentoku
```

### From source

```bash
git clone https://github.com/eridgd/tentoku.git
cd tentoku
pip install -e .
```

### Optional Dependencies

For better performance and progress bars:
- `lxml` - Faster XML parsing (recommended)
- `tqdm` - Progress bars during database building

Install with:
```bash
pip install tentoku[full]  # From PyPI
# or
pip install -e ".[full]"   # From source
```

Or individually:
```bash
pip install lxml tqdm
```

## Usage

### Basic Usage

The dictionary will automatically download and build the JMDict database on first use:

```python
from tentoku import tokenize

tokens = tokenize("私は学生です")

for token in tokens:
    print(f"{token.text} ({token.start}-{token.end})")
    if token.dictionary_entry:
        entry = token.dictionary_entry.ent_seq
        meaning = token.dictionary_entry.senses[0].glosses[0].text
        print(f"  Entry: {entry}")
        print(f"  Meaning: ({meaning})\n", end="")
        
# Output:
# 私 (0-1)
#   Entry: 1311110
#   Meaning: (I)
# は (1-2)
#   Entry: 2028920
#   Meaning: (indicates sentence topic)
# 学生 (2-4)
#   Entry: 1206900
#   Meaning: (student (esp. a university student))
# です (4-6)
#   Entry: 1628500
#   Meaning: (be)
```

### Verb Forms and Deinflection

The tokenizer automatically handles verb conjugation and provides deinflection information:

```python
from tentoku import tokenize

tokens = tokenize("食べました")

for token in tokens:
    if token.deinflection_reasons:
        for chain in token.deinflection_reasons:
            reasons = [r.name for r in chain]
            print(f"{token.text} -> {', '.join(reasons)}")

# Output: 食べました -> PolitePast
```

Available `Reason` values include:
- `PolitePast` - Polite past (ました)
- `Polite` - Polite form (ます)
- `Past` - Past tense (た)
- `Negative` - Negative (ない)
- `Continuous` - Continuous (ている)
- `Potential` - Potential form
- `Causative` - Causative form
- `Passive` - Passive form
- `Tai` - Want to (たい)
- `Volitional` - Volitional (う/よう)
- And many more (see `Reason` enum in `_types.py`)

### Using a Custom Dictionary

If you need to use a custom database path or want to manage the dictionary instance yourself:

```python
from tentoku import SQLiteDictionary, tokenize

# Create dictionary with custom path
dictionary = SQLiteDictionary(db_path="/path/to/custom/jmdict.db")

# Pass it explicitly to tokenize
tokens = tokenize("私は学生です", dictionary)

# Don't forget to close when done
dictionary.close()
```

### Manual Database Building

You can also build the database manually:

```python
from tentoku import build_database

# Build database at specified location
build_database("/path/to/custom/jmdict.db")
```

Or from the command line:

```bash
python -m tentoku.build_database --db-path /path/to/custom/jmdict.db
```

### Word Search (Advanced)

For advanced usage, you can use the word search function directly:

```python
from tentoku import SQLiteDictionary
from tentoku.word_search import word_search
from tentoku.normalize import normalize_input

dictionary = SQLiteDictionary()

# Normalize input
text = "食べています"
normalized, input_lengths = normalize_input(text)

# Search for words
result = word_search(normalized, dictionary, max_results=7, input_lengths=input_lengths)

if result:
    for word_result in result.data:
        # Show matched text and entry
        matched_text = text[:word_result.match_len]
        entry_word = word_result.entry.kana_readings[0].text if word_result.entry.kana_readings else "N/A"
        print(f"'{matched_text}' -> {entry_word} (entry: {word_result.entry.ent_seq})")
        
        if word_result.reason_chains:
            from tentoku import Reason
            for chain in word_result.reason_chains:
                reason_names = [r.name for r in chain]
                print(f"  Deinflected from: {' -> '.join(reason_names)}")

# Output:
# '食べています' -> たべる (entry: 1358280)
#   Deinflected from: Continuous -> Polite
```

### Deinflection (Advanced)

For advanced usage, you can use the deinflection function directly:

```python
from tentoku.deinflect import deinflect

# Deinflect a conjugated verb
candidates = deinflect("食べました")

# Show the most relevant deinflected form
for candidate in candidates:
    if candidate.reason_chains and candidate.word == "食べる":
        for chain in candidate.reason_chains:
            reason_names = [r.name for r in chain]
            print(f"{candidate.word} <- {' -> '.join(reason_names)}")
            break

# Output: 食べる <- PolitePast
```

## Architecture

The tokenizer consists of several modules:

- **`_types.py`**: Core type definitions (Token, WordEntry, WordResult, WordType, Reason)
- **`normalize.py`**: Text normalization (Unicode, full-width numbers, ZWNJ stripping)
- **`variations.py`**: Text variations (choon expansion, kyuujitai conversion)
- **`yoon.py`**: Yoon (拗音) detection
- **`deinflect.py`**: Core deinflection algorithm
- **`deinflect_rules.py`**: ~400 deinflection rules
- **`dictionary.py`**: Dictionary interface abstraction
- **`sqlite_dict.py`**: SQLite dictionary implementation
- **`word_search.py`**: Backtracking word search algorithm
- **`type_matching.py`**: Word type validation
- **`sorting.py`**: Result sorting by priority
- **`tokenizer.py`**: Main tokenization function
- **`database_path.py`**: Database path utilities
- **`build_database.py`**: Database building and downloading

## Algorithm

The tokenization algorithm works as follows:

1. **Normalize input**: Convert to full-width numbers, normalize Unicode, strip ZWNJ
2. **Greedy longest-match**: Start at position 0, find longest matching word
3. **Word search**: For each substring:
   - Generate variations (choon expansion, kyuujitai conversion)
   - Deinflect to get candidate dictionary forms
   - Look up candidates in dictionary and validate against word types
   - Track longest successful match
   - If no match, shorten input and repeat (by 2 characters if ending in yoon like きゃ, else 1)
4. **Advance**: Move forward by match length, or 1 character if no match

## Database

The tokenizer uses a JMDict SQLite database. On first use, it will:

1. Check for an existing database in the appropriate location:
   - **When installed from PyPI**: User data directory
     - Linux: `~/.local/share/tentoku/jmdict.db`
     - macOS: `~/Library/Application\ Support/tentoku/jmdict.db`
     - Windows: `%APPDATA%/tentoku/jmdict.db`
   - **When running from source**: Module's data directory
     - `data/jmdict.db` (relative to where the module files are located)
2. If not found, download `JMdict_e.xml.gz` from the official EDRDG source (`https://www.edrdg.org/pub/Nihongo/JMdict_e.gz`)
3. Extract and parse the XML file (~10MB compressed, ~113MB uncompressed)
4. Build the SQLite database with all necessary indexes (~105MB)
5. Save the database for future use
6. Clean up temporary XML files

This is a one-time operation that takes several minutes. Subsequent uses are instant.

The database includes:
- `entries`: Entry IDs and sequence numbers
- `kanji`: Kanji readings with priority
- `readings`: Kana readings with priority
- `senses`: Word senses with POS tags
- `glosses`: Definitions/glosses
- Additional metadata tables: `sense_pos`, `sense_field`, `sense_misc`, `sense_dial`

## Testing

Run the test suite:

```bash
python tests/run_all_tests.py
```

Or run individual test files:

```bash
python -m unittest tentoku.tests.test_basic
python -m unittest tentoku.tests.test_deinflect
# etc.
```

See [TEST_COVERAGE_INVENTORY.md](TEST_COVERAGE_INVENTORY.md) for detailed test coverage information.

## Credits

The tokenization logic, including the deinflection rules and matching strategy, is derived from the original TypeScript implementation used by [10ten Japanese Reader](https://github.com/birchill/10ten-ja-reader).

### Dictionary Data

This module uses the [JMDict](https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project) dictionary data, which is the property of the [Electronic Dictionary Research and Development Group](https://www.edrdg.org/) (EDRDG). The dictionary data is licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/) (CC BY-SA 4.0).

Copyright is held by James William BREEN and The Electronic Dictionary Research and Development Group.

The JMDict data is automatically downloaded from the official EDRDG source when building the database. For more information about JMDict and its license, see:
- **JMDict Project**: https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project
- **EDRDG License Statement**: https://www.edrdg.org/edrdg/licence.html
- **EDRDG Home Page**: https://www.edrdg.org/

See [JMDICT_ATTRIBUTION.md](JMDICT_ATTRIBUTION.md) for complete attribution details.

## License

This project is licensed under the GNU General Public License v3.0 or later (GPL-3.0-or-later).

See the [LICENSE](LICENSE) file for the full license text.

**Note on Dictionary Data**: While this software is licensed under GPL-3.0-or-later, the JMDict dictionary data used by this module is separately licensed under CC BY-SA 4.0. When distributing this software with the database, both licenses apply to their respective components.
