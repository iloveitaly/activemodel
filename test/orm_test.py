"""
Test core ORM functions
"""

from contextlib import contextmanager

from activemodel import BaseModel, get_engine
from activemodel.mixins.timestamps import TimestampsMixin
from activemodel.mixins.typeid import TypeIDMixin
from sqlmodel import SQLModel


@contextmanager
def temporary_tables():
    SQLModel.metadata.create_all(get_engine())

    try:
        yield
    finally:
        SQLModel.metadata.drop_all(
            # tables=[SQLModel.metadata.tables[AIVisitNote.__tablename__]],
            bind=get_engine(),
        )


EXAMPLE_TABLE_PREFIX = "test_record"


class ExampleRecord(
    BaseModel, TimestampsMixin, TypeIDMixin(EXAMPLE_TABLE_PREFIX), table=True
):
    pass


def test_list():
    with temporary_tables():
        # create 10 example records
        for i in range(10):
            ExampleRecord().save()

        assert ExampleRecord.count() == 10

        all_records = list(ExampleRecord.all())
        assert len(all_records) == 10

        record = all_records[0]
        assert isinstance(record, ExampleRecord)


def test_foreign_key():
    field = ExampleRecord.foreign_key()
    assert field.sa_type.prefix == EXAMPLE_TABLE_PREFIX
