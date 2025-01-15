from typing import Annotated

import pytest
import sqlalchemy
from fastapi import Depends, FastAPI, Path, Request
from fastapi.testclient import TestClient
from starlette.testclient import TestClient

from activemodel.session_manager import aglobal_session
from activemodel.types.typeid import TypeIDType
from test.models import AnotherExample, ExampleWithComputedProperty, ExampleWithId


def fake_app():
    api_app = FastAPI(dependencies=[Depends(aglobal_session)])

    @api_app.get("/typeid")
    async def index() -> ExampleWithId:
        return ExampleWithId().save()

    @api_app.get("/computed")
    async def computed():
        another_example = AnotherExample(note="hello").save()
        computed_example = ExampleWithComputedProperty(
            another_example_id=another_example.id
        ).save()
        # computed_example.model_dump_json()
        return computed_example

    @api_app.post("/example/{example_id}")
    async def get_record(
        request: Request,
        example_id: Annotated[TypeIDType, Path()],
    ) -> ExampleWithId:
        example = ExampleWithId.get(id=example_id)
        assert example
        return example

    return api_app


def fake_client():
    app = fake_app()
    return app, TestClient(app)


def test_openapi_generation():
    openapi = fake_app().openapi()


def test_typeid_input_parsing(create_and_wipe_database):
    example = ExampleWithId().save()
    example_id = example.id

    app, client = fake_client()

    response = client.post(f"/example/{example_id}")

    assert response.status_code == 200


def test_typeid_invalid_prefix_match(create_and_wipe_database):
    app, client = fake_client()

    # TODO we should really be able to assert against this:
    # with pytest.raises(TypeIDValidationError):
    # we'll need to

    with pytest.raises(sqlalchemy.exc.StatementError):
        response = client.post("/example/user_01h45ytscbebyvny4gc8cr8ma2")


def test_computed_property(create_and_wipe_database):
    app, client = fake_client()

    response = client.get("/computed")

    assert response.status_code == 200
    assert response.json()["special_note"] == "SPECIAL: hello"
