import subprocess as sp
import sys

import pytest


def run_tests():
    result = pytest.main(["tests/pyt", "-x", "-v", "--capture", "no"])

    if result > 0:
        sys.exit()

    # Run visual tests

    sp.run(["python", "tests/test_visuals.py"])
