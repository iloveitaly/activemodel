# activemodel.mixins

## Submodules

* [activemodel.mixins.pydantic_json](pydantic_json/index.md)
* [activemodel.mixins.soft_delete](soft_delete/index.md)
* [activemodel.mixins.timestamps](timestamps/index.md)
* [activemodel.mixins.typeid](typeid/index.md)

## Classes

| [`PydanticJSONMixin`](#activemodel.mixins.PydanticJSONMixin)   | By default, SQLModel does not convert JSONB columns into pydantic models when they are loaded from the database.   |
|----------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| [`SoftDeletionMixin`](#activemodel.mixins.SoftDeletionMixin)   |                                                                                                                    |
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

#### \_\_transform_dict_to_pydantic_\_()

Transforms dictionary fields into Pydantic models upon loading.

- Reconstructor only runs once, when the object is loaded.
- We manually call this method on save(), etc to ensure the pydantic types are maintained
- set_committed_value sets Pydantic models as committed, avoiding setattr marking fields as modified
  after loading from the database.

### *class* activemodel.mixins.SoftDeletionMixin

#### deleted_at *: [datetime.datetime](https://docs.python.org/3/library/datetime.html#datetime.datetime)* *= None*

#### soft_delete()

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
