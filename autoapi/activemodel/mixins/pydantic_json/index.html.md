# activemodel.mixins.pydantic_json

Need to store nested Pydantic models in PostgreSQL using FastAPI and SQLModel.

SQLModel lacks a direct JSONField equivalent (like Tortoise ORM’s JSONField), making it tricky to handle nested model data as JSON in the DB.

Extensive discussion on the problem: [https://github.com/fastapi/sqlmodel/issues/63](https://github.com/fastapi/sqlmodel/issues/63)

## Classes

| [`PydanticJSONMixin`](#activemodel.mixins.pydantic_json.PydanticJSONMixin)   | By default, SQLModel does not convert JSONB columns into pydantic models when they are loaded from the database.   |
|------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|

## Module Contents

### *class* activemodel.mixins.pydantic_json.PydanticJSONMixin

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
