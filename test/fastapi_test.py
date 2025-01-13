from fastapi import FastAPI

from test.models import ExampleWithId


def fake_app():
    api_app = FastAPI()  # type: ignore

    @api_app.get("/typeid")
    async def index() -> ExampleWithId:
        return "hi"

    return api_app


def test_openapi():
    openapi = fake_app().openapi()
    breakpoint()
