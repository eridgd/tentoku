"""
Type definitions for the Japanese tokenizer.
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import IntEnum


class WordType(IntEnum):
    """Word type flags for deinflection matching."""
    # Final word types
    IchidanVerb = 1 << 0  # i.e. ru-verbs
    GodanVerb = 1 << 1   # i.e. u-verbs
    IAdj = 1 << 2
    KuruVerb = 1 << 3
    SuruVerb = 1 << 4
    SpecialSuruVerb = 1 << 5
    NounVS = 1 << 6
    
    # Combined final types
    All = IchidanVerb | GodanVerb | IAdj | KuruVerb | SuruVerb | SpecialSuruVerb | NounVS
    
    # Intermediate types (not valid dictionary entries)
    Initial = 1 << 7      # original word before any deinflection (from-type only)
    TaTeStem = 1 << 8
    DaDeStem = 1 << 9
    MasuStem = 1 << 10
    IrrealisStem = 1 << 11


class Reason(IntEnum):
    """Reasons for deinflection transformations."""
    PolitePastNegative = 0
    PoliteNegative = 1
    PoliteVolitional = 2
    Chau = 3
    Sugiru = 4
    PolitePast = 5
    Tara = 6
    Tari = 7
    Causative = 8
    PotentialOrPassive = 9
    Toku = 10
    Sou = 11
    Tai = 12
    Polite = 13
    Respectful = 14
    Humble = 15
    HumbleOrKansaiDialect = 16
    Past = 17
    Negative = 18
    Passive = 19
    Ba = 20
    Volitional = 21
    Potential = 22
    EruUru = 23
    CausativePassive = 24
    Te = 25
    Zu = 26
    Imperative = 27
    MasuStem = 28
    Adv = 29
    Noun = 30
    ImperativeNegative = 31
    Continuous = 32
    Ki = 33
    SuruNoun = 34
    ZaruWoEnai = 35
    NegativeTe = 36
    Irregular = 37


@dataclass
class CandidateWord:
    """A candidate word from deinflection."""
    word: str
    type: int  # WordType bitmask
    reason_chains: List[List[Reason]]  # How this word was derived


@dataclass
class KanjiReading:
    """Kanji reading (written form)."""
    text: str
    priority: Optional[str] = None
    info: Optional[str] = None


@dataclass
class KanaReading:
    """Kana reading (pronunciation)."""
    text: str
    no_kanji: bool = False
    priority: Optional[str] = None
    info: Optional[str] = None


@dataclass
class Gloss:
    """Definition/gloss for a sense."""
    text: str
    lang: str = "eng"
    g_type: Optional[str] = None


@dataclass
class Sense:
    """A sense (meaning) of a dictionary entry."""
    index: int
    pos_tags: List[str]  # Parts of speech
    glosses: List[Gloss]
    info: Optional[str] = None
    field: Optional[List[str]] = None
    misc: Optional[List[str]] = None
    dial: Optional[List[str]] = None


@dataclass
class WordEntry:
    """A dictionary word entry."""
    entry_id: int
    ent_seq: str
    kanji_readings: List[KanjiReading]
    kana_readings: List[KanaReading]
    senses: List[Sense]


@dataclass
class WordResult:
    """Result from word search."""
    entry: WordEntry
    match_len: int
    reason_chains: Optional[List[List[Reason]]] = None


@dataclass
class Token:
    """A token from tokenization."""
    text: str
    start: int
    end: int
    dictionary_entry: Optional[WordEntry] = None
    deinflection_reasons: Optional[List[List[Reason]]] = None

