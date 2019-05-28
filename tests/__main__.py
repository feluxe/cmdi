import pytest
import sys
import subprocess as sp

# Run basic test with pytest

result = pytest.main(['tests/test_basics.py', '-x', '-v'])
result += pytest.main(['tests/test_print_summary.py', '-x', '-v'])

if result > 0:
    sys.exit()

# Run visual tests

sp.run(['python', 'tests/test_visuals.py'])


