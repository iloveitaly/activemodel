import pytest

from tests.models import (
    CompoundUniqueUpsertModel,
    ExampleRecord,
    UpsertTestModel,
    WheneverUpsertModel,
)


def test_unique_constraints_lists_unique_indexes_and_constraints(
    create_and_wipe_database,
):
    assert WheneverUpsertModel.unique_constraints() == [["external_id"]]
    assert CompoundUniqueUpsertModel.unique_constraints() == [["film_id", "email"]]
    assert ExampleRecord.unique_constraints() == [["another_with_index"]]

    # Field(unique=True) plus a compound UniqueConstraint — both listed
    assert UpsertTestModel.unique_constraints() == [
        ["name"],
        ["name", "category"],
    ]


def test_upsert_infers_unique_by_from_single_constraint(create_and_wipe_database):
    result = CompoundUniqueUpsertModel.upsert(
        data={"film_id": "film_1", "email": "a@example.com", "note": "first"},
    )

    assert result.note == "first"
    assert CompoundUniqueUpsertModel.count() == 1

    updated = CompoundUniqueUpsertModel.upsert(
        data={"film_id": "film_1", "email": "a@example.com", "note": "greenlit"},
    )

    assert updated.id == result.id
    assert updated.note == "greenlit"
    assert CompoundUniqueUpsertModel.count() == 1


def test_upsert_infers_unique_by_from_unique_index(create_and_wipe_database):
    result = ExampleRecord.upsert(
        data={"something": "a", "another_with_index": "unique-key"},
    )
    updated = ExampleRecord.upsert(
        data={"something": "b", "another_with_index": "unique-key"},
    )

    assert updated.id == result.id
    assert updated.something == "b"
    assert ExampleRecord.count() == 1


def test_upsert_requires_unique_by_when_multiple_constraints(
    create_and_wipe_database,
):
    with pytest.raises(AssertionError, match="multiple unique constraints"):
        UpsertTestModel.upsert(
            data={"name": "x", "category": "y", "value": 1},
        )

    # Explicit unique_by still works when inference is ambiguous
    result = UpsertTestModel.upsert(
        data={"name": "x", "category": "y", "value": 1},
        unique_by="name",
    )
    assert result.name == "x"


def test_upsert_instance_uses_exclude_unset_fields(create_and_wipe_database):
    created = CompoundUniqueUpsertModel(
        film_id="film_2",
        email="b@example.com",
        note="initial",
    ).upsert()

    assert created.note == "initial"
    assert CompoundUniqueUpsertModel.count() == 1

    updated = CompoundUniqueUpsertModel(
        film_id="film_2",
        email="b@example.com",
        note="updated",
    ).upsert()

    assert updated.id == created.id
    assert updated.note == "updated"
    assert CompoundUniqueUpsertModel.count() == 1


def test_upsert_single_unique_field(create_and_wipe_database):
    """Test upsert with a single unique field"""
    # Create initial record
    result = UpsertTestModel.upsert(
        data={"name": "test1", "category": "A", "value": 10},
        unique_by="name",
    )

    # 3. Ensure return value is never null
    assert result is not None

    # 2. Check field values on returned model
    assert result.name == "test1"
    assert result.category == "A"
    assert result.value == 10

    # Get record to verify it was created
    db_record = UpsertTestModel.one(name="test1")

    # 1. Check that returned model's ID matches the DB record
    assert db_record.id == result.id

    # Perform upsert that updates the existing record
    updated_result = UpsertTestModel.upsert(
        data={"name": "test1", "category": "B", "value": 20},
        unique_by="name",
    )

    # 4. Ensure multiple upserts with same unique_by keys return object with same ID
    assert updated_result.id == result.id

    # 2. Check field values on returned model
    assert updated_result.name == "test1"
    assert updated_result.category == "B"
    assert updated_result.value == 20

    assert UpsertTestModel.count() == 1
    record = UpsertTestModel.get(name="test1")
    assert record is not None
    # 1. Double-check that DB record matches what was returned
    assert record.id == updated_result.id
    assert record.category == "B"
    assert record.value == 20


def test_upsert_multiple_unique_fields(create_and_wipe_database):
    """Test upsert with multiple unique fields"""
    # Create initial records
    result1 = UpsertTestModel.upsert(
        data={"name": "multi1", "category": "X", "value": 100},
        unique_by=["name", "category"],
    )

    # 3. Ensure return value is never null
    assert result1 is not None
    # 2. Check field values on returned model
    assert result1.name == "multi1"
    assert result1.category == "X"
    assert result1.value == 100

    # 1. Check that returned model's ID matches the DB record
    db_record1 = UpsertTestModel.get(name="multi1", category="X")
    assert db_record1 is not None
    assert db_record1.id == result1.id

    result2 = UpsertTestModel.upsert(
        data={"name": "multi2", "category": "X", "value": 200},
        unique_by=["name", "category"],
    )

    # Different name should create a new record with different ID
    assert result2.id != result1.id
    # 2. Check field values on returned model
    assert result2.name == "multi2"
    assert result2.category == "X"
    assert result2.value == 200

    assert UpsertTestModel.count() == 2

    # Update one record based on both unique fields
    updated_result = UpsertTestModel.upsert(
        data={"name": "multi1", "category": "X", "value": 150},
        unique_by=["name", "category"],
    )

    # 4. Ensure multiple upserts with same unique_by keys return object with same ID
    assert updated_result.id == result1.id
    # 2. Check field values on returned model
    assert updated_result.name == "multi1"
    assert updated_result.category == "X"
    assert updated_result.value == 150

    # Get records to verify one was updated and one unchanged
    record_x = UpsertTestModel.one(name="multi1", category="X")
    record_y = UpsertTestModel.one(name="multi2", category="X")

    # 1. Check that DB records match what was returned
    assert record_x.id == updated_result.id
    assert record_x.value == 150  # Updated
    assert record_y.value == 200  # Unchanged


def test_upsert_single_update_field(create_and_wipe_database):
    """Test upsert that updates a single field"""
    # Create initial record
    result = UpsertTestModel.upsert(
        data={"name": "update1", "category": "Z", "value": 5, "description": "Initial"},
        unique_by="name",
    )

    # 3. Ensure return value is never null
    assert result is not None
    # 2. Check field values on returned model
    assert result.name == "update1"
    assert result.category == "Z"
    assert result.value == 5
    assert result.description == "Initial"

    # Perform upsert that only updates the value
    updated_result = UpsertTestModel.upsert(
        data={"name": "update1", "category": "Z", "value": 25},
        unique_by="name",
    )

    # 4. Ensure multiple upserts with same unique_by keys return object with same ID
    assert updated_result.id == result.id
    # 2. Check field values on returned model
    assert updated_result.name == "update1"
    assert updated_result.category == "Z"
    assert updated_result.value == 25
    assert updated_result.description == "Initial"  # Should be preserved

    # Get record to verify field was updated
    record = UpsertTestModel.get(name="update1")
    assert record is not None
    # 1. Check that DB record matches what was returned
    assert record.id == updated_result.id
    assert record.value == 25  # Updated
    assert record.category == "Z"  # Unchanged
    assert record.description == "Initial"  # Unchanged


def test_upsert_multiple_update_fields(create_and_wipe_database):
    """Test upsert that updates multiple fields"""
    # Create initial record
    result = UpsertTestModel.upsert(
        data={"name": "update2", "category": "M", "value": 42, "description": "Old"},
        unique_by="name",
    )

    # 3. Ensure return value is never null
    assert result is not None
    # 2. Check field values on returned model
    assert result.name == "update2"
    assert result.category == "M"
    assert result.value == 42
    assert result.description == "Old"

    # Perform upsert that updates multiple fields
    updated_result = UpsertTestModel.upsert(
        data={"name": "update2", "value": 99, "description": "New", "category": "N"},
        unique_by="name",
    )

    # 4. Ensure multiple upserts with same unique_by keys return object with same ID
    assert updated_result.id == result.id
    # 2. Check field values on returned model
    assert updated_result.name == "update2"
    assert updated_result.category == "N"
    assert updated_result.value == 99
    assert updated_result.description == "New"

    # Get record to verify all fields were updated
    record = UpsertTestModel.get(name="update2")
    assert record is not None
    # 1. Check that DB record matches what was returned
    assert record.id == updated_result.id
    assert record.value == 99
    assert record.description == "New"
    assert record.category == "N"
