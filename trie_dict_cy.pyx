# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: initializedcheck=False
"""
Cython-optimized trie dictionary lookups.

Provides fast entry ID unpacking and trie existence checks.
"""

from cpython.bytes cimport PyBytes_AS_STRING, PyBytes_GET_SIZE

from tentoku.normalize_cy import kana_to_hiragana


cpdef list unpack_entry_ids(bytes packed):
    """
    Fast unpacking of entry IDs from bytes.

    Args:
        packed: Bytes containing packed 4-byte little-endian unsigned integers

    Returns:
        List of entry IDs
    """
    cdef int num_ids = len(packed) // 4
    cdef list result = []
    cdef int i
    cdef unsigned int entry_id
    cdef const unsigned char* data = <const unsigned char*>PyBytes_AS_STRING(packed)

    for i in range(num_ids):
        # Little-endian 4-byte unsigned int
        entry_id = (data[i*4] |
                    (data[i*4 + 1] << 8) |
                    (data[i*4 + 2] << 16) |
                    (data[i*4 + 3] << 24))
        result.append(entry_id)

    return result


cpdef list get_entry_ids_fast(object trie, str text):
    """
    Fast entry ID lookup from trie.

    Args:
        trie: marisa_trie.BytesTrie instance
        text: Text to look up

    Returns:
        List of entry IDs, empty if not found
    """
    if text not in trie:
        return []

    cdef bytes packed = trie[text][0]
    return unpack_entry_ids(packed)


cpdef list get_entry_ids_normalized_fast(object trie, str text):
    """
    Fast normalized entry ID lookup.

    Tries both original text and hiragana-normalized form.

    Args:
        trie: marisa_trie.BytesTrie instance
        text: Text to look up (may be katakana)

    Returns:
        Sorted list of entry IDs from both forms
    """
    cdef set ids = set()
    cdef str normalized
    cdef bytes packed

    # Try original
    if text in trie:
        packed = trie[text][0]
        ids.update(unpack_entry_ids(packed))

    # Try hiragana-normalized
    normalized = kana_to_hiragana(text)
    if normalized != text and normalized in trie:
        packed = trie[normalized][0]
        ids.update(unpack_entry_ids(packed))

    return sorted(ids)


cpdef bint trie_exists(object trie, str text):
    """
    Fast existence check in trie.

    Checks both original text and hiragana-normalized form.

    Args:
        trie: marisa_trie.BytesTrie instance
        text: Text to check

    Returns:
        True if text (or its normalized form) exists in trie
    """
    cdef str normalized

    if text in trie:
        return True

    # Also check hiragana-normalized form
    normalized = kana_to_hiragana(text)
    if normalized != text and normalized in trie:
        return True

    return False
