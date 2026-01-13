# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: initializedcheck=False
"""
Parallel/batch tokenization utilities.

This module provides utilities for batch processing, which uses Python's
multiprocessing for true parallelism when processing many texts.
"""

from typing import List
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing


def parallel_normalize_batch(texts: List[str], num_workers: int = None):
    """
    Normalize multiple texts in parallel using multiprocessing.

    Args:
        texts: List of strings to normalize
        num_workers: Number of worker processes (default: CPU count)

    Returns:
        List of normalized strings
    """
    from tentoku.normalize_cy import normalize_input

    if num_workers is None:
        num_workers = multiprocessing.cpu_count()

    # For small batches, don't bother with parallelism
    if len(texts) < 10:
        return [normalize_input(text) for text in texts]

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(normalize_input, texts))

    return results


def parallel_deinflect_batch(words: List[str], num_workers: int = None):
    """
    Deinflect multiple words in parallel using multiprocessing.

    Args:
        words: List of words to deinflect
        num_workers: Number of worker processes (default: CPU count)

    Returns:
        List of deinflection results (each is a list of CandidateWord objects)
    """
    from tentoku.deinflect_cy import deinflect

    if num_workers is None:
        num_workers = multiprocessing.cpu_count()

    # For small batches, don't bother with parallelism
    if len(words) < 10:
        return [deinflect(word) for word in words]

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(deinflect, words))

    return results


def parallel_tokenize_batch(texts: List[str], dictionary, max_results: int = 7, num_workers: int = None):
    """
    Tokenize multiple texts in parallel.

    This is useful for batch processing many texts (e.g., multiple manga pages).
    Uses multiprocessing for true parallelism.

    Args:
        texts: List of text strings to tokenize
        dictionary: Dictionary to use for lookups
        max_results: Maximum results per lookup
        num_workers: Number of worker processes (default: CPU count)

    Returns:
        List of token lists
    """
    from tentoku import tokenizer

    if num_workers is None:
        num_workers = multiprocessing.cpu_count()

    # For small batches, don't bother with parallelism
    if len(texts) < 5:
        return [tokenizer.tokenize(text, dictionary=dictionary, max_results=max_results) for text in texts]

    def tokenize_one(text):
        return tokenizer.tokenize(text, dictionary=dictionary, max_results=max_results)

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(tokenize_one, texts))

    return results


def get_num_cpus():
    """Get the number of CPU cores available."""
    return multiprocessing.cpu_count()
