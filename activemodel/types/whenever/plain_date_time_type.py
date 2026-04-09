from datetime import datetime

from pydantic import GetJsonSchemaHandler
from pydantic_core import CoreSchema, core_schema
from sqlalchemy import types
from whenever import PlainDateTime


class PlainDateTimeType(types.TypeDecorator):
    """
    SQLAlchemy TypeDecorator for whenever.PlainDateTime.

    Stores as a naive datetime in the database.
    Reconstructs as a PlainDateTime on read.

    This is useful for SQLite and other databases that do not have robust
    timezone-aware datetime support, or for fields that are intentionally meant
    to represent a local wall-clock time without timezone information.

    Usage:
        local_time: PlainDateTime | None = None
    """

    impl = types.DateTime(timezone=False)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value

        if isinstance(value, PlainDateTime):
            return value.to_stdlib()

        raise ValueError(f"Cannot convert {type(value)} to PlainDateTime")

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        return PlainDateTime(value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: object, handler: GetJsonSchemaHandler
    ) -> CoreSchema:
        def validate(value: str | PlainDateTime) -> PlainDateTime:
            if isinstance(value, PlainDateTime):
                return value
            return PlainDateTime.parse_iso(value)

        schema = core_schema.no_info_plain_validator_function(
            validate,
            json_schema_input_schema=core_schema.str_schema(),
        )
        return core_schema.json_or_python_schema(
            json_schema=schema,
            python_schema=core_schema.union_schema([schema]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: v.format_iso()
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: CoreSchema, handler: GetJsonSchemaHandler
    ):
        return {"type": "string", "format": "date-time"}