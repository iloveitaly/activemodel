# ActiveModel: ORM Wrapper for SQLModel

No, this isn't *really* [ActiveModel](https://guides.rubyonrails.org/active_model_basics.html). It's just a wrapper around SQLModel that provides a more ActiveRecord-like interface.

SQLModel is *not* an ORM. It's a SQL query builder and a schema definition tool.

This package provides a thin wrapper around SQLModel that provides a more ActiveRecord-like interface with things like:

* Timestamp column mixins
* Lifecycle hooks

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

## Inspiration

* https://github.com/peterdresslar/fastapi-sqlmodel-alembic-pg
* [Albemic instructions](https://github.com/fastapi/sqlmodel/pull/899/files)
* https://github.com/fastapiutils/fastapi-utils/
* https://github.com/fastapi/full-stack-fastapi-template
* https://github.com/DarylStark/my_data/
* https://github.com/petrgazarov/FastAPI-app/tree/main/fastapi_app