from test.lifecycle._helpers import (
    AfterInitializeModel,
    AfterInitializeModelWithRelationships,
    events,
)
from test.models import AnotherExample


def test_after_initialize_called_on_construction():
    record = AfterInitializeModel(name="new instance")
    assert record.initialized_name == "initialized:new instance"
    assert events == ["after_initialize:new instance"]


def test_after_initialize_called_for_base_model_finders_in_order():
    record = AfterInitializeModel(name="finder").save()

    events.clear()
    found = AfterInitializeModel.get(record.id)
    assert found is not None
    assert found.initialized_name == "initialized:finder"
    assert events == ["after_find:finder", "after_initialize:finder"]

    events.clear()
    found = AfterInitializeModel.one(record.id)
    assert found is not None
    assert found.initialized_name == "initialized:finder"
    assert events == ["after_find:finder", "after_initialize:finder"]

    events.clear()
    found = AfterInitializeModel.one_or_none(record.id)
    assert found is not None
    assert found.initialized_name == "initialized:finder"
    assert events == ["after_find:finder", "after_initialize:finder"]


def test_after_initialize_called_for_query_wrapper_methods_in_order():
    first_record = AfterInitializeModel(name="first").save()
    AfterInitializeModel(name="second").save()

    events.clear()
    found = (
        AfterInitializeModel.select()
        .where(AfterInitializeModel.id == first_record.id)
        .one()
    )
    assert found is not None
    assert found.initialized_name == "initialized:first"
    assert events == ["after_find:first", "after_initialize:first"]

    events.clear()
    found = AfterInitializeModel.select().first()
    assert found is not None
    assert found.initialized_name == f"initialized:{found.name}"
    assert events == [f"after_find:{found.name}", f"after_initialize:{found.name}"]

    events.clear()
    found = AfterInitializeModel.select().last()
    assert found is not None
    assert found.initialized_name == f"initialized:{found.name}"
    assert events == [f"after_find:{found.name}", f"after_initialize:{found.name}"]

    events.clear()
    found = list(AfterInitializeModel.select().all())
    assert len(found) == 2
    assert {record.initialized_name for record in found} == {
        "initialized:first",
        "initialized:second",
    }
    assert sorted(events) == [
        "after_find:first",
        "after_find:second",
        "after_initialize:first",
        "after_initialize:second",
    ]

    events.clear()
    found = AfterInitializeModel.select().sample()
    assert found is not None
    assert found.initialized_name == f"initialized:{found.name}"
    assert events == [f"after_find:{found.name}", f"after_initialize:{found.name}"]


def test_after_initialize_called_for_find_or_initialize_paths():
    AfterInitializeModel(name="existing").save()

    events.clear()
    existing = AfterInitializeModel.find_or_initialize_by(name="existing")
    assert existing is not None
    assert existing.initialized_name == "initialized:existing"
    assert events == ["after_find:existing", "after_initialize:existing"]

    events.clear()
    new_instance = AfterInitializeModel.find_or_initialize_by(name="missing")
    assert isinstance(new_instance, AfterInitializeModel)
    assert new_instance.id is None
    assert new_instance.initialized_name == "initialized:missing"
    assert events == ["after_initialize:missing"]


def test_after_initialize_runs_after_after_find_with_relationship_access():
    parent = AnotherExample(note="parent note").save()
    child = AfterInitializeModelWithRelationships(
        note="child",
        another_example_id=parent.id,
    ).save()

    events.clear()
    found = AfterInitializeModelWithRelationships.get(child.id)

    assert found is not None
    assert events == [
        "after_find_relationship:parent note",
        "after_initialize_relationship:parent note",
    ]
