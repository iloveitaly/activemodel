import pytest

from activemodel.session_manager import (
    get_session,
    global_session,
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
