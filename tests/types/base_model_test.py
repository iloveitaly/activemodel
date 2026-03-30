from typing import assert_type

from activemodel import BaseModel
from activemodel.query_wrapper import QueryWrapper
from tests.models import ExampleWithId


def assert_where_returns_query_wrapper[T: BaseModel](
    model_cls: type[T], condition: object
) -> None:
    assert_type(model_cls.where(condition), QueryWrapper[T])


def test_classmethod_return_types_are_model_specific(create_and_wipe_database):
    condition = ExampleWithId.another_example_id.is_(None)

    assert_type(ExampleWithId.select(), QueryWrapper[ExampleWithId])
    assert_type(ExampleWithId.where(condition), QueryWrapper[ExampleWithId])
    assert_where_returns_query_wrapper(ExampleWithId, condition)
    assert_type(ExampleWithId.get(), ExampleWithId | None)
    assert_type(ExampleWithId.one_or_none(), ExampleWithId | None)
