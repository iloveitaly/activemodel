from activemodel import SessionManager


def database_reset_transaction():
    """
    Wrap all database interactions for a given test in a nested transaction and roll it back after the test.

    >>> from activemodel.pytest import database_reset_transaction
    >>> pytest.fixture(scope="function", autouse=True)(database_reset_transaction)

    References:

    - https://stackoverflow.com/questions/62433018/how-to-make-sqlalchemy-transaction-rollback-drop-tables-it-created
    - https://aalvarez.me/posts/setting-up-a-sqlalchemy-and-pytest-based-test-suite/
    - https://github.com/nickjj/docker-flask-example/blob/93af9f4fbf185098ffb1d120ee0693abcd77a38b/test/conftest.py#L77
    - https://github.com/caiola/vinhos.com/blob/c47d0a5d7a4bf290c1b726561d1e8f5d2ac29bc8/backend/test/conftest.py#L46
    """

    engine = SessionManager.get_instance().get_engine()

    with engine.begin() as connection:
        transaction = connection.begin_nested()

        SessionManager.get_instance().session_connection = connection

        try:
            yield
        finally:
            transaction.rollback()
            # TODO is this necessary?
            connection.close()
