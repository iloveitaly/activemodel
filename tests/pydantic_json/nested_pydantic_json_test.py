"""
By default, fast API does not handle converting JSONB to and from Pydantic models.
"""

from typing import Optional, Tuple
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm.base import instance_state
from sqlalchemy.types import UserDefinedType
from sqlmodel import Field, Session

from activemodel import BaseModel
from sqlalchemy.dialects.postgresql import JSON
from activemodel.mixins import PydanticJSONMixin, TypeIDMixin
from activemodel.session_manager import get_engine
from activemodel.session_manager import global_session
from tests.models import AnotherExample, ExampleWithComputedProperty


class CustomTupleType(UserDefinedType):
    """Custom SQLAlchemy type for testing tuple serialization."""

    def get_col_spec(self, **kw):
        return "TEXT"

    def bind_processor(self, dialect):
        return lambda value: None if value is None else ",".join(map(str, value))

    def result_processor(self, dialect, coltype):
        def process_value(value) -> Tuple[float, float] | None:
            if value is None:
                return None
            parts = value.split(",")
            return (float(parts[0]), float(parts[1]))

        return process_value


class SubObject(PydanticBaseModel):
    name: str
    value: int


class ExampleWithJSONB(
    BaseModel, PydanticJSONMixin, TypeIDMixin("json_test"), table=True
):
    list_field: list[SubObject] = Field(sa_type=JSONB)
    # list_with_generator: list[SubObject] = Field(sa_type=JSONB)
    optional_list_field: list[SubObject] | None = Field(sa_type=JSONB, default=None)
    generic_list_field: list[dict] = Field(sa_type=JSONB)
    object_field: SubObject = Field(sa_type=JSONB)
    unstructured_field: dict = Field(sa_type=JSONB)
    semi_structured_field: dict[str, str] = Field(sa_type=JSONB)
    optional_object_field: SubObject | None = Field(sa_type=JSONB, default=None)
    old_optional_object_field: Optional[SubObject] = Field(sa_type=JSONB, default=None)
    tuple_field: tuple[float, float] = Field(sa_type=CustomTupleType)
    optional_tuple: Tuple | None = Field(sa_type=CustomTupleType, default=None)
    normal_field: str | None = Field(default=None)


class ExampleWithSimpleJSON(
    BaseModel, PydanticJSONMixin, TypeIDMixin("simple_json_test"), table=True
):
    # NOT JSONB!
    object_field: SubObject = Field(sa_type=JSON)


def test_json_serialization(create_and_wipe_database):
    sub_object = SubObject(name="test", value=1)

    example = ExampleWithJSONB(
        list_field=[sub_object],
        # list_with_generator=(x for x in [sub_object]),
        generic_list_field=[{"one": "two", "three": 3, "four": [1, 2, 3]}],
        optional_list_field=[sub_object],
        object_field=sub_object,
        unstructured_field={"one": "two", "three": 3, "four": [1, 2, 3]},
        normal_field="test",
        semi_structured_field={"one": "two", "three": "three"},
        optional_object_field=sub_object,
        old_optional_object_field=sub_object,
        tuple_field=(1.0, 2.0),
        optional_tuple=(1.0, 2.0),
    ).save()

    def assert_types_preserved(obj: ExampleWithJSONB):
        """Helper to verify all JSONB fields maintain their proper types."""
        assert isinstance(obj.list_field[0], SubObject)
        assert obj.optional_list_field is not None
        assert isinstance(obj.optional_list_field[0], SubObject)
        assert isinstance(obj.object_field, SubObject)
        assert isinstance(obj.optional_object_field, SubObject)
        assert isinstance(obj.old_optional_object_field, SubObject)
        assert isinstance(obj.tuple_field, tuple)
        assert isinstance(obj.optional_tuple, tuple)
        assert isinstance(obj.generic_list_field, list)
        assert isinstance(obj.generic_list_field[0], dict)
        assert isinstance(obj.unstructured_field, dict)
        assert isinstance(obj.semi_structured_field, dict)

    # make sure the types are preserved when saved
    assert_types_preserved(example)

    example.refresh()

    # make sure the automatic dict re-parse doesn't mark as dirty
    assert not instance_state(example).modified

    # make sure the types are preserved when refreshed
    assert_types_preserved(example)

    fresh_example = ExampleWithJSONB.get(example.id)

    assert fresh_example is not None
    # make sure the types are preserved when loaded from database
    assert_types_preserved(fresh_example)


def test_computed_serialization(create_and_wipe_database):
    # count()s are a bit paranoid because I don't understand the sqlalchemy session model yet

    with global_session():
        another_example = AnotherExample(note="test").save()

        example = ExampleWithComputedProperty(
            another_example_id=another_example.id,
        ).save()

        assert ExampleWithComputedProperty.count() == 1
        assert AnotherExample.count() == 1

        # what if the query is done through our magic `select()` method
        example_2 = list(ExampleWithComputedProperty.select().all())[0]

        assert Session.object_session(another_example)
        assert Session.object_session(example)

        example.model_dump_json()
        example_2.model_dump_json()

    assert ExampleWithComputedProperty.count() == 1
    assert AnotherExample.count() == 1


def test_simple_json_object(create_and_wipe_database):
    sub_object = SubObject(name="test", value=1)
    example = ExampleWithSimpleJSON(
        object_field=sub_object,
    ).save()

    # make sure the types are preserved when saved
    assert isinstance(example.object_field, SubObject)

    example.refresh()
    assert not instance_state(example).modified

    # make sure the types are preserved when refreshed
    assert isinstance(example.object_field, SubObject)
    assert example.object_field.name == "test"
    assert example.object_field.value == 1

    fresh_example = ExampleWithSimpleJSON.get(example.id)

    assert fresh_example is not None
    assert isinstance(fresh_example.object_field, SubObject)
    assert fresh_example.object_field.name == "test"
    assert fresh_example.object_field.value == 1


def test_optional_pydantic_json_fields_preserve_none(create_and_wipe_database):
    example = ExampleWithJSONB(
        list_field=[SubObject(name="test", value=1)],
        generic_list_field=[{"one": "two"}],
        # `None` here exercises the optional rehydration path on save, refresh, and reload.
        optional_list_field=None,
        object_field=SubObject(name="test", value=1),
        unstructured_field={"one": "two"},
        semi_structured_field={"one": "two"},
        optional_object_field=None,
        old_optional_object_field=None,
        tuple_field=(1.0, 2.0),
        optional_tuple=None,
    ).save()

    assert example.optional_list_field is None
    assert example.optional_object_field is None
    assert example.old_optional_object_field is None
    assert example.optional_tuple is None

    example.refresh()

    assert example.optional_list_field is None
    assert example.optional_object_field is None
    assert example.old_optional_object_field is None
    assert example.optional_tuple is None

    fresh_example = ExampleWithJSONB.get(example.id)

    assert fresh_example is not None
    assert fresh_example.optional_list_field is None
    assert fresh_example.optional_object_field is None
    assert fresh_example.old_optional_object_field is None
    assert fresh_example.optional_tuple is None


def test_json_object_update(create_and_wipe_database):
    "if we update a entry in a list of json objects, does the change persist?"

    sub_object = SubObject(name="test", value=1)
    sub_object_2 = SubObject(name="test_2", value=2)

    example = ExampleWithJSONB(
        list_field=[sub_object, sub_object_2],
        generic_list_field=[{"one": "two"}],
        object_field=sub_object,
        unstructured_field={"one": "two"},
        semi_structured_field={"one": "two"},
        tuple_field=(1.0, 2.0),
    ).save()

    # saving serializes the pydantic model and reloads it, which must not mark the object as dirty!
    assert not instance_state(example).modified

    # modify a nested object
    example.list_field[0].name = "updated"

    # the field will *not* be marked as dirty by default
    assert not instance_state(example).modified

    # so we have to force it to be dirty
    example.flag_modified("list_field")

    example.object_field.value = 42
    assert instance_state(example).modified

    example.save()

    assert example.list_field[0].name == "updated"

    # NOTE this should be inverted, but we are asserting against the current behavior of `object_field` state not being updated
    assert example.object_field.value != 42

    # now, let's mark it as modified
    example.object_field.value = 42
    example.flag_modified("object_field")
    example.save()

    assert example.object_field.value == 42

    # refresh from database
    fresh_example = ExampleWithJSONB.one(example.id)
    assert not instance_state(example).modified

    # verify changes persisted
    assert fresh_example.list_field[0].name == "updated"
    assert fresh_example.object_field.value == 42


def test_refresh_discards_unflushed_nested_json_mutation(create_and_wipe_database):
    sub_object = SubObject(name="test", value=1)

    example = ExampleWithJSONB(
        list_field=[sub_object],
        generic_list_field=[{"one": "two"}],
        object_field=sub_object,
        unstructured_field={"one": "two"},
        semi_structured_field={"one": "two"},
        tuple_field=(1.0, 2.0),
    ).save()

    example.list_field[0].name = "updated"

    # In-place nested mutation is not tracked, so a refresh should replace it with DB state.
    assert not instance_state(example).modified

    example.refresh()

    assert isinstance(example.list_field[0], SubObject)
    assert example.list_field[0].name == "test"


def test_refresh_discards_flagged_but_unflushed_nested_json_mutation(
    create_and_wipe_database,
):
    sub_object = SubObject(name="test", value=1)

    example = ExampleWithJSONB(
        list_field=[sub_object],
        generic_list_field=[{"one": "two"}],
        object_field=sub_object,
        unstructured_field={"one": "two"},
        semi_structured_field={"one": "two"},
        tuple_field=(1.0, 2.0),
    ).save()

    example.list_field[0].name = "updated"

    # Dirty tracking is not the same as persistence; refresh should still replace DB-backed state.
    example.flag_modified("list_field")

    assert instance_state(example).modified

    example.refresh()

    assert isinstance(example.list_field[0], SubObject)
    assert example.list_field[0].name == "test"
    assert not instance_state(example).modified


def test_partial_refresh_rehydrates_only_requested_json_fields(create_and_wipe_database):
    example = ExampleWithJSONB(
        list_field=[SubObject(name="list_original", value=1)],
        generic_list_field=[{"one": "two"}],
        object_field=SubObject(name="object_original", value=1),
        unstructured_field={"one": "two"},
        semi_structured_field={"one": "two"},
        optional_object_field=SubObject(name="optional_original", value=1),
        tuple_field=(1.0, 2.0),
    ).save()

    with Session(get_engine()) as session:
        # Keep one instance alive while a separate session changes the row underneath it.
        refreshed_example = session.get(ExampleWithJSONB, example.id)

        assert refreshed_example is not None
        assert isinstance(refreshed_example.object_field, SubObject)
        assert isinstance(refreshed_example.optional_object_field, SubObject)

        # Snapshot the untouched field so we can prove partial refresh leaves it alone in memory.
        original_optional_object = refreshed_example.optional_object_field

        with Session(get_engine()) as update_session:
            stored_example = update_session.get(ExampleWithJSONB, example.id)

            assert stored_example is not None

            stored_example.object_field = SubObject(name="object_updated", value=2)
            stored_example.optional_object_field = SubObject(
                name="optional_updated", value=2
            )
            update_session.commit()

        # Only reload `object_field`; `optional_object_field` should keep its old in-memory object.
        session.refresh(refreshed_example, attribute_names=["object_field"])

        assert isinstance(refreshed_example.object_field, SubObject)
        assert refreshed_example.object_field.name == "object_updated"

        # A partial refresh should leave unrelated fields untouched in memory.
        assert refreshed_example.optional_object_field is original_optional_object
        assert refreshed_example.optional_object_field.name == "optional_original"


def test_transform_is_idempotent_for_already_hydrated_json_fields(
    create_and_wipe_database,
):
    sub_object = SubObject(name="test", value=1)

    example = ExampleWithJSONB(
        list_field=[sub_object],
        generic_list_field=[{"one": "two"}],
        optional_list_field=[sub_object],
        object_field=sub_object,
        unstructured_field={"one": "two"},
        semi_structured_field={"one": "two"},
        optional_object_field=sub_object,
        old_optional_object_field=sub_object,
        tuple_field=(1.0, 2.0),
        optional_tuple=(1.0, 2.0),
    ).save()

    # Capture object identity so this test proves rehydration is a no-op for already-parsed fields.
    list_item = example.list_field[0]
    object_field = example.object_field
    assert example.optional_list_field is not None
    optional_list_item = example.optional_list_field[0]
    optional_object_field = example.optional_object_field
    old_optional_object_field = example.old_optional_object_field

    example.__transform_dict_to_pydantic__()

    assert example.list_field[0] is list_item
    assert example.object_field is object_field
    assert example.optional_list_field is not None
    assert example.optional_list_field[0] is optional_list_item
    assert example.optional_object_field is optional_object_field
    assert example.old_optional_object_field is old_optional_object_field