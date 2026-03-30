from tests.lifecycle._helpers import (
    AfterFindModel,
    AfterFindModelWithRelationships,
    events,
)
from tests.models import AnotherExample


def test_after_find_not_called_on_construction():
    AfterFindModel(name="new instance")
    assert events == []


def test_after_find_called_for_base_model_finders():
    record = AfterFindModel(name="finder").save()

    events.clear()
    found = AfterFindModel.get(record.id)
    assert found is not None
    assert events == ["after_find:finder"]

    events.clear()
    found = AfterFindModel.one(record.id)
    assert found is not None
    assert events == ["after_find:finder"]

    events.clear()
    found = AfterFindModel.one_or_none(record.id)
    assert found is not None
    assert events == ["after_find:finder"]


def test_after_find_called_for_query_wrapper_methods():
    first_record = AfterFindModel(name="first").save()
    AfterFindModel(name="second").save()

    events.clear()
    found = AfterFindModel.select().where(AfterFindModel.id == first_record.id).one()
    assert found is not None
    assert events == ["after_find:first"]

    events.clear()
    found = AfterFindModel.select().first()
    assert found is not None
    assert events == [f"after_find:{found.name}"]

    events.clear()
    found = AfterFindModel.select().last()
    assert found is not None
    assert events == [f"after_find:{found.name}"]

    events.clear()
    found = list(AfterFindModel.select().all())
    assert len(found) == 2
    assert sorted(events) == ["after_find:first", "after_find:second"]

    events.clear()
    found = AfterFindModel.select().sample()
    assert found is not None
    assert events == [f"after_find:{found.name}"]


def test_after_find_called_for_find_or_initialize_existing_only():
    AfterFindModel(name="existing").save()

    events.clear()
    existing = AfterFindModel.find_or_initialize_by(name="existing")
    assert existing is not None
    assert events == ["after_find:existing"]

    events.clear()
    new_instance = AfterFindModel.find_or_initialize_by(name="missing")
    assert isinstance(new_instance, AfterFindModel)
    assert new_instance.id is None
    assert events == []


def test_after_find_runs_within_active_session_for_relationship_access():
    parent = AnotherExample(note="parent note").save()
    child = AfterFindModelWithRelationships(
        note="child",
        another_example_id=parent.id,
    ).save()

    events.clear()
    found = AfterFindModelWithRelationships.get(child.id)

    assert found is not None
    assert events == ["after_find_relationship:parent note"]
