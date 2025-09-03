"""Tests for BaseModel lifecycle hooks.

Covers these hooks registered in `BaseModel.__init_subclass__`:

        before_insert, before_update, before_save, after_insert, after_update, after_save

We verify ordering and that only the appropriate hooks fire for insert vs update.
"""

from sqlmodel import Field

from activemodel import BaseModel


# simple event capture list used by the test model hooks
events: list[str] = []


class LifecycleModel(BaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str | None = None

    # Each hook appends its name; BaseModel's event wrapper will call with the appropriate args.
    def before_insert(self):  # type: ignore[override]
        events.append("before_insert")

    def before_update(self):  # type: ignore[override]
        events.append("before_update")

    def before_save(self):  # type: ignore[override]
        events.append("before_save")

    def after_insert(self):  # type: ignore[override]
        events.append("after_insert")

    def after_update(self):  # type: ignore[override]
        events.append("after_update")

    def after_save(self):  # type: ignore[override]
        events.append("after_save")


def test_insert_lifecycle_hooks(create_and_wipe_database):
    events.clear()

    LifecycleModel(name="first").save()

    # Only insert + save hooks should have fired, in the order they were registered.
    assert events == [
        "before_insert",
        "before_save",
        "after_insert",
        "after_save",
    ]
    assert "before_update" not in events
    assert "after_update" not in events


def test_update_lifecycle_hooks(create_and_wipe_database):
    events.clear()

    obj = LifecycleModel(name="first").save()

    # Clear after initial insert so we isolate update events.
    events.clear()
    obj.name = "second"
    obj.save()

    # Only update + save hooks should have fired for the second save.
    assert events == [
        "before_update",
        "before_save",
        "after_update",
        "after_save",
    ]
    assert "before_insert" not in events
    assert "after_insert" not in events
