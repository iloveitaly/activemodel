import json
from activemodel.types.typeid import TypeIDType
from test.models import ExampleWithId
from pydantic import BaseModel as PydanticBaseModel
from typeid import TypeID


def test_json_schema(create_and_wipe_database):
    "json schema generation shouldn't be meaningfully different than json rendering, but let's check it anyway"

    example = ExampleWithId().save()
    example.model_json_schema()


class PydanticResponseModel(PydanticBaseModel):
    id: TypeID


def test_typeid_render(create_and_wipe_database):
    """
    ensure that pydantic models can render the type id, this requires dunder methods to be added to the TypeID type
    which is done thruogh the typeid_patch file
    """

    example = ExampleWithId().save()
    response = PydanticResponseModel(id=example.id)

    # check that the TypeID is serialized as a string
    assert json.loads(response.model_dump_json())["id"] == str(example.id)
    assert response.model_json_schema()["properties"]["id"]["type"] == "string"


class PydanticResponseTypeIDTypeModel(PydanticBaseModel):
    id: TypeIDType


def test_typeid_type_render(create_and_wipe_database):
    """
    ensure that pydantic models can render the type id, this requires dunder methods to be added to the TypeID type
    which is done thruogh the typeid_patch file
    """

    example = ExampleWithId().save()
    response = PydanticResponseTypeIDTypeModel(id=example.id)

    # check that the TypeID is serialized as a string
    assert json.loads(response.model_dump_json())["id"] == str(example.id)
    assert response.model_json_schema()["properties"]["id"]["type"] == "string"
