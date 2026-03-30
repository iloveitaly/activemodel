from test.lifecycle._helpers import LifecycleModel, events


def test_after_create_runs_on_insert_only():
    LifecycleModel(name="first").save()
    assert "after_create" in events
    assert "after_update" not in events
