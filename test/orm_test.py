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
