import datetime

from whenever import Time

from tests.whenever.models import WheneverModel, WheneverSchema, example_whenever


def test_time_round_trip(create_and_wipe_database):
    alarm = Time.parse_iso("07:30:00")
    record = WheneverModel(alarm_time=alarm).save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.alarm_time is not None
    assert isinstance(fetched.alarm_time, Time)
    assert fetched.alarm_time == alarm


def test_time_nullable(create_and_wipe_database):
    record = WheneverModel().save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.alarm_time is None


def test_time_pydantic_serialization():
    t = Time.parse_iso("07:30:00")
    schema = example_whenever(time=t)
    assert schema.time == t

    json_str = schema.model_dump_json()
    restored = WheneverSchema.model_validate_json(json_str)
    assert restored.time == t


def test_time_pydantic_from_string():
    iso = "07:30:00"
    schema = WheneverSchema.model_validate(example_whenever(time=iso).model_dump())
    assert isinstance(schema.time, Time)
    assert schema.time == Time.parse_iso(iso)


def test_time_pydantic_json_schema():
    json_schema = WheneverSchema.model_json_schema()
    assert json_schema["properties"]["time"]["type"] == "string"


def test_time_accepts_stdlib_time_assignment(create_and_wipe_database):
    value = datetime.time(7, 30, 0)
    record = WheneverModel()
    record.alarm_time = value  # type: ignore[assignment]
    record.save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.alarm_time is not None
    assert isinstance(fetched.alarm_time, Time)
    assert fetched.alarm_time == Time(value)
