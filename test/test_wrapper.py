from typing import Any, Generator, assert_type

import sqlmodel as sm
from sqlmodel.sql.expression import SelectOfScalar

from activemodel.query_wrapper import QueryWrapper
from test.models import ExampleRecord


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


def test_select_with_args():
    result = ExampleRecord.select(sm.func.max(ExampleRecord.id)).one()


def test_result_types():
    "ensure the result types are lists of the specific classes the wrapper was generated from"

    ExampleRecord().save()

    s = sm.select("id").select_from(ExampleRecord)
    result = ExampleRecord.select().all()
