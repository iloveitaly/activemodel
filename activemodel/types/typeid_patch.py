"""
Pydantic v2 support for TypeID.

TODO should push this upstream to the typeid package
"""

from typing import Any, Type

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema
from typeid import TypeID


@classmethod
def get_pydantic_core_schema(
    cls: Type[TypeID], source_type: Any, handler: GetCoreSchemaHandler
) -> CoreSchema:
    return core_schema.union_schema(
        [
            core_schema.str_schema(),
            core_schema.is_instance_schema(cls),
        ],
        serialization=core_schema.plain_serializer_function_ser_schema(str),
    )


existing_schema = getattr(TypeID, "__get_pydantic_core_schema__", None)
assert existing_schema is None or existing_schema == get_pydantic_core_schema, (
    "TypeID already has a __get_pydantic_core_schema__, cannot apply patch"
)

TypeID.__get_pydantic_core_schema__ = get_pydantic_core_schema
