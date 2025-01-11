from activemodel import BaseModel
from activemodel.mixins import TypeIDMixin

TYPEID_PREFIX = "myid"


class ExampleWithId(BaseModel, TypeIDMixin(TYPEID_PREFIX), table=True):
    pass


def test_delete(create_and_wipe_database):
    example = ExampleWithId().save()

    assert ExampleWithId.count() == 1

    result = example.delete()

    assert ExampleWithId.count() == 0
    assert result is True
