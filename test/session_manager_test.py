import pytest

from activemodel.session_manager import (
    get_engine,
    get_session,
    global_session,
    table_exists,
)
from test.models import AnotherExample, ExampleRecord, ExampleWithId
from test.utils import drop_all_tables
from sqlmodel import SQLModel


def test_global_session_raises_when_nested():
    """Test that global_session raises an error when used in a nested context."""

    # First global_session should work fine
    with global_session() as outer_session:
        assert outer_session is not None

        # Attempting to create a nested global_session should fail
        with pytest.raises(RuntimeError) as excinfo:
            with global_session() as _:
                pass  # This code shouldn't execute

        assert "global session already set" in str(excinfo.value)

    # After exiting the outer context, we should be able to use global_session again
    with global_session() as session:
        assert session is not None


def test_global_session_raises_with_different_session():
    """Test that global_session raises an error when a different session is passed."""

    with global_session() as outer_session:
        # Create a different session
        from sqlmodel import Session
        different_session = Session(get_engine())

        try:
            with pytest.raises(RuntimeError) as excinfo:
                with global_session(session=different_session):
                    pass

            assert "different session" in str(excinfo.value)
        finally:
            different_session.close()


def test_global_session_with_passed_session(create_and_wipe_database):
    """Test that global_session accepts an existing session."""
    # Create our own session using get_session()
    with get_session() as custom_session:
        # Pass the custom session to global_session
        with global_session(session=custom_session) as session:
            # Verify the session inside the context manager is our custom session
            assert session is custom_session

            # Add a record to verify session works
            ExampleRecord(something="test", another_with_index="unique1").save()

            # Verify record was added
            result = ExampleRecord.one(another_with_index="unique1")
            assert result is not None
            assert result.something == "test"


def test_global_session_noop_with_same_session(create_and_wipe_database):
    """Test that global_session should be a noop when the same session is passed."""

    with global_session() as custom_session:
        with global_session(session=custom_session) as session1:
            assert session1 is custom_session

            # According to the docstring, passing the same session reference
            # should result in a noop
            with global_session(session=custom_session) as session2:
                # This should be a noop and session2 should be the same as session1
                assert session2 is custom_session
                assert session2 is session1
                assert session2 is session2


def test_table_exists_with_existing_table(create_and_wipe_database):
    """Test that table_exists returns True when a table exists."""
    # The create_and_wipe_database fixture creates all tables
    assert table_exists(ExampleRecord) is True
    assert table_exists(AnotherExample) is True
    assert table_exists(ExampleWithId) is True


def test_table_exists_with_nonexistent_table():
    """Test that table_exists returns False when a table doesn't exist."""
    # Drop all tables first
    drop_all_tables()

    try:
        # Now the tables should not exist
        assert table_exists(ExampleRecord) is False
        assert table_exists(AnotherExample) is False
        assert table_exists(ExampleWithId) is False
    finally:
        # Clean up by recreating tables for other tests
        SQLModel.metadata.create_all(get_engine())


def test_table_exists_after_creating_table():
    """Test that table_exists returns True after creating tables."""
    # Drop all tables first
    drop_all_tables()

    try:
        # Verify tables don't exist
        assert table_exists(ExampleRecord) is False
        assert table_exists(AnotherExample) is False
        assert table_exists(ExampleWithId) is False

        # Create all tables
        SQLModel.metadata.create_all(get_engine())

        # Now they should all exist
        assert table_exists(ExampleRecord) is True
        assert table_exists(AnotherExample) is True
        assert table_exists(ExampleWithId) is True
    finally:
        # Clean up
        drop_all_tables()


def test_table_exists_after_dropping_table(create_and_wipe_database):
    """Test that table_exists returns False after dropping a table."""
    # Initially table should exist (from the fixture)
    assert table_exists(ExampleRecord) is True

    # Drop the table
    ExampleRecord.metadata.drop_all(get_engine())

    # Now it should not exist
    assert table_exists(ExampleRecord) is False

    # Recreate for cleanup
    ExampleRecord.metadata.create_all(get_engine())
