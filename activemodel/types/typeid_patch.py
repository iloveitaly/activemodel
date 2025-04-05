import importlib.util
from typing import Any


from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema

from typeid import TypeID


def patch_typeid_for_pydantic():
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.union_schema(
            [
                core_schema.str_schema(),
                # Accepts TypeID instances
                core_schema.is_instance_schema(cls),
            ],
            # this infers the json schema type for us
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

    TypeID.__get_pydantic_core_schema__ = __get_pydantic_core_schema__


patch_typeid_for_pydantic()
