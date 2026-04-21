from datetime import datetime
from zoneinfo import ZoneInfo

from whenever import ZonedDateTime

from tests.whenever.models import WheneverModel, WheneverSchema, example_whenever


def test_zoned_datetime_round_trip(create_and_wipe_database):
    now = ZonedDateTime.now("America/New_York")
    record = WheneverModel(scheduled_at=now).save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.scheduled_at is not None
    assert isinstance(fetched.scheduled_at, ZonedDateTime)
    assert fetched.scheduled_at.timestamp_millis() == now.timestamp_millis()


def test_zoned_datetime_pydantic_serialization():
    now = ZonedDateTime.now("Europe/Amsterdam")
    schema = example_whenever(zoned_datetime=now)
    assert schema.zoned_datetime == now

    json_str = schema.model_dump_json()
    restored = WheneverSchema.model_validate_json(json_str)
    assert restored.zoned_datetime.timestamp_millis() == now.timestamp_millis()


def test_zoned_datetime_pydantic_json_schema():
    json_schema = WheneverSchema.model_json_schema()

    assert json_schema["properties"]["zoned_datetime"]["type"] == "string"
    assert json_schema["properties"]["zoned_datetime"]["title"] == "Zoned Datetime"
    assert "zoned_datetime" in json_schema["required"]


def test_zoned_datetime_accepts_datetime_assignment(create_and_wipe_database):
    value = datetime(2024, 6, 1, 10, 0, tzinfo=ZoneInfo("America/New_York"))
    record = WheneverModel()
    record.scheduled_at = value
    record.save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.scheduled_at is not None
    assert isinstance(fetched.scheduled_at, ZonedDateTime)
    assert fetched.scheduled_at == ZonedDateTime(value)
