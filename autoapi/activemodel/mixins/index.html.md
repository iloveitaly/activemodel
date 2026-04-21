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

| [`TypeIDMixin`](#activemodel.mixins.TypeIDMixin)(prefix)          | Mixin that adds a TypeID primary key field to a SQLModel. Specify the prefix to use for the TypeID.   |
|-------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| [`TypeIDPrimaryKey`](#activemodel.mixins.TypeIDPrimaryKey)(→ Any) | Field factory for the declarative form:                                                               |

## Package Contents

### *class* activemodel.mixins.PydanticJSONMixin

Restore JSON-backed fields to their annotated Pydantic shapes after ORM reloads.

This mixin is paired with the engine-level JSON serializer so the same field can:

1. Persist Pydantic models as JSON on write
2. Automatically convert raw JSON to Pydantic models on load or refresh

```pycon
>>> class ExampleWithJSON(BaseModel, PydanticJSONMixin, table=True):
>>>    list_field: list[SubObject] = Field(sa_type=JSONB())
```

Supported field annotations:

- SubModel
- SubModel | None
- list[SubModel]
- list[SubModel] | None

These are the supported rehydration shapes. Raw dict and list[dict] fields
stay as plain Python containers, but snapshot tracking can still detect mutations
on them.

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

#### \_\_transform_dict_to_pydantic_\_(jsonb_field_names: [set](https://docs.python.org/3/library/stdtypes.html#set)[[str](https://docs.python.org/3/library/stdtypes.html#str)] | [None](https://docs.python.org/3/library/constants.html#None) = None)

Replace raw JSON payloads on the instance with annotated Pydantic objects.

@reconstructor is SQLAlchemy’s class-decorator form of the load event, so
this method runs automatically for the initial ORM load. The dedicated refresh
listener above reuses the same logic for later reloads of an existing instance.

set_committed_value is used so the converted value becomes the instance’s
committed state instead of looking like a user mutation.

#### has_json_mutations() → [bool](https://docs.python.org/3/library/functions.html#bool)

Check whether any Pydantic JSON field has been mutated since the last snapshot.

Eagerly detects mutations by comparing current field values against their
serialized snapshots, and calls flag_modified for any that changed. Returns
True if at least one field was mutated.

This is an escape hatch for code that needs to know about pending JSON mutations
before the automatic before_flush detection fires.

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

### activemodel.mixins.TypeIDPrimaryKey(prefix: [str](https://docs.python.org/3/library/stdtypes.html#str)) → Any

Field factory for the declarative form:

> id: TypeIDField[Literal[“user”]] = TypeIDPrimaryKey(“user”)

Use this when you want static type-checking of the prefix.

Returns Any so that type checkers accept it as a default value for any
annotation (e.g. TypeIDField[Literal[“user”]]), matching the same pattern
used by pydantic’s own Field() factory.

Returns Any (not TypeID) because Pydantic discovers fields via \_\_annotations_\_ at class creation —
the annotation is required for field registration, so the return type cannot replace it.
