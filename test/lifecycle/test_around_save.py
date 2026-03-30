from test.lifecycle._helpers import LifecycleModel, events


def test_around_save_wraps_create_and_update():
    obj = LifecycleModel(name="first").save()
    assert events.count("around_save_before") == 1
    assert events.count("around_save_after") == 1

    events.clear()
    obj.name = "second"
    obj.save()

    assert events.count("around_save_before") == 1
    assert events.count("around_save_after") == 1
