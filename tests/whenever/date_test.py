import datetime

from whenever import Date

from tests.whenever.models import WheneverModel, WheneverSchema, example_whenever


def test_date_round_trip(create_and_wipe_database):
    birthday = Date.parse_iso("1990-06-15")
    record = WheneverModel(birthday=birthday).save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.birthday is not None
    assert isinstance(fetched.birthday, Date)
    assert fetched.birthday == birthday


def test_date_nullable(create_and_wipe_database):
    record = WheneverModel().save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.birthday is None


def test_date_pydantic_serialization():
    d = Date.parse_iso("2024-01-15")
    schema = example_whenever(date=d)
    assert schema.date == d

    json_str = schema.model_dump_json()
    restored = WheneverSchema.model_validate_json(json_str)
    assert restored.date == d


def test_date_pydantic_from_string():
    iso = "2024-06-15"
    schema = WheneverSchema.model_validate(example_whenever(date=iso).model_dump())
    assert isinstance(schema.date, Date)
    assert schema.date == Date.parse_iso(iso)


def test_date_pydantic_json_schema():
    json_schema = WheneverSchema.model_json_schema()
    assert json_schema["properties"]["date"]["type"] == "string"
    assert json_schema["properties"]["date"]["format"] == "date"


def test_date_accepts_stdlib_date_assignment(create_and_wipe_database):
    value = datetime.date(2024, 6, 15)
    record = WheneverModel()
    record.birthday = value  # type: ignore[assignment]
    record.save()

    fetched = WheneverModel.get(record.id)
    assert fetched is not None
    assert fetched.birthday is not None
    assert isinstance(fetched.birthday, Date)
    assert fetched.birthday == Date(value)
