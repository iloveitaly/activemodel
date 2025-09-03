"""
Tests for the activemodel.pytest.transaction.test_session function.

The test_session function provides a database session for testing purposes,
particularly useful for tests that need to interact with the database multiple
times before calling application code that uses the objects.
"""

import pytest
from sqlmodel import Session

from activemodel.pytest.transaction import (
    test_session,
    database_reset_transaction,
    _test_session,
)
from activemodel.session_manager import global_session
from activemodel import SessionManager
from test.models import ExampleRecord, AnotherExample


class TestTestSession:
    """Tests for the test_session context manager"""

    @pytest.fixture(autouse=True)
    def setup_database(self, create_and_wipe_database):
        """Ensure clean database state for each test"""
        yield from database_reset_transaction()

    def test_test_session_provides_session(self):
        """Test that test_session provides a valid session"""
        with test_session() as session:
            assert isinstance(session, Session)
            assert session is not None

    def test_test_session_uses_global_test_session_when_set(self):
        """Test that test_session uses the global test session when one is set"""
        # Get the current test session that should be set by database_reset_transaction
        current_test_session = _test_session.get()
        assert current_test_session is not None

        # Now test_session should use this same session
        with test_session() as session:
            assert session is current_test_session

    def test_test_session_allows_database_operations(self):
        """Test that the session from test_session can perform database operations"""
        with test_session():
            # Create a test record
            record = ExampleRecord(something="test value").save()

            # Verify we can query it back
            found_record = ExampleRecord.get(record.id)
            assert found_record is not None
            assert found_record.something == "test value"

    def test_test_session_with_relationships(self):
        """Test that test_session works with related models"""
        with test_session() as session:
            # Create related records
            another = AnotherExample(note="test note").save()

            # Verify the relationship works
            assert another.id is not None
            found_another = AnotherExample.get(another.id)

            assert found_another is not None
            assert found_another.note == "test note"

    def test_test_session_nested_usage(self):
        """Test that test_session can be used nested within database_reset_transaction"""
        # Create a record in the outer transaction
        outer_session = _test_session.get()
        assert outer_session

        record1 = ExampleRecord(something="outer record")
        outer_session.add(record1)
        outer_session.commit()

        # Use test_session (should be the same session)
        with test_session() as session:
            assert session is outer_session

            # Create another record
            record2 = ExampleRecord(something="inner record").save()

            # Both records should be visible
            records = list(ExampleRecord.all())
            assert len(records) == 2
            values = [r.something for r in records]
            assert "outer record" in values
            assert "inner record" in values

    def test_test_session_isolation_between_calls(self):
        """Test that separate test_session calls are properly isolated"""
        record_id = None

        # First session - create a record
        with test_session() as session1:
            assert session1

            record = ExampleRecord(something="first session")
            session1.add(record)
            session1.commit()
            record_id = record.id

        # Second session - should be able to see the committed record
        with test_session() as session2:
            found_record = session2.get(ExampleRecord, record_id)
            assert found_record is not None
            assert found_record.something == "first session"

    def test_test_session_respects_global_session_context(self):
        """Test that test_session raises error when global session already set"""
        with SessionManager.get_instance().get_session() as manual_session:
            with global_session(manual_session):
                # test_session should raise an error when global session is already set
                with pytest.raises(RuntimeError, match="global session already set"):
                    with test_session() as session:
                        pass

    def test_test_session_handles_exceptions_gracefully(self):
        """Test that test_session handles exceptions within the context properly"""
        with pytest.raises(ValueError, match="test exception"):
            with test_session() as session:
                # Create a record
                ExampleRecord(something="test").save()

                # Raise an exception
                raise ValueError("test exception")

        # After the exception, we should still be able to use test_session
        with test_session() as session:
            assert isinstance(session, Session)
