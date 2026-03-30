# activemodel.mixins.soft_delete

## Classes

| [`SoftDeleteRecord`](#activemodel.mixins.soft_delete.SoftDeleteRecord)   | Base class for protocol classes.                                       |
|--------------------------------------------------------------------------|------------------------------------------------------------------------|
| [`SoftDeletionMixin`](#activemodel.mixins.soft_delete.SoftDeletionMixin) | Soft delete records by setting deleted_at instead of removing the row. |

## Module Contents

### *class* activemodel.mixins.soft_delete.SoftDeleteRecord

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

#### deleted_at *: [datetime.datetime](https://docs.python.org/3/library/datetime.html#datetime.datetime) | [None](https://docs.python.org/3/library/constants.html#None)*

#### save() → Self

### *class* activemodel.mixins.soft_delete.SoftDeletionMixin

Soft delete records by setting deleted_at instead of removing the row.

Call soft_delete() to timestamp the record and persist that change.

#### deleted_at *: [datetime.datetime](https://docs.python.org/3/library/datetime.html#datetime.datetime) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

#### soft_delete() → [T](../../pytest/truncate/index.md#activemodel.pytest.truncate.T)

Timestamp deleted_at and persist the record.
