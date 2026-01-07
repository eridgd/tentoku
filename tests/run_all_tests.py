#!/usr/bin/env python3
"""
Run all tests in order, with stress tests last.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def run_all_tests():
    """Run all test suites in order."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Test order: unit tests first, integration, then stress tests last
    # Import from tentoku.tests
    test_modules = [
        'tentoku.tests.test_basic',
        'tentoku.tests.test_normalize',
        'tentoku.tests.test_variations',
        'tentoku.tests.test_yoon',
        'tentoku.tests.test_deinflect',
        'tentoku.tests.test_type_matching',
        'tentoku.tests.test_sorting',
        'tentoku.tests.test_dictionary',
        'tentoku.tests.test_integration',
        'tentoku.tests.test_tokenize',
        'tentoku.tests.test_edge_cases',
        'tentoku.tests.test_corpus',
        'tentoku.tests.test_comparison',
        'tentoku.tests.test_regression',
        # Stress tests last
        'tentoku.tests.test_stress',
    ]
    
    print("Running test suites in order...\n")
    
    for module_name in test_modules:
        try:
            module = __import__(module_name, fromlist=[''])
            tests = loader.loadTestsFromModule(module)
            suite.addTests(tests)
            print(f"✓ Loaded {module_name}")
        except Exception as e:
            print(f"✗ Failed to load {module_name}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Running {suite.countTestCases()} tests...")
    print(f"{'='*60}\n")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n{'='*60}")
    if result.wasSuccessful():
        print(f"✓ All tests passed! ({result.testsRun} tests)")
    else:
        print(f"✗ Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}")
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}")
    print(f"{'='*60}")
    
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_all_tests())

