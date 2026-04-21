from activemodel import BaseModel
from activemodel.mixins import SoftDeletionMixin, TypeIDPrimaryKey
from typeid import TypeID


class SoftDeleteExample(BaseModel, SoftDeletionMixin, table=True):
    id: TypeID = TypeIDPrimaryKey("soft_delete")


def test_soft_delete_sets_timestamp_and_persists(create_and_wipe_database):
    example = SoftDeleteExample().save()

    result = example.soft_delete()
    persisted = SoftDeleteExample.get(example.id)

    assert result is example
    assert example.deleted_at is not None
    assert example.deleted_at.tzinfo is not None
    assert persisted is not None
    assert persisted.deleted_at == example.deleted_at
    assert SoftDeleteExample.count() == 1
