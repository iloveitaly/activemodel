"""
Pydantic v2 support for TypeID.

TODO should push this upstream to the typeid package
"""

from typing import Any

from pydantic import GetCoreSchemaHandler
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
        serialization=core_schema.plain_serializer_function_ser_schema(str),
    )


existing_schema = getattr(TypeID, "__get_pydantic_core_schema__", None)
assert existing_schema is None or existing_schema == get_pydantic_core_schema, (
    "TypeID already has a __get_pydantic_core_schema__, cannot apply patch"
)

TypeID.__get_pydantic_core_schema__ = get_pydantic_core_schema
