from tests.lifecycle._helpers import DeleteModel, events


def test_after_delete_runs_on_delete():
    obj = DeleteModel().save()

    events.clear()
    obj.delete()

    assert "after_delete" in events
