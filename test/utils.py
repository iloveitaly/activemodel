import os
from contextlib import contextmanager

from activemodel import get_engine
from sqlmodel import SQLModel


def database_url():
    """
    This is also used by alembic logic as well, which is why it's extracted out
    """

    url = os.environ["DATABASE_URL"]

    assert url.startswith("postgresql")

    # sqlalchemy does *not* allow to specify the dialect of the DB outside of the url protocol
    # https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls
    # without this, psycopg2 would be used, which is not intended!
    return url.replace("postgresql://", "postgresql+psycopg://")


@contextmanager
def temporary_tables():
    SQLModel.metadata.create_all(get_engine())

    try:
        yield
    finally:
        SQLModel.metadata.drop_all(
            bind=get_engine(),
        )
