"""
Test core ORM functions
"""

from activemodel import BaseModel
from activemodel.mixins.timestamps import TimestampsMixin
from activemodel.mixins.typeid import TypeIDMixin

EXAMPLE_TABLE_PREFIX = "test_record"


class ExampleRecord(
    BaseModel, TimestampsMixin, TypeIDMixin(EXAMPLE_TABLE_PREFIX), table=True
):
    something: str | None


def test_all_and_count(create_and_wipe_database):
    records_to_create = 10

    # create 10 example records
    for i in range(records_to_create):
        ExampleRecord().save()

    assert ExampleRecord.count() == records_to_create

    all_records = list(ExampleRecord.all())
    assert len(all_records) == records_to_create

    assert ExampleRecord.count() == records_to_create

    record = all_records[0]
    assert isinstance(record, ExampleRecord)


def test_foreign_key():
    field = ExampleRecord.foreign_key()
    assert field.sa_type.prefix == EXAMPLE_TABLE_PREFIX


def test_basic_query(create_and_wipe_database):
    example = ExampleRecord(something="hi").save()
    query = ExampleRecord.select().where(ExampleRecord.something == "hi")

    query_as_str = str(query)
    result = query.first()
