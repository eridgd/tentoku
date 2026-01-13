# cython: language_level=3
"""
C++ unordered_map declarations for Cython.
"""

from libcpp.unordered_map cimport unordered_map
from libcpp.string cimport string
from libcpp.pair cimport pair

# Declare the C++ map type for string to int mapping
ctypedef unordered_map[string, int] StringIntMap
