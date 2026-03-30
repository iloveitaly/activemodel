from test.lifecycle._helpers import DeleteModel, events


def test_before_delete_runs_on_delete():
    obj = DeleteModel().save()

    events.clear()
    obj.delete()

    assert "before_delete" in events
