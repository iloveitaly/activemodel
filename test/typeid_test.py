import json

import pytest
from pydantic import BaseModel as PydanticBaseModel
from typeid import TypeID

from test.models import TYPEID_PREFIX, ExampleWithId
from test.utils import temporary_tables

from activemodel.mixins import TypeIDMixin


def test_enforces_unique_prefixes():
    TypeIDMixin("hi")

    with pytest.raises(AssertionError):
        TypeIDMixin("hi")


def test_no_empty_prefixes_test():
    with pytest.raises(AssertionError):
        TypeIDMixin("")


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


def test_get_through_plain_uid_as_str(create_and_wipe_database):
    type_uid = TypeID(prefix=TYPEID_PREFIX)

    # pass uid as string. Ex: '01942886-7afc-7129-8f57-db09137ed002'
    record = ExampleWithId.get(str(type_uid.uuid))
    assert record is None


def test_get_through_plain_uid(create_and_wipe_database):
    type_uid = TypeID(prefix=TYPEID_PREFIX)

    record = ExampleWithId.get(type_uid.uuid)
    assert record is None


# def test_non_primary_typeid_key():
#     class NonPrimaryKeyExample(PydanticBaseModel, table=True):
#         something: str | None = None


# the wrapped test is probably overkill, but it's protecting against a weird edge case I was running into with fastapi
# rendering. A top-level object render worked fine, but rendering a list of SQLModel objects containing TypeID fields
# would fail with 'Unable to serialize unknown type'
class WrappedExample(PydanticBaseModel):
    example: ExampleWithId


def test_render_typeid(create_and_wipe_database):
    """
    ensure that pydantic models can render the type id

    `__pydantic_serializer__` seems to generate a serialization plan that gets passed to the underlying rust library
    which actually renders the object. This is why grepping for various errors in the serialization process does not
    yield any results.
    """

    example = ExampleWithId().save()

    assert example.model_dump()["id"] == str(example.id)
    assert json.loads(example.model_dump_json())["id"] == str(example.id)

    wrapped_example = WrappedExample(example=example)
    assert wrapped_example.model_dump()["example"]["id"] == str(example.id)
    assert json.loads(wrapped_example.model_dump_json())["example"]["id"] == str(
        example.id
    )


def test_json_schema(create_and_wipe_database):
    "json schema generation shouldn't be meaningfully different than json rendering, but let's check it anyway"

    example = ExampleWithId().save()
    example.model_json_schema()
