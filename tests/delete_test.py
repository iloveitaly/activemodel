from activemodel import BaseModel
from activemodel.mixins import TypeIDMixin


class DeleteExampleWithId(BaseModel, TypeIDMixin("delete_test"), table=True):
    pass


def test_delete(create_and_wipe_database):
    example = DeleteExampleWithId().save()

    assert DeleteExampleWithId.count() == 1

    result = example.delete()

    assert DeleteExampleWithId.count() == 0
    assert result is True
