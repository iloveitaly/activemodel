# activemodel.patches.get_sqlalchemy_type_patch

Extends SQLModel’s get_sqlalchemy_type to recognize whenever datetime types.

This allows using whenever.Instant, whenever.PlainDateTime, and
whenever.ZonedDateTime as bare field
type annotations without needing to specify sa_type= explicitly:

> class MyModel(BaseModel, table=True):
> : created_at: whenever.Instant | None = None
>   local_time: whenever.PlainDateTime | None = None
>   scheduled_at: whenever.ZonedDateTime | None = None

## Functions

| [`get_sqlalchemy_type`](#activemodel.patches.get_sqlalchemy_type_patch.get_sqlalchemy_type)(field)   |    |
|------------------------------------------------------------------------------------------------------|----|

## Module Contents

### activemodel.patches.get_sqlalchemy_type_patch.get_sqlalchemy_type(field)
