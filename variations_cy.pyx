# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: initializedcheck=False
"""
Text variation utilities - Cython optimized version.

Handles choon (ー) expansion and kyuujitai (旧字体) to shinjitai (新字体) conversion.
"""

from typing import List

# Choon (ー) can represent various vowel extensions
cdef str CHOON = 'ー'

# Kyuujitai to shinjitai mapping
cdef dict KYUUJITAI_TO_SHINJITAI = {
    '舊': '旧', '體': '体', '國': '国', '學': '学', '會': '会',
    '實': '実', '寫': '写', '讀': '読', '賣': '売', '來': '来',
    '歸': '帰', '變': '変', '傳': '伝', '轉': '転', '廣': '広',
    '應': '応', '當': '当', '擔': '担', '戰': '戦', '殘': '残',
    '歲': '歳', '圖': '図', '團': '団', '圓': '円', '壓': '圧',
    '圍': '囲', '醫': '医', '鹽': '塩', '處': '処', '廳': '庁',
    '與': '与', '餘': '余', '價': '価', '兒': '児', '產': '産',
    '縣': '県', '顯': '顕', '驗': '験', '險': '険', '獻': '献',
    '嚴': '厳', '靈': '霊', '齡': '齢', '勞': '労', '營': '営',
    '榮': '栄', '櫻': '桜', '驛': '駅', '驢': '驢', '驤': '驤',
}


cpdef list expand_choon(str text):
    """
    Expand choon (ー) to its various possibilities.

    Args:
        text: Input text that may contain ー

    Returns:
        List of text variations with ー expanded to different vowels
    """
    cdef list variations = []
    cdef list choon_positions = []
    cdef int i, first_pos
    cdef str vowel, variation
    cdef list vowels = ['あ', 'い', 'う', 'え', 'お']

    if CHOON not in text:
        return []

    # Find first position of ー
    for i in range(len(text)):
        if text[i] == CHOON:
            first_pos = i
            break
    else:
        return []

    # Generate variations by replacing the first ー with each vowel
    for vowel in vowels:
        variation = text[:first_pos] + vowel + text[first_pos + 1:]
        variations.append(variation)

    return variations


cpdef str kyuujitai_to_shinjitai(str text):
    """
    Convert kyuujitai (旧字体, old kanji forms) to shinjitai (新字体, new kanji forms).

    Args:
        text: Input text that may contain old kanji forms

    Returns:
        Text with old kanji forms converted to new forms
    """
    cdef list result = []
    cdef bint changed = False
    cdef str char, converted

    for char in text:
        if char in KYUUJITAI_TO_SHINJITAI:
            result.append(KYUUJITAI_TO_SHINJITAI[char])
            changed = True
        else:
            result.append(char)

    return ''.join(result) if changed else text
