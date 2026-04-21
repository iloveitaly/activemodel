from typing import Any, Generator, Literal, assert_type

import sqlalchemy as sa
from typeid import TypeID

from activemodel import BaseModel
from activemodel.query_wrapper import QueryWrapper
from tests.models import ExampleRecord, ExampleWithId, UpsertTestModel


def assert_where_returns_query_wrapper[T: BaseModel](
    model_cls: type[T], condition: object
) -> None:
    assert_type(model_cls.where(condition), QueryWrapper[T])


def test_classmethod_return_types_are_model_specific(create_and_wipe_database):
    condition = sa.column("another_example_id").is_(None)
    example = ExampleWithId().save()

    ExampleRecord(something="typed").save()

    assert_type(ExampleWithId.select(), QueryWrapper[ExampleWithId])
    assert_type(ExampleWithId.where(condition), QueryWrapper[ExampleWithId])
    assert_where_returns_query_wrapper(ExampleWithId, condition)
    assert_type(example.id, TypeID)
    assert_type(ExampleWithId.get(example.id), ExampleWithId | None)
    assert_type(ExampleWithId.one_or_none(example.id), ExampleWithId | None)
    assert_type(ExampleWithId.one(example.id), ExampleWithId)
    assert_type(example.refresh(), ExampleWithId)
    assert_type(example.delete(), Literal[True])

    assert_type(
        UpsertTestModel.upsert(
            {"name": "typed-upsert", "category": "type-tests", "value": 1},
            unique_by="name",
        ),
        UpsertTestModel,
    )
    assert_type(ExampleRecord.count(), int)
    assert_type(ExampleRecord.first(), ExampleRecord | None)
    assert_type(ExampleRecord.find_or_create_by(something="typed"), ExampleRecord)
    assert_type(ExampleRecord.find_or_initialize_by(something="typed"), ExampleRecord)
    assert_type(ExampleRecord.all(), Generator[ExampleRecord, Any, None])
    assert_type(list(ExampleRecord.all()), list[ExampleRecord])
    assert_type(ExampleRecord.sample(), ExampleRecord)
