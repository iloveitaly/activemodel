# activemodel.mixins

## Submodules

* [activemodel.mixins.pydantic_json](pydantic_json/index.md)
* [activemodel.mixins.soft_delete](soft_delete/index.md)
* [activemodel.mixins.timestamps](timestamps/index.md)
* [activemodel.mixins.typeid](typeid/index.md)

## Classes

| [`SoftDeletionMixin`](#activemodel.mixins.SoftDeletionMixin)   | Soft delete records by setting deleted_at instead of removing the row.   |
|----------------------------------------------------------------|--------------------------------------------------------------------------|
| [`TimestampsMixin`](#activemodel.mixins.TimestampsMixin)       | Simple created at and updated at timestamps. Mix them into your model:   |

## Functions

| [`TypeIDMixin`](#activemodel.mixins.TypeIDMixin)(prefix)   | Mixin that adds a TypeID primary key field to a SQLModel. Specify the prefix to use for the TypeID.   |
|------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|

## Package Contents

### *class* activemodel.mixins.SoftDeletionMixin

Soft delete records by setting deleted_at instead of removing the row.

Call soft_delete() to timestamp the record and persist that change.

#### deleted_at *: [datetime.datetime](https://docs.python.org/3/library/datetime.html#datetime.datetime) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

#### soft_delete() → [T](../pytest/truncate/index.md#activemodel.pytest.truncate.T)

Timestamp deleted_at and persist the record.

### *class* activemodel.mixins.TimestampsMixin

Simple created at and updated at timestamps. Mix them into your model:

```pycon
>>> class MyModel(TimestampsMixin, SQLModel):
>>>    pass
```

Notes:

- Originally pulled from: [https://github.com/tiangolo/sqlmodel/issues/252](https://github.com/tiangolo/sqlmodel/issues/252)
- Related issue: [https://github.com/fastapi/sqlmodel/issues/539](https://github.com/fastapi/sqlmodel/issues/539)

#### created_at *: [datetime.datetime](https://docs.python.org/3/library/datetime.html#datetime.datetime) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

#### updated_at *: [datetime.datetime](https://docs.python.org/3/library/datetime.html#datetime.datetime) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

### activemodel.mixins.TypeIDMixin(prefix: [str](https://docs.python.org/3/library/stdtypes.html#str))

Mixin that adds a TypeID primary key field to a SQLModel. Specify the prefix to use for the TypeID.
