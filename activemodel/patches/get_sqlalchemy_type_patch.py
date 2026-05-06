"""
Extends SQLModel's get_sqlalchemy_type to recognize whenever datetime types.

This allows using whenever.Instant, whenever.PlainDateTime, and
whenever.ZonedDateTime as bare field type annotations without needing to
specify sa_type= explicitly:

    class MyModel(BaseModel, table=True):
        created_at: whenever.Instant | None = None
        local_time: whenever.PlainDateTime | None = None
        scheduled_at: whenever.ZonedDateTime | None = None

We also update SQLModel's default_registry.type_annotation_map so that plain
SQLAlchemy DeclarativeBase models sharing the same registry get the same
automatic type resolution.
"""

import sqlmodel
from sqlmodel.main import get_sqlalchemy_type as _original_get_sqlalchemy_type
from whenever import Date, Instant, PlainDateTime, Time, ZonedDateTime

from activemodel.types.whenever import (
    DateType,
    InstantType,
    PlainDateTimeType,
    TimeType,
    ZonedDateTimeType,
)
from activemodel.utils import hash_function_code

# https://github.com/fastapi/sqlmodel/blob/5c2dbe419edc2d15200eee5269c9508987944ed8/sqlmodel/main.py#L691
assert (
    hash_function_code(sqlmodel.main.get_sqlalchemy_type)
    == "ac1225457303bb04a41d72382161914047b03891b76a427bdcc6668af5570933"
), (
    f"get_sqlalchemy_type has changed, please verify the patch is still valid: {hash_function_code(sqlmodel.main.get_sqlalchemy_type)}"
)


def get_sqlalchemy_type(field):  # type: ignore[misc]
    # Only inspect the type if it can be extracted cleanly — if it raises
    # (e.g. non-optional union), fall through to the original which will
    # also raise with a proper error message.
    try:
        from sqlmodel.main import (
            get_sa_type_from_field,  # type: ignore[attr-defined]
        )

        type_ = get_sa_type_from_field(field)
        if issubclass(type_, Instant):
            return InstantType()
        if issubclass(type_, PlainDateTime):
            return PlainDateTimeType()
        if issubclass(type_, ZonedDateTime):
            return ZonedDateTimeType()
        if issubclass(type_, Date):
            return DateType()
        if issubclass(type_, Time):
            return TimeType()
    except (ValueError, TypeError):
        pass

    return _original_get_sqlalchemy_type(field)


sqlmodel.main.get_sqlalchemy_type = get_sqlalchemy_type

# SQLModel's get_sqlalchemy_type is a separate code path from SQLAlchemy's
# registry._resolve_type, so we register in both places. This covers plain
# SQLAlchemy DeclarativeBase models that share the default_registry.
sqlmodel.main.default_registry.update_type_annotation_map(
    {
        Instant: InstantType(),
        PlainDateTime: PlainDateTimeType(),
        ZonedDateTime: ZonedDateTimeType(),
        Date: DateType(),
        Time: TimeType(),
    }
)
