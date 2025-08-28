"""Pytest plugin integration for activemodel.

Currently provides:

* ``db_session`` fixture – quick access to a database session (see ``test_session``)
* ``activemodel_preserve_tables`` ini option – configure tables to preserve when using
  ``database_reset_truncate`` (comma separated list or multiple lines depending on config style)

Configuration examples:

pytest.ini::

    [pytest]
    activemodel_preserve_tables = alembic_version,zip_code,seed_table

pyproject.toml::

    [tool.pytest.ini_options]
    activemodel_preserve_tables = [
      "alembic_version",
      "zip_code",
      "seed_table",
    ]

The list always implicitly includes ``alembic_version`` even if not specified.
"""

from activemodel.session_manager import global_session
import pytest

from .transaction import set_factory_session, set_polyfactory_session, test_session


def pytest_addoption(
    parser: pytest.Parser,
) -> None:  # pragma: no cover - executed during collection
    """Register custom ini options.

    We treat this as a *linelist* so pyproject.toml list syntax works. Comma separated works too because
    pytest splits lines first; users can still provide one line with commas.
    """

    parser.addini(
        "activemodel_preserve_tables",
        help=(
            "Tables to preserve when calling activemodel.pytest.database_reset_truncate. "
        ),
        type="linelist",
        default=["alembic_version"],
    )


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


@pytest.fixture(scope="function")
def db_truncate_session():
    """
    Provides a database session for testing when using a truncation cleaning strategy.

    When not using a transaction cleaning strategy, no global test session is set
    """
    with global_session() as session:
        # set global database sessions for model factories to avoid lazy loading issues
        set_factory_session(session)
        set_polyfactory_session(session)

        yield session
