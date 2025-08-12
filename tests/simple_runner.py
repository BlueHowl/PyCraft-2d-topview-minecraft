"""
Simple test runner for PyCraft 2D that works without external dependencies.
"""

import unittest
import sys
import os
import time
from pathlib import Path

# Add the game directory to Python path
GAME_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(GAME_DIR))


def discover_and_run_tests():
    """Discover and run all tests in the tests directory."""
    print("PyCraft 2D - Test Suite Runner")
    print("="*50)
    
    # Discover tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Print summary
    print("\n" + "="*50)
    print("TEST EXECUTION SUMMARY")
    print("="*50)
    
    duration = end_time - start_time
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    successes = total_tests - failures - errors - skipped
    
    print(f"Execution Time: {duration:.2f} seconds")
    print(f"Total Tests:    {total_tests}")
    print(f"Passed:         {successes}")
    print(f"Failed:         {failures}")
    print(f"Errors:         {errors}")
    print(f"Skipped:        {skipped}")
    
    if total_tests > 0:
        success_rate = (successes / total_tests) * 100
        print(f"Success Rate:   {success_rate:.1f}%")
    
    # Show failed tests
    if failures:
        print(f"\nFAILED TESTS ({failures}):")
        for i, (test, trace) in enumerate(result.failures, 1):
            print(f"{i}. {test}")
    
    if errors:
        print(f"\nERROR TESTS ({errors}):")
        for i, (test, trace) in enumerate(result.errors, 1):
            print(f"{i}. {test}")
    
    # Final message
    if failures == 0 and errors == 0:
        print("\n🎉 All tests passed successfully!")
    else:
        print(f"\n⚠️  {failures + errors} tests need attention")
    
    return result.wasSuccessful()


def run_specific_test_module(module_name):
    """Run tests from a specific module."""
    print(f"Running tests for module: {module_name}")
    print("="*50)
    
    try:
        # Import the specific test module
        module = __import__(f'tests.{module_name}', fromlist=[''])
        
        # Load tests from the module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"Error: Could not import test module '{module_name}'")
        print(f"Details: {e}")
        return False


def main():
    """Main function for test runner."""
    if len(sys.argv) > 1:
        # Run specific test module
        module_name = sys.argv[1]
        success = run_specific_test_module(module_name)
    else:
        # Run all tests
        success = discover_and_run_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
