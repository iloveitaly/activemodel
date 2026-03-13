# activemodel.pytest.truncate

## Attributes

| [`T`](#activemodel.pytest.truncate.T)   |    |
|-----------------------------------------|----|

## Functions

| [`database_reset_truncate`](#activemodel.pytest.truncate.database_reset_truncate)([preserve_tables, pytest_config])   | Transaction is most likely the better way to go, but there are some scenarios where the session override   |
|-----------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|

## Module Contents

### activemodel.pytest.truncate.T

### activemodel.pytest.truncate.database_reset_truncate(preserve_tables: [list](https://docs.python.org/3/library/stdtypes.html#list)[[str](https://docs.python.org/3/library/stdtypes.html#str)] | [None](https://docs.python.org/3/library/constants.html#None) = None, pytest_config: pytest.Config | [None](https://docs.python.org/3/library/constants.html#None) = None)

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
