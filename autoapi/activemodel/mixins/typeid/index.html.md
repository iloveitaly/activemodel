# activemodel.mixins.typeid

## Functions

| [`TypeIDPrimaryKey`](#activemodel.mixins.typeid.TypeIDPrimaryKey)(→ Any)   | Field factory for the declarative form:                                                             |
|----------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| [`TypeIDMixin`](#activemodel.mixins.typeid.TypeIDMixin)(prefix)            | Mixin that adds a TypeID primary key field to a SQLModel. Specify the prefix to use for the TypeID. |

## Module Contents

### activemodel.mixins.typeid.TypeIDPrimaryKey(prefix: [str](https://docs.python.org/3/library/stdtypes.html#str)) → Any

Field factory for the declarative form:

> id: TypeIDField[Literal[“user”]] = TypeIDPrimaryKey(“user”)

Use this when you want static type-checking of the prefix.

Returns Any so that type checkers accept it as a default value for any
annotation (e.g. TypeIDField[Literal[“user”]]), matching the same pattern
used by pydantic’s own Field() factory.

Returns Any (not TypeID) because Pydantic discovers fields via \_\_annotations_\_ at class creation —
the annotation is required for field registration, so the return type cannot replace it.

### activemodel.mixins.typeid.TypeIDMixin(prefix: [str](https://docs.python.org/3/library/stdtypes.html#str))

Mixin that adds a TypeID primary key field to a SQLModel. Specify the prefix to use for the TypeID.
