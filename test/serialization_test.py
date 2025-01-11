from pydantic import BaseModel as PydanticBaseModel

from activemodel import BaseModel
from activemodel.mixins import TypeIDMixin
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

TYPEID_PREFIX = "myid"


class SubObject(PydanticBaseModel):
    name: str
    value: int


class ExampleWithId(BaseModel, TypeIDMixin(TYPEID_PREFIX), table=True):
    list_field: list[SubObject] = Field(sa_type=JSONB())
    object_field: SubObject = Field(sa_type=JSONB())
    unstructured_field: dict = Field(sa_type=JSONB())


def test_json_serialization(create_and_wipe_database):
    sub_object = SubObject(name="test", value=1)
    example = ExampleWithId(
        list_field=[sub_object],
        object_field=sub_object,
        unstructured_field={"one": "two", "three": 3, "four": [1, 2, 3]},
    ).save()

    fresh_example = ExampleWithId.get(example.id)

    breakpoint()
