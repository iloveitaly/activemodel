from activemodel import BaseModel
from activemodel.mixins import TypeIDPrimaryKey
from typeid import TypeID


class DeleteExampleWithId(BaseModel, table=True):
    id: TypeID = TypeIDPrimaryKey("delete_test")


def test_delete(create_and_wipe_database):
    example = DeleteExampleWithId().save()

    assert DeleteExampleWithId.count() == 1

    result = example.delete()

    assert DeleteExampleWithId.count() == 0
    assert result is True
