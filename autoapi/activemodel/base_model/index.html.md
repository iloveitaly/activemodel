# activemodel.base_model

## Attributes

| [`POSTGRES_INDEXES_NAMING_CONVENTION`](#activemodel.base_model.POSTGRES_INDEXES_NAMING_CONVENTION)   | By default, the foreign key naming convention in sqlalchemy do not create unique identifiers when there are multiple   |
|------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------|

## Classes

| [`BaseModel`](#activemodel.base_model.BaseModel)   | Base model class to inherit from so we can hate python less.   |
|----------------------------------------------------|----------------------------------------------------------------|

## Module Contents

### activemodel.base_model.POSTGRES_INDEXES_NAMING_CONVENTION

By default, the foreign key naming convention in sqlalchemy do not create unique identifiers when there are multiple
foreign keys in a table. This naming convention is a workaround to fix this issue:

- [https://github.com/zhanymkanov/fastapi-best-practices?tab=readme-ov-file#set-db-keys-naming-conventions](https://github.com/zhanymkanov/fastapi-best-practices?tab=readme-ov-file#set-db-keys-naming-conventions)
- [https://github.com/fastapi/sqlmodel/discussions/1213](https://github.com/fastapi/sqlmodel/discussions/1213)
- Implementation lifted from: [https://github.com/AlexanderZharyuk/billing-service/blob/3c8aaf19ab7546b97cc4db76f60335edec9fc79d/src/models.py#L24](https://github.com/AlexanderZharyuk/billing-service/blob/3c8aaf19ab7546b97cc4db76f60335edec9fc79d/src/models.py#L24)

### *class* activemodel.base_model.BaseModel(\*\*data: Any)

Bases: `sqlmodel.SQLModel`

Base model class to inherit from so we can hate python less.

Some notes:

- Inspired by [https://github.com/woofz/sqlmodel-basecrud/blob/main/sqlmodel_basecrud/basecrud.py](https://github.com/woofz/sqlmodel-basecrud/blob/main/sqlmodel_basecrud/basecrud.py)
- lifecycle hooks are modeled after Rails.
- class docstrings are converted to table-level comments
- save(), delete(), select(), where(), and other easy methods you would expect in a real ORM
- Fixes foreign key naming conventions
- Sane table names

Here’s how hooks work:

> Create/Update: before_create, after_create, before_update, after_update, before_save, after_save, around_save
> Delete: before_delete, after_delete, around_delete

around_\* hooks must be context managers (method returning a CM or a CM attribute).
Ordering (create): before_create -> before_save -> (enter around_save) -> persist -> after_create -> after_save -> (exit around_save)
Ordering (update): before_update -> before_save -> (enter around_save) -> persist -> after_update -> after_save -> (exit around_save)
Delete: before_delete -> (enter around_delete) -> delete -> after_delete -> (exit around_delete)

> # TODO document this in activemodel, this is an interesting edge case

# [https://claude.ai/share/f09e4f70-2ff7-4cd0-abff-44645134693a](https://claude.ai/share/f09e4f70-2ff7-4cd0-abff-44645134693a)

#### \_\_table_args_\_ *= None*

#### *classmethod* \_\_init_subclass_\_(\*\*kwargs)

This signature is included purely to help type-checkers check arguments to class declaration, which
provides a way to conveniently set model_config key/value pairs.

```
``
```

```
`
```

python
from pydantic import BaseModel

class MyModel(BaseModel, extra=’allow’): …

```
``
```

```
`
```

However, this may be deceiving, since the \_actual_ calls to \_\_init_subclass_\_ will not receive any
of the config arguments, and will only receive any keyword arguments passed during class initialization
that are \_not_ expected keys in ConfigDict. (This is due to the way ModelMetaclass._\_new_\_ works.)

* **Parameters:**
  **\*\*kwargs** – Keyword arguments passed to the class definition, which set model_config

#### NOTE
You may want to override \_\_pydantic_init_subclass_\_ instead, which behaves similarly but is called
*after* the class is fully initialized.

#### \_\_tablename_\_() → [str](https://docs.python.org/3/library/stdtypes.html#str)

Automatically generates the table name for the model by converting the model’s class name from camel case to snake case.
This is the recommended text case style for table names:

[https://wiki.postgresql.org/wiki/Don%27t_Do_This#Don.27t_use_upper_case_table_or_column_names](https://wiki.postgresql.org/wiki/Don%27t_Do_This#Don.27t_use_upper_case_table_or_column_names)

By default, the model’s class name is lower cased which makes it harder to read.

Also, many text case conversion libraries struggle handling words like “LLMCache”, this is why we are using
a more precise library which processes such acronyms: [textcase]([https://pypi.org/project/textcase/](https://pypi.org/project/textcase/)).

[https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case](https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case)

#### *classmethod* foreign_key(\*\*kwargs)

Returns a Field object referencing the foreign key of the model.

Helps quickly build a many-to-one or one-to-one relationship.

```pycon
>>> other_model_id: int = OtherModel.foreign_key()
>>> other_model = Relationship()
```

#### *classmethod* select(\*args)

create a query wrapper to easily run sqlmodel queries on this model

#### *classmethod* where(\*args)

convenience method to avoid having to write .select().where() in order to add conditions

#### *classmethod* upsert(data: [dict](https://docs.python.org/3/library/stdtypes.html#dict)[[str](https://docs.python.org/3/library/stdtypes.html#str), Any], unique_by: [str](https://docs.python.org/3/library/stdtypes.html#str) | [list](https://docs.python.org/3/library/stdtypes.html#list)[[str](https://docs.python.org/3/library/stdtypes.html#str)]) → Self

This method will insert a new record if it doesn’t exist, or update the existing record if it does.

It uses SQLAlchemy’s on_conflict_do_update and does not yet support MySQL. Some implementation details below.

—

- index_elements=[“name”]: Specifies the column(s) to check for conflicts (e.g., unique constraint or index). If a row with the same “name” exists, it triggers the update instead of an insert.
- values: Defines the data to insert (e.g., name=”example”, value=123). If no conflict occurs, this data is inserted as a new row.

The set_ parameter (e.g., set_=dict(value=123)) then dictates what gets updated on conflict, overriding matching fields in values if specified.

#### delete()

Delete instance running delete hooks and optional around_delete context manager.

#### save()

Persist instance running create/update hooks and optional around_save context manager.

#### refresh()

Refreshes an object from the database

#### json(\*\*kwargs)

#### *classmethod* count() → [int](https://docs.python.org/3/library/functions.html#int)

Returns the number of records in the database.

#### *classmethod* first()

#### is_new() → [bool](https://docs.python.org/3/library/functions.html#bool)

#### flag_modified(\*args: [str](https://docs.python.org/3/library/stdtypes.html#str)) → [None](https://docs.python.org/3/library/constants.html#None)

Flag one or more fields as modified/mutated/dirty. Useful for marking a field containing sub-objects as modified.

Will throw an error if an invalid field is passed.

#### modified_fields() → [set](https://docs.python.org/3/library/stdtypes.html#set)[[str](https://docs.python.org/3/library/stdtypes.html#str)]

set of fields that are modified

#### *classmethod* find_or_create_by(\*\*kwargs)

Find record or create it with the passed args if it doesn’t exist.

#### *classmethod* find_or_initialize_by(\*\*kwargs)

Unfortunately, unlike ruby, python does not have a great lambda story. This makes writing convenience methods
like this a bit more difficult.

#### *classmethod* primary_key_column() → sqlmodel.Column

Returns the primary key column of the model by inspecting SQLAlchemy field information.

```pycon
>>> ExampleModel.primary_key_field().name
```

#### *classmethod* get(\*args: Any, \*\*kwargs: Any)

Gets a single record (or None) from the database. Pass an PK ID or kwargs to filter by.

#### *classmethod* one_or_none(\*args: Any, \*\*kwargs: Any)

Gets a single record from the database. Pass an PK ID or a kwarg to filter by.
Returns None if no record is found. Throws an error if more than one record is found.

#### *classmethod* one(\*args: Any, \*\*kwargs: Any)

Gets a single record from the database. Pass an PK ID or a kwarg to filter by.

#### *classmethod* \_\_process_filter_args_\_(\*args: Any, \*\*kwargs: Any)

Helper method to process filter arguments and implement some nice DX for our devs.

#### *classmethod* all()

get a generator for all records in the database

#### *classmethod* sample()

Pick a random record from the database. Raises if none exist.

Helpful for testing and console debugging.
