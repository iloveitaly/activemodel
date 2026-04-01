from activemodel.utils import is_database_empty
from tests.models import ExampleRecord


def test_is_database_empty(create_and_wipe_database):
    # check that the database is initially empty
    assert is_database_empty() is True

    # add a record to one of the tables
    record = ExampleRecord(something="test")
    record.save()

    # check that the database is no longer empty
    assert is_database_empty() is False

    # check that excluding the table returns True
    assert is_database_empty(exclude=[ExampleRecord]) is True
