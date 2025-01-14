"""
Class to make managing sessions with SQL Model easy. Also provides a common entrypoint to make it easy to mutate the
database environment when testing.
"""

import contextlib
import json
import typing as t

from decouple import config
from pydantic import BaseModel
from sqlalchemy import Connection, Engine
from sqlmodel import Session, create_engine


def _serialize_pydantic_model(model: BaseModel | list[BaseModel] | None) -> str | None:
    """
    Pydantic models do not serialize to JSON by default. You'll get an error such as:

    'TypeError: Object of type TranscriptEntry is not JSON serializable'

    https://github.com/fastapi/sqlmodel/issues/63#issuecomment-2581016387
    """

    # TODO I bet this will fail on lists with mixed types

    if isinstance(model, BaseModel):
        return model.model_dump_json()
    if isinstance(model, list):
        # not everything in a list is a pydantic model
        def dump_if_model(m):
            if isinstance(m, BaseModel):
                return m.model_dump()
            return m

        return json.dumps([dump_if_model(m) for m in model])
    else:
        return json.dumps(model)


class SessionManager:
    _instance: t.ClassVar[t.Optional["SessionManager"]] = None

    session_connection: Connection | None
    "optionally specify a specific session connection to use for all get_session() calls, useful for testing"

    session: Session | None

    @classmethod
    def get_instance(cls, database_url: str | None = None) -> "SessionManager":
        if cls._instance is None:
            assert database_url is not None, (
                "Database URL required for first initialization"
            )
            cls._instance = cls(database_url)

        return cls._instance

    def __init__(self, database_url: str):
        self._database_url = database_url
        self._engine = None

        self.session_connection = None
        self.session = None

    # TODO why is this type not reimported?
    def get_engine(self) -> Engine:
        if not self._engine:
            self._engine = create_engine(
                self._database_url,
                json_serializer=_serialize_pydantic_model,
                echo=config("ACTIVEMODEL_LOG_SQL", cast=bool, default=False),
                # https://docs.sqlalchemy.org/en/20/core/pooling.html#disconnect-handling-pessimistic
                pool_pre_ping=True,
                # some implementations include `future=True` but it's not required anymore
            )

        return self._engine

    def get_session(self):
        if self.session:

            @contextlib.contextmanager
            def _fake():
                assert self.session
                yield self.session

            return _fake()

        if self.session_connection:
            return Session(bind=self.session_connection)

        return Session(self.get_engine())

    @contextlib.contextmanager
    def global_session(self):
        """
        Context manager that generates a new session and sets it as the
        `session_connection`, restoring it to `None` at the end.
        """

        # Generate a new connection and set it as the session_connection
        with self.get_session() as session:
            self.session = session

            try:
                yield
            finally:
                self.session = None


def init(database_url: str):
    return SessionManager.get_instance(database_url)


def get_engine():
    return SessionManager.get_instance().get_engine()


def get_session():
    return SessionManager.get_instance().get_session()


def global_session():
    with SessionManager.get_instance().global_session():
        yield
