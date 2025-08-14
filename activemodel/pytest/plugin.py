"""
Entrypoint for the pytest plugin
"""

import pytest

from .transaction import test_session


@pytest.fixture(scope="function")
def db_session():
    """
    Helpful for tests that are more similar to unit tests. If you doing a routing or integration test, you
    probably don't need this. If your unit test is simple (you are just creating a couple of models) you
    can most likely skip this.

    This is helpful if you are doing a lot of lazy-loaded params or need a database session to be in place
    for testing code that will run within a celery worker or something similar.

    >>> def the_test(db_session):
    """
    with test_session() as session:
        yield session
