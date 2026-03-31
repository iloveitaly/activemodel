# activemodel.mixins

## Submodules

* [activemodel.mixins.pydantic_json](pydantic_json/index.md)
* [activemodel.mixins.soft_delete](soft_delete/index.md)
* [activemodel.mixins.timestamps](timestamps/index.md)
* [activemodel.mixins.typeid](typeid/index.md)

## Classes

| [`PydanticJSONMixin`](#activemodel.mixins.PydanticJSONMixin)   | By default, SQLModel does not convert JSONB columns into pydantic models when they are loaded from the database.   |
|----------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| [`SoftDeletionMixin`](#activemodel.mixins.SoftDeletionMixin)   | Soft delete records by setting deleted_at instead of removing the row.                                             |
| [`TimestampsMixin`](#activemodel.mixins.TimestampsMixin)       | Simple created at and updated at timestamps. Mix them into your model:                                             |

## Functions

| [`TypeIDMixin`](#activemodel.mixins.TypeIDMixin)(prefix)   | Mixin that adds a TypeID primary key field to a SQLModel. Specify the prefix to use for the TypeID.   |
|------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|

## Package Contents

### *class* activemodel.mixins.PydanticJSONMixin

By default, SQLModel does not convert JSONB columns into pydantic models when they are loaded from the database.

This mixin, combined with a custom serializer (\_serialize_pydantic_model), fixes that issue.

```pycon
>>> class ExampleWithJSON(BaseModel, PydanticJSONMixin, table=True):
>>>    list_field: list[SubObject] = Field(sa_type=JSONB()
```

Notes:

- Tuples of pydantic models are not supported, only lists.
- Nested lists of pydantic models are not supported, e.g. list[list[SubObject]]

#### *classmethod* \_\_init_subclass_\_(\*\*kwargs)

Register per-model SQLAlchemy instance events when a mapped subclass is declared.

load fires after SQLAlchemy first constructs an instance from query results.
refresh fires after SQLAlchemy reloads one or more attributes on an existing
instance, including session.refresh(…) and expired-attribute reloads.

#### \_\_transform_dict_to_pydantic_\_(field_names: [set](https://docs.python.org/3/library/stdtypes.html#set)[[str](https://docs.python.org/3/library/stdtypes.html#str)] | [None](https://docs.python.org/3/library/constants.html#None) = None)

Transforms dictionary fields into Pydantic models upon loading.

> - Reconstructor is SQLAlchemy’s class-decorator form of the load event.
> - It only runs for the initial ORM load, not for later refresh events.
> - The dedicated refresh listener above covers reloads of existing instances.
> - We manually call this method on save(), etc to ensure the pydantic types are maintained
- set_committed_value sets Pydantic models as committed, avoiding setattr marking fields as modified
  after loading from the database.

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
