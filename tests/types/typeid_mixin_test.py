import json
from typing import Literal, assert_type

import pytest

from activemodel import BaseModel
from activemodel.mixins import TypeIDField, TypeIDMixin, TypeIDPrimaryKey


def test_enforces_unique_prefixes():
    with pytest.warns(DeprecationWarning):
        TypeIDMixin("hi")

    with pytest.raises(AssertionError):
        with pytest.warns(DeprecationWarning):
            TypeIDMixin("hi")


def test_no_empty_prefixes_test():
    with pytest.raises(AssertionError):
        with pytest.warns(DeprecationWarning):
            TypeIDMixin("")


def test_typeid_primary_key_rejects_empty_prefix():
    with pytest.raises(AssertionError):
        TypeIDPrimaryKey("")


# ---------------------------------------------------------------------------
# Declarative form: id: TypeIDField[Literal["..."]] = TypeIDPrimaryKey("...")
# ---------------------------------------------------------------------------


class DeclarativeModel(BaseModel, table=True):
    id: TypeIDField[Literal["decl"]] = TypeIDPrimaryKey("decl")
    name: str


def test_declarative_model_auto_generates_id(create_and_wipe_database):
    record = DeclarativeModel(name="Alice").save()

    assert_type(record, DeclarativeModel)
    assert_type(record.id, TypeIDField[Literal["decl"]])
    assert record.id is not None
    assert str(record.id).startswith("decl_")


def test_declarative_model_round_trips(create_and_wipe_database):
    record = DeclarativeModel(name="Bob").save()

    fetched = DeclarativeModel.get(record.id)

    assert_type(fetched, DeclarativeModel | None)
    assert fetched is not None
    assert fetched.id == record.id
    assert fetched.name == "Bob"


def test_declarative_model_json_schema_includes_typeid_format():
    schema = DeclarativeModel.model_json_schema()
    id_schema = schema["properties"]["id"]

    assert id_schema["type"] == "string"
    assert id_schema["format"] == "typeid"
    assert "decl" in id_schema["description"]
    assert any("decl_" in ex for ex in id_schema.get("examples", []))


def test_declarative_model_model_dump_json(create_and_wipe_database):
    record = DeclarativeModel(name="Carol").save()

    data = json.loads(record.model_dump_json())
    assert data["id"].startswith("decl_")
    assert data["name"] == "Carol"
