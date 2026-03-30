from tests.lifecycle._helpers import LifecycleModel, events


def test_before_update_runs_on_update_only():
    obj = LifecycleModel(name="first").save()

    events.clear()
    obj.name = "second"
    obj.save()

    assert "before_update" in events
    assert "before_create" not in events
