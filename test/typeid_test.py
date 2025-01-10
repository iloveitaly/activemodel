import json

import pytest
from pydantic import BaseModel as PydanticBaseModel
from typeid import TypeID

from test.utils import temporary_tables

from activemodel import BaseModel
from activemodel.mixins import TypeIDMixin


def test_enforces_unique_prefixes():
    TypeIDMixin("hi")

    with pytest.raises(AssertionError):
        TypeIDMixin("hi")


def test_no_empty_prefixes_test():
    with pytest.raises(AssertionError):
        TypeIDMixin("")


TYPEID_PREFIX = "myid"


class ExampleWithId(BaseModel, TypeIDMixin(TYPEID_PREFIX), table=True):
    pass


def test_get_through_prefixed_uid():
    type_uid = TypeID(prefix=TYPEID_PREFIX)

    with temporary_tables():
        record = ExampleWithId.get(type_uid)
        assert record is None


def test_get_through_prefixed_uid_as_str():
    type_uid = TypeID(prefix=TYPEID_PREFIX)

    with temporary_tables():
        record = ExampleWithId.get(str(type_uid))
        assert record is None


def test_get_through_plain_uid_as_str():
    type_uid = TypeID(prefix=TYPEID_PREFIX)

    with temporary_tables():
        # pass uid as string. Ex: '01942886-7afc-7129-8f57-db09137ed002'
        record = ExampleWithId.get(str(type_uid.uuid))
        assert record is None


def test_get_through_plain_uid():
    type_uid = TypeID(prefix=TYPEID_PREFIX)

    with temporary_tables():
        record = ExampleWithId.get(type_uid.uuid)
        assert record is None


# the wrapped test is probably overkill, but it's protecting against a weird edge case I was running into
class WrappedExample(PydanticBaseModel):
    example: ExampleWithId


def test_render_typeid():
    "ensure that pydantic models can render the type id"

    with temporary_tables():
        example = ExampleWithId().save()

        assert example.model_dump()["id"] == str(example.id)
        assert json.loads(example.model_dump_json())["id"] == str(example.id)

        wrapped_example = WrappedExample(example=example)
        assert wrapped_example.model_dump()["example"]["id"] == str(example.id)
        assert json.loads(wrapped_example.model_dump_json())["example"]["id"] == str(
            example.id
        )
