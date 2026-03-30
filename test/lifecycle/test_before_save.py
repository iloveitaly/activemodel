from test.lifecycle._helpers import LifecycleModel, events


def test_before_save_runs_on_create_and_update():
    obj = LifecycleModel(name="first").save()
    assert "before_save" in events

    events.clear()
    obj.name = "second"
    obj.save()

    assert "before_save" in events
