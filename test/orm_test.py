"""
Test core ORM functions
"""

from test.models import EXAMPLE_TABLE_PREFIX, AnotherExample, ExampleRecord


def test_empty_count(create_and_wipe_database):
    assert ExampleRecord.count() == 0


def test_all_and_count(create_and_wipe_database):
    AnotherExample().save()

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


def test_query_count(create_and_wipe_database):
    AnotherExample().save()

    example = ExampleRecord(something="hi").save()
    count = ExampleRecord.select().where(ExampleRecord.something == "hi").count()

    assert count == 1
