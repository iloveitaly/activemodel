import json
import typing as t

import pydash
import sqlalchemy as sa
import sqlmodel as sm
from sqlalchemy.orm import declared_attr
from sqlmodel import Session, SQLModel, select
from typeid import TypeID

from .query_wrapper import QueryWrapper
from .session_manager import get_session


class BaseModel(SQLModel):
    """
    Base model class to inherit from so we can hate python less

    https://github.com/woofz/sqlmodel-basecrud/blob/main/sqlmodel_basecrud/basecrud.py

    {before,after} hooks are modeled after Rails.
    """

    # TODO implement actually calling these hooks

    def before_delete(self):
        pass

    def after_delete(self):
        pass

    def before_update(self):
        pass

    def after_update(self):
        pass

    def before_create(self):
        pass

    def after_create(self):
        pass

    def before_save(self):
        pass

    def after_save(self):
        pass

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

            self.before_update()
            self.before_save()

            # breakpoint()
            # self.before_save()

            session.add(self)
            session.commit()
            session.refresh(self)

        self.after_update()
        self.after_save()
        # self.after_create()

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
