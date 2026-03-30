from test.lifecycle._helpers import DeleteModel, LifecycleModel, events


def test_create_lifecycle_order():
    LifecycleModel(name="first").save()

    assert events == [
        "before_create",
        "before_save",
        "around_save_before",
        "around_save_after",
        "after_create",
        "after_save",
    ]


def test_update_lifecycle_order():
    obj = LifecycleModel(name="first").save()

    events.clear()
    obj.name = "second"
    obj.save()

    assert events == [
        "before_update",
        "before_save",
        "around_save_before",
        "around_save_after",
        "after_update",
        "after_save",
    ]


def test_delete_lifecycle_order():
    obj = DeleteModel().save()

    events.clear()
    obj.delete()

    assert events == [
        "before_delete",
        "around_delete_before",
        "around_delete_after",
        "after_delete",
    ]
