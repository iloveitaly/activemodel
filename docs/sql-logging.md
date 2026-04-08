# SQL Logging

Configure SQL logging through `engine_options` when you initialize `activemodel`.

`activemodel` passes `engine_options` straight through to `sqlmodel.create_engine()`, so the standard SQLAlchemy logging flags work as expected.

## Log SQL Statements

Set `echo=True` to print SQL statements emitted by the engine.

```python
import activemodel

activemodel.init(
    "postgresql://user:password@localhost:5432/app",
    engine_options={"echo": True},
)
```

## Log Pool Activity Too

Set both `echo` and `echo_pool` if you also want connection pool checkout and return activity in the logs.

```python
import activemodel

activemodel.init(
    "postgresql://user:password@localhost:5432/app",
    engine_options={
        "echo": True,
        "echo_pool": True,
    },
)
```

## Reuse Existing Engine Configuration

Because `engine_options` maps directly to SQLAlchemy engine keyword arguments, you can keep your logging settings alongside the rest of your engine configuration.

```python
import activemodel

activemodel.init(
    "postgresql://user:password@localhost:5432/app",
    engine_options={
        "echo": True,
        "echo_pool": True,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    },
)
```

See the SQLAlchemy engine docs for the full list of supported options.
