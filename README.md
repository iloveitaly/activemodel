# ActiveModel: ORM Wrapper for SQLModel

No, this isn't *really* [ActiveModel](https://guides.rubyonrails.org/active_model_basics.html). It's just a wrapper around SQLModel that provides a more ActiveRecord-like interface.

SQLModel is *not* an ORM. It's a SQL query builder and a schema definition tool.

This package provides a thin wrapper around SQLModel that provides a more ActiveRecord-like interface with things like:

* Timestamp column mixins
* Lifecycle hooks

## Related Projects

* https://github.com/woofz/sqlmodel-basecrud

## Inspiration

* https://github.com/peterdresslar/fastapi-sqlmodel-alembic-pg
* [Albemic instructions](https://github.com/fastapi/sqlmodel/pull/899/files)
* https://github.com/fastapiutils/fastapi-utils/
*