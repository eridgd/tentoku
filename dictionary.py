"""
Dictionary interface abstraction.

This module defines the abstract base class for dictionary implementations.
"""

from abc import ABC, abstractmethod
from typing import List
from ._types import WordEntry


class Dictionary(ABC):
    """Abstract base class for dictionary implementations."""
    
    @abstractmethod
    def get_words(self, input_text: str, max_results: int) -> List[WordEntry]:
        """
        Look up words in the dictionary.
        
        Args:
            input_text: The text to look up (should be normalized to hiragana)
            max_results: Maximum number of results to return
            
        Returns:
            List of WordEntry objects matching the input
        """
        pass

