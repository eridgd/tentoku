"""
Text variation utilities.

Handles choon (ー) expansion and kyuujitai (旧字体) to shinjitai (新字体) conversion.
"""

from typing import List

# Choon (ー) can represent various vowel extensions
# When we see ー, we need to try different possibilities
CHOON = 'ー'


def expand_choon(text: str) -> List[str]:
    """
    Expand choon (ー) to its various possibilities.
    
    The choon mark (ー) can represent different vowel extensions depending on context.
    This function generates variations by replacing ー with possible vowels.
    
    Args:
        text: Input text that may contain ー
        
    Returns:
        List of text variations with ー expanded to different vowels
    """
    if CHOON not in text:
        return []
    
    variations = []
    
    # Find all positions of ー
    choon_positions = [i for i, char in enumerate(text) if char == CHOON]
    
    # For each ー, try replacing with common vowel extensions
    # Common patterns: あ, い, う, え, お
    vowels = ['あ', 'い', 'う', 'え', 'お']
    
    # Generate variations by replacing each ー with each vowel
    # For simplicity, we'll generate variations for the first ー only
    # (to avoid combinatorial explosion)
    if choon_positions:
        first_pos = choon_positions[0]
        for vowel in vowels:
            variation = text[:first_pos] + vowel + text[first_pos + 1:]
            variations.append(variation)
    
    return variations


# Kyuujitai (旧字体) to shinjitai (新字体) conversion map
# This is a simplified mapping - a full implementation would need a comprehensive table
KYUUJITAI_TO_SHINJITAI = {
    '舊': '旧',
    '體': '体',
    '國': '国',
    '學': '学',
    '會': '会',
    '實': '実',
    '寫': '写',
    '讀': '読',
    '賣': '売',
    '來': '来',
    '歸': '帰',
    '變': '変',
    '傳': '伝',
    '轉': '転',
    '廣': '広',
    '應': '応',
    '當': '当',
    '擔': '担',
    '戰': '戦',
    '殘': '残',
    '歲': '歳',
    '圖': '図',
    '團': '団',
    '圓': '円',
    '壓': '圧',
    '圍': '囲',
    '醫': '医',
    '鹽': '塩',
    '處': '処',
    '廳': '庁',
    '與': '与',
    '餘': '余',
    '價': '価',
    '兒': '児',
    '產': '産',
    '縣': '県',
    '顯': '顕',
    '驗': '験',
    '險': '険',
    '獻': '献',
    '嚴': '厳',
    '靈': '霊',
    '齡': '齢',
    '勞': '労',
    '營': '営',
    '榮': '栄',
    '櫻': '桜',
    '驛': '駅',
    '驢': '驢',
    '驤': '驤',
    '驗': '験',
    '驗': '験',
}


def kyuujitai_to_shinjitai(text: str) -> str:
    """
    Convert kyuujitai (旧字体, old kanji forms) to shinjitai (新字体, new kanji forms).
    
    Args:
        text: Input text that may contain old kanji forms
        
    Returns:
        Text with old kanji forms converted to new forms
    """
    result = []
    changed = False
    
    for char in text:
        if char in KYUUJITAI_TO_SHINJITAI:
            result.append(KYUUJITAI_TO_SHINJITAI[char])
            changed = True
        else:
            result.append(char)
    
    return ''.join(result) if changed else text

