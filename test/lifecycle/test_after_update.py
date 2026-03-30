from test.lifecycle._helpers import LifecycleModel, events


def test_after_update_runs_on_update_only():
    obj = LifecycleModel(name="first").save()

    events.clear()
    obj.name = "second"
    obj.save()

    assert "after_update" in events
    assert "after_create" not in events
