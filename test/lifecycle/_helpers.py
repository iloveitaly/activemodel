from contextlib import contextmanager

from sqlmodel import Field, Relationship

from activemodel import BaseModel
from activemodel.types.typeid import TypeIDType
from test.models import AnotherExample

events: list[str] = []


class LifecycleModelWithRelationships(BaseModel, table=True):
    """Model used to test after_save accessing a relationship."""

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


class AfterFindModel(BaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str | None = None

    def after_find(self):
        events.append(f"after_find:{self.name}")


class AfterFindModelWithRelationships(BaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    note: str | None = Field(default=None)
    another_example_id: TypeIDType = AnotherExample.foreign_key()
    another_example: AnotherExample = Relationship(
        sa_relationship_kwargs={"load_on_pending": True}
    )

    def after_find(self):
        events.append(f"after_find_relationship:{self.another_example.note}")


class AfterInitializeModel(BaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str | None = None

    def after_find(self):
        events.append(f"after_find:{self.name}")

    def after_initialize(self):
        events.append(f"after_initialize:{self.name}")


class AfterInitializeModelWithRelationships(BaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    note: str | None = Field(default=None)
    another_example_id: TypeIDType = AnotherExample.foreign_key()
    another_example: AnotherExample = Relationship(
        sa_relationship_kwargs={"load_on_pending": True}
    )

    def after_find(self):
        events.append(f"after_find_relationship:{self.another_example.note}")

    def after_initialize(self):
        if self.id is None:
            events.append("after_initialize:new")
            return

        events.append(f"after_initialize_relationship:{self.another_example.note}")
