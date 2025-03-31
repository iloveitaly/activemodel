import contextlib
import pytest
from activemodel.session_manager import global_session


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
