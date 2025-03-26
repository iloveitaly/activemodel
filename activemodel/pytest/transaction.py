from activemodel import SessionManager

from ..logger import logger


def database_reset_transaction():
    """
    Wrap all database interactions for a given test in a nested transaction and roll it back after the test.

    >>> from activemodel.pytest import database_reset_transaction
    >>> database_reset_transaction = pytest.fixture(scope="function", autouse=True)(database_reset_transaction)

    Transaction-based DB cleaning does *not* work if the DB mutations are happening in a separate process, which should
    use spawn, because the same session is not shared across processes. Note that using `fork` is dangerous.

    In this case, you should use the truncate.

    References:

    - https://stackoverflow.com/questions/62433018/how-to-make-sqlalchemy-transaction-rollback-drop-tables-it-created
    - https://aalvarez.me/posts/setting-up-a-sqlalchemy-and-pytest-based-test-suite/
    - https://github.com/nickjj/docker-flask-example/blob/93af9f4fbf185098ffb1d120ee0693abcd77a38b/test/conftest.py#L77
    - https://github.com/caiola/vinhos.com/blob/c47d0a5d7a4bf290c1b726561d1e8f5d2ac29bc8/backend/test/conftest.py#L46
    - https://stackoverflow.com/questions/64095876/multiprocessing-fork-vs-spawn

    Using a named SAVEPOINT does not give us anything extra, so we are not using it.
    """

    engine = SessionManager.get_instance().get_engine()

    logger.info("starting global database transaction")

    with engine.begin() as connection:
        transaction = connection.begin_nested()

        if SessionManager.get_instance().session_connection is not None:
            logger.warning("session override already exists")
            # TODO should we throw an exception here?

        SessionManager.get_instance().session_connection = connection

        try:
            with SessionManager.get_instance().get_session() as factory_session:
                try:
                    from factory.alchemy import SQLAlchemyModelFactory

                    # Ensure that all factories use the same session
                    for factory in SQLAlchemyModelFactory.__subclasses__():
                        factory._meta.sqlalchemy_session = factory_session
                        factory._meta.sqlalchemy_session_persistence = "commit"
                except ImportError:
                    pass

                yield
        finally:
            logger.debug("rolling back transaction")

            transaction.rollback()

            # TODO is this necessary? unclear
            connection.close()

            SessionManager.get_instance().session_connection = None
