"""
Test core ORM functions
"""

import pytest
from test.models import (
    EXAMPLE_TABLE_PREFIX,
    AnotherExample,
    ExampleRecord,
    ExampleWithId,
)
import sqlalchemy.exc


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


def test_where_returns_expected(create_and_wipe_database):
    # Create records with distinct "something" field values
    ExampleRecord(something="hello").save()
    ExampleRecord(something="world").save()
    ExampleRecord(something="hello").save()

    # Use the "where" convenience method to filter records
    results = list(ExampleRecord.where(ExampleRecord.something == "hello").all())

    # Expecting 2 records that match "hello"
    assert len(results) == 2
    for record in results:
        assert record.something == "hello"


def test_where_no_results(create_and_wipe_database):
    # Create a record with a specific value
    ExampleRecord(something="foo").save()

    # Filter by a value that does not exist to get no results
    result = ExampleRecord.where(ExampleRecord.something == "bar").first()
    assert result is None


def test_where_chaining(create_and_wipe_database):
    # Save multiple records; using the same condition twice should be harmless
    ExampleRecord(something="chain").save()
    ExampleRecord(something="chain").save()
    ExampleRecord(something="other").save()

    # Chain where calls; in our implementation, chaining should work the same as a single call
    query = (
        ExampleRecord.where(ExampleRecord.something == "chain")
        .where(ExampleRecord.something == "chain")
        .all()
    )
    results = list(query)

    # Expecting 2 records that match "chain" even after chaining the condition
    assert len(results) == 2
    for record in results:
        assert record.something == "chain"


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


def test_get_non_pk(create_and_wipe_database):
    # some paranoid checks here as I attempt to debug the issue
    example = ExampleRecord(something="hi", another_with_index="key_123").save()

    assert ExampleRecord.count() == 1

    retrieved_example = ExampleRecord.find_or_create_by(another_with_index="key_123")

    assert retrieved_example
    assert retrieved_example.id == example.id


def test_database_refresh(create_and_wipe_database):
    example = ExampleRecord(something="hi").save()
    example_2 = ExampleRecord.get(example.id)

    # now, let's update the "hi" on the 2nd example
    example_2.something = "hello"
    example_2.save()

    # now let's refresh the first example
    example.refresh()

    assert example.something == "hello"


def test_primary_key_column():
    assert ExampleRecord.primary_key_column().name == "id"
    assert ExampleWithId.primary_key_column().name == "id"


def test_one_no_results(create_and_wipe_database):
    record = ExampleRecord()
    # do not save!

    with pytest.raises(sqlalchemy.exc.NoResultFound):
        ExampleRecord.one(record.id)


def test_one_single_result(create_and_wipe_database):
    example = ExampleRecord().save()
    result = ExampleRecord.one(example.id)

    assert result
    assert isinstance(result, ExampleRecord)
    assert result.id == example.id


def test_one_multiple_results(create_and_wipe_database):
    # not a pk, but should still throw an error
    example = ExampleRecord(something="hi").save()
    another_example = ExampleRecord(something="hi").save()

    with pytest.raises(sqlalchemy.exc.MultipleResultsFound):
        ExampleRecord.one(something="hi")
