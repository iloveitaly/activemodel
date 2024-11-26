import json
import typing as t

import pydash
import sqlalchemy as sa
import sqlmodel as sm
from sqlalchemy import Connection, event
from sqlalchemy.orm import Mapper, declared_attr
from sqlmodel import Session, SQLModel, select
from typeid import TypeID

from .logger import logger
from .query_wrapper import QueryWrapper
from .session_manager import get_session


# TODO this does not seem to work with the latest 2.9.x pydantic and sqlmodel
# https://github.com/SE-Sustainability-OSS/ecodev-core/blob/main/ecodev_core/sqlmodel_utils.py
class SQLModelWithValidation(SQLModel):
    """
    Helper class to ease validation in SQLModel classes with table=True
    """

    @classmethod
    def create(cls, **kwargs):
        """
        Forces validation to take place, even for SQLModel classes with table=True
        """
        return cls(**cls.__bases__[0](**kwargs).model_dump())


class BaseModel(SQLModel):
    """
    Base model class to inherit from so we can hate python less

    https://github.com/woofz/sqlmodel-basecrud/blob/main/sqlmodel_basecrud/basecrud.py

    {before,after} hooks are modeled after Rails.
    """

    # TODO implement actually calling these hooks

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        def event_wrapper(method_name: str):
            def wrapper(mapper: Mapper, connection: Connection, target: BaseModel):
                if hasattr(cls, method_name):
                    method = getattr(cls, method_name)

                    if callable(method):
                        arg_count = method.__code__.co_argcount

                        if arg_count == 1:  # Just self/cls
                            method(target)
                        elif arg_count == 2:  # Self, mapper
                            method(target, mapper)
                        elif arg_count == 3:  # Full signature
                            method(target, mapper, connection)
                        else:
                            raise TypeError(
                                f"Method {method_name} must accept either 1 to 3 arguments, got {arg_count}"
                            )
                    else:
                        logger.warning(
                            "SQLModel lifecycle hook found, but not callable hook_name=%s",
                            method_name,
                        )

            return wrapper

        event.listen(cls, "before_insert", event_wrapper("before_insert"))
        event.listen(cls, "before_update", event_wrapper("before_update"))

        # before_save maps to two type of events
        event.listen(cls, "before_insert", event_wrapper("before_save"))
        event.listen(cls, "before_update", event_wrapper("before_save"))

        # now, let's handle after_* variants
        event.listen(cls, "after_insert", event_wrapper("after_insert"))
        event.listen(cls, "after_update", event_wrapper("after_update"))

        # after_save maps to two type of events
        event.listen(cls, "after_insert", event_wrapper("after_save"))
        event.listen(cls, "after_update", event_wrapper("after_save"))

    # TODO no type check decorator here
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Automatically generates the table name for the model by converting the class name from camel case to snake case.

        By default, the class is lower cased which makes it harder to read.

        Many snake_case libraries struggle with snake case for names like LLMCache, which is why we are using a more
        complicated implementation from pydash.

        https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
        """
        return pydash.strings.snake_case(cls.__name__)

    @classmethod
    def select(cls, *args):
        return QueryWrapper[cls](cls, *args)

    def save(self):
        with get_session() as session:
            if old_session := Session.object_session(self):
                # I was running into an issue where the object was already
                # associated with a session, but the session had been closed,
                # to get around this, you need to remove it from the old one,
                # then add it to the new one (below)
                old_session.expunge(self)

            session.add(self)
            # NOTE very important method! This triggers sqlalchemy lifecycle hooks automatically
            session.commit()
            session.refresh(self)

        return self

        # except IntegrityError:
        #     log.quiet(f"{self} already exists in the database.")
        #     session.rollback()

    # TODO shouldn't this be handled by pydantic?
    def json(self, **kwargs):
        return json.dumps(self.dict(), default=str, **kwargs)

    # TODO should move this to the wrapper
    @classmethod
    def count(cls) -> int:
        """
        Returns the number of records in the database.
        """
        return get_session().exec(sm.select(sm.func.count()).select_from(cls)).one()

    # TODO what's super dangerous here is you pass a kwarg which does not map to a specific
    #      field it will result in `True`, which will return all records, and not give you any typing
    #      errors. Dangerous when iterating on structure quickly
    # TODO can we pass the generic of the superclass in?
    @classmethod
    def get(cls, *args: sa.BinaryExpression, **kwargs: t.Any):
        """
        Gets a single record from the database. Pass an PK ID or a kwarg to filter by.
        """

        # special case for getting by ID
        if len(args) == 1 and isinstance(args[0], int):
            # TODO id is hardcoded, not good! Need to dynamically pick the best uid field
            kwargs["id"] = args[0]
            args = []
        elif len(args) == 1 and isinstance(args[0], TypeID):
            kwargs["id"] = args[0]
            args = []

        statement = select(cls).filter(*args).filter_by(**kwargs)
        return get_session().exec(statement).first()

    @classmethod
    def all(cls):
        with get_session() as session:
            results = session.exec(sa.sql.select(cls))

            # TODO do we need this or can we just return results?
            for result in results:
                yield result

    @classmethod
    def sample(cls):
        """
        Pick a random record from the database.

        Helpful for testing and console debugging.
        """

        query = sql.select(cls).order_by(sql.func.random()).limit(1)

        with get_session() as session:
            return session.exec(query).one()
