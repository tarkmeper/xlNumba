"""
Modifies test items to ensure optimize order in which we run the tests.

Attempts to ensure that basic tests are run before more complex tests cases. Combined with maxfail
option in pytest this lets us fail more quickly and avoid executing many test cases that are likely to fail if the
preliminary tests fail.

It also adds an option to enable benchmark tests.  Since these tests are fairly time-consuming this ensures that
these tests
"""
from collections import defaultdict

import pytest

TEST_ORDER = [
    'tests.test_basic',
    'tests.test_errors',
    'tests.test_user_function',
    'tests.test_operators',
    'tests.test_ranges',
    'tests.test_functions'
]

SORTING_ORDER = defaultdict(lambda: 1000)
SORTING_ORDER.update({name: i for i, name in enumerate(TEST_ORDER)})

# Move testing benchmarks late, there is little value in running if they are likely to fail, they relay
SORTING_ORDER['tests.test_benchmark'] = 2000


def pytest_addoption(parser):
    parser.addoption(
        "--benchmark", action="store_true", default=False, help="Enable the benchrmark tests"
    )


def pytest_collection_modifyitems(items):
    sorted_items = sorted(items,
                          key=lambda item: SORTING_ORDER[item.module.__name__] if hasattr(item, 'module') else -1)
    items[:] = sorted_items


def pytest_runtest_setup(item):
    if 'benchmark' in item.keywords and not item.config.getoption("--benchmark"):
        pytest.skip("add --benchmark option to run this test")
