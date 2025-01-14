"""
By default, fast API does not handle converting JSONB to and from Pydantic models.
"""

from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from activemodel import BaseModel
from activemodel.mixins import PydanticJSONMixin, TypeIDMixin


class SubObject(PydanticBaseModel):
    name: str
    value: int


class ExampleWithJSON(
    BaseModel, PydanticJSONMixin, TypeIDMixin("json_test"), table=True
):
    list_field: list[SubObject] = Field(sa_type=JSONB())
    # list_with_generator: list[SubObject] = Field(sa_type=JSONB())
    optional_list_field: list[SubObject] | None = Field(sa_type=JSONB(), default=None)
    generic_list_field: list[dict] = Field(sa_type=JSONB())
    object_field: SubObject = Field(sa_type=JSONB())
    unstructured_field: dict = Field(sa_type=JSONB())
    semi_structured_field: dict[str, str] = Field(sa_type=JSONB())
    optional_object_field: SubObject | None = Field(sa_type=JSONB(), default=None)

    normal_field: str | None = Field(default=None)


def test_json_serialization(create_and_wipe_database):
    sub_object = SubObject(name="test", value=1)
    example = ExampleWithJSON(
        list_field=[sub_object],
        # list_with_generator=(x for x in [sub_object]),
        generic_list_field=[{"one": "two", "three": 3, "four": [1, 2, 3]}],
        optional_list_field=[sub_object],
        object_field=sub_object,
        unstructured_field={"one": "two", "three": 3, "four": [1, 2, 3]},
        normal_field="test",
        semi_structured_field={"one": "two", "three": "three"},
        optional_object_field=sub_object,
    ).save()

    fresh_example = ExampleWithJSON.get(example.id)

    assert fresh_example is not None
    assert isinstance(fresh_example.object_field, SubObject)
    assert isinstance(fresh_example.optional_object_field, SubObject)
    assert isinstance(fresh_example.generic_list_field, list)
    assert isinstance(fresh_example.generic_list_field[0], dict)
    assert isinstance(fresh_example.list_field[0], SubObject)
    assert fresh_example.optional_list_field
    assert isinstance(fresh_example.optional_list_field[0], SubObject)
    assert isinstance(fresh_example.unstructured_field, dict)
