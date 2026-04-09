"""Shared pydantic_json test fixtures.

Keep these models out of the test modules themselves so pytest collection only registers
each `TypeIDMixin(...)` prefix once.
"""

from typing import Optional, Tuple

from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.types import UserDefinedType
from sqlmodel import Field

from activemodel import BaseModel
from activemodel.mixins import PydanticJSONMixin, TypeIDMixin


class CustomTupleType(UserDefinedType):
    """Custom SQLAlchemy type for testing tuple serialization."""

    def get_col_spec(self, **kw):
        return "TEXT"

    def bind_processor(self, dialect):
        return lambda value: None if value is None else ",".join(map(str, value))

    def result_processor(self, dialect, coltype):
        def process_value(value) -> Tuple[float, float] | None:
            if value is None:
                return None

            parts = value.split(",")
            return (float(parts[0]), float(parts[1]))

        return process_value


class InnerObject(PydanticBaseModel):
    label: str
    score: float = 0.0


class SubObject(PydanticBaseModel):
    name: str
    value: int
    inner: InnerObject | None = None


class ExampleWithJSONB(
    BaseModel, PydanticJSONMixin, TypeIDMixin("json_test"), table=True
):
    list_field: list[SubObject] = Field(sa_type=JSONB)
    optional_list_field: list[SubObject] | None = Field(sa_type=JSONB, default=None)
    generic_list_field: list[dict] = Field(sa_type=JSONB)
    object_field: SubObject = Field(sa_type=JSONB)
    unstructured_field: dict = Field(sa_type=JSONB)
    semi_structured_field: dict[str, str] = Field(sa_type=JSONB)
    optional_object_field: SubObject | None = Field(sa_type=JSONB, default=None)
    old_optional_object_field: Optional[SubObject] = Field(sa_type=JSONB, default=None)
    tuple_field: tuple[float, float] = Field(sa_type=CustomTupleType)
    optional_tuple: Tuple | None = Field(sa_type=CustomTupleType, default=None)
    normal_field: str | None = Field(default=None)


class ExampleWithSimpleJSON(
    BaseModel, PydanticJSONMixin, TypeIDMixin("simple_json_test"), table=True
):
    object_field: SubObject = Field(sa_type=JSON)


class ExampleWithAmbiguousUnion(
    BaseModel, PydanticJSONMixin, TypeIDMixin("ambiguous_union_json_test"), table=True
):
    ambiguous_object_field: SubObject | dict | None = Field(sa_type=JSONB, default=None)


def make_example(extra_items: int = 0) -> ExampleWithJSONB:
    # the baseline payload intentionally includes both pydantic-backed and raw dict fields
    items = [SubObject(name="item_0", value=0)] + [
        SubObject(name=f"item_{i}", value=i) for i in range(1, extra_items + 1)
    ]

    return ExampleWithJSONB(
        list_field=items,
        generic_list_field=[{"key": "val"}],
        object_field=SubObject(name="original", value=1),
        unstructured_field={"k": "v"},
        semi_structured_field={"k": "v"},
        tuple_field=(1.0, 2.0),
    ).save()
