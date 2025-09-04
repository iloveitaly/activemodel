"""
Example models to test various ORM cases
"""

from pydantic import computed_field
from sqlalchemy import UniqueConstraint
from sqlmodel import Column, Field, Integer, Relationship

from activemodel import BaseModel
from activemodel.mixins import TypeIDMixin
from activemodel.mixins.timestamps import TimestampsMixin
from activemodel.types.typeid import TypeIDType

TYPEID_PREFIX = "myid"

EXAMPLE_TABLE_PREFIX = "test_record"


class ExampleRecord(
    BaseModel, TimestampsMixin, TypeIDMixin(EXAMPLE_TABLE_PREFIX), table=True
):
    something: str | None = None
    another_with_index: str | None = Field(index=True, default=None, unique=True)


class AnotherExample(BaseModel, TypeIDMixin("myotherid"), table=True):
    note: str | None = Field(nullable=True)


class ExampleWithId(BaseModel, TypeIDMixin(TYPEID_PREFIX), table=True):
    "example table with foreign keys"

    another_example_id: TypeIDType = AnotherExample.foreign_key(nullable=True)
    another_example: AnotherExample = Relationship()

    example_record_id: TypeIDType = ExampleRecord.foreign_key(nullable=True)
    example_record: ExampleRecord = Relationship()


class ExampleWithComputedProperty(
    BaseModel, TypeIDMixin("example_computed"), table=True
):
    another_example_id: TypeIDType = AnotherExample.foreign_key()
    another_example: AnotherExample = Relationship()

    @computed_field
    @property
    def special_note(self) -> str:
        return f"SPECIAL: {self.another_example.note}"


class UpsertTestModel(BaseModel, TypeIDMixin("upsert_test"), table=True):
    """Test model for upsert operations"""

    name: str = Field(unique=True)
    category: str = Field(index=True)
    value: int = Field(default=0)
    description: str | None = Field(default=None)

    # Add a composite unique constraint for the multiple unique field test
    __table_args__ = (UniqueConstraint("name", "category", name="compound_constraint"),)


class RelationshipAfterSaveModel(BaseModel, table=True):
    """Model used to test after_save accessing a relationship.

    Intentionally written so that the after_save hook closes the session then attempts
    to lazy-load the relationship, which should raise a SQLAlchemy error (DetachedInstanceError).
    """

    id: int | None = Field(default=None, primary_key=True)
    note: str | None = Field(default=None)
    another_example_id: TypeIDType = AnotherExample.foreign_key()
    another_example: AnotherExample = Relationship()

    def after_save(self):
        from activemodel.logger import logger

        logger.info("self.note=%s", self.note)
        logger.info("another_example.note=%s", self.another_example.note)
