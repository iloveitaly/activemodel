from datetime import datetime, timezone

from whenever import Instant

from tests.whenever.models import WheneverModel, WheneverSchema


def test_instant_round_trip(create_and_wipe_database):
    now = Instant.now()
    record = WheneverModel(triggered_at=now).save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.triggered_at is not None
    assert isinstance(fetched.triggered_at, Instant)
    # microsecond precision — whenever uses nanoseconds but DB stores microseconds
    assert fetched.triggered_at.timestamp_millis() == now.timestamp_millis()
    # object equality should also work!
    assert fetched.triggered_at == now


def test_instant_pydantic_serialization():
    now = Instant.now()
    schema = WheneverSchema(instant=now, zoned_datetime="2024-01-15T12:00:00+00:00[UTC]")
    assert schema.instant == now

    json_str = schema.model_dump_json()
    restored = WheneverSchema.model_validate_json(json_str)
    assert restored.instant == now


def test_instant_pydantic_from_string():
    iso = "2024-01-15T12:00:00Z"
    schema = WheneverSchema.model_validate(
        {"instant": iso, "zoned_datetime": "2024-01-15T12:00:00+00:00[UTC]"}
    )
    assert isinstance(schema.instant, Instant)
    assert schema.instant == Instant.parse_iso(iso)


def test_instant_pydantic_json_schema():
    json_schema = WheneverSchema.model_json_schema()

    assert json_schema["properties"]["instant"]["type"] == "string"
    assert json_schema["properties"]["instant"]["title"] == "Instant"
    assert "instant" in json_schema["required"]


def test_instant_type_decorator_accepts_string(create_and_wipe_database):
    iso = "2024-06-01T10:00:00Z"
    record = WheneverModel(triggered_at=Instant.parse_iso(iso)).save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.triggered_at == Instant.parse_iso(iso)


def test_instant_accepts_datetime_assignment(create_and_wipe_database):
    value = datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc)
    record = WheneverModel()
    record.triggered_at = value  # type: ignore[assignment]
    record.save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.triggered_at is not None
    assert isinstance(fetched.triggered_at, Instant)
    assert fetched.triggered_at == Instant(value)


def test_nullable_fields(create_and_wipe_database):
    record = WheneverModel().save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.triggered_at is None
    assert fetched.scheduled_at is None