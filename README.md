# ActiveModel: ORM Wrapper for SQLModel

No, this isn't *really* [ActiveModel](https://guides.rubyonrails.org/active_model_basics.html). It's just a wrapper around SQLModel that provides a more ActiveRecord-like interface.

SQLModel is *not* an ORM. It's a SQL query builder and a schema definition tool.

This package provides a thin wrapper around SQLModel that provides a more ActiveRecord-like interface with things like:

* Timestamp column mixins
* Lifecycle hooks

## Getting Started

First, setup your DB:

```python

```

Then, setup some models:

```python
from activemodel import BaseModel
from activemodel.mixins import TimestampsMixin, TypeIDMixin

class User(
    BaseModel, TimestampsMixin, TypeIDMixin("user"), table=True
):
    a_field: str
```

## Usage

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
    # `foreign_key` is a activemodel-specific method to generate the right `Field` for the relationship
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
