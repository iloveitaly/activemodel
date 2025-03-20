from pydantic import computed_field
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
