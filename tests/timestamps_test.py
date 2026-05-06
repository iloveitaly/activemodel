from whenever import ZonedDateTime

from tests.models import ExampleRecord


def test_created_at_is_set_on_save(create_and_wipe_database):
    record = ExampleRecord().save()
    assert isinstance(record.created_at, ZonedDateTime)


def test_updated_at_is_set_on_save(create_and_wipe_database):
    record = ExampleRecord().save()
    assert isinstance(record.updated_at, ZonedDateTime)


def test_created_at_does_not_change_on_update(create_and_wipe_database):
    record = ExampleRecord().save()
    created_at = record.created_at

    record.something = "changed"
    record.save()

    refreshed = ExampleRecord.get(record.id)
    assert refreshed is not None
    assert refreshed.created_at == created_at


def test_updated_at_changes_on_update(create_and_wipe_database):
    record = ExampleRecord().save()
    original_updated_at = record.updated_at

    record.something = "changed"
    updated = record.save()

    refreshed = ExampleRecord.get(updated.id)
    assert refreshed is not None
    assert isinstance(refreshed.updated_at, ZonedDateTime)
    assert refreshed.updated_at != original_updated_at
