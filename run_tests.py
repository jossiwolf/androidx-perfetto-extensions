import unittest
import sys
import os

if __name__ == '__main__':
    # Add the current directory to sys.path so tests can import helpers.py
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'tests')))

    # Discover and run tests in the 'tests' directory
    loader = unittest.TestLoader()
    suite = loader.discover('tests')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if not result.wasSuccessful():
        sys.exit(1)
