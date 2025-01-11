"""
Class to make managing sessions with SQL Model easy. Also provides a common entrypoint to make it easy to mutate the
database environment when testing.
"""

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
        return json.dumps([m.model_dump() for m in model])
    else:
        return json.dumps(model)


class SessionManager:
    _instance: t.ClassVar[t.Optional["SessionManager"]] = None

    session_connection: Connection | None

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
        if self.session_connection:
            return Session(bind=self.session_connection)

        return Session(self.get_engine())


def init(database_url: str):
    return SessionManager.get_instance(database_url)


def get_engine():
    return SessionManager.get_instance().get_engine()


def get_session():
    return SessionManager.get_instance().get_session()
