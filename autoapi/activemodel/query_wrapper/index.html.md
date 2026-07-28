# activemodel.query_wrapper

## Classes

| [`QueryWrapper`](#activemodel.query_wrapper.QueryWrapper)   | Make it easy to run queries on a model.   |
|-------------------------------------------------------------|-------------------------------------------|

## Module Contents

### *class* activemodel.query_wrapper.QueryWrapper(cls: [type](https://docs.python.org/3/library/functions.html#type)[TModel], \*args: Any)

Bases: [`activemodel.types.sqlalchemy_protocol.SQLAlchemyQueryMethods`](../types/sqlalchemy_protocol/index.md#activemodel.types.sqlalchemy_protocol.SQLAlchemyQueryMethods)[`TModel`]

Make it easy to run queries on a model.

#### target *: sqlmodel.sql.expression.SelectOfScalar[TModel]*

#### no_autoflush() → Self

#### first()

#### last()

#### one()

requires exactly one result in the dataset

#### all()

#### count()

I did some basic tests

#### scalar()

```pycon
>>>
```

#### exec()

#### delete()

#### exists() → [bool](https://docs.python.org/3/library/functions.html#bool)

Return True if the current query yields at least one row.

Uses the SQLAlchemy exists() construct against a LIMIT 1 version of
the current target for efficiency. Keeps the original target intact.

SQLAlchemy exists works differently and does not return a simple boolean.

#### sql()

Output the raw SQL of the query for debugging

#### sample() → TModel | [None](https://docs.python.org/3/library/constants.html#None)

#### sample(n: [int](https://docs.python.org/3/library/functions.html#int)) → [list](https://docs.python.org/3/library/stdtypes.html#list)[TModel]

Return a random sample of rows from the current query.

### Parameters

n: int
: Number of rows to return. Defaults to 1.

### Behavior

- Returns a single model instance when `n == 1` (or `None` if no rows)
- Returns a list[Model] when `n > 1` (possibly empty list when no rows)
- Sampling is performed by appending an `ORDER BY RANDOM()` / `func.random()`
  and `LIMIT n` clause to the existing query target.
- Keeps original query intact (does not mutate `self.target`) so further
  chaining works as expected.
