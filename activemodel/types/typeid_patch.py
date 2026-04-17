"""
Add pydantic v2 support for TypeID.

* The TypeID package has a `TypeIDField[Literal["prefix"]]` support, but this is not a subclass of TypeID
  which causes errors when a TypeID object is assigned to a field of that type.
* `TypeIDField` generates a unique type and embeds the prefix in the type, which is how how the instance of the object
  can validate incoming strs as having the correct prefix.
* This isn't exactly required in our case since the prefix validation is handled within the SQLAlchemy type adapter.
* However,

"""

from typing import Any

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema
from typeid import TypeID


@classmethod
def get_pydantic_core_schema(
    cls: type[TypeID], source_type: Any, handler: GetCoreSchemaHandler
) -> CoreSchema:
    def validate(value: Any) -> TypeID:
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return TypeID.from_string(value)
        raise TypeError(f"TypeID must be str or TypeID, got {type(value).__name__}")

    return core_schema.no_info_plain_validator_function(
        validate,
        json_schema_input_schema=core_schema.str_schema(),
        serialization=core_schema.plain_serializer_function_ser_schema(
            str, when_used="json"
        ),
    )


@classmethod
def get_pydantic_json_schema(
    cls: type[TypeID], core_schema_: CoreSchema, handler: GetJsonSchemaHandler
) -> JsonSchemaValue:
    schema = handler(core_schema_.get("json_schema_input_schema", core_schema_))
    schema.update(
        {
            "type": "string",
            "format": "typeid",
        }
    )
    return schema


existing_schema = getattr(TypeID, "__get_pydantic_core_schema__", None)
assert existing_schema is None or existing_schema == get_pydantic_core_schema, (
    "TypeID already has a __get_pydantic_core_schema__, cannot apply patch"
)

TypeID.__get_pydantic_core_schema__ = get_pydantic_core_schema
TypeID.__get_pydantic_json_schema__ = get_pydantic_json_schema
