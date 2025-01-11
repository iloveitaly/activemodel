from pydantic import BaseModel as PydanticBaseModel

from activemodel import BaseModel
from activemodel.mixins import PydanticJSONMixin, TypeIDMixin
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field


class SubObject(PydanticBaseModel):
    name: str
    value: int


class ExampleWithJSON(
    BaseModel, PydanticJSONMixin, TypeIDMixin("json_test"), table=True
):
    list_field: list[SubObject] = Field(sa_type=JSONB())
    object_field: SubObject = Field(sa_type=JSONB())
    unstructured_field: dict = Field(sa_type=JSONB())


def test_json_serialization(create_and_wipe_database):
    sub_object = SubObject(name="test", value=1)
    example = ExampleWithJSON(
        list_field=[sub_object],
        object_field=sub_object,
        unstructured_field={"one": "two", "three": 3, "four": [1, 2, 3]},
    ).save()

    fresh_example = ExampleWithJSON.get(example.id)

    assert fresh_example is not None
    assert isinstance(fresh_example.object_field, SubObject)
    assert isinstance(fresh_example.list_field[0], SubObject)
    assert isinstance(fresh_example.unstructured_field, dict)
