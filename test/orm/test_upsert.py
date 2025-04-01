import pytest
from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from activemodel import BaseModel
from activemodel.mixins.typeid import TypeIDMixin
from test.models import UpsertTestModel


def test_upsert_single_unique_field(create_and_wipe_database):
    """Test upsert with a single unique field"""
    # Create initial record
    UpsertTestModel.upsert(
        data={"name": "test1", "category": "A", "value": 10},
        unique_by="name",
    )

    # Get record to verify it was created
    record = UpsertTestModel.get(name="test1")
    assert record is not None
    assert record.name == "test1"
    assert record.category == "A"
    assert record.value == 10

    # Perform upsert that updates the existing record
    UpsertTestModel.upsert(
        data={"name": "test1", "category": "B", "value": 20},
        unique_by="name",
    )

    assert UpsertTestModel.count() == 1

    record = UpsertTestModel.first()
    assert record
    assert record.name == "test1"
    assert record.category == "B"
    assert record.value == 20


def test_upsert_multiple_unique_fields(create_and_wipe_database):
    """Test upsert with multiple unique fields"""
    # Create initial records
    UpsertTestModel.upsert(
        data={"name": "multi1", "category": "X", "value": 100},
        unique_by=["name", "category"],
    )

    UpsertTestModel.upsert(
        data={"name": "multi2", "category": "X", "value": 200},
        unique_by=["name", "category"],
    )

    assert UpsertTestModel.count() == 2

    # Update one record based on both unique fields
    UpsertTestModel.upsert(
        data={"name": "multi1", "category": "X", "value": 150},
        unique_by=["name", "category"],
    )

    # Get records to verify one was updated and one unchanged
    record_x = UpsertTestModel.one(name="multi1", category="X")
    record_y = UpsertTestModel.one(name="multi2", category="X")

    assert record_x.value == 150  # Updated
    assert record_y.value == 200  # Unchanged


def test_upsert_single_update_field(create_and_wipe_database):
    """Test upsert that updates a single field"""
    # Create initial record
    UpsertTestModel.upsert(
        data={"name": "update1", "category": "Z", "value": 5, "description": "Initial"},
        unique_by="name",
    )

    # Perform upsert that only updates the value
    UpsertTestModel.upsert(
        data={"name": "update1", "category": "Z", "value": 25},
        unique_by="name",
    )

    # Get record to verify field was updated
    record = UpsertTestModel.get(name="update1")
    assert record.value == 25  # Updated
    assert record.category == "Z"  # Unchanged
    assert record.description == "Initial"  # Unchanged


def test_upsert_multiple_update_fields(create_and_wipe_database):
    """Test upsert that updates multiple fields"""
    # Create initial record
    UpsertTestModel.upsert(
        data={"name": "update2", "category": "M", "value": 42, "description": "Old"},
        unique_by="name",
    )

    # Perform upsert that updates multiple fields
    UpsertTestModel.upsert(
        data={"name": "update2", "value": 99, "description": "New", "category": "N"},
        unique_by="name",
    )

    # Get record to verify all fields were updated
    record = UpsertTestModel.get(name="update2")
    assert record.value == 99
    assert record.description == "New"
    assert record.category == "N"
