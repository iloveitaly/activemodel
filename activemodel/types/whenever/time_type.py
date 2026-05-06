import datetime

from pydantic import GetJsonSchemaHandler
from pydantic_core import CoreSchema, core_schema
from sqlalchemy import types
from whenever import Time


# Lifted from https://github.com/ariebovenberg/whenever-sqlalchemy/blob/main/src/whenever_sqlalchemy/__init__.py
class TimeType(types.TypeDecorator):
    """
    SQLAlchemy TypeDecorator for whenever.Time.

    Stores as a TIME column. Nanoseconds are truncated to microseconds on storage.
    Reconstructs as a Time on read.

    Usage:
        alarm_time: Time | None = None
    """

    impl = types.Time()
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, datetime.time):
            return value

        if isinstance(value, Time):
            return value.to_stdlib()

        raise ValueError(f"Cannot convert {type(value)} to Time")

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        return Time(value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: object, handler: GetJsonSchemaHandler
    ) -> CoreSchema:
        def validate(value: str | Time) -> Time:
            if isinstance(value, Time):
                return value
            return Time.parse_iso(value)

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
        return {"type": "string", "format": "time"}
