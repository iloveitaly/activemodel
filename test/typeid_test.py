import pytest
from typeid import TypeID

from test.utils import temporary_tables

from activemodel import BaseModel
from activemodel.mixins import TypeIDMixin


def test_enforces_unique_prefixes():
    TypeIDMixin("hi")

    with pytest.raises(AssertionError):
        TypeIDMixin("hi")


def test_no_empty_prefixes_test():
    with pytest.raises(AssertionError):
        TypeIDMixin("")


TYPEID_PREFIX = "myid"


class ExampleWithId(BaseModel, TypeIDMixin(TYPEID_PREFIX), table=True):
    pass


# the UIDs stored in the DB are NOT the same as the
def test_get_through_prefixed_uid():
    type_uid = TypeID(prefix=TYPEID_PREFIX)

    with temporary_tables():
        record = ExampleWithId.get(type_uid)
        assert record is None


def test_get_through_prefixed_uid_as_str():
    type_uid = TypeID(prefix=TYPEID_PREFIX)

    with temporary_tables():
        record = ExampleWithId.get(str(type_uid))
        assert record is None


def test_get_through_plain_uid_as_str():
    type_uid = TypeID(prefix=TYPEID_PREFIX)

    with temporary_tables():
        # pass uid as string. Ex: '01942886-7afc-7129-8f57-db09137ed002'
        record = ExampleWithId.get(str(type_uid.uuid))
        assert record is None


def test_get_through_plain_uid():
    type_uid = TypeID(prefix=TYPEID_PREFIX)

    with temporary_tables():
        record = ExampleWithId.get(type_uid.uuid)
        assert record is None
