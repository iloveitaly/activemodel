"""
Class to make managing sessions with SQL Model easy
"""

from sqlalchemy import Engine
from sqlmodel import Session, create_engine


class SessionManager:
    def __init__(self, database_url: str):
        self._database_url = database_url
        self._engine = None

    # TODO why is this type not reimported?
    def get_engine(self) -> Engine:
        if not self._engine:
            self._engine = create_engine(
                self._database_url,
                # echo=config("ACTIVEMODEL_LOG_SQL", cast=bool, default=False),
                echo=True,
                # https://docs.sqlalchemy.org/en/20/core/pooling.html#disconnect-handling-pessimistic
                pool_pre_ping=True,
            )

        return self._engine

    def get_session(self):
        return Session(self.get_engine())


import os

# TODO need a way to specify the session generator
manager = SessionManager(os.environ["TEST_DATABASE_URL"])
get_engine = manager.get_engine
get_session = manager.get_session

from sqlmodel.sql.expression import SelectOfScalar


def compile_sql(target: SelectOfScalar):
    dialect = get_engine().dialect
    # TODO I wonder if we could store the dialect to avoid getting an engine reference
    compiled = target.compile(dialect=dialect, compile_kwargs={"literal_binds": True})
    return str(compiled)
