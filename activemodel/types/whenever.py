from datetime import datetime

from pydantic import GetJsonSchemaHandler
from pydantic_core import CoreSchema, core_schema
from sqlalchemy import types
from whenever import Instant, ZonedDateTime


class InstantType(types.TypeDecorator):
    """
    SQLAlchemy TypeDecorator for whenever.Instant.

    Stores as a timezone-aware datetime in the database (UTC).
    Reconstructs as an Instant on read.

    Usage:
        created_at: Instant | None = None
    """

    impl = types.DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, Instant):
            return value.py_datetime()
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return Instant.parse_iso(value).py_datetime()
        raise ValueError(f"Cannot convert {type(value)} to Instant")

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return Instant.from_py_datetime(value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: object, handler: GetJsonSchemaHandler
    ) -> CoreSchema:
        def validate(value: str | Instant) -> Instant:
            if isinstance(value, Instant):
                return value
            return Instant.parse_iso(value)

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


class ZonedDateTimeType(types.TypeDecorator):
    """
    SQLAlchemy TypeDecorator for whenever.ZonedDateTime.

    Stores as a timezone-aware datetime in the database. Note that the IANA
    timezone name is not preserved — the DB stores the UTC offset at the time
    of writing. On read, the value is reconstructed as a ZonedDateTime, but
    the timezone will be a fixed-offset zone rather than the original IANA name.

    Usage:
        scheduled_at: ZonedDateTime | None = None
    """

    impl = types.DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, ZonedDateTime):
            return value.py_datetime()
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return ZonedDateTime.parse_iso(value).py_datetime()
        raise ValueError(f"Cannot convert {type(value)} to ZonedDateTime")

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return ZonedDateTime.from_py_datetime(value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: object, handler: GetJsonSchemaHandler
    ) -> CoreSchema:
        def validate(value: str | ZonedDateTime) -> ZonedDateTime:
            if isinstance(value, ZonedDateTime):
                return value
            return ZonedDateTime.parse_iso(value)

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
