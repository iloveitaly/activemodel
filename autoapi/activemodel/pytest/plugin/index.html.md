# activemodel.pytest.plugin

Pytest plugin integration for activemodel.

Currently provides:

* `db_session` fixture - quick access to a database session (see `test_session`)
* `activemodel_preserve_tables` ini option - configure tables to preserve when using
  `database_reset_truncate` (comma separated list or multiple lines depending on config style)

Configuration examples:

pytest.ini:

```default
[pytest]
activemodel_preserve_tables = alembic_version,zip_code,seed_table
```

pyproject.toml:

```default
[tool.pytest.ini_options]
activemodel_preserve_tables = [
  "alembic_version",
  "zip_code",
  "seed_table",
]
```

The list always implicitly includes `alembic_version` even if not specified.

## Functions

| [`pytest_addoption`](#activemodel.pytest.plugin.pytest_addoption)(→ None)   | Register custom ini options.                                                                      |
|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| [`db_session`](#activemodel.pytest.plugin.db_session)()                     | Helpful for tests that are similar to unit tests. If you doing a routing or integration test, you |
| [`db_truncate_session`](#activemodel.pytest.plugin.db_truncate_session)()   | Provides a database session for testing when using a truncation cleaning strategy.                |

## Module Contents

### activemodel.pytest.plugin.pytest_addoption(parser: pytest.Parser) → [None](https://docs.python.org/3/library/constants.html#None)

Register custom ini options.

We treat this as a *linelist* so pyproject.toml list syntax works. Comma separated works too because
pytest splits lines first; users can still provide one line with commas.

### activemodel.pytest.plugin.db_session()

Helpful for tests that are similar to unit tests. If you doing a routing or integration test, you
probably don’t need this because the router, job harness, etc should wrap the logic in a database session.

If your unit test is simple (you are just creating a couple of models) you
can most likely skip this, unless your factories or models do something more complex with nested database calls.

This is helpful if you are doing a lot of lazy-loaded params or need a database session to be in place
for testing code that will run within a celery worker or something similar.

```pycon
>>> def the_test(db_session):
```

### activemodel.pytest.plugin.db_truncate_session()

Provides a database session for testing when using a truncation cleaning strategy.

When using a truncation cleaning strategy, no global test session is set. This means all models that are created
are tied to a detached session, which makes it hard to mutate models after creation. This fixture fixes that problem
by setting the session used by all model factories to a global session.
