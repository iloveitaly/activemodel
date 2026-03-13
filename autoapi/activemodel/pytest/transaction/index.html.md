# activemodel.pytest.transaction

## Attributes

| [`factory_exists`](#activemodel.pytest.transaction.factory_exists)         |    |
|----------------------------------------------------------------------------|----|
| [`polyfactory_exists`](#activemodel.pytest.transaction.polyfactory_exists) |    |

## Functions

| [`set_factory_session`](#activemodel.pytest.transaction.set_factory_session)(session)         |                                                                                                          |
|-----------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| [`set_polyfactory_session`](#activemodel.pytest.transaction.set_polyfactory_session)(session) |                                                                                                          |
| [`set_factory_sessions`](#activemodel.pytest.transaction.set_factory_sessions)(session)       | set all supported model factories to use the provided session                                            |
| [`test_session`](#activemodel.pytest.transaction.test_session)()                              | Configures a session-global database session for a test.                                                 |
| [`database_truncate_session`](#activemodel.pytest.transaction.database_truncate_session)()    | Provides a database session for testing when using a truncation cleaning strategy.                       |
| [`database_reset_transaction`](#activemodel.pytest.transaction.database_reset_transaction)()  | Wrap all database interactions for a given test in a nested transaction and roll it back after the test. |

## Module Contents

### activemodel.pytest.transaction.factory_exists *= None*

### activemodel.pytest.transaction.polyfactory_exists *= None*

### activemodel.pytest.transaction.set_factory_session(session)

### activemodel.pytest.transaction.set_polyfactory_session(session)

### activemodel.pytest.transaction.set_factory_sessions(session)

set all supported model factories to use the provided session

### activemodel.pytest.transaction.test_session()

Configures a session-global database session for a test.

Use this as a fixture using db_session. This method is meant to be used as a context manager.

This is useful for tests that need to interact with the database multiple times before calling application code
that uses the objects. This is intended to be used outside of an integration test. Integration tests generally
do not use database transactions to clean the database and instead use truncation. The transaction fixture
configures a session, which is then used here. This method requires that this global test session is already
configured. If the transaction fixture is not used, then there is no session available for use and this will fail.

ActiveModelFactory.save() does this automatically, but if you need to manually create objects
and persist them to a DB, you can run into issues with the simple expunge() call
used to reassociate an object with a new session. If there are more complex relationships
this approach will fail and give you detached object errors.

```pycon
>>> from activemodel.pytest import test_session
>>> def test_the_thing():
>>>     with test_session():
...         obj = MyModel(name="test").save()
...         obj2 = MyModelFactory.save()
```

More information: [https://grok.com/share/bGVnYWN5_c21dd39f-84a7-44cf-a05b-9b26c8febb0b](https://grok.com/share/bGVnYWN5_c21dd39f-84a7-44cf-a05b-9b26c8febb0b)

### activemodel.pytest.transaction.database_truncate_session()

Provides a database session for testing when using a truncation cleaning strategy.

When not using a transaction cleaning strategy, no global test session is set

### activemodel.pytest.transaction.database_reset_transaction()

Wrap all database interactions for a given test in a nested transaction and roll it back after the test.

This is provided as a function, not a fixture, since you’ll need to determine when a integration test is run. Here’s
an example of how to build a fixture from this method:

```pycon
>>> from activemodel.pytest import database_reset_transaction
>>> database_reset_transaction = pytest.fixture(scope="function", autouse=True)(database_reset_transaction)
```

Transaction-based DB cleaning does *not* work if the DB mutations are happening in a separate process because the
same session is not shared across python processes. For this scenario, use the truncate method.

Note that using fork as a multiprocess start method is dangerous. Use spawn. This link has more documentation
around this topic:

[https://github.com/iloveitaly/python-starter-template/blob/master/app/configuration/lang.py](https://github.com/iloveitaly/python-starter-template/blob/master/app/configuration/lang.py)

References:

- [https://stackoverflow.com/questions/62433018/how-to-make-sqlalchemy-transaction-rollback-drop-tables-it-created](https://stackoverflow.com/questions/62433018/how-to-make-sqlalchemy-transaction-rollback-drop-tables-it-created)
- [https://aalvarez.me/posts/setting-up-a-sqlalchemy-and-pytest-based-test-suite/](https://aalvarez.me/posts/setting-up-a-sqlalchemy-and-pytest-based-test-suite/)
- [https://github.com/nickjj/docker-flask-example/blob/93af9f4fbf185098ffb1d120ee0693abcd77a38b/test/conftest.py#L77](https://github.com/nickjj/docker-flask-example/blob/93af9f4fbf185098ffb1d120ee0693abcd77a38b/test/conftest.py#L77)
- [https://github.com/caiola/vinhos.com/blob/c47d0a5d7a4bf290c1b726561d1e8f5d2ac29bc8/backend/test/conftest.py#L46](https://github.com/caiola/vinhos.com/blob/c47d0a5d7a4bf290c1b726561d1e8f5d2ac29bc8/backend/test/conftest.py#L46)
- [https://stackoverflow.com/questions/64095876/multiprocessing-fork-vs-spawn](https://stackoverflow.com/questions/64095876/multiprocessing-fork-vs-spawn)

Using a named SAVEPOINT does not give us anything extra, so we are not using it.
