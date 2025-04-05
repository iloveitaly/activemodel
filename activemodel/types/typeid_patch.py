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


TypeID.__get_pydantic_core_schema__ = get_pydantic_core_schema
