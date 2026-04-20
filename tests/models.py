"""
Example models to test various ORM cases
"""

from pydantic import computed_field
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship

from activemodel import BaseModel
from activemodel.mixins import TypeIDPrimaryKey
from activemodel.mixins.timestamps import TimestampsMixin
from typeid import TypeID

TYPEID_PREFIX = "myid"

EXAMPLE_TABLE_PREFIX = "test_record"


class ExampleRecord(BaseModel, TimestampsMixin, table=True):
    id: TypeID = TypeIDPrimaryKey(EXAMPLE_TABLE_PREFIX)
    something: str | None = None
    another_with_index: str | None = Field(index=True, default=None, unique=True)


class AnotherExample(BaseModel, table=True):
    id: TypeID = TypeIDPrimaryKey("myotherid")
    note: str | None = Field(nullable=True)


class ExampleWithId(BaseModel, table=True):
    "example table with foreign keys"

    id: TypeID = TypeIDPrimaryKey(TYPEID_PREFIX)
    another_example_id: TypeID = AnotherExample.foreign_key(nullable=True)
    another_example: AnotherExample = Relationship()

    example_record_id: TypeID = ExampleRecord.foreign_key(nullable=True)
    example_record: ExampleRecord = Relationship()


class ExampleWithComputedProperty(BaseModel, table=True):
    id: TypeID = TypeIDPrimaryKey("example_computed")
    another_example_id: TypeID = AnotherExample.foreign_key()
    another_example: AnotherExample = Relationship()

    @computed_field
    @property
    def special_note(self) -> str:
        return f"SPECIAL: {self.another_example.note}"


class UpsertTestModel(BaseModel, table=True):
    """Test model for upsert operations"""

    id: TypeID = TypeIDPrimaryKey("upsert_test")
    name: str = Field(unique=True)
    category: str = Field(index=True)
    value: int = Field(default=0)
    description: str | None = Field(default=None)

    # Add a composite unique constraint for the multiple unique field test
    __table_args__ = (UniqueConstraint("name", "category", name="compound_constraint"),)


class ExampleRelatedModel(BaseModel, table=True):
    """
    Test model with a foreign key relationship to ExampleRecord, used to test related model creation in factories.
    """

    id: TypeID = TypeIDPrimaryKey("related_model")
    example_record_id: TypeID = ExampleRecord.foreign_key(index=True)
    example_record: ExampleRecord = Relationship()
