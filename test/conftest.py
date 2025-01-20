import pytest
from sqlmodel import SQLModel

import activemodel
from activemodel.session_manager import get_engine

from .utils import database_url, temporary_tables

activemodel.init(database_url())

SQLModel.metadata.drop_all(
    bind=get_engine(),
)


@pytest.fixture(scope="function")
def create_and_wipe_database():
    with temporary_tables():
        yield
