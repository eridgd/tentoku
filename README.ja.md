<div align="center">
  <img src="https://raw.githubusercontent.com/eridgd/tentoku/main/images/tentoku_icon.svg" alt="Tentoku Logo" width="128">
</div>

# Tentoku（天読）- 日本語トークナイザ

**辞書ベースの日本語トークナイザ（活用形の復元機能付き）**

[![PyPI version](https://img.shields.io/pypi/v/tentoku.svg)](https://pypi.org/project/tentoku/)
[![Python versions](https://img.shields.io/pypi/pyversions/tentoku.svg)](https://pypi.org/project/tentoku/)
[![License](https://img.shields.io/pypi/l/tentoku.svg)](https://pypi.org/project/tentoku/)

> **⚠️ 注意（自動翻訳）**  
> この README（日本語版）は自動翻訳（機械翻訳）です。  
> 内容の正確性および最新情報については、英語版 README を正としてください。

---

Tentokuは、[10ten Japanese Reader](https://github.com/birchill/10ten-ja-reader)で使用されている高精度トークナイゼーションエンジンのPython移植版です。

MeCabやSudachiなどの統計的分かち書きツールとは異なり、Tentokuは貪欲最長一致アルゴリズムと、活用形を辞書形に戻すルールベースシステムを組み合わせています。速度よりも検索精度を優先するため、リーディング支援ツール、辞書ツール、アノテーション作業フローに適しています。

## 機能

- **貪欲最長一致トークナイゼーション**: テキスト内で可能な限り長い単語を見つけます
- **活用形復元サポート**: 約400の活用規則を処理し、動詞と形容詞を辞書形に戻します
- **時制と形式の検出**: 「丁寧過去形」「継続形」「否定形」などの動詞形式を識別します
- **自動データベースセットアップ**: 初回使用時にJMDictデータベースを自動的にダウンロードして構築します
- **辞書検索**: JMDict SQLiteデータベースを使用して単語を検索します
- **テキストのバリエーション**: 長音（ー）の展開と旧字体から新字体への変換を処理します
- **型検証**: 活用形を復元した形式を品詞タグに対して検証します

## インストール

トークナイザーにはPython 3.8以上が必要で、標準ライブラリモジュール（sqlite3、unicodedata、dataclasses、typing）のみを使用します。

### PyPIからインストール

```bash
pip install tentoku
```

### ソースからインストール

```bash
git clone https://github.com/eridgd/tentoku.git
cd tentoku
pip install -e .
```

### オプションの依存関係

パフォーマンスとプログレスバーの向上のため：
- `lxml` - より高速なXML解析（推奨）
- `tqdm` - データベース構築中のプログレスバー

インストール方法：
```bash
pip install tentoku[full]  # PyPIから
# または
pip install -e ".[full]"   # ソースから
```

個別にインストールする場合：
```bash
pip install lxml tqdm
```

## 使用方法

### 基本的な使用方法

辞書は初回使用時に自動的にJMDictデータベースをダウンロードして構築します：

```python
from tentoku import tokenize

tokens = tokenize("私は学生です")

for token in tokens:
    print(f"{token.text} ({token.start}-{token.end})")
    if token.dictionary_entry:
        entry = token.dictionary_entry
        sense = entry.senses[0]
        meaning = sense.glosses[0].text
        
        print(f"  Entry: {entry.ent_seq}")
        print(f"  Meaning: {meaning}")
        
        # 品詞
        if sense.pos_tags:
            print(f"  POS: {', '.join(sense.pos_tags)}")
        
        # 語種・文体（misc）
        if sense.misc:
            print(f"  Usage: {', '.join(sense.misc)}")
        
        # 分野（例：コンピュータ、医学）
        if sense.field:
            print(f"  Field: {', '.join(sense.field)}")
        
        # 方言情報
        if sense.dial:
            print(f"  Dialect: {', '.join(sense.dial)}")
        
        print()
        
# 出力:
# 私 (0-1)
#   Entry: 1311110
#   Meaning: I
#   POS: pronoun

# は (1-2)
#   Entry: 2028920
#   Meaning: indicates sentence topic
#   POS: particle

# 学生 (2-4)
#   Entry: 1206900
#   Meaning: student (esp. a university student)
#   POS: noun (common) (futsuumeishi)

# です (4-6)
#   Entry: 1628500
#   Meaning: be
#   POS: copula, auxiliary verb
#   Usage: polite (teineigo) language
```

### 動詞の形式と活用形の復元

トークナイザーは動詞の活用を自動的に処理し、活用形の復元情報を提供します：

```python
from tentoku import tokenize

tokens = tokenize("食べました")

for token in tokens:
    if token.deinflection_reasons:
        for chain in token.deinflection_reasons:
            reasons = [r.name for r in chain]
            print(f"{token.text} -> {', '.join(reasons)}")

# 出力: 食べました -> PolitePast
```

利用可能な`Reason`の値には以下が含まれます：
- `PolitePast` - 丁寧過去形（ました）
- `Polite` - 丁寧形（ます）
- `Past` - 過去形（た）
- `Negative` - 否定形（ない）
- `Continuous` - 継続形（ている）
- `Potential` - 可能形
- `Causative` - 使役形
- `Passive` - 受身形
- `Tai` - 希望形（たい）
- `Volitional` - 意志形（う/よう）
- その他多数（`_types.py`の`Reason`列挙型を参照）

### カスタム辞書の使用

カスタムデータベースパスを使用する必要がある場合、または辞書インスタンスを自分で管理したい場合：

```python
from tentoku import SQLiteDictionary, tokenize

# カスタムパスで辞書を作成
dictionary = SQLiteDictionary(db_path="/path/to/custom/jmdict.db")

# 明示的にtokenizeに渡す
tokens = tokenize("私は学生です", dictionary)

# 完了したら閉じることを忘れずに
dictionary.close()
```

### 手動でのデータベース構築

データベースを手動で構築することもできます：

```python
from tentoku import build_database

# 指定した場所にデータベースを構築
build_database("/path/to/custom/jmdict.db")
```

コマンドラインから：

```bash
python -m tentoku.build_database --db-path /path/to/custom/jmdict.db
```

### 単語検索（上級者向け）

上級者向けの使用方法として、単語検索関数を直接使用できます：

```python
from tentoku import SQLiteDictionary
from tentoku.word_search import word_search
from tentoku.normalize import normalize_input

dictionary = SQLiteDictionary()

# 入力を正規化
text = "食べています"
normalized, input_lengths = normalize_input(text)

# 単語を検索
result = word_search(normalized, dictionary, max_results=7, input_lengths=input_lengths)

if result:
    for word_result in result.data:
        # 一致したテキストとエントリを表示
        matched_text = text[:word_result.match_len]
        entry_word = word_result.entry.kana_readings[0].text if word_result.entry.kana_readings else "N/A"
        print(f"'{matched_text}' -> {entry_word} (entry: {word_result.entry.ent_seq})")
        
        if word_result.reason_chains:
            for chain in word_result.reason_chains:
                reason_names = [r.name for r in chain]
                print(f"  Deinflected from: {' -> '.join(reason_names)}")

# 出力:
# '食べています' -> たべる (entry: 1358280)
#   Deinflected from: Continuous -> Polite
```

### 活用形の復元（上級者向け）

上級者向けの使用方法として、活用形の復元関数を直接使用できます：

```python
from tentoku.deinflect import deinflect

# 活用された動詞を復元
candidates = deinflect("食べました")

# 最も関連性の高い復元形式を表示
for candidate in candidates:
    if candidate.reason_chains and candidate.word == "食べる":
        for chain in candidate.reason_chains:
            reason_names = [r.name for r in chain]
            print(f"{candidate.word} <- {' -> '.join(reason_names)}")
            break

# 出力: 食べる <- PolitePast
```

## アーキテクチャ

トークナイザーは以下のモジュールで構成されています：

- **`_types.py`**: コア型定義（Token、WordEntry、WordResult、WordType、Reason）
- **`normalize.py`**: テキスト正規化（Unicode、全角数字、ZWNJの削除）
- **`variations.py`**: テキストのバリエーション（長音の展開、旧字体変換）
- **`yoon.py`**: 拗音の検出
- **`deinflect.py`**: コア活用形復元アルゴリズム
- **`deinflect_rules.py`**: 約400の活用形復元規則
- **`dictionary.py`**: 辞書インターフェースの抽象化
- **`sqlite_dict.py`**: SQLite辞書の実装
- **`word_search.py`**: バックトラッキング単語検索アルゴリズム
- **`type_matching.py`**: 単語型の検証
- **`sorting.py`**: 優先度による結果のソート
- **`tokenizer.py`**: メインのトークナイゼーション関数
- **`database_path.py`**: データベースパスユーティリティ
- **`build_database.py`**: データベースの構築とダウンロード

## アルゴリズム

トークナイゼーションアルゴリズムは以下のように動作します：

1. **入力の正規化**: 全角数字に変換、Unicodeの正規化、ZWNJの削除
2. **貪欲最長一致**: 位置0から開始し、最長の一致する単語を見つける
3. **単語検索**: 各部分文字列について：
   - バリエーションを生成（長音の展開、旧字体変換）
   - 活用形を復元して候補の辞書形を取得
   - 候補を辞書で検索し、単語型に対して検証
   - 最長の成功した一致を追跡
   - 一致がない場合、入力を短縮して繰り返す（きゃなどの拗音で終わる場合は2文字、それ以外は1文字）
4. **進行**: 一致した長さだけ進む、または一致がない場合は1文字進む

## データベース

トークナイザーはJMDict SQLiteデータベースを使用します。初回使用時には：

1. 適切な場所に既存のデータベースがあるか確認：
   - **PyPIからインストールした場合**: ユーザーデータディレクトリ
     - Linux: `~/.local/share/tentoku/jmdict.db`
     - macOS: `~/Library/Application\ Support/tentoku/jmdict.db`
     - Windows: `%APPDATA%/tentoku/jmdict.db`
   - **ソースから実行する場合**: モジュールのデータディレクトリ
     - `data/jmdict.db`（モジュールファイルが配置されている場所からの相対パス）
2. 見つからない場合、公式EDRDGソース（`https://www.edrdg.org/pub/Nihongo/JMdict_e.gz`）から`JMdict_e.xml.gz`をダウンロード
3. XMLファイルを展開して解析（圧縮時約10MB、非圧縮時約113MB）
4. 必要なインデックスを含むSQLiteデータベースを構築（約105MB）
5. 将来の使用のためにデータベースを保存
6. 一時的なXMLファイルをクリーンアップ

これは数分かかる一回限りの操作です。以降の使用は即座に行われます。

データベースには以下が含まれます：
- `entries`: エントリIDとシーケンス番号
- `kanji`: 優先度付きの漢字読み
- `readings`: 優先度付きのかな読み
- `senses`: 品詞タグ付きの単語の意味
- `glosses`: 定義/語義
- 追加のメタデータテーブル: `sense_pos`、`sense_field`、`sense_misc`、`sense_dial`

## テスト

テストスイートを実行：

```bash
python tests/run_all_tests.py
```

個別のテストファイルを実行：

```bash
python -m unittest tentoku.tests.test_basic
python -m unittest tentoku.tests.test_deinflect
# など
```

詳細なテストカバレッジ情報については、[TEST_COVERAGE_INVENTORY.md](TEST_COVERAGE_INVENTORY.md)を参照してください。

## パフォーマンスベンチマーク

パフォーマンスを測定するための包括的なベンチマークスイートが利用可能です：

```bash
python benchmark.py
```

これにより、以下のパフォーマンステストが実行されます：
- トークナイゼーション速度（トークン/秒、文字/秒）
- 活用形復元のパフォーマンス
- 辞書検索のパフォーマンス
- 異なるテキストの複雑さのシナリオ
- 多数のテキストでのスループット

反復回数をカスタマイズできます：

```bash
python benchmark.py --iterations 1000
```

ウォームアップフェーズをスキップすることもできます：

```bash
python benchmark.py --no-warmup
```

ベンチマークスクリプトは、以下の詳細なメトリクスを提供します：
- 平均、中央値、最小、最大の実行時間
- 標準偏差
- スループット（1秒あたりの操作数）
- トークン/文字あたりの時間

パフォーマンステストはテストスイート（`tests/test_stress.py`）にも含まれており、以下で実行できます：

```bash
python -m unittest tentoku.tests.test_stress
```

## クレジット

トークナイゼーションロジック（活用形復元規則とマッチング戦略を含む）は、[10ten Japanese Reader](https://github.com/birchill/10ten-ja-reader)で使用されている元のTypeScript実装から派生しています。

### 辞書データ

このモジュールは、[JMDict](https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project)辞書データを使用しています。このデータは[電子辞書研究開発グループ](https://www.edrdg.org/)（EDRDG）の所有物です。辞書データは[Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/)（CC BY-SA 4.0）の下でライセンスされています。

著作権はJames William BREENと電子辞書研究開発グループが保持しています。

JMDictデータは、データベース構築時に公式EDRDGソースから自動的にダウンロードされます。JMDictとそのライセンスの詳細については、以下を参照してください：
- **JMDictプロジェクト**: https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project
- **EDRDGライセンス声明**: https://www.edrdg.org/edrdg/licence.html
- **EDRDGホームページ**: https://www.edrdg.org/

完全な帰属の詳細については、[JMDICT_ATTRIBUTION.md](JMDICT_ATTRIBUTION.md)を参照してください。

## ライセンス

このプロジェクトは、GNU General Public License v3.0以降（GPL-3.0-or-later）の下でライセンスされています。

完全なライセンステキストについては、[LICENSE](LICENSE)ファイルを参照してください。

**辞書データに関する注意**: このソフトウェアはGPL-3.0-or-laterの下でライセンスされていますが、このモジュールで使用されるJMDict辞書データは、CC BY-SA 4.0の下で別途ライセンスされています。データベースと共にこのソフトウェアを配布する場合、両方のライセンスがそれぞれのコンポーネントに適用されます。
