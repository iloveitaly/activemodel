# ActiveModel: ORM Wrapper for SQLModel

No, this isn't *really* [ActiveModel](https://guides.rubyonrails.org/active_model_basics.html). It's just a wrapper around SQLModel that provides a more ActiveRecord-like interface.

SQLModel is *not* an ORM. It's a SQL query builder and a schema definition tool.

This package provides a thin wrapper around SQLModel that provides a more ActiveRecord-like interface with things like:

* Timestamp column mixins
* Lifecycle hooks

## Getting Started

First, setup your DB:

```python
import activemodel
activemodel.init("sqlite:///database.db")
```

Create models:

```python
from activemodel import BaseModel
from activemodel.mixins import TimestampsMixin, TypeIDMixin

class User(
    BaseModel,
    # optionally, obviously
    TimestampsMixin,
    # you can use a different pk type, but why would you?
    # put this mixin last otherwise `id` will not be the first column in the DB
    TypeIDMixin("user"),
    # wire this model into the DB, without this alembic will not generate a migration
    table=True
):
    a_field: str
```

You'll need to create the models in the DB. Alembic is the best way to do it, but you can cheat as well:

```python
from sqlmodel import SQLModel

SQLModel.metadata.create_all(get_engine())

# now you can create a user!
User(a_field="a").save()
```

Maybe you like JSON:

```python
from activemodel import BaseModel
from pydantic import BaseModel as PydanticBaseModel
from activemodel.mixins import PydanticJSONMixin, TypeIDMixin, TimestampsMixin

class SubObject(PydanticBaseModel):
    name: str
    value: int

class User(
    BaseModel,
    TimestampsMixin,
    PydanticJSONMixin,
    TypeIDMixin("user"),
    table=True
):
    list_field: list[SubObject] = Field(sa_type=JSONB())
```

## Usage

### Integrating Alembic

`alembic init` will not work out of the box. You need to mutate a handful of files:

* To import all of your models you want in your DB. [Here's my recommended way to do this.](https://github.com/iloveitaly/python-starter-template/blob/master/app/models/__init__.py)
* Use your DB URL from the ENV
* Target sqlalchemy metadata to the sqlmodel-generated metadata
* Most likely you'll want to add [alembic-postgresql-enum](https://pypi.org/project/alembic-postgresql-enum/) so migrations work properly

[Take a look at these scripts for an example of how to fully integrate Alembic into your development workflow.](https://github.com/iloveitaly/python-starter-template/blob/0af2c7e95217e34bde7357cc95be048900000e48/Justfile#L618-L712)

Here's a diff from the bare `alembic init` from version `1.14.1`.

```diff
diff --git i/test/migrations/alembic.ini w/test/migrations/alembic.ini
index 0d07420..a63631c 100644
--- i/test/migrations/alembic.ini
+++ w/test/migrations/alembic.ini
@@ -3,13 +3,14 @@
 [alembic]
 # path to migration scripts
 # Use forward slashes (/) also on windows to provide an os agnostic path
-script_location = .
+script_location = migrations
 
 # template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
 # Uncomment the line below if you want the files to be prepended with date and time
 # see https://alembic.sqlalchemy.org/en/latest/tutorial.html#editing-the-ini-file
 # for all available tokens
 # file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s
+file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(rev)s_%%(slug)s
 
 # sys.path path, will be prepended to sys.path if present.
 # defaults to the current working directory.
diff --git i/test/migrations/env.py w/test/migrations/env.py
index 36112a3..a1e15c2 100644
--- i/test/migrations/env.py
+++ w/test/migrations/env.py
@@ -1,3 +1,6 @@
+# fmt: off
+# isort: off
+
 from logging.config import fileConfig
 
 from sqlalchemy import engine_from_config
@@ -14,11 +17,17 @@ config = context.config
 if config.config_file_name is not None:
     fileConfig(config.config_file_name)
 
+from sqlmodel import SQLModel
+from test.models import *
+from test.utils import database_url
+
+config.set_main_option("sqlalchemy.url", database_url())
+
 # add your model's MetaData object here
 # for 'autogenerate' support
 # from myapp import mymodel
 # target_metadata = mymodel.Base.metadata
-target_metadata = None
+target_metadata = SQLModel.metadata
 
 # other values from the config, defined by the needs of env.py,
 # can be acquired:
diff --git i/test/migrations/script.py.mako w/test/migrations/script.py.mako
index fbc4b07..9dc78bb 100644
--- i/test/migrations/script.py.mako
+++ w/test/migrations/script.py.mako
@@ -9,6 +9,8 @@ from typing import Sequence, Union
 
 from alembic import op
 import sqlalchemy as sa
+import sqlmodel
+import activemodel
 ${imports if imports else ""}
 
 # revision identifiers, used by Alembic.
```

Here are some useful resources around Alembic + SQLModel:

* https://github.com/fastapi/sqlmodel/issues/85
* https://testdriven.io/blog/fastapi-sqlmodel/

### Query Wrapper

This tool is added to all `BaseModel`s and makes it easy to write SQL queries. Some examples:



### Easy Database Sessions

I hate the idea f 

* Behavior should be intuitive and easy to understand. If you run `save()`, it should save, not stick the save in a transaction.
* Don't worry about dead sessions. This makes it easy to lazy-load computed properties and largely eliminates the need to think about database sessions.

There are a couple of thorny problems we need to solve for here:

* In-memory fastapi servers are not the same as a uvicorn server, which is threaded *and* uses some sort of threadpool model for handling async requests. I don't claim to understand the entire implementation. For global DB session state (a) we can't use global variables (b) we can't use thread-local variables.
* 

https://github.com/tomwojcik/starlette-context

### Example Queries

* Conditional: `Scrape.select().where(Scrape.id < last_scraped.id).all()`
* Equality: `MenuItem.select().where(MenuItem.menu_id == menu.id).all()`
* `IN` example: `CanonicalMenuItem.select().where(col(CanonicalMenuItem.id).in_(canonized_ids)).all()`
* Compound where query: `User.where((User.last_active_at != None) & (User.last_active_at > last_24_hours)).count()`

### SQLModel Internals

SQLModel & SQLAlchemy are tricky. Here are some useful internal tricks:

* `__sqlmodel_relationships__` is where any `RelationshipInfo` objects are stored. This is used to generate relationship fields on the object.
* `ModelClass.relationship_name.property.local_columns` 
* Get cached fields from a model `object_state(instance).dict.get(field_name)`

### TypeID

I'm a massive fan of Stripe-style prefixed UUIDs. [There's an excellent project](https://github.com/jetify-com/typeid)
that defined a clear spec for these IDs. I've used the python implementation of this spec and developed a clean integration
with SQLModel that plays well with fastapi as well.

Here's an example of defining a relationship:

```python
import uuid

from activemodel import BaseModel
from activemodel.mixins import TimestampsMixin, TypeIDMixin
from activemodel.types import TypeIDType
from sqlmodel import Field, Relationship

from .patient import Patient

class Appointment(
    BaseModel,
    # this adds an `id` field to the model with the correct type
    TypeIDMixin("appointment"),
    table=True
):
    # `foreign_key` is a activemodel method to generate the right `Field` for the relationship
    # TypeIDType is really important here for fastapi serialization
    doctor_id: TypeIDType = Doctor.foreign_key()
    doctor: Doctor = Relationship()
```

## Limitations

### Validation

SQLModel does not currently support pydantic validations (when `table=True`). This is very surprising, but is actually the intended functionality:

* https://github.com/fastapi/sqlmodel/discussions/897
* https://github.com/fastapi/sqlmodel/pull/1041
* https://github.com/fastapi/sqlmodel/issues/453
* https://github.com/fastapi/sqlmodel/issues/52#issuecomment-1311987732

For validation:

* When consuming API data, use a separate shadow model to validate the data with `table=False` and then inherit from that model in a model with `table=True`.
* When validating ORM data, use SQL Alchemy hooks.

<!--

This looks neat
https://github.com/DarylStark/my_data/blob/a17b8b3a8463b9953821b89fee895e272f94d2a4/src/my_model/model.py#L155
        schema_extra={
            'pattern': r'^[a-z0-9_\-\.]+\@[a-z0-9_\-\.]+\.[a-z\.]+$'
        },

extra constraints

https://github.com/DarylStark/my_data/blob/a17b8b3a8463b9953821b89fee895e272f94d2a4/src/my_model/model.py#L424C1-L426C6
-->
## Related Projects

* https://github.com/woofz/sqlmodel-basecrud
* https://github.com/0xthiagomartins/sqlmodel-controller

## Inspiration

* https://github.com/peterdresslar/fastapi-sqlmodel-alembic-pg
* [Albemic instructions](https://github.com/fastapi/sqlmodel/pull/899/files)
* https://github.com/fastapiutils/fastapi-utils/
* https://github.com/fastapi/full-stack-fastapi-template
* https://github.com/DarylStark/my_data/
* https://github.com/petrgazarov/FastAPI-app/tree/main/fastapi_app

## Upstream Changes

- [ ] https://github.com/fastapi/sqlmodel/pull/1293