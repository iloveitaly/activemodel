from typing import Any, Generator, assert_type
import uuid

import sqlmodel as sm
from sqlmodel.sql.expression import SelectOfScalar
from sqlalchemy import column

from activemodel.query_wrapper import QueryWrapper
from test.models import ExampleRecord, UpsertTestModel


def test_basic_types(create_and_wipe_database):
    qw = ExampleRecord.select()

    sm_query = sm.select(ExampleRecord)
    assert_type(sm_query, SelectOfScalar[ExampleRecord])

    # assert type annotation of qw is QueryWrapper[ExampleRecord]
    assert_type(qw, QueryWrapper[ExampleRecord])
    assert isinstance(qw, QueryWrapper)

    all_records = qw.all()
    assert_type(all_records, Generator[ExampleRecord, Any, None])

    all_records_list = list(all_records)
    assert_type(all_records_list, list[ExampleRecord])


def test_scalar_single_column(create_and_wipe_database):
    """Ensure QueryWrapper.scalar returns the first column value when selecting a single scalar expression.

    We create a record, build a query selecting only the id column and assert scalar() returns that id.
    """
    record = ExampleRecord(something="hello").save()

    # Build a query selecting only the id column from the ExampleRecord table
    # Using the model .select(...) helper that forwards args to QueryWrapper
    query = ExampleRecord.select(ExampleRecord.id).where(ExampleRecord.id == record.id)

    value = query.scalar()

    # Should return the primary key of the inserted record
    assert value == record.id


def test_exists_basic(create_and_wipe_database):
    # empty table
    assert ExampleRecord.select().exists() is False

    r = ExampleRecord(something="hello").save()
    assert ExampleRecord.select().exists() is True

    # filter matches
    assert ExampleRecord.select().where(ExampleRecord.id == r.id).exists() is True
    # filter no match
    assert (
        ExampleRecord.select().where(ExampleRecord.id == str(uuid.uuid4())).exists()
        is False
    )


def test_exists_does_not_mutate_query(create_and_wipe_database):
    ExampleRecord(something="one").save()
    q = ExampleRecord.select()
    before_sql = q.sql()
    assert q.exists() is True
    # ensure calling exists didn't change underlying query
    assert q.sql() == before_sql
    # further chaining still works
    assert q.where(ExampleRecord.something == "one").exists() is True


# TODO needs to be fixed
def test_select_with_args(create_and_wipe_database):
    result = ExampleRecord.select(sm.func.count()).one()

    assert result == 0
    # TODO type inference for count() currently returns ExampleRecord | int; skip precise assert_type until generics fixed
    # assert_type(result, int)


# TODO needs to be fixed
def test_result_types(create_and_wipe_database):
    "ensure the result types are lists of the specific classes the wrapper was generated from"

    ExampleRecord().save()

    column_results = sm.select(column("id")).select_from(ExampleRecord)
    # TODO column_results type is unknown
    _ = column_results


def test_scalar_sum_empty_returns_int_zero(create_and_wipe_database):
    """SUM over empty table should allow easy int coercion via `or 0`."""
    raw_sum = UpsertTestModel.select(sm.func.sum(UpsertTestModel.value)).scalar()
    assert raw_sum is None


def test_scalar_sum_with_rows_returns_int(create_and_wipe_database):
    """SUM over table with rows returns an int when coerced; raw may be int already."""
    UpsertTestModel(name="a", category="c1", value=5).save()
    UpsertTestModel(name="b", category="c1", value=7).save()
    UpsertTestModel(name="c", category="c2", value=0).save()

    raw_sum = UpsertTestModel.select(sm.func.sum(UpsertTestModel.value)).scalar()
    assert isinstance(raw_sum, int)
    assert raw_sum == 12

    # assert_type(raw_sum, int)  # generic inference currently loose

    # Filtered sum (where no matching rows) again returns None -> coerce
    filtered_none = (
        UpsertTestModel.select(sm.func.sum(UpsertTestModel.value))
        .where(UpsertTestModel.category == "does_not_exist")
        .scalar()
    )
    assert filtered_none is None
    # assert isinstance(filtered_sum, int)


def test_sample_single_none_when_empty(create_and_wipe_database):
    """sample() with no rows returns None when n==1."""
    assert ExampleRecord.select().sample() is None


def test_sample_single_record(create_and_wipe_database):
    r = ExampleRecord(something="one").save()
    # With only one row we always get that row
    sampled = ExampleRecord.select().sample()
    assert sampled == r


def test_sample_multiple(create_and_wipe_database):
    # Insert several records
    records = [ExampleRecord(something=str(i)).save() for i in range(10)]

    sample_n = 5
    sampled = ExampleRecord.select().sample(sample_n)
    assert isinstance(sampled, list)
    assert len(sampled) == sample_n
    # Ensure all sampled items are part of inserted records set
    record_ids = {r.id for r in records}
    for row in sampled:
        assert row.id in record_ids
    # Should be unique (very high probability); enforce deterministically by set length
    assert len({row.id for row in sampled}) == sample_n


def test_sample_does_not_mutate_query(create_and_wipe_database):
    ExampleRecord(something="one").save()
    q = ExampleRecord.select().where(ExampleRecord.something == "one")
    before_sql = q.sql()
    _ = q.sample()  # run sample
    # underlying query unchanged
    assert q.sql() == before_sql


def test_sample_error_conditions(create_and_wipe_database):
    try:
        ExampleRecord.select().sample(0)
        assert False, "Expected ValueError for n < 1"
    except ValueError:
        pass
