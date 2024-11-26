from sqlmodel import SQLModel

from ..logger import logger
from ..session_manager import get_engine


def database_reset_truncate():
    """
    Transaction is most likely the better way to go, but there are some scenarios where the session override
    logic does not work properly and you need to truncate tables back to their original state.

    Here's how to do this once at the start of the test:

    >>> from activemodel.pytest import database_reset_truncation
    >>> def pytest_configure(config):
    >>> 	database_reset_truncation()

    Or, if you want to use this as a fixture:

    >>> pytest.fixture(scope="function")(database_reset_truncation)
    >>> def test_the_thing(database_reset_truncation)

    This approach has a couple of problems:

    * You can't run multiple tests in parallel without separate databases
    * If you have important seed data and want to truncate those tables, the seed data will be lost
    """

    logger.info("truncating database")

    # TODO get additonal tables to preserve from config
    exception_tables = ["alembic_version"]

    assert (
        SQLModel.metadata.sorted_tables
    ), "No model metadata. Ensure model metadata is imported before running truncate_db"

    with get_engine().connect() as connection:
        for table in reversed(SQLModel.metadata.sorted_tables):
            transaction = connection.begin()

            if table.name not in exception_tables:
                logger.debug("truncating table=%s", table.name)
                connection.execute(table.delete())

            transaction.commit()
