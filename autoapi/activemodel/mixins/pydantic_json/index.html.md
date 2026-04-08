# activemodel.mixins.pydantic_json

Rehydrate JSON-backed SQLModel fields into Pydantic objects after ORM loads.

SQLModel persists JSON columns as plain Python dict / list values when rows are
loaded from the database. This module restores the annotated Pydantic shapes on the
model instance after SQLAlchemy load and refresh operations.

Supported annotations are intentionally narrow:

- SubModel
- SubModel | None
- list[SubModel]
- list[SubModel] | None

Raw dict and tuple-shaped fields are left alone, and ambiguous unions are treated as
out of scope instead of being coerced heuristically.

Background: [https://github.com/fastapi/sqlmodel/issues/63](https://github.com/fastapi/sqlmodel/issues/63)

## Classes

| [`PydanticJSONMixin`](#activemodel.mixins.pydantic_json.PydanticJSONMixin)   | Restore JSON-backed fields to their annotated Pydantic shapes after ORM reloads.   |
|------------------------------------------------------------------------------|------------------------------------------------------------------------------------|

## Module Contents

### *class* activemodel.mixins.pydantic_json.PydanticJSONMixin

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
