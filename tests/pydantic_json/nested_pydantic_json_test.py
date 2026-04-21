"""
By default, fast API does not handle converting JSONB to and from Pydantic models.
"""

from sqlalchemy.orm.base import instance_state
from sqlmodel import Session

from activemodel.jsonb_snapshot import detect_json_mutations
from activemodel.session_manager import get_engine
from activemodel.session_manager import global_session
from tests.models import AnotherExample, ExampleWithComputedProperty
from tests.pydantic_json.helpers import (
    ExampleWithJSONB,
    ExampleWithSimpleJSON,
    InnerObject,
    SubObject,
    make_example,
)


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

    # modify nested objects -- auto-detected before flush with no manual dirty-marking
    example.list_field[0].name = "updated"
    example.object_field.value = 42
    example.save()

    assert example.list_field[0].name == "updated"
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

    # Mutation is detected before flush, but since we haven't saved, refresh discards it.
    example.refresh()

    assert isinstance(example.list_field[0], SubObject)
    assert example.list_field[0].name == "test"


def test_refresh_discards_unflushed_nested_json_mutation_after_in_place_edit(
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

    # Refresh should discard the in-memory mutation and replace with DB-backed state.
    example.refresh()

    assert isinstance(example.list_field[0], SubObject)
    assert example.list_field[0].name == "test"
    assert not instance_state(example).modified


def test_partial_refresh_rehydrates_only_requested_json_fields(
    create_and_wipe_database,
):
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


def test_list_append_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.list_field.append(SubObject(name="appended", value=99))
    example.save()
    fresh = ExampleWithJSONB.one(example.id)
    assert len(fresh.list_field) == 2
    assert fresh.list_field[-1].name == "appended"


def test_list_pop_persists(create_and_wipe_database):
    example = make_example(extra_items=1)
    assert not instance_state(example).modified

    example.list_field.pop()
    example.save()
    fresh = ExampleWithJSONB.one(example.id)
    assert len(fresh.list_field) == 1


def test_list_remove_persists(create_and_wipe_database):
    example = make_example(extra_items=1)
    assert not instance_state(example).modified

    # remove() uses ==; Pydantic __eq__ compares field values.
    example.list_field.remove(SubObject(name="item_1", value=1))
    example.save()
    fresh = ExampleWithJSONB.one(example.id)
    assert len(fresh.list_field) == 1
    assert fresh.list_field[0].name == "item_0"


def test_list_clear_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.list_field.clear()
    example.save()
    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.list_field == []


def test_list_extend_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.list_field.extend(
        [SubObject(name="ext_1", value=10), SubObject(name="ext_2", value=11)]
    )
    example.save()
    fresh = ExampleWithJSONB.one(example.id)
    assert len(fresh.list_field) == 3
    assert fresh.list_field[1].name == "ext_1"


def test_list_setitem_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.list_field[0] = SubObject(name="replaced", value=42)
    example.save()
    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.list_field[0].name == "replaced"
    assert fresh.list_field[0].value == 42


def test_list_iadd_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.list_field += [SubObject(name="iadd", value=7)]
    example.save()
    fresh = ExampleWithJSONB.one(example.id)
    assert len(fresh.list_field) == 2
    assert fresh.list_field[-1].name == "iadd"


def test_rehydrated_pydantic_preserves_isinstance_and_model_dump(
    create_and_wipe_database,
):
    example = make_example()

    assert isinstance(example.object_field, SubObject)
    assert isinstance(example.list_field[0], SubObject)
    assert example.object_field.model_dump() == {
        "name": "original",
        "value": 1,
        "inner": None,
    }
    assert example.list_field[0].model_dump() == {
        "name": "item_0",
        "value": 0,
        "inner": None,
    }

    fresh = ExampleWithJSONB.one(example.id)
    assert isinstance(fresh.object_field, SubObject)
    assert isinstance(fresh.list_field[0], SubObject)
    assert fresh.object_field.model_dump() == {
        "name": "original",
        "value": 1,
        "inner": None,
    }


def test_mutation_detected_across_save_cycles(create_and_wipe_database):
    "snapshot is re-taken after save() refreshes the instance, so a second mutation is also detected"
    example = make_example()

    example.object_field.value = 10
    example.save()
    assert example.object_field.value == 10

    # After save() the snapshot is reset; a second mutation must still be detected.
    example.object_field.value = 20

    example.save()
    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.object_field.value == 20


def test_replace_entire_field_persists_via_assignment_tracking(
    create_and_wipe_database,
):
    "replacing a JSONB field outright goes through SQLAlchemy instrumentation, not our tracking"
    example = make_example()

    example.object_field = SubObject(name="replaced", value=99)
    assert instance_state(example).modified

    example.save()
    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.object_field.name == "replaced"
    assert fresh.object_field.value == 99


def test_has_json_mutations_returns_true_when_mutated(create_and_wipe_database):
    example = make_example()
    assert not example.has_json_mutations()

    example.object_field.value = 999
    assert example.has_json_mutations()


def test_has_json_mutations_returns_false_when_clean(create_and_wipe_database):
    example = make_example()
    assert not example.has_json_mutations()

    # save and re-check -- snapshot is reset, still no mutations
    example.object_field.value = 5
    example.save()
    assert not example.has_json_mutations()


def test_has_json_mutations_returns_false_after_revert_to_original(
    create_and_wipe_database,
):
    "mutating then reverting to the original value should not be detected as a change"
    example = make_example()
    original_value = example.object_field.value

    example.object_field.value = 999
    assert example.has_json_mutations()

    example.object_field.value = original_value
    assert not example.has_json_mutations()


def test_detect_json_mutations_returns_field_names(create_and_wipe_database):
    example = make_example()
    assert detect_json_mutations(example) == []

    example.object_field.value = 999
    assert detect_json_mutations(example) == ["object_field"]


def test_deep_nested_mutation_detected(create_and_wipe_database):
    "mutating a Pydantic model inside a Pydantic model is caught by serialize-and-compare"
    example = ExampleWithJSONB(
        list_field=[
            SubObject(name="item", value=1, inner=InnerObject(label="deep", score=1.0))
        ],
        generic_list_field=[{"k": "v"}],
        object_field=SubObject(
            name="obj", value=2, inner=InnerObject(label="nested", score=2.0)
        ),
        unstructured_field={"k": "v"},
        semi_structured_field={"k": "v"},
        tuple_field=(1.0, 2.0),
    ).save()

    # mutate two levels deep
    example.object_field.inner.label = "changed"
    example.list_field[0].inner.score = 99.9
    example.save()

    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.object_field.inner.label == "changed"
    assert fresh.list_field[0].inner.score == 99.9


def test_no_op_save_does_not_produce_spurious_update(create_and_wipe_database):
    "saving without mutations should not generate an UPDATE"
    example = make_example()

    # re-save with zero changes
    example.save()

    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.object_field == SubObject(name="original", value=1)
    assert fresh.list_field == [SubObject(name="item_0", value=0)]


def test_list_sort_persists(create_and_wipe_database):
    example = make_example(extra_items=2)
    assert not instance_state(example).modified

    example.list_field.sort(key=lambda s: s.name, reverse=True)
    example.save()

    fresh = ExampleWithJSONB.one(example.id)
    assert [s.name for s in fresh.list_field] == ["item_2", "item_1", "item_0"]


def test_list_reverse_persists(create_and_wipe_database):
    example = make_example(extra_items=2)
    assert not instance_state(example).modified

    example.list_field.reverse()
    example.save()

    fresh = ExampleWithJSONB.one(example.id)
    assert [s.name for s in fresh.list_field] == ["item_2", "item_1", "item_0"]


def test_equivalent_reassignment_does_not_produce_spurious_update(
    create_and_wipe_database,
):
    "reassigning a field to a value that serializes identically should not generate an UPDATE"
    example = make_example()

    # direct assignment of an equivalent value — SQLAlchemy will mark the field modified,
    # but our before_commit handler should clear it since the serialized form is unchanged
    example.object_field = SubObject(name="original", value=1, inner=None)
    assert instance_state(example).modified

    example.save()
    assert not instance_state(example).modified
