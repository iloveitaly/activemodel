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


def test_list():
    class TestRecord(
        BaseModel, TimestampsMixin, TypeIDMixin("test_record"), table=True
    ):
        pass

    with temporary_tables():
        # create 10 example records
        for i in range(10):
            TestRecord().save()

        assert TestRecord.count() == 10

        all_records = list(TestRecord.all())
        assert len(all_records) == 10

        record = all_records[0]
        assert isinstance(record, TestRecord)
