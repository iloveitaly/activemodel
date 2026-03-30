import pytest

from activemodel.pytest.transaction import database_reset_transaction

from tests.lifecycle._helpers import events


@pytest.fixture(autouse=True)
def setup_database(create_and_wipe_database):
    events.clear()
    yield from database_reset_transaction()
