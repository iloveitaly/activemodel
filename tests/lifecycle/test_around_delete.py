from tests.lifecycle._helpers import DeleteModel, events


def test_around_delete_wraps_delete():
    obj = DeleteModel().save()

    events.clear()
    obj.delete()

    assert events.count("around_delete_before") == 1
    assert events.count("around_delete_after") == 1
