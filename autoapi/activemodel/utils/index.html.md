# activemodel.utils

## Functions

| [`compile_sql`](#activemodel.utils.compile_sql)(→ str)              | convert a query into SQL, helpful for debugging sqlalchemy/sqlmodel queries   |
|---------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [`raw_sql_exec`](#activemodel.utils.raw_sql_exec)(raw_query)        |                                                                               |
| [`hash_function_code`](#activemodel.utils.hash_function_code)(func) | get sha of a function to easily assert that it hasn't changed                 |

## Module Contents

### activemodel.utils.compile_sql(target: sqlmodel.sql.expression.SelectOfScalar) → [str](https://docs.python.org/3/library/stdtypes.html#str)

convert a query into SQL, helpful for debugging sqlalchemy/sqlmodel queries

### activemodel.utils.raw_sql_exec(raw_query: [str](https://docs.python.org/3/library/stdtypes.html#str))

### activemodel.utils.hash_function_code(func)

get sha of a function to easily assert that it hasn’t changed
