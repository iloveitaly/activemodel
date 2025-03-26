import json
import typing as t
from uuid import UUID

import pydash
import sqlalchemy as sa
from sqlalchemy.orm.attributes import flag_modified as sa_flag_modified
from sqlalchemy.orm.base import instance_state
import sqlmodel as sm
from sqlalchemy import Connection, event
from sqlalchemy.orm import Mapper, declared_attr
from sqlmodel import Column, Field, Session, SQLModel, inspect, select
from typeid import TypeID

from activemodel.mixins.pydantic_json import PydanticJSONMixin

# NOTE: this patches a core method in sqlmodel to support db comments
from . import get_column_from_field_patch  # noqa: F401
from .logger import logger
from .query_wrapper import QueryWrapper
from .session_manager import get_session

POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}
"""
By default, the foreign key naming convention in sqlalchemy do not create unique identifiers when there are multiple
foreign keys in a table. This naming convention is a workaround to fix this issue:

- https://github.com/zhanymkanov/fastapi-best-practices?tab=readme-ov-file#set-db-keys-naming-conventions
- https://github.com/fastapi/sqlmodel/discussions/1213
- Implementation lifted from: https://github.com/AlexanderZharyuk/billing-service/blob/3c8aaf19ab7546b97cc4db76f60335edec9fc79d/src/models.py#L24
"""

SQLModel.metadata.naming_convention = POSTGRES_INDEXES_NAMING_CONVENTION


class BaseModel(SQLModel):
    """
    Base model class to inherit from so we can hate python less

    https://github.com/woofz/sqlmodel-basecrud/blob/main/sqlmodel_basecrud/basecrud.py

    - {before,after} lifecycle hooks are modeled after Rails.
    - class docstrings are converd to table-level comments
    - save(), delete(), select(), where(), and other easy methods you would expect
    - Fixes foreign key naming conventions
    """

    # this is used for table-level comments
    __table_args__ = None

    @classmethod
    def __init_subclass__(cls, **kwargs):
        "Setup automatic sqlalchemy lifecycle events for the class"

        super().__init_subclass__(**kwargs)

        from sqlmodel._compat import set_config_value

        # enables field-level docstrings on the pydanatic `description` field, which we then copy into
        # sa_args, which is persisted to sql table comments
        set_config_value(model=cls, parameter="use_attribute_docstrings", value=True)

        cls._apply_class_doc()

        def event_wrapper(method_name: str):
            """
            This does smart heavy lifting for us to make sqlalchemy lifecycle events nicer to work with:

            * Passes the target first to the lifecycle method, so it feels like an instance method
            * Allows as little as a single positional argument, so methods can be simple
            * Removes the need for decorators or anything fancy on the subclass
            """

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

        # def foreign_key()
        # table.id

    @classmethod
    def _apply_class_doc(cls):
        """
        Pull class-level docstring into a table comment.

        This will help AI SQL writers like: https://github.com/iloveitaly/sql-ai-prompt-generator
        """

        doc = cls.__doc__.strip() if cls.__doc__ else None

        if doc:
            table_args = getattr(cls, "__table_args__", None)

            if table_args is None:
                cls.__table_args__ = {"comment": doc}
            elif isinstance(table_args, dict):
                table_args.setdefault("comment", doc)
            else:
                raise ValueError("Unexpected __table_args__ type")

    # TODO no type check decorator here
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Automatically generates the table name for the model by converting the class name from camel case to snake case.
        This is the recommended format for table names:

        https://wiki.postgresql.org/wiki/Don%27t_Do_This#Don.27t_use_upper_case_table_or_column_names

        By default, the class is lower cased which makes it harder to read.

        Many snake_case libraries struggle with snake case for names like LLMCache, which is why we are using a more
        complicated implementation from pydash.

        https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
        """
        return pydash.strings.snake_case(cls.__name__)

    @classmethod
    def foreign_key(cls, **kwargs):
        """
        Returns a `Field` object referencing the foreign key of the model.

        >>> other_model_id: int
        >>> other_model = OtherModel.foreign_key()
        """

        field_options = {"nullable": False} | kwargs

        return Field(
            # TODO id field is hard coded, should pick the PK field in case it's different
            sa_type=cls.model_fields["id"].sa_column.type,  # type: ignore
            foreign_key=f"{cls.__tablename__}.id",
            **field_options,
        )

    @classmethod
    def select(cls, *args):
        "create a query wrapper to easily run sqlmodel queries on this model"
        return QueryWrapper[cls](cls, *args)

    @classmethod
    def where(cls, *args):
        "convenience method to avoid having to write .select().where() in order to add conditions"
        return cls.select().where(*args)

    def delete(self):
        with get_session() as session:
            if old_session := Session.object_session(self):
                old_session.expunge(self)

            session.delete(self)
            session.commit()
            return True

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

            # Only call the transform method if the class is a subclass of PydanticJSONMixin
            if issubclass(self.__class__, PydanticJSONMixin):
                self.__class__.__transform_dict_to_pydantic__(self)

        return self

    def refresh(self):
        "Refreshes an object from the database"

        with get_session() as session:
            if (
                old_session := Session.object_session(self)
            ) and old_session is not session:
                old_session.expunge(self)

            session.add(self)
            session.refresh(self)

            # Only call the transform method if the class is a subclass of PydanticJSONMixin
            if issubclass(self.__class__, PydanticJSONMixin):
                self.__class__.__transform_dict_to_pydantic__(self)

        return self

    # TODO shouldn't this be handled by pydantic?
    # TODO where is this actually used? shoudl prob remove this
    def json(self, **kwargs):
        return json.dumps(self.dict(), default=str, **kwargs)

    # TODO should move this to the wrapper
    @classmethod
    def count(cls) -> int:
        """
        Returns the number of records in the database.
        """
        with get_session() as session:
            return session.scalar(sm.select(sm.func.count()).select_from(cls))

    # TODO got to be a better way to fwd these along...
    @classmethod
    def first(cls):
        return cls.select().first()

    # TODO throw an error if this field is set on the model
    def is_new(self) -> bool:
        return not self._sa_instance_state.has_identity

    def flag_modified(self, *args: str):
        """
        Flag one or more fields as modified. Useful for marking a field containing sub-objects as modified.

        Will throw an error if an invalid field is passed.
        """

        assert len(args) > 0, "Must pass at least one field name"

        for field_name in args:
            if field_name not in self.__fields__:
                raise ValueError(f"Field '{field_name}' does not exist in the model.")

            # check if the field exists
            sa_flag_modified(self, field_name)

    def modified_fields(self) -> set[str]:
        "set of fields that are modified"

        insp = inspect(self)

        return {attr.key for attr in insp.attrs if attr.history.has_changes()}

    @classmethod
    def find_or_create_by(cls, **kwargs):
        """
        Find record or create it with the passed args if it doesn't exist.
        """

        result = cls.get(**kwargs)

        if result:
            return result

        new_model = cls(**kwargs)
        new_model.save()

        return new_model

    @classmethod
    def find_or_initialize_by(cls, **kwargs):
        """
        Unfortunately, unlike ruby, python does not have a great lambda story. This makes writing convenience methods
        like this a bit more difficult.
        """

        result = cls.get(**kwargs)

        if result:
            return result

        new_model = cls(**kwargs)
        return new_model

    @classmethod
    def primary_key_column(cls) -> Column:
        """
        Returns the primary key column of the model by inspecting SQLAlchemy field information.

        >>> ExampleModel.primary_key_field().name
        """

        # TODO note_schema.__class__.__table__.primary_key
        # TODO no reason why this couldn't be cached

        pk_columns = list(cls.__table__.primary_key.columns)

        if not pk_columns:
            raise ValueError("No primary key defined for the model.")

        if len(pk_columns) > 1:
            raise ValueError(
                "Multiple primary keys defined. This method supports only single primary key models."
            )

        return pk_columns[0]

    # TODO what's super dangerous here is you pass a kwarg which does not map to a specific
    #      field it will result in `True`, which will return all records, and not give you any typing
    #      errors. Dangerous when iterating on structure quickly
    # TODO can we pass the generic of the superclass in?
    # TODO can we type the method signature a bit better?
    # def get(cls, *args: sa.BinaryExpression, **kwargs: t.Any):
    @classmethod
    def get(cls, *args: t.Any, **kwargs: t.Any):
        """
        Gets a single record (or None) from the database. Pass an PK ID or kwargs to filter by.
        """
        # TODO id is hardcoded, not good! Need to dynamically pick the best uid field
        id_field_name = "id"

        # special case for getting by ID
        if len(args) == 1 and isinstance(args[0], (int, TypeID, str, UUID)):
            kwargs[id_field_name] = args[0]
            args = ()

        statement = select(cls).filter(*args).filter_by(**kwargs)

        with get_session() as session:
            return session.exec(statement).first()

    @classmethod
    def one(cls, *args: t.Any, **kwargs: t.Any):
        """
        Gets a single record from the database. Pass an PK ID or a kwarg to filter by.
        """

        args, kwargs = cls.__process_filter_args__(*args, **kwargs)
        statement = select(cls).filter(*args).filter_by(**kwargs)

        with get_session() as session:
            return session.exec(statement).one()

    @classmethod
    def __process_filter_args__(cls, *args: t.Any, **kwargs: t.Any):
        """
        Helper method to process filter arguments and implement some nice DX for our devs.
        """

        id_field_name = cls.primary_key_column().name

        # special case for getting by ID without having to specify the field name
        # TODO should dynamically add new pk types based on column definition
        if len(args) == 1 and isinstance(args[0], (int, TypeID, str, UUID)):
            kwargs[id_field_name] = args[0]
            args = ()

        return args, kwargs

    @classmethod
    def all(cls):
        "get a generator for all records in the database"
        with get_session() as session:
            results = session.exec(sm.select(cls))

            # TODO do we need this or can we just return results?
            for result in results:
                yield result

    @classmethod
    def sample(cls):
        """
        Pick a random record from the database. Raises if none exist.

        Helpful for testing and console debugging.
        """

        query = sm.select(cls).order_by(sa.sql.func.random()).limit(1)

        with get_session() as session:
            return session.exec(query).one()
