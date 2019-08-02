import pytest
import sys
import subprocess as sp


def run_tests():
    result = pytest.main(['tests/pyt', '-x', '-v', '--capture', 'no'])

    if result > 0:
        sys.exit()

    # Run visual tests

    sp.run(['python', 'tests/test_visuals.py'])
