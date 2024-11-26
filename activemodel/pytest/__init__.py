from sqlmodel import SQLModel

from activemodel import logger

from ..session_manager import get_engine


def truncate_db():
    # TODO Problem with truncation is you can't run multiple tests in parallel without separate containers

    logger.info("Truncating database")

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
