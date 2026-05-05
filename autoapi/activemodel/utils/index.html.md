# activemodel.utils

## Functions

| [`to_snake_case`](#activemodel.utils.to_snake_case)(→ str)          | Converts a PascalCase or camelCase string to snake_case.                    |
|---------------------------------------------------------------------|-----------------------------------------------------------------------------|
| [`compile_sql`](#activemodel.utils.compile_sql)(→ str)              | convert a query into SQL, helpful for debugging sqlalchemy/sqlmodel queries |
| [`raw_sql_exec`](#activemodel.utils.raw_sql_exec)(raw_query)        |                                                                             |
| [`hash_function_code`](#activemodel.utils.hash_function_code)(func) | get sha of a function to easily assert that it hasn't changed               |
| [`is_database_empty`](#activemodel.utils.is_database_empty)(→ bool) | Check if any table in the database has records using Model.count().         |

## Module Contents

### activemodel.utils.to_snake_case(name: [str](https://docs.python.org/3/library/stdtypes.html#str)) → [str](https://docs.python.org/3/library/stdtypes.html#str)

Converts a PascalCase or camelCase string to snake_case.
Properly handles acronyms like ‘LLMCache’ -> ‘llm_cache’.

Source: [https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case](https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case)

### activemodel.utils.compile_sql(target: sqlmodel.sql.expression.SelectOfScalar) → [str](https://docs.python.org/3/library/stdtypes.html#str)

convert a query into SQL, helpful for debugging sqlalchemy/sqlmodel queries

### activemodel.utils.raw_sql_exec(raw_query: [str](https://docs.python.org/3/library/stdtypes.html#str))

### activemodel.utils.hash_function_code(func)

get sha of a function to easily assert that it hasn’t changed

### activemodel.utils.is_database_empty(exclude: [list](https://docs.python.org/3/library/stdtypes.html#list)[[type](https://docs.python.org/3/library/functions.html#type)] = []) → [bool](https://docs.python.org/3/library/functions.html#bool)

Check if any table in the database has records using Model.count().

Useful for detecting an empty database state to run operations such as seeding, etc.
