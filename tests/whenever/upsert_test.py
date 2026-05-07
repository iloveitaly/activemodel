from whenever import Date, Instant, Time, ZonedDateTime

from tests.models import WheneverUpsertModel


def test_upsert_insert_with_whenever_fields(create_and_wipe_database):
    now = Instant.now()
    scheduled = ZonedDateTime(2025, 6, 1, 9, 0, tz="America/New_York")
    bday = Date(1990, 3, 15)
    alarm = Time(7, 30, 0)

    result = WheneverUpsertModel.upsert(
        data={
            "external_id": "user_123",
            "last_active_at": now,
            "scheduled_at": scheduled,
            "birthday": bday,
            "alarm_time": alarm,
        },
        unique_by="external_id",
    )

    assert result is not None
    assert result.last_active_at == now.round("microsecond", mode="floor")
    assert result.scheduled_at == scheduled
    assert result.birthday == bday
    assert result.alarm_time == alarm

    fetched = WheneverUpsertModel.one(external_id="user_123")
    assert fetched.id == result.id
    assert fetched.last_active_at == now.round("microsecond", mode="floor")
    assert fetched.scheduled_at == scheduled
    assert fetched.birthday == bday
    assert fetched.alarm_time == alarm


def test_upsert_update_whenever_fields_on_conflict(create_and_wipe_database):
    first_active = Instant.now()
    WheneverUpsertModel.upsert(
        data={"external_id": "user_123", "last_active_at": first_active},
        unique_by="external_id",
    )

    second_active = Instant.now()
    result = WheneverUpsertModel.upsert(
        data={"external_id": "user_123", "last_active_at": second_active},
        unique_by="external_id",
    )

    assert result.last_active_at == second_active.round("microsecond", mode="floor")
    assert WheneverUpsertModel.count() == 1

    fetched = WheneverUpsertModel.one(external_id="user_123")
    assert fetched.id == result.id
    assert fetched.last_active_at == second_active.round("microsecond", mode="floor")


def test_upsert_partial_update_preserves_existing_whenever_fields(create_and_wipe_database):
    bday = Date(1990, 3, 15)
    alarm = Time(7, 30, 0)
    scheduled = ZonedDateTime(2025, 6, 1, 9, 0, tz="America/New_York")
    initial_active = Instant.now()

    WheneverUpsertModel.upsert(
        data={
            "external_id": "user_123",
            "last_active_at": initial_active,
            "birthday": bday,
            "alarm_time": alarm,
            "scheduled_at": scheduled,
        },
        unique_by="external_id",
    )

    new_active = Instant.now()
    result = WheneverUpsertModel.upsert(
        data={"external_id": "user_123", "last_active_at": new_active},
        unique_by="external_id",
    )

    assert result.last_active_at == new_active.round("microsecond", mode="floor")

    fetched = WheneverUpsertModel.one(external_id="user_123")
    assert fetched.last_active_at == new_active.round("microsecond", mode="floor")
    # Columns absent from data are preserved in DB
    assert fetched.birthday == bday
    assert fetched.alarm_time == alarm
    assert fetched.scheduled_at == scheduled


def test_upsert_with_date_field_in_data(create_and_wipe_database):
    bday = Date(1985, 12, 25)

    result = WheneverUpsertModel.upsert(
        data={"external_id": "user_123", "birthday": bday},
        unique_by="external_id",
    )

    assert result is not None
    assert result.birthday == bday

    fetched = WheneverUpsertModel.one(external_id="user_123")
    assert fetched.birthday == bday
