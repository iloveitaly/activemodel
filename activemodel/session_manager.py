"""
Class to make managing sessions with SQL Model easy. Also provides a common entrypoint to make it easy to mutate the
database environment when testing.
"""

import typing as t

from decouple import config
from sqlalchemy import Engine
from sqlmodel import Session, create_engine


class SessionManager:
    _instance: t.ClassVar[t.Optional["SessionManager"]] = None

    session_connection: str

    @classmethod
    def get_instance(cls, database_url: str | None = None) -> "SessionManager":
        if cls._instance is None:
            assert (
                database_url is not None
            ), "Database URL required for first initialization"
            cls._instance = cls(database_url)

        return cls._instance

    def __init__(self, database_url: str):
        self._database_url = database_url
        self._engine = None
        self.session_connection = None

    # TODO why is this type not reimported?
    def get_engine(self) -> Engine:
        if not self._engine:
            self._engine = create_engine(
                self._database_url,
                echo=config("ACTIVEMODEL_LOG_SQL", cast=bool, default=False),
                # https://docs.sqlalchemy.org/en/20/core/pooling.html#disconnect-handling-pessimistic
                pool_pre_ping=True,
                # some implementations include `future=True` but it's not required anymore
            )

        return self._engine

    def get_session(self):
        if self.session_connection:
            return Session(bind=self.session_connection)

        return Session(self.get_engine())


def init(database_url: str):
    return SessionManager.get_instance(database_url)


def get_engine():
    return SessionManager.get_instance().get_engine()


def get_session():
    return SessionManager.get_instance().get_session()
