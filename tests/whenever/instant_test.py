from pydantic import BaseModel as PydanticBaseModel
from whenever import Instant

from .models import WheneverModel


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
    class Schema(PydanticBaseModel):
        ts: Instant

    now = Instant.now()
    schema = Schema(ts=now)
    assert schema.ts == now

    json_str = schema.model_dump_json()
    restored = Schema.model_validate_json(json_str)
    assert restored.ts == now


def test_instant_pydantic_from_string():
    class Schema(PydanticBaseModel):
        ts: Instant

    iso = "2024-01-15T12:00:00Z"
    schema = Schema.model_validate({"ts": iso})
    assert isinstance(schema.ts, Instant)
    assert schema.ts == Instant.parse_iso(iso)


def test_instant_type_decorator_accepts_string(create_and_wipe_database):
    iso = "2024-06-01T10:00:00Z"
    record = WheneverModel(triggered_at=Instant.parse_iso(iso)).save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.triggered_at == Instant.parse_iso(iso)


def test_nullable_fields(create_and_wipe_database):
    record = WheneverModel().save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.triggered_at is None
    assert fetched.scheduled_at is None