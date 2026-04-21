"""
Pytester-based tests verifying that database_reset_transaction correctly injects the
transaction-scoped session into both factory_boy and polyfactory factory subclasses,
and that records created through those factories are rolled back between tests.
"""

import pathlib
import textwrap

import pytest

pytest_plugins = ["pytester"]

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent

_CONFTEST = textwrap.dedent("""
    import sys
    import os
    import pytest
    import activemodel
    from activemodel.pytest.transaction import database_reset_transaction
    from tests.utils import database_url, temporary_tables

    def pytest_sessionstart(session):
        activemodel.init(database_url())

    @pytest.fixture(scope="session")
    def _tables():
        with temporary_tables():
            yield

    @pytest.fixture(autouse=True)
    def _tx(_tables):
        yield from database_reset_transaction()
""")


def test_factory_boy_session_injected_and_rolls_back(pytester, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(PROJECT_ROOT))

    pytester.makeconftest(_CONFTEST)

    pytester.makepyfile(textwrap.dedent("""
        from factory.alchemy import SQLAlchemyModelFactory
        from tests.models import ExampleRecord

        class ExampleRecordFB(SQLAlchemyModelFactory):
            class Meta:
                model = ExampleRecord
            something = "fb"

        def test_session_is_injected():
            assert ExampleRecordFB._meta.sqlalchemy_session is not None
            assert ExampleRecordFB._meta.sqlalchemy_session_persistence == "commit"

        def test_record_persists_within_transaction():
            rec = ExampleRecordFB()
            assert rec.id is not None
            found = ExampleRecord.get(rec.id)
            assert found is not None
            assert found.something == "fb"

        def test_previous_record_rolled_back():
            # the row from test_record_persists_within_transaction should be gone
            all_records = list(ExampleRecord.all())
            assert all_records == []
    """))

    result = pytester.runpytest_subprocess("--override-ini=addopts=")
    result.assert_outcomes(passed=3)


def test_polyfactory_session_injected_and_rolls_back(pytester, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(PROJECT_ROOT))

    pytester.makeconftest(_CONFTEST)

    pytester.makepyfile(textwrap.dedent("""
        from activemodel.pytest.factories import ActiveModelFactory
        from tests.models import ExampleRecord

        class ExampleRecordPF(ActiveModelFactory[ExampleRecord]):
            __model__ = ExampleRecord

        def test_session_is_injected():
            assert ActiveModelFactory.__sqlalchemy_session__ is not None

        def test_record_persists_within_transaction():
            rec = ExampleRecordPF.save()
            assert rec.id is not None
            found = ExampleRecord.get(rec.id)
            assert found is not None

        def test_previous_record_rolled_back():
            # the row from test_record_persists_within_transaction should be gone
            all_records = list(ExampleRecord.all())
            assert all_records == []
    """))

    result = pytester.runpytest_subprocess("--override-ini=addopts=")
    result.assert_outcomes(passed=3)
