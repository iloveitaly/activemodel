"""
Test core ORM functions
"""

from test.utils import temporary_tables

from activemodel import BaseModel
from activemodel.mixins.timestamps import TimestampsMixin
from activemodel.mixins.typeid import TypeIDMixin

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
