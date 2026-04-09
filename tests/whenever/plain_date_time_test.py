from datetime import datetime

from whenever import PlainDateTime

from tests.whenever.models import WheneverModel, WheneverSchema, example_whenever


def test_plain_datetime_round_trip(create_and_wipe_database):
    now = PlainDateTime.parse_iso("2024-06-01T10:00:00")
    record = WheneverModel(plain_datetime=now).save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.plain_datetime is not None
    assert isinstance(fetched.plain_datetime, PlainDateTime)
    assert fetched.plain_datetime == now


def test_plain_datetime_pydantic_serialization():
    now = PlainDateTime.parse_iso("2024-06-01T10:00:00")
    schema = example_whenever(plain_datetime=now)
    assert schema.plain_datetime == now

    json_str = schema.model_dump_json()
    restored = WheneverSchema.model_validate_json(json_str)
    assert restored.plain_datetime == now


def test_plain_datetime_pydantic_from_string():
    iso = "2024-06-01T10:00:00"
    schema = WheneverSchema.model_validate(example_whenever(plain_datetime=iso).model_dump())
    assert isinstance(schema.plain_datetime, PlainDateTime)
    assert schema.plain_datetime == PlainDateTime.parse_iso(iso)


def test_plain_datetime_pydantic_json_schema():
    json_schema = WheneverSchema.model_json_schema()

    assert json_schema["properties"]["plain_datetime"]["type"] == "string"
    assert json_schema["properties"]["plain_datetime"]["title"] == "Plain Datetime"
    assert "plain_datetime" in json_schema["required"]


def test_plain_datetime_accepts_datetime_assignment(create_and_wipe_database):
    value = datetime(2024, 6, 1, 10, 0)
    record = WheneverModel()
    record.plain_datetime = value  # type: ignore[assignment]
    record.save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.plain_datetime is not None
    assert isinstance(fetched.plain_datetime, PlainDateTime)
    assert fetched.plain_datetime == PlainDateTime(value)