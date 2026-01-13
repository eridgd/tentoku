# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: initializedcheck=False
"""
Yoon (拗音) detection utilities - Cython optimized version.

Yoon are combinations like きゃ, しゅ, ちょ where a consonant + small や/ゆ/よ
form a single mora.
"""

# Define constants as C arrays for faster lookup
cdef int YOON_START[11]
YOON_START[:] = [
    0x304d, 0x3057, 0x3061, 0x306b, 0x3072, 0x307f, 0x308a, 0x304e, 0x3058,
    0x3073, 0x3074,
]

cdef int SMALL_Y[3]
SMALL_Y[:] = [0x3083, 0x3085, 0x3087]


cpdef bint ends_in_yoon(str input_text):
    """
    Check if the input ends in a yoon (拗音).

    Args:
        input_text: The text to check

    Returns:
        True if the text ends in a yoon (e.g., きゃ, しゅ, ちょ)
    """
    cdef int length = len(input_text)
    cdef int last_cp, second_last_cp
    cdef int i
    cdef bint last_in_small_y = False
    cdef bint second_in_yoon_start = False

    if length < 2:
        return False

    # Get the last two characters' code points
    last_cp = ord(input_text[length - 1])
    second_last_cp = ord(input_text[length - 2])

    # Check if last char is in SMALL_Y
    for i in range(3):
        if last_cp == SMALL_Y[i]:
            last_in_small_y = True
            break

    if not last_in_small_y:
        return False

    # Check if second-to-last char is in YOON_START
    for i in range(11):
        if second_last_cp == YOON_START[i]:
            second_in_yoon_start = True
            break

    return second_in_yoon_start
