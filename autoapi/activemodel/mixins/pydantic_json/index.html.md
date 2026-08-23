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

Raw dict and tuple-shaped fields are left alone during rehydration, and ambiguous
unions are treated as out of scope instead of being coerced heuristically.

Snapshot-based mutation tracking is broader than rehydration and can still detect
in-place changes on raw dict and list[dict] fields.

Background: [https://github.com/fastapi/sqlmodel/issues/63](https://github.com/fastapi/sqlmodel/issues/63)

## Classes

| [`PydanticJSONMixin`](#activemodel.mixins.pydantic_json.PydanticJSONMixin)   | Restore JSON-backed fields to their annotated Pydantic shapes after ORM reloads.   |
|----------------------------------------------------------------------|------------------------------------------------------------------------------------|

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

These are the supported rehydration shapes. Raw dict and list[dict] fields
stay as plain Python containers, but snapshot tracking can still detect mutations
on them.

Not supported:

- tuples of Pydantic models
- nested lists such as list[list[SubModel]]
- ambiguous unions with multiple non-None JSON shapes

#### has_json_mutations() → [bool](https://docs.python.org/3/library/functions.html#bool)

Check whether any Pydantic JSON field has been mutated since the last snapshot.

Eagerly detects mutations by comparing current field values against their
serialized snapshots, and calls flag_modified for any that changed. Returns
True if at least one field was mutated.

This is an escape hatch for code that needs to know about pending JSON mutations
before the automatic before_flush detection fires.
