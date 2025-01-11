from typing import get_args, get_origin

from pydantic import BaseModel as PydanticBaseModel

from activemodel import BaseModel
from activemodel.mixins import TypeIDMixin
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import reconstructor
from sqlmodel import Field

TYPEID_PREFIX = "myid"


class SubObject(PydanticBaseModel):
    name: str
    value: int


class ExampleWithId(BaseModel, TypeIDMixin(TYPEID_PREFIX), table=True):
    list_field: list[SubObject] = Field(sa_type=JSONB())
    object_field: SubObject = Field(sa_type=JSONB())
    unstructured_field: dict = Field(sa_type=JSONB())

    @reconstructor
    def init_on_load(self):
        for field_name, field_info in self.model_fields.items():
            raw_value = getattr(self, field_name, None)

            if raw_value is None:
                continue

            annotation = field_info.annotation
            origin = get_origin(annotation)
            args = get_args(annotation)

            # e.g. list[SomePydanticModel]
            if origin is list and len(args) == 1:
                model_cls = args[0]  # e.g. SomePydanticModel
                if issubclass(model_cls, PydanticBaseModel) and isinstance(
                    raw_value, list
                ):
                    parsed_value = [model_cls(**item) for item in raw_value]
                    setattr(self, field_name, parsed_value)
            # single model
            elif issubclass(annotation, PydanticBaseModel):
                setattr(self, field_name, annotation(**raw_value))


def test_json_serialization(create_and_wipe_database):
    sub_object = SubObject(name="test", value=1)
    example = ExampleWithId(
        list_field=[sub_object],
        object_field=sub_object,
        unstructured_field={"one": "two", "three": 3, "four": [1, 2, 3]},
    ).save()

    fresh_example = ExampleWithId.get(example.id)

    assert fresh_example is not None
    assert isinstance(fresh_example.object_field, SubObject)
    assert isinstance(fresh_example.list_field[0], SubObject)
    assert isinstance(fresh_example.unstructured_field, dict)
