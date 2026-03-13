# activemodel.pytest

## Submodules

* [activemodel.pytest.factories](factories/index.md)
* [activemodel.pytest.plugin](plugin/index.md)
* [activemodel.pytest.transaction](transaction/index.md)
* [activemodel.pytest.truncate](truncate/index.md)

## Functions

| [`database_reset_transaction`](#activemodel.pytest.database_reset_transaction)()                           | Wrap all database interactions for a given test in a nested transaction and roll it back after the test.   |
|------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| [`test_session`](#activemodel.pytest.test_session)()                                                       | Configures a session-global database session for a test.                                                   |
| [`database_reset_truncate`](#activemodel.pytest.database_reset_truncate)([preserve_tables, pytest_config]) | Transaction is most likely the better way to go, but there are some scenarios where the session override   |

## Package Contents

### activemodel.pytest.database_reset_transaction()

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

### activemodel.pytest.test_session()

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

### activemodel.pytest.database_reset_truncate(preserve_tables: [list](https://docs.python.org/3/library/stdtypes.html#list)[[str](https://docs.python.org/3/library/stdtypes.html#str)] | [None](https://docs.python.org/3/library/constants.html#None) = None, pytest_config: pytest.Config | [None](https://docs.python.org/3/library/constants.html#None) = None)

Transaction is most likely the better way to go, but there are some scenarios where the session override
logic does not work properly and you need to truncate tables back to their original state.

Here’s how to do this once at the start of the test:

```pycon
>>> from activemodel.pytest import database_reset_truncation
>>> def pytest_configure(config):
>>>         database_reset_truncation()
```

Or, if you want to use this as a fixture:

```pycon
>>> pytest.fixture(scope="function")(database_reset_truncation)
>>> def test_the_thing(database_reset_truncation)
```

This approach has a couple of problems:

* You can’t run multiple tests in parallel without separate databases
* If you have important seed data and want to truncate those tables, the seed data will be lost
