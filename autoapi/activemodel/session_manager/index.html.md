# activemodel.session_manager

Class to make managing sessions with SQL Model easy. Also provides a common entrypoint to make it easy to mutate the
database environment when testing.

## Attributes

| [`ACTIVEMODEL_LOG_SQL`](#activemodel.session_manager.ACTIVEMODEL_LOG_SQL)   |    |
|-----------------------------------------------------------------------------|----|

## Classes

| [`SessionManager`](#activemodel.session_manager.SessionManager)   |    |
|-------------------------------------------------------------------|----|

## Functions

| [`init`](#activemodel.session_manager.init)(database_url, \*[, engine_options])   | configure activemodel to connect to a specific database                              |
|-----------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| [`table_exists`](#activemodel.session_manager.table_exists)(→ bool)               | Check if the table for the given model exists in the database.                       |
| [`get_engine`](#activemodel.session_manager.get_engine)()                         | alias to get the database engine without importing SessionManager                    |
| [`get_session`](#activemodel.session_manager.get_session)()                       | alias to get a database session without importing SessionManager                     |
| [`global_session`](#activemodel.session_manager.global_session)([session])        | Generate a session and share it across all activemodel calls.                        |
| [`aglobal_session`](#activemodel.session_manager.aglobal_session)()               | Use this as a fastapi dependency to get a session that is shared across the request: |

## Module Contents

### activemodel.session_manager.ACTIVEMODEL_LOG_SQL

### *class* activemodel.session_manager.SessionManager(database_url: [str](https://docs.python.org/3/library/stdtypes.html#str), , engine_options: [dict](https://docs.python.org/3/library/stdtypes.html#dict)[[str](https://docs.python.org/3/library/stdtypes.html#str), Any] | [None](https://docs.python.org/3/library/constants.html#None) = None)

#### session_connection *: sqlalchemy.Connection | [None](https://docs.python.org/3/library/constants.html#None)*

optionally specify a specific session connection to use for all get_session() calls, useful for testing and migrations

#### *classmethod* get_instance(database_url: [str](https://docs.python.org/3/library/stdtypes.html#str) | [None](https://docs.python.org/3/library/constants.html#None) = None, , engine_options: [dict](https://docs.python.org/3/library/stdtypes.html#dict)[[str](https://docs.python.org/3/library/stdtypes.html#str), Any] | [None](https://docs.python.org/3/library/constants.html#None) = None) → [SessionManager](#activemodel.session_manager.SessionManager)

#### get_engine() → sqlalchemy.Engine

#### get_session()

get a new database session, respecting any globally set sessions

### activemodel.session_manager.init(database_url: [str](https://docs.python.org/3/library/stdtypes.html#str), , engine_options: [dict](https://docs.python.org/3/library/stdtypes.html#dict)[[str](https://docs.python.org/3/library/stdtypes.html#str), Any] | [None](https://docs.python.org/3/library/constants.html#None) = None)

configure activemodel to connect to a specific database

### activemodel.session_manager.table_exists(model: [type](https://docs.python.org/3/library/functions.html#type)[sqlmodel.SQLModel]) → [bool](https://docs.python.org/3/library/functions.html#bool)

Check if the table for the given model exists in the database.

### activemodel.session_manager.get_engine()

alias to get the database engine without importing SessionManager

### activemodel.session_manager.get_session()

alias to get a database session without importing SessionManager

### activemodel.session_manager.global_session(session: sqlmodel.Session | [None](https://docs.python.org/3/library/constants.html#None) = None)

Generate a session and share it across all activemodel calls.

Alternatively, you can pass a session to use globally into the context manager, which is helpful for migrations
and testing.

This may only be called a single time per callstack. There is one exception: if you call this multiple times
and pass in the same session reference, it will result in a noop.

In complex testing code, you’ll need to be careful here. For example:

- Unit test using a transaction db fixture (which sets \_\_sqlalchemy_session_\_)
- Factory has a after_save hook
- That hook triggers a celery job
- The celery job (properly) calls with global_session()
- However, since global_session() is already set with \_\_sqlalchemy_session_\_, this will raise an error

* **Parameters:**
  **session** – Use an existing session instead of creating a new one

### *async* activemodel.session_manager.aglobal_session()

Use this as a fastapi dependency to get a session that is shared across the request:

```pycon
>>> APIRouter(
>>>     prefix="/internal/v1",
>>>     dependencies=[
>>>         Depends(aglobal_session),
>>>     ]
>>> )
```
