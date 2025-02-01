from typing import Any, Generator, assert_type

import sqlmodel as sm
from sqlalchemy import column
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


# TODO needs to be fixed
def test_select_with_args(create_and_wipe_database):
    result = ExampleRecord.select(sm.func.count()).one()

    assert result == 0
    # TODO shouldn't this fail?
    assert_type(result, int)


# TODO needs to be fixed
def test_result_types(create_and_wipe_database):
    "ensure the result types are lists of the specific classes the wrapper was generated from"

    ExampleRecord().save()

    column_results = sm.select(column("id")).select_from(ExampleRecord)
    # TODO column_results type is unknown
