"""
A SQLAlchemy TypeDecorator for storing TypeIDs in the database as native UUID fields, with the prefix handled in Python.

Adapted from:

https://github.com/akhundMurad/typeid-python/blob/main/examples/sqlalchemy.py
"""

from typing import Any, Self
from uuid import UUID

import uuid_utils
from pydantic import (
    GetJsonSchemaHandler,
)
from pydantic_core import CoreSchema, core_schema
from sqlalchemy import types
from sqlmodel import Column, Field
from typeid import TypeID, typeid_factory

from activemodel.errors import TypeIDValidationError

# global list of prefixes to ensure uniqueness
# NOTE this will cause issues on code reloads
_prefixes: list[str] = []


class TypeIDType(types.TypeDecorator):
    """
    A SQLAlchemy TypeDecorator that allows storing TypeIDs in the database.

    The prefix will not be persisted to the database, instead the database-native UUID field will be used.
    At retrieval time a TypeID will be constructed (in python) based on the configured prefix and the UUID
    value from the database.

    For example:

    >>> id = mapped_column(
    >>>     TypeIDType("user"),
    >>>     primary_key=True,
    >>>     default=lambda: TypeID("user")
    >>> )

    Will result in TypeIDs such as "user_01h45ytscbebyvny4gc8cr8ma2". There's a mixin provided to make it easy
    to add a `id` pk field to your model with a specific prefix.
    """

    # impl must be a SQLAlchemy type that represents a primitive data type to use as the database storage type?
    impl = types.Uuid
    cache_ok = True

    prefix: str | None

    def __init__(self, prefix: str | None, *args, _raw: bool = False, **kwargs):
        if _raw:
            assert prefix is None
        else:
            assert prefix is not None

        self.prefix = prefix
        super().__init__(*args, **kwargs)

    @classmethod
    def raw(cls) -> Self:
        return cls(prefix=None, _raw=True)

    def __repr__(self) -> str:
        # Customize __repr__ to ensure that auto-generated code e.g. from alembic includes
        # the right __init__ params (otherwise by default prefix will be omitted because
        # uuid.__init__ does not have such an argument).
        # TODO this makes it so inspected code does NOT include the suffix
        if self.prefix is None:
            return "TypeIDType.raw()"

        return f"TypeIDType({self.prefix!r})"

    def process_bind_param(self, value, dialect):
        """
        This is run when a search query is built or ...
        """

        if value is None:
            return None

        # then it's a stdlib UUID class, such as UUID('01942886-7afc-7129-8f57-db09137ed002')
        if isinstance(value, UUID):
            return value

        # TODO we should be able to register the custom UUID type into pyscog to avoid conversion here
        if isinstance(value, uuid_utils.UUID):
            # uuid_utils.UUID (from typeid-python) is not a stdlib uuid.UUID, psycopg needs stdlib UUID
            return UUID(bytes=value.bytes)

        if isinstance(value, str) and "_" in value:
            # then it's a TypeID such as 'user_01h45ytscbebyvny4gc8cr8ma2'
            value = TypeID.from_string(value)

        if isinstance(value, str):
            # no prefix, raw UUID, let's coerce it into a UUID which SQLAlchemy can handle
            # ex: '01942886-7afc-7129-8f57-db09137ed002'
            # if an invalid uuid is passed, `ValueError('badly formed hexadecimal UUID string')` will be raised
            return UUID(value)

        if isinstance(value, TypeID):
            if self.prefix is None:
                return UUID(bytes=value.uuid.bytes)

            if value.prefix != self.prefix:
                raise TypeIDValidationError(
                    f"Expected '{self.prefix}' but got '{value.prefix}'"
                )

            # always returns a uuid_utils.UUID, which we need to convert
            # TODO should be able to register a custom type in psycopg to avoid this conversion
            return UUID(bytes=value.uuid.bytes)

        raise ValueError("Unexpected input type")

    def process_result_value(self, value, dialect):
        "convert a raw UUID, without a prefix, to a TypeID with the correct prefix"

        if value is None:
            return None

        if self.prefix is None:
            return value

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
        """
        This fixes the following error: 'Unable to serialize unknown type' by telling pydantic how to serialize this field.

        Note that TypeIDType MUST be the type of the field in SQLModel otherwise you'll get serialization errors.
        This is done automatically for the mixin but for any relationship fields you'll need to specify the type explicitly.

        - https://github.com/karma-dev-team/karma-system/blob/ee0c1a06ab2cb7aaca6dc4818312e68c5c623365/app/server/value_objects/steam_id.py#L88
        - https://github.com/hhimanshu/uv-workspaces/blob/main/packages/api/src/_lib/dto/typeid_field.py
        - https://github.com/karma-dev-team/karma-system/blob/ee0c1a06ab2cb7aaca6dc4818312e68c5c623365/app/base/typeid/type_id.py#L14
        - https://github.com/pydantic/pydantic/issues/10060
        - https://github.com/fastapi/fastapi/discussions/10027
        - https://github.com/alice-biometrics/petisco/blob/b01ef1b84949d156f73919e126ed77aa8e0b48dd/petisco/base/domain/model/uuid.py#L50
        """

        def convert_from_string(value: str | TypeID) -> TypeID:
            if isinstance(value, TypeID):
                return value

            return TypeID.from_string(value)

        from_uuid_schema = core_schema.chain_schema(
            [
                # TODO not sure how this is different from the UUID schema, should try it  out.
                # core_schema.is_instance_schema(TypeID),
                # core_schema.uuid_schema(),
                core_schema.no_info_plain_validator_function(
                    convert_from_string,
                    json_schema_input_schema=core_schema.str_schema(),
                ),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_uuid_schema,
            # TODO in the the future we could add more exact types
            # metadata=core_schema.str_schema(
            #     pattern="^[0-9a-f]{24}$",
            #     min_length=24,
            #     max_length=24,
            # ),
            # metadata={
            #     "pydantic_js_input_core_schema": core_schema.str_schema(
            #         pattern="^[0-9a-f]{24}$",
            #         min_length=24,
            #         max_length=24,
            #     )
            # },
            python_schema=core_schema.union_schema([from_uuid_schema]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                str, when_used="json"
            ),
        )

    # TODO I have a feeling that the `serialization` param in the above method solves this for us.
    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: CoreSchema, handler: GetJsonSchemaHandler
    ):
        """
        Called when generating the openapi schema. This overrides the `function-plain` type which
        is generated by the `no_info_plain_validator_function`.

        This logic seems to be a hot part of the codebase, so I'd expect this to break as pydantic
        fastapi continue to evolve.

        Note that this method can return multiple types. A return value can be as simple as:

        >>> {"type": "string"}

        Or, you could return a more specific JSON schema type:

        >>> core_schema.uuid_schema()

        The problem with using something like uuid_schema is the specific patterns

        https://github.com/BeanieODM/beanie/blob/2190cd9d1fc047af477d5e6897cc283799f54064/beanie/odm/fields.py#L153
        """

        return {
            "type": "string",
            "format": "typeid",
            # TODO implement a more strict pattern in regex
            #      https://github.com/jetify-com/typeid/blob/3d182feed5687c21bb5ab93d5f457ff96749b68b/spec/README.md?plain=1#L38
            # "pattern": "^[0-9a-f]{24}$",
            # "minLength": 24,
            # "maxLength": 24,
        }


def TypeIDPrimaryKey(prefix: str) -> Any:
    """
    Field factory for the declarative form:

        id: TypeIDField[Literal["user"]] = TypeIDPrimaryKey("user")

    Use this when you want static type-checking of the prefix.

    Returns Any so that type checkers accept it as a default value for any
    annotation (e.g. TypeIDField[Literal["user"]]), matching the same pattern
    used by pydantic's own Field() factory.

    Returns Any (not TypeID) because Pydantic discovers fields via __annotations__ at class creation —
    the annotation is required for field registration, so the return type cannot replace it.
    """

    # make sure duplicate prefixes are not used!
    # NOTE this will cause issues on code reloads

    assert prefix
    assert prefix not in _prefixes, (
        f"TypeID prefix '{prefix}' already exists, pick a different one"
    )

    ret = Field(
        sa_column=Column(
            TypeIDType(prefix),
            primary_key=True,
            nullable=False,
            # default on the sa_column level ensures that an ID is generated when creating a new record, even when
            # raw SQLAlchemy operations are used instead of activemodel operations
            default=typeid_factory(prefix),
        ),
        description=f"TypeID with prefix: {prefix}",
    )

    _prefixes.append(prefix)

    return ret
