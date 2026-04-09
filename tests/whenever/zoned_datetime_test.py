from pydantic import BaseModel as PydanticBaseModel
from whenever import ZonedDateTime

from .models import WheneverModel


def test_zoned_datetime_round_trip(create_and_wipe_database):
    now = ZonedDateTime.now("America/New_York")
    record = WheneverModel(scheduled_at=now).save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.scheduled_at is not None
    assert isinstance(fetched.scheduled_at, ZonedDateTime)
    assert fetched.scheduled_at.timestamp_millis() == now.timestamp_millis()


def test_zoned_datetime_pydantic_serialization():
    class Schema(PydanticBaseModel):
        ts: ZonedDateTime

    now = ZonedDateTime.now("Europe/Amsterdam")
    schema = Schema(ts=now)
    assert schema.ts == now

    json_str = schema.model_dump_json()
    restored = Schema.model_validate_json(json_str)
    assert restored.ts.timestamp_millis() == now.timestamp_millis()