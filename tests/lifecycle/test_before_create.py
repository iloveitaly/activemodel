from tests.lifecycle._helpers import LifecycleModel, events


def test_before_create_runs_on_insert_only():
    LifecycleModel(name="first").save()
    assert "before_create" in events
    assert "before_update" not in events
