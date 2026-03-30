from tests.lifecycle._helpers import (
    LifecycleModel,
    LifecycleModelWithRelationships,
    events,
)
from tests.models import AnotherExample


def test_after_save_runs_on_create_and_update():
    obj = LifecycleModel(name="first").save()
    assert "after_save" in events

    events.clear()
    obj.name = "second"
    obj.save()

    assert "after_save" in events


def test_after_save_with_relationship(db_session):
    parent = AnotherExample(note="parent").save()

    model_with_relationship = LifecycleModelWithRelationships(
        another_example_id=parent.id
    ).save()

    model_with_relationship.refresh()
    model_with_relationship.note = "a new note"
    model_with_relationship.save()
