"""
Yoon (拗音) detection utilities.

Yoon are combinations like きゃ, しゅ, ちょ where a consonant + small や/ゆ/よ
form a single mora.
"""

# Try to import Cython-optimized version, fall back to Python if not available
try:
    from .yoon_cy import ends_in_yoon as _ends_in_yoon_cy
    _CYTHON_AVAILABLE = True
except ImportError:
    _CYTHON_AVAILABLE = False

# きしちにひみりぎじびぴ
YOON_START = [
    0x304d, 0x3057, 0x3061, 0x306b, 0x3072, 0x307f, 0x308a, 0x304e, 0x3058,
    0x3073, 0x3074,
]

# ゃゅょ
SMALL_Y = [0x3083, 0x3085, 0x3087]


def _ends_in_yoon_py(input_text: str) -> bool:
    """
    Check if the input ends in a yoon (拗音).
    
    Args:
        input_text: The text to check
        
    Returns:
        True if the text ends in a yoon (e.g., きゃ, しゅ, ちょ)
    """
    if not input_text:
        return False
    
    # Convert to list of characters to handle surrogate pairs correctly
    chars = list(input_text)
    length = len(chars)
    
    if length < 2:
        return False
    
    # Get the last two characters' code points
    last_char = chars[-1]
    second_last_char = chars[-2]
    
    last_cp = ord(last_char) if len(last_char) == 1 else ord(last_char[0])
    second_last_cp = ord(second_last_char) if len(second_last_char) == 1 else ord(second_last_char[0])
    
    return (
        last_cp in SMALL_Y and
        second_last_cp in YOON_START
    )


# Use Cython version if available, otherwise use Python fallback
if _CYTHON_AVAILABLE:
    ends_in_yoon = _ends_in_yoon_cy
else:
    ends_in_yoon = _ends_in_yoon_py

