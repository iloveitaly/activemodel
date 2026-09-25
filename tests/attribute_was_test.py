from typing import assert_type, cast

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import InstrumentedAttribute
from sqlmodel import Field

from activemodel import BaseModel
from activemodel.session_manager import get_session


class AttributeWasRecord(BaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    value: str | None = None
    other: str | None = None


VALUE = cast(InstrumentedAttribute[str | None], AttributeWasRecord.value)
OTHER = cast(InstrumentedAttribute[str | None], AttributeWasRecord.other)


@pytest.fixture
def history_session(create_and_wipe_database):
    with get_session() as session:
        yield session


@pytest.mark.parametrize("value", [None, "", "original"])
def test_attribute_was_without_history(value):
    record = AttributeWasRecord(value=value)
    assert_type(record.attribute_was(VALUE), str | None)
    assert record.attribute_was(VALUE) == value


@pytest.mark.parametrize("original", [None, "", "original"])
def test_attribute_was_preserves_original_until_flush(history_session, original):
    record = AttributeWasRecord(value=original)
    history_session.add(record)
    history_session.flush()

    assert record.attribute_was(VALUE) == original
    record.value = "first change"
    record.value = "second change"
    assert record.attribute_was(VALUE) == original
    assert record.value == "second change"
    assert record.modified_fields() == {"value"}

    history_session.flush()
    assert record.attribute_was(VALUE) == "second change"
    record.value = None
    assert record.attribute_was(VALUE) == "second change"


def test_attribute_was_loads_expired_value(history_session):
    record = AttributeWasRecord(value="original")
    history_session.add(record)
    history_session.commit()

    state = inspect(record)
    assert state is not None
    assert "value" in state.expired_attributes
    assert record.attribute_was(VALUE) == "original"
    record.value = "changed"
    assert record.attribute_was(VALUE) == "original"


def test_attribute_was_cannot_recover_overwritten_expired_value(history_session):
    record = AttributeWasRecord(value="original")
    history_session.add(record)
    history_session.commit()

    record.value = "changed"
    assert record.attribute_was(VALUE) == "changed"


def test_attribute_was_on_loaded_detached_record(history_session):
    record = AttributeWasRecord(value="original")
    history_session.add(record)
    history_session.flush()
    history_session.expunge(record)

    record.value = "changed"
    assert record.attribute_was(VALUE) == "original"


@pytest.mark.parametrize(
    ("original", "updated"),
    [(None, "changed"), ("original", None), ("", "changed")],
)
def test_dirty_tracking_detects_net_changes(history_session, original, updated):
    record = AttributeWasRecord(value=original)
    history_session.add(record)
    history_session.flush()

    assert_type(record.has_attribute_changed(VALUE), bool)
    assert_type(record.modified_fields(), set[str])
    assert not record.has_attribute_changed(VALUE)
    assert record.modified_fields() == set()

    record.value = original
    assert not record.has_attribute_changed(VALUE)
    assert record.modified_fields() == set()

    record.value = updated
    assert record.has_attribute_changed(VALUE)
    assert record.attribute_was(VALUE) == original
    assert record.modified_fields() == {"value"}

    record.value = original
    assert not record.has_attribute_changed(VALUE)
    assert record.modified_fields() == set()


def test_dirty_tracking_multiple_fields_and_flush(history_session):
    record = AttributeWasRecord(value="original", other="unchanged")
    history_session.add(record)
    history_session.flush()

    record.value = "changed"
    record.other = None
    assert record.has_attribute_changed(VALUE)
    assert record.has_attribute_changed(OTHER)
    assert record.modified_fields() == {"value", "other"}

    record.other = "unchanged"
    assert not record.has_attribute_changed(OTHER)
    assert record.modified_fields() == {"value"}

    history_session.flush()
    assert not record.has_attribute_changed(VALUE)
    assert record.modified_fields() == set()


def test_dirty_tracking_resets_on_save_and_refresh(create_and_wipe_database):
    record = AttributeWasRecord(value="original").save()
    assert not record.has_attribute_changed(VALUE)
    assert record.modified_fields() == set()

    record.value = "changed"
    assert record.has_attribute_changed(VALUE)
    record.save()
    assert not record.has_attribute_changed(VALUE)
    assert record.modified_fields() == set()

    record.value = None
    record.refresh()
    assert record.value == "changed"
    assert not record.has_attribute_changed(VALUE)
    assert record.modified_fields() == set()


def test_dirty_tracking_respects_explicit_flag_modified(history_session):
    record = AttributeWasRecord(value=None)
    history_session.add(record)
    history_session.flush()

    record.flag_modified("value")
    assert record.has_attribute_changed(VALUE)
    assert record.modified_fields() == {"value"}


def test_dirty_tracking_does_not_load_expired_attributes(history_session):
    record = AttributeWasRecord(value="original")
    history_session.add(record)
    history_session.commit()
    state = inspect(record)
    assert state is not None
    expired = state.expired_attributes.copy()

    assert not record.has_attribute_changed(VALUE)
    assert record.modified_fields() == set()
    assert state.expired_attributes == expired

    record.value = "original"
    # Without active_history, the unloaded original cannot be compared.
    assert record.has_attribute_changed(VALUE)
    assert record.modified_fields() == {"value"}


def test_dirty_tracking_on_new_record():
    record = AttributeWasRecord(value="new")
    assert record.has_attribute_changed(VALUE)
    assert "value" in record.modified_fields()
