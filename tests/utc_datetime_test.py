from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import StatementError
from sqlmodel import Field
from typeid import TypeID

from activemodel import BaseModel
from activemodel.mixins import TypeIDPrimaryKey


class DatedRecord(BaseModel, table=True):
    id: TypeID = TypeIDPrimaryKey("dated")
    ends_at: datetime | None = Field(default=None)

    def before_create(self):
        if self.ends_at is None:
            self.ends_at = datetime.now(UTC) + timedelta(days=30)


def test_naive_datetime_is_rejected(create_and_wipe_database):
    record = DatedRecord(ends_at=datetime.now())  # noqa: DTZ005

    with pytest.raises(StatementError, match="timezone information"):
        record.save()


def test_aware_utc_datetime_round_trips(create_and_wipe_database):
    value = datetime(2024, 6, 1, 10, 0, tzinfo=UTC)
    record = DatedRecord(ends_at=value).save()

    fetched = DatedRecord.get(record.id)

    assert fetched is not None
    assert fetched.ends_at == value


def test_before_create_default_is_aware(create_and_wipe_database):
    record = DatedRecord().save()

    assert record.ends_at is not None
    assert record.ends_at.tzinfo is not None
