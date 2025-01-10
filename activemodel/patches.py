from pydantic import (
    GetJsonSchemaHandler,
    WithJsonSchema,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema
from typeid import TypeID


def typeid__get_pydantic_core_schema__(
    cls, _source_type: type[TypeID], _handler: WithJsonSchema
) -> CoreSchema:
    """
    'Unable to serialize unknown type'

    https://github.com/karma-dev-team/karma-system/blob/ee0c1a06ab2cb7aaca6dc4818312e68c5c623365/app/server/value_objects/steam_id.py#L88
    https://github.com/hhimanshu/uv-workspaces/blob/main/packages/api/src/_lib/dto/typeid_field.py
    https://github.com/karma-dev-team/karma-system/blob/ee0c1a06ab2cb7aaca6dc4818312e68c5c623365/app/base/typeid/type_id.py#L14
    https://github.com/pydantic/pydantic/issues/10060
    """

    from_uuid_schema = core_schema.chain_schema(
        [
            # core_schema.is_instance_schema(TypeID),
            core_schema.str_schema(),
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


def typeid__get_pydantic_json_schema__(
    cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
) -> JsonSchemaValue:
    return handler(core_schema.str_schema())
    return handler(core_schema.uuid_schema())


# Monkey-patch the TypeID class
TypeID.__get_pydantic_core_schema__ = classmethod(typeid__get_pydantic_core_schema__)
# TypeID.__get_pydantic_json_schema__ = classmethod(typeid__get_pydantic_json_schema__)

# https://github.com/fastapi/fastapi/discussions/10027
# https://github.com/hhimanshu/uv-workspaces/blob/main/packages/api/src/_lib/dto/typeid_field.py
# https://github.com/alice-biometrics/petisco/blob/b01ef1b84949d156f73919e126ed77aa8e0b48dd/petisco/base/domain/model/uuid.py#L50
