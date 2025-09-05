"""Tests for manual lifecycle hooks (Rails-style subset).

Hooks covered:
    before_create, after_create
    before_update, after_update
    before_save, after_save
    around_save (context manager)
    before_delete, after_delete, around_delete (context manager)

Ordering expectation (create):
    before_create -> before_save -> around_save_before -> after_create -> after_save -> around_save_after
Ordering expectation (update):
    before_update -> before_save -> around_save_before -> after_update -> after_save -> around_save_after
Ordering expectation (delete):
    before_delete -> around_delete_before -> after_delete -> around_delete_after
"""

from contextlib import contextmanager
from sqlmodel import Field, Relationship

import pytest
from activemodel import BaseModel
from activemodel.pytest.transaction import database_reset_transaction
from activemodel.types.typeid import TypeIDType

from .models import AnotherExample

# simple event capture list used by the test model hooks
events: list[str] = []


@pytest.fixture(autouse=True)
def setup_database(create_and_wipe_database):
    """Ensure clean database state for each test"""
    events.clear()
    yield from database_reset_transaction()


class LifecycleModelWithRelationships(BaseModel, table=True):
    """Model used to test after_save accessing a relationship.

    Intentionally written so that the after_save hook closes the session then attempts
    to lazy-load the relationship, which should raise a SQLAlchemy error (DetachedInstanceError).
    """

    id: int | None = Field(default=None, primary_key=True)
    note: str | None = Field(default=None)
    another_example_id: TypeIDType = AnotherExample.foreign_key()
    another_example: AnotherExample = Relationship(
        sa_relationship_kwargs={"load_on_pending": True}
    )

    def log_self_and_relationships(self):
        from activemodel.logger import logger

        logger.info("self.note=%s", self.note)
        logger.info("another_example.note=%s", self.another_example.note)

    def before_create(self):
        events.append("before_create")
        self.log_self_and_relationships()

    def before_update(self):
        events.append("before_update")
        self.log_self_and_relationships()

    def before_save(self):
        events.append("before_save")
        self.log_self_and_relationships()

    def after_save(self):
        events.append("after_save")
        self.log_self_and_relationships()

    def after_create(self):
        events.append("after_create")
        self.log_self_and_relationships()

    def after_update(self):
        events.append("after_update")
        self.log_self_and_relationships()


class LifecycleModel(BaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str | None = None

    # Each hook appends its name; BaseModel's event wrapper will call with the appropriate args.
    def before_create(self):
        events.append("before_create")

    def before_update(self):
        events.append("before_update")

    def before_save(self):
        events.append("before_save")

    def after_create(self):
        events.append("after_create")

    def after_update(self):
        events.append("after_update")

    def after_save(self):
        events.append("after_save")

    @contextmanager
    def around_save(self):
        events.append("around_save_before")
        try:
            yield
        finally:
            events.append("around_save_after")


def test_create_lifecycle_hooks():
    LifecycleModel(name="first").save()

    assert events == [
        "before_create",
        "before_save",
        "around_save_before",
        "around_save_after",
        "after_create",
        "after_save",
    ]

    assert "before_update" not in events
    assert "after_update" not in events


def test_update_lifecycle_hooks():
    events.clear()

    obj = LifecycleModel(name="first").save()

    # Clear after initial insert so we isolate update events.
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
    assert "before_create" not in events
    assert "after_create" not in events


class DeleteModel(BaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    def before_delete(self):
        events.append("before_delete")

    def after_delete(self):
        events.append("after_delete")

    @contextmanager
    def around_delete(self):
        events.append("around_delete_before")
        yield
        events.append("around_delete_after")


def test_delete_hooks():
    obj = DeleteModel().save()

    events.clear()
    obj.delete()

    assert events == [
        "before_delete",
        "around_delete_before",
        "around_delete_after",
        "after_delete",
    ]


def test_after_save_with_relationship(db_session):
    parent = AnotherExample(note="parent").save()

    model_with_relationship = LifecycleModelWithRelationships(
        another_example_id=parent.id
    ).save()

    # test after_save when the relationship exists
    model_with_relationship.refresh()
    model_with_relationship.note = "a new note"
    model_with_relationship.save()
