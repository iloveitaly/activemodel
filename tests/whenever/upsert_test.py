from whenever import Date, Instant, Time, ZonedDateTime

from tests.models import WheneverUpsertModel

CLERK_ID = "user_clerk_123"


def test_upsert_insert_with_whenever_fields(create_and_wipe_database):
    now = Instant.now()
    scheduled = ZonedDateTime(2025, 6, 1, 9, 0, tz="America/New_York")
    bday = Date(1990, 3, 15)
    alarm = Time(7, 30, 0)

    result = WheneverUpsertModel.upsert(
        data={
            "clerk_id": CLERK_ID,
            "last_active_at": now,
            "scheduled_at": scheduled,
            "birthday": bday,
            "alarm_time": alarm,
        },
        unique_by="clerk_id",
    )

    assert result is not None
    assert result.clerk_id == CLERK_ID
    assert result.last_active_at == now
    assert result.scheduled_at == scheduled
    assert result.birthday == bday
    assert result.alarm_time == alarm

    fetched = WheneverUpsertModel.one(clerk_id=CLERK_ID)
    assert fetched.id == result.id
    assert fetched.last_active_at == now
    assert fetched.scheduled_at == scheduled
    assert fetched.birthday == bday
    assert fetched.alarm_time == alarm


def test_upsert_update_whenever_fields_on_conflict(create_and_wipe_database):
    first_active = Instant.now()
    WheneverUpsertModel.upsert(
        data={"clerk_id": CLERK_ID, "last_active_at": first_active},
        unique_by="clerk_id",
    )

    second_active = Instant.now()
    result = WheneverUpsertModel.upsert(
        data={"clerk_id": CLERK_ID, "last_active_at": second_active},
        unique_by="clerk_id",
    )

    assert result.last_active_at == second_active
    assert WheneverUpsertModel.count() == 1

    fetched = WheneverUpsertModel.one(clerk_id=CLERK_ID)
    assert fetched.id == result.id
    assert fetched.last_active_at == second_active


def test_upsert_partial_update_preserves_existing_whenever_fields(create_and_wipe_database):
    bday = Date(1990, 3, 15)
    alarm = Time(7, 30, 0)
    scheduled = ZonedDateTime(2025, 6, 1, 9, 0, tz="America/New_York")
    initial_active = Instant.now()

    WheneverUpsertModel.upsert(
        data={
            "clerk_id": CLERK_ID,
            "last_active_at": initial_active,
            "birthday": bday,
            "alarm_time": alarm,
            "scheduled_at": scheduled,
        },
        unique_by="clerk_id",
    )

    new_active = Instant.now()
    result = WheneverUpsertModel.upsert(
        data={"clerk_id": CLERK_ID, "last_active_at": new_active},
        unique_by="clerk_id",
    )

    assert result.last_active_at == new_active

    fetched = WheneverUpsertModel.one(clerk_id=CLERK_ID)
    assert fetched.last_active_at == new_active
    # Columns absent from data are preserved in DB
    assert fetched.birthday == bday
    assert fetched.alarm_time == alarm
    assert fetched.scheduled_at == scheduled


def test_upsert_with_date_field_in_data(create_and_wipe_database):
    bday = Date(1985, 12, 25)

    result = WheneverUpsertModel.upsert(
        data={"clerk_id": CLERK_ID, "birthday": bday},
        unique_by="clerk_id",
    )

    assert result is not None
    assert result.birthday == bday

    fetched = WheneverUpsertModel.one(clerk_id=CLERK_ID)
    assert fetched.birthday == bday
