import datetime

from pydantic import GetJsonSchemaHandler
from pydantic_core import CoreSchema, core_schema
from sqlalchemy import types
from whenever import Date


# Lifted from https://github.com/ariebovenberg/whenever-sqlalchemy/blob/main/src/whenever_sqlalchemy/__init__.py
class DateType(types.TypeDecorator):
    """
    SQLAlchemy TypeDecorator for whenever.Date.

    Stores as a DATE column. Reconstructs as a Date on read.

    Usage:
        birthday: Date | None = None
    """

    impl = types.Date()
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, datetime.date):
            return value

        if isinstance(value, Date):
            return value.to_stdlib()

        raise ValueError(f"Cannot convert {type(value)} to Date")

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        return Date(value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: object, handler: GetJsonSchemaHandler
    ) -> CoreSchema:
        def validate(value: str | Date) -> Date:
            if isinstance(value, Date):
                return value
            return Date.parse_iso(value)

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
        return {"type": "string", "format": "date"}
