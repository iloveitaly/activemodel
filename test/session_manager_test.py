import contextlib
import pytest
from sqlmodel import Session, select
from activemodel.session_manager import (
    global_session,
    get_engine,
    get_session,
    SessionManager,
)
from test.models import ExampleRecord


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


def test_global_session_with_passed_session(create_and_wipe_database):
    """Test that global_session accepts an existing session."""
    # Create our own session
    custom_session = Session(get_engine())

    try:
        # Pass the custom session to global_session
        with global_session(session=custom_session) as session:
            # Verify the session inside the context manager is our custom session
            assert session is custom_session

            # Add a record to verify session works
            test_record = ExampleRecord(something="test", another_with_index="unique1")
            session.add(test_record)
            session.commit()

            # Verify record was added
            result = session.exec(
                select(ExampleRecord).where(
                    ExampleRecord.another_with_index == "unique1"
                )
            ).first()
            assert result is not None
            assert result.something == "test"
    finally:
        custom_session.close()


def test_nested_session_isolation(create_and_wipe_database):
    """Test that nested=True creates an actual nested transaction."""
    # Create a record in the outer session
    with get_session() as outer_session:
        outer_record = ExampleRecord(something="outer", another_with_index="unique2")
        outer_session.add(outer_record)
        outer_session.commit()

        # Use nested session for isolated operations
        with global_session(nested=True) as nested_session:
            # Verify we can see the outer record
            result = nested_session.exec(
                select(ExampleRecord).where(
                    ExampleRecord.another_with_index == "unique2"
                )
            ).first()
            assert result is not None

            # Add a record in the nested session
            nested_record = ExampleRecord(
                something="nested", another_with_index="unique3"
            )
            nested_session.add(nested_record)

            # Verify the record is visible within the nested session
            result = nested_session.exec(
                select(ExampleRecord).where(
                    ExampleRecord.another_with_index == "unique3"
                )
            ).first()
            assert result is not None

        # After the nested session closes (and commits), check that the record is visible in the outer session
        result = outer_session.exec(
            select(ExampleRecord).where(ExampleRecord.another_with_index == "unique3")
        ).first()
        assert result is not None
        assert result.something == "nested"


def test_nested_session_rollback(create_and_wipe_database):
    """Test that errors in nested sessions cause proper rollbacks."""
    # Create a record in the outer session
    with get_session() as outer_session:
        outer_record = ExampleRecord(something="main", another_with_index="unique4")
        outer_session.add(outer_record)
        outer_session.commit()

        try:
            # Use nested session but raise an exception inside
            with global_session(nested=True) as nested_session:
                # Add a record in the nested session
                nested_record = ExampleRecord(
                    something="will_rollback", another_with_index="unique5"
                )
                nested_session.add(nested_record)

                # Verify the record is visible within the nested session
                result = nested_session.exec(
                    select(ExampleRecord).where(
                        ExampleRecord.another_with_index == "unique5"
                    )
                ).first()
                assert result is not None

                # Raise an exception to trigger rollback
                raise ValueError("Test exception to trigger rollback")
        except ValueError:
            pass  # Expected exception

        # After the nested session rolls back, verify the record is not visible
        result = outer_session.exec(
            select(ExampleRecord).where(ExampleRecord.another_with_index == "unique5")
        ).first()
        assert result is None

        # But the original record should still be there
        result = outer_session.exec(
            select(ExampleRecord).where(ExampleRecord.another_with_index == "unique4")
        ).first()
        assert result is not None


def test_nested_session_autocommit(create_and_wipe_database):
    """Test that nested sessions automatically commit when exiting normally."""
    # Start with an outer session
    with get_session() as outer_session:
        # Use a nested session
        with global_session(nested=True) as nested_session:
            # Add a record in the nested session
            nested_record = ExampleRecord(
                something="autocommit", another_with_index="unique6"
            )
            nested_session.add(nested_record)
            # No explicit commit here - should auto-commit on exit

        # After the nested session closes, verify the record was committed
        # Refresh outer session to see new records
        outer_session.expire_all()

        # Check if the record is visible
        result = outer_session.exec(
            select(ExampleRecord).where(ExampleRecord.another_with_index == "unique6")
        ).first()
        assert result is not None
        assert result.something == "autocommit"
        assert result.value == 3
