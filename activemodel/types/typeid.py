"""
Lifted from: https://github.com/akhundMurad/typeid-python/blob/main/examples/sqlalchemy.py
"""

from typing import Optional
from uuid import UUID

from pydantic import (
    GetJsonSchemaHandler,
)
from pydantic_core import CoreSchema, core_schema
from sqlalchemy import types
from sqlalchemy.util import generic_repr
from typeid import TypeID

from activemodel.errors import TypeIDValidationError


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

        if value is None:
            return None

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
                if value.prefix is None:
                    raise TypeIDValidationError(
                        "Must have a valid prefix set on the class"
                    )
            else:
                if value.prefix != self.prefix:
                    raise TypeIDValidationError(
                        f"Expected '{self.prefix}' but got '{value.prefix}'"
                    )

            return value.uuid

        raise ValueError("Unexpected input type")

    def process_result_value(self, value, dialect):
        if value is None:
            return None

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

        from_uuid_schema = core_schema.chain_schema(
            [
                # TODO not sure how this is different from the UUID schema, should try it  out.
                # core_schema.is_instance_schema(TypeID),
                # core_schema.uuid_schema(),
                core_schema.no_info_plain_validator_function(
                    TypeID.from_string,
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
                lambda x: str(x)
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: CoreSchema, handler: GetJsonSchemaHandler
    ):
        """
        Called when generating the openapi schema. This overrides the `function-plain` type which
        is generated by the `no_info_plain_validator_function`.

        This logis seems to be a hot part of the codebase, so I'd expect this to break as pydantic
        fastapi continue to evolve.

        Note that this method can return multiple types. A return value can be as simple as:

        {"type": "string"}

        Or, you could return a more specific JSON schema type:

        core_schema.uuid_schema()

        The problem with using something like uuid_schema is the specifi patterns

        https://github.com/BeanieODM/beanie/blob/2190cd9d1fc047af477d5e6897cc283799f54064/beanie/odm/fields.py#L153
        """

        return {
            "type": "string",
            # TODO implement a more strict pattern in regex
            #      https://github.com/jetify-com/typeid/blob/3d182feed5687c21bb5ab93d5f457ff96749b68b/spec/README.md?plain=1#L38
            # "pattern": "^[0-9a-f]{24}$",
            # "minLength": 24,
            # "maxLength": 24,
        }
