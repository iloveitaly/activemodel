# activemodel.types.sqlalchemy_protocol

## Classes

| [`SQLAlchemyQueryMethods`](#activemodel.types.sqlalchemy_protocol.SQLAlchemyQueryMethods)   | Base class for protocol classes.   |
|---------------------------------------------------------------------------------------------|------------------------------------|

## Module Contents

### *class* activemodel.types.sqlalchemy_protocol.SQLAlchemyQueryMethods

Bases: `Protocol`

Base class for protocol classes.

Protocol classes are defined as:

```default
class Proto(Protocol):
    def meth(self) -> int:
        ...
```

Such classes are primarily used with static type checkers that recognize
structural subtyping (static duck-typing).

For example:

```default
class C:
    def meth(self) -> int:
        return 0

def func(x: Proto) -> int:
    return x.meth()

func(C())  # Passes static type check
```

See PEP 544 for details. Protocol classes decorated with
@typing.runtime_checkable act as simple-minded runtime protocols that check
only the presence of given attributes, ignoring their type signatures.
Protocol classes can be generic, they are defined as:

```default
class GenProto[T](Protocol):
    def meth(self) -> T:
        ...
```
