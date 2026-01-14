#!/usr/bin/env python3
"""
Setup script for Tentoku with Cython extensions.

This setup.py builds Cython extensions for performance-critical modules.
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import os
import sys

# Compiler directives for Cython optimization
compiler_directives = {
    'language_level': '3',
    'boundscheck': False,  # Disable bounds checking for speed
    'wraparound': False,   # Disable negative indexing for speed
    'initializedcheck': False,  # Disable checking for initialized variables
    'nonecheck': False,    # Disable None checks for speed
    'overflowcheck': False,  # Disable overflow checks
    'cdivision': True,     # Use C division (faster)
    'embedsignature': True,  # Embed function signatures in docstrings
    'infer_types': True,   # Infer types automatically
    'optimize.use_switch': True,  # Use switch statements for if/elif chains
    'optimize.unpack_method_calls': True,  # Optimize method calls
}

# Performance-critical modules to compile with Cython
cython_modules = [
    'deinflect_cy.pyx',
    'word_search_cy.pyx',
    'normalize_cy.pyx',
    'sorting_cy.pyx',
    'type_matching_cy.pyx',
    'variations_cy.pyx',
    'yoon_cy.pyx',
    'parallel_tokenize.pyx',  # Parallel processing module
    'sqlite_dict_cy.pyx',  # Fast SQLite dictionary
]

# Create Extension objects
extensions = []
for module in cython_modules:
    # Extract module name from filename
    # e.g., 'deinflect_cy.pyx' -> 'tentoku.deinflect_cy'
    module_name = 'tentoku.' + module.replace('.pyx', '')

    # deinflect_cy needs C++ for std::unordered_map
    if module == 'deinflect_cy.pyx':
        extensions.append(
            Extension(
                module_name,
                [module],
                language='c++',  # Enable C++ compilation
                extra_compile_args=['-O3', '-std=c++11'],  # Maximum optimization with C++11
            )
        )
    # parallel_tokenize uses Python multiprocessing, no special flags needed
    elif module == 'parallel_tokenize.pyx':
        extensions.append(
            Extension(
                module_name,
                [module],
                extra_compile_args=['-O3'],
            )
        )
    else:
        extensions.append(
            Extension(
                module_name,
                [module],
                extra_compile_args=['-O3'],  # Maximum optimization
            )
        )

# Read long description from README
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='tentoku',
    version='0.2.0',
    description='Japanese text tokenization with deinflection support (Cython-optimized)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tentoku Contributors',
    license='GPL-3.0-or-later',
    packages=['tentoku', 'tentoku.tests'],
    ext_modules=cythonize(
        extensions,
        compiler_directives=compiler_directives,
        annotate=True,  # Generate HTML annotation files
    ),
    setup_requires=[
        'Cython>=0.29.0',
    ],
    install_requires=[
        # Cython is not required at runtime, only at build time
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
        ],
        'full': [
            'lxml>=4.0.0',
            'tqdm>=4.0.0',
        ],
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Programming Language :: Cython',
        'Topic :: Text Processing :: Linguistic',
    ],
)
