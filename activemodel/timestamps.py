from datetime import datetime
from typing import TypeVar

import sqlalchemy as sa

# TODO raw sql https://github.com/tiangolo/sqlmodel/discussions/772
from sqlmodel import Field
from sqlmodel.sql.expression import SelectOfScalar

from .database import get_engine

# TODO Stripe-style prefixed ID? https://stackoverflow.com/questions/62400011/how-can-i-create-a-serial-id-with-as-a-string-with-common-prefix-ie-tag-1-tag


def compile_sql(target: SelectOfScalar):
    return str(target.compile(get_engine().connect()))


WrappedModelType = TypeVar("WrappedModelType")


# @classmethod
# def select(cls):
#     with get_session() as session:
#         results = session.exec(sql.select(cls))

#         for result in results:
#             yield result


class TimestampMixin:
    """
    Simple created at and updated at timestamps. Mix them into your model:

    >>> class MyModel(TimestampMixin, SQLModel):
    >>>    pass

    Originally pulled from: https://github.com/tiangolo/sqlmodel/issues/252
    """

    created_at: datetime | None = Field(
        default=None,
        sa_type=sa.DateTime(timezone=True),
        sa_column_kwargs={"server_default": sa.func.now()},
        nullable=False,
    )

    updated_at: datetime | None = Field(
        default=None,
        sa_type=sa.DateTime(timezone=True),
        sa_column_kwargs={"onupdate": sa.func.now(), "server_default": sa.func.now()},
    )
