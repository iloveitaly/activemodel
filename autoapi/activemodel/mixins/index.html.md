# activemodel.mixins

## Submodules

* [activemodel.mixins.pydantic_json](pydantic_json/index.md)
* [activemodel.mixins.soft_delete](soft_delete/index.md)
* [activemodel.mixins.timestamps](timestamps/index.md)
* [activemodel.mixins.typeid](typeid/index.md)

## Classes

| [`PydanticJSONMixin`](#activemodel.mixins.PydanticJSONMixin)   | Restore JSON-backed fields to their annotated Pydantic shapes after ORM reloads.   |
|----------------------------------------------------------------|------------------------------------------------------------------------------------|
| [`SoftDeletionMixin`](#activemodel.mixins.SoftDeletionMixin)   | Soft delete records by setting deleted_at instead of removing the row.             |
| [`TimestampsMixin`](#activemodel.mixins.TimestampsMixin)       | Simple created at and updated at timestamps. Mix them into your model:             |

## Functions

| [`TypeIDMixin`](#activemodel.mixins.TypeIDMixin)(prefix)   | Mixin that adds a TypeID primary key field to a SQLModel. Specify the prefix to use for the TypeID.   |
|------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|

## Package Contents

### *class* activemodel.mixins.PydanticJSONMixin

Restore JSON-backed fields to their annotated Pydantic shapes after ORM reloads.

This mixin is paired with the engine-level JSON serializer so the same field can:

1. persist Pydantic models as JSON on write
2. come back as Pydantic models on load or refresh

```pycon
>>> class ExampleWithJSON(BaseModel, PydanticJSONMixin, table=True):
>>>    list_field: list[SubObject] = Field(sa_type=JSONB()
```

Supported field annotations:

- SubModel
- SubModel | None
- list[SubModel]
- list[SubModel] | None

Not supported:

- tuples of Pydantic models
- nested lists such as list[list[SubModel]]
- ambiguous unions with multiple non-None JSON shapes

#### *classmethod* \_\_init_subclass_\_(\*\*kwargs)

Register per-model SQLAlchemy instance events when a mapped subclass is declared.

load fires after SQLAlchemy first constructs an instance from query results.
refresh fires after SQLAlchemy reloads one or more attributes on an existing
instance, including session.refresh(…) and expired-attribute reloads.

The listeners are attached once per concrete model class so every mapped subclass
gets the same rehydration behavior automatically.

#### \_\_transform_dict_to_pydantic_\_(field_names: [set](https://docs.python.org/3/library/stdtypes.html#set)[[str](https://docs.python.org/3/library/stdtypes.html#str)] | [None](https://docs.python.org/3/library/constants.html#None) = None)

Replace raw JSON payloads on the instance with annotated Pydantic objects.

@reconstructor is SQLAlchemy’s class-decorator form of the load event, so
this method runs automatically for the initial ORM load. The dedicated refresh
listener above reuses the same logic for later reloads of an existing instance.

set_committed_value is used so the converted value becomes the instance’s
committed state instead of looking like a user mutation.

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
