"""
Test runner for PyCraft 2D game tests.

This script runs all test suites and generates a comprehensive test report.
"""

import unittest
import sys
import os
from pathlib import Path

# Add the game directory to Python path
GAME_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(GAME_DIR))

# Import all test modules
from tests.core.test_game import TestGame, TestGameState, TestGameResourceAccess
from tests.entities.test_entities import TestPlayer, TestFloatingItem, TestProjectile, TestMob, TestEntityInteractions
from tests.systems.test_systems import (TestWorldManager, TestGameStateManager, TestRenderManager, 
                                       TestInputManager, TestCamera, TestChunkManager)
from tests.ui.test_ui import TestInventory, TestHotbar, TestLifebar, TestMenu, TestInputBox
from tests.utils.test_utils import (TestLogger, TestPerformanceMonitor, TestAudioUtils, 
                                   TestMathUtils, TestDataValidation)
from tests.world.test_world import TestMap, TestGround, TestLayer1Objects, TestChunkSystem, TestWorldGeneration


def create_test_suite():
    """Create a comprehensive test suite with all test cases."""
    suite = unittest.TestSuite()
    
    # Core tests
    suite.addTest(unittest.makeSuite(TestGame))
    suite.addTest(unittest.makeSuite(TestGameState))
    suite.addTest(unittest.makeSuite(TestGameResourceAccess))
    
    # Entity tests
    suite.addTest(unittest.makeSuite(TestPlayer))
    suite.addTest(unittest.makeSuite(TestFloatingItem))
    suite.addTest(unittest.makeSuite(TestProjectile))
    suite.addTest(unittest.makeSuite(TestMob))
    suite.addTest(unittest.makeSuite(TestEntityInteractions))
    
    # System tests
    suite.addTest(unittest.makeSuite(TestWorldManager))
    suite.addTest(unittest.makeSuite(TestGameStateManager))
    suite.addTest(unittest.makeSuite(TestRenderManager))
    suite.addTest(unittest.makeSuite(TestInputManager))
    suite.addTest(unittest.makeSuite(TestCamera))
    suite.addTest(unittest.makeSuite(TestChunkManager))
    
    # UI tests
    suite.addTest(unittest.makeSuite(TestInventory))
    suite.addTest(unittest.makeSuite(TestHotbar))
    suite.addTest(unittest.makeSuite(TestLifebar))
    suite.addTest(unittest.makeSuite(TestMenu))
    suite.addTest(unittest.makeSuite(TestInputBox))
    
    # Utility tests
    suite.addTest(unittest.makeSuite(TestLogger))
    suite.addTest(unittest.makeSuite(TestPerformanceMonitor))
    suite.addTest(unittest.makeSuite(TestAudioUtils))
    suite.addTest(unittest.makeSuite(TestMathUtils))
    suite.addTest(unittest.makeSuite(TestDataValidation))
    
    # World tests
    suite.addTest(unittest.makeSuite(TestMap))
    suite.addTest(unittest.makeSuite(TestGround))
    suite.addTest(unittest.makeSuite(TestLayer1Objects))
    suite.addTest(unittest.makeSuite(TestChunkSystem))
    suite.addTest(unittest.makeSuite(TestWorldGeneration))
    
    return suite


def run_tests_with_coverage():
    """Run tests with coverage reporting if available."""
    try:
        import coverage
        
        # Start coverage
        cov = coverage.Coverage()
        cov.start()
        
        # Run tests
        suite = create_test_suite()
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Stop coverage and report
        cov.stop()
        cov.save()
        
        print("\n" + "="*50)
        print("COVERAGE REPORT")
        print("="*50)
        cov.report()
        
        # Save HTML coverage report
        cov.html_report(directory='tests/coverage_html_report')
        print(f"\nHTML coverage report saved to: tests/coverage_html_report/index.html")
        
        return result
        
    except ImportError:
        print("Coverage module not available. Install with: pip install coverage")
        return run_tests_basic()


def run_tests_basic():
    """Run tests without coverage reporting."""
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


def print_test_summary(result):
    """Print a summary of test results."""
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    successes = total_tests - failures - errors - skipped
    
    print(f"Total Tests:    {total_tests}")
    print(f"Successes:      {successes}")
    print(f"Failures:       {failures}")
    print(f"Errors:         {errors}")
    print(f"Skipped:        {skipped}")
    
    if failures > 0:
        print(f"\nFAILURES ({failures}):")
        for test, traceback in result.failures:
            print(f"- {test}")
    
    if errors > 0:
        print(f"\nERRORS ({errors}):")
        for test, traceback in result.errors:
            print(f"- {test}")
    
    success_rate = (successes / total_tests) * 100 if total_tests > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 All tests passed!")
    elif success_rate >= 90:
        print("✅ Most tests passed - good job!")
    elif success_rate >= 70:
        print("⚠️  Some tests failed - needs attention")
    else:
        print("❌ Many tests failed - significant issues")


def main():
    """Main test runner function."""
    print("PyCraft 2D - Comprehensive Test Suite")
    print("="*50)
    
    # Check if we should run with coverage
    use_coverage = '--coverage' in sys.argv or '-c' in sys.argv
    
    if use_coverage:
        result = run_tests_with_coverage()
    else:
        result = run_tests_basic()
    
    print_test_summary(result)
    
    # Exit with non-zero code if tests failed
    if result.failures or result.errors:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
