"""
Lifted from: https://github.com/akhundMurad/typeid-python/blob/main/examples/sqlalchemy.py
"""

from typing import Optional
from uuid import UUID

from pydantic import (
    GetJsonSchemaHandler,
)
from pydantic_core import CoreSchema, core_schema
from typeid import TypeID

from sqlalchemy import types
from sqlalchemy.util import generic_repr


class TypeIDType(types.TypeDecorator):
    """
    A SQLAlchemy TypeDecorator that allows storing TypeIDs in the database.
    The prefix will not be persisted, instead the database-native UUID field will be used.
    At retrieval time a TypeID will be constructed based on the configured prefix and the
    UUID value from the database.

    Usage:
        # will result in TypeIDs such as "user_01h45ytscbebyvny4gc8cr8ma2"
        id = mapped_column(
            TypeIDType("user"),
            primary_key=True,
            default=lambda: TypeID("user")
        )
    """

    impl = types.Uuid
    # impl = uuid.UUID
    cache_ok = True
    prefix: Optional[str] = None

    def __init__(self, prefix: Optional[str], *args, **kwargs):
        self.prefix = prefix
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        # Customize __repr__ to ensure that auto-generated code e.g. from alembic includes
        # the right __init__ params (otherwise by default prefix will be omitted because
        # uuid.__init__ does not have such an argument).
        # TODO this makes it so inspected code does NOT include the suffix
        return generic_repr(
            self,
            to_inspect=TypeID(self.prefix),
        )

    def process_bind_param(self, value, dialect):
        """
        This is run when a search query is built or ...
        """

        if isinstance(value, UUID):
            # then it's a UUID class, such as UUID('01942886-7afc-7129-8f57-db09137ed002')
            return value

        if isinstance(value, str) and value.startswith(self.prefix + "_"):
            # then it's a TypeID such as 'user_01h45ytscbebyvny4gc8cr8ma2'
            value = TypeID.from_string(value)

        if isinstance(value, str):
            # no prefix, raw UUID, let's coerce it into a UUID which SQLAlchemy can handle
            # ex: '01942886-7afc-7129-8f57-db09137ed002'
            return UUID(value)

        if isinstance(value, TypeID):
            # TODO in what case could this None prefix ever occur?
            if self.prefix is None:
                assert value.prefix is None
            else:
                assert value.prefix == self.prefix

            return value.uuid

        raise ValueError("Unexpected input type")

    def process_result_value(self, value, dialect):
        return TypeID.from_uuid(value, self.prefix)

    # def coerce_compared_value(self, op, value):
    #     """
    #     This method is called when SQLAlchemy needs to compare a column to a value.
    #     By returning self, we indicate that this type can handle TypeID instances.
    #     """
    #     if isinstance(value, TypeID):
    #         return self

    #     return super().coerce_compared_value(op, value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> CoreSchema:
        from_uuid_schema = core_schema.chain_schema(
            [
                # core_schema.is_instance_schema(TypeID),
                core_schema.uuid_schema(),
                core_schema.no_info_plain_validator_function(TypeID.from_string),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_uuid_schema,
            python_schema=core_schema.union_schema(
                [
                    from_uuid_schema
                    # core_schema.is_instance_schema(TypeID),
                    # core_schema.str_schema(),
                    # core_schema.no_info_plain_validator_function(TypeID.from_string),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )
