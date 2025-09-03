import contextlib
import contextvars

from sqlmodel import Session
from activemodel import SessionManager
from activemodel.session_manager import global_session

from ..logger import logger

try:
    import factory as factory_exists
except ImportError:
    factory_exists = None

try:
    import polyfactory as polyfactory_exists
except ImportError:
    polyfactory_exists = None


_test_session = contextvars.ContextVar[Session | None]("test_session", default=None)


def set_factory_session(session):
    if not factory_exists:
        return
    from factory.alchemy import SQLAlchemyModelFactory

    # Ensure that all factories use the same session
    for factory in SQLAlchemyModelFactory.__subclasses__():
        factory._meta.sqlalchemy_session = factory_session
        factory._meta.sqlalchemy_session_persistence = "commit"


def set_polyfactory_session(session):
    if not polyfactory_exists:
        return

    from .factories import ActiveModelFactory

    ActiveModelFactory.__sqlalchemy_session__ = session


@contextlib.contextmanager
def test_session():
    """
    Configures a session-global database session for a test.

    Use this as a fixture using `db_session`. This method is meant to be used as a context manager.

    This is useful for tests that need to interact with the database multiple times before calling application code
    that uses the objects. This is intended to be used outside of an integration test. Integration tests generally
    do not use database transactions to clean the database and instead use truncation. The transaction fixture
    configures a session, which is then used here. This method requires that this global test session is already
    configured. If the transaction fixture is not used, then there is no session available for use and this will fail.

    ActiveModelFactory.save() does this automatically, but if you need to manually create objects
    and persist them to a DB, you can run into issues with the simple `expunge()` call
    used to reassociate an object with a new session. If there are more complex relationships
    this approach will fail and give you detached object errors.

    >>> from activemodel.pytest import test_session
    >>> def test_the_thing():
    >>>     with test_session():
    ...         obj = MyModel(name="test").save()
    ...         obj2 = MyModelFactory.save()

    More information: https://grok.com/share/bGVnYWN5_c21dd39f-84a7-44cf-a05b-9b26c8febb0b
    """

    if model_factory_session := _test_session.get():
        with global_session(model_factory_session) as session:
            yield session
    else:
        raise ValueError("No test session available")


def database_truncate_session():
    """
    Provides a database session for testing when using a truncation cleaning strategy.

    When not using a transaction cleaning strategy, no global test session is set
    """
    with test_session() as session:
        yield session


def database_reset_transaction():
    """
    Wrap all database interactions for a given test in a nested transaction and roll it back after the test.

    This is provided as a function, not a fixture, since you'll need to determine when a integration test is run. Here's
    an example of how to build a fixture from this method:

    >>> from activemodel.pytest import database_reset_transaction
    >>> database_reset_transaction = pytest.fixture(scope="function", autouse=True)(database_reset_transaction)

    Transaction-based DB cleaning does *not* work if the DB mutations are happening in a separate process because the
    same session is not shared across python processes. For this scenario, use the truncate method.

    Note that using `fork` as a multiprocess start method is dangerous. Use spawn. This link has more documentation
    around this topic:

    https://github.com/iloveitaly/python-starter-template/blob/master/app/configuration/lang.py

    References:

    - https://stackoverflow.com/questions/62433018/how-to-make-sqlalchemy-transaction-rollback-drop-tables-it-created
    - https://aalvarez.me/posts/setting-up-a-sqlalchemy-and-pytest-based-test-suite/
    - https://github.com/nickjj/docker-flask-example/blob/93af9f4fbf185098ffb1d120ee0693abcd77a38b/test/conftest.py#L77
    - https://github.com/caiola/vinhos.com/blob/c47d0a5d7a4bf290c1b726561d1e8f5d2ac29bc8/backend/test/conftest.py#L46
    - https://stackoverflow.com/questions/64095876/multiprocessing-fork-vs-spawn

    Using a named SAVEPOINT does not give us anything extra, so we are not using it.
    """

    engine = SessionManager.get_instance().get_engine()

    logger.debug("starting global database transaction")

    with engine.begin() as connection:
        transaction = connection.begin_nested()

        if SessionManager.get_instance().session_connection is not None:
            raise ValueError("global session already set")

        # NOTE we very intentionally do NOT
        SessionManager.get_instance().session_connection = connection

        try:
            with SessionManager.get_instance().get_session() as model_factory_session:
                # set global database sessions for model factories to avoid lazy loading issues
                set_factory_session(model_factory_session)
                set_polyfactory_session(model_factory_session)

                test_session_token = _test_session.set(model_factory_session)

                try:
                    yield
                finally:
                    _test_session.reset(test_session_token)
        finally:
            logger.debug("rolling back transaction")

            transaction.rollback()

            # TODO is this necessary? unclear
            connection.close()

            SessionManager.get_instance().session_connection = None
