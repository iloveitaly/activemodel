# TypeID

`activemodel` includes first-class support for [TypeIDs](https://github.com/jetpack-io/typeid) — type-safe, globally unique identifiers with a human-readable prefix. The `TypeIDMixin` handles the primary key, while `TypeIDType` and `.foreign_key()` cover related IDs, prefix enforcement, and polymorphic references.

## Foreign Keys

```python
from activemodel import BaseModel
from activemodel.mixins import TypeIDMixin
from activemodel.types import TypeIDType
from sqlmodel import Relationship

class Distribution(BaseModel, TypeIDMixin("dst"), table=True):
    name: str

class Screening(BaseModel, TypeIDMixin("scr"), table=True):
    distribution_id: TypeIDType = Distribution.foreign_key(index=True)
    distribution: Distribution = Relationship()
```

## Prefix Enforcement

Use `sa_type=TypeIDType(prefix="...")` to enforce that a field always stores a TypeID with a specific prefix.

```python
from activemodel import BaseModel
from activemodel.mixins import TypeIDMixin
from activemodel.types import TypeIDType
from sqlmodel import Field

class Screening(BaseModel, TypeIDMixin("scr"), table=True):
    merged_into_screening_id: TypeIDType | None = Field(
        default=None,
        sa_type=TypeIDType(prefix="scr")  # type: ignore
    )
```

## Raw Polymorphic References

Use `TypeIDType.raw()` for polymorphic reference IDs where the field can be assigned TypeIDs with multiple prefixes, but only the UUID needs to be stored and read back. This mode accepts `TypeID` objects and TypeID strings with any prefix, persists a native UUID, and returns a plain `UUID`.

```python
from uuid import UUID

from activemodel import BaseModel
from activemodel.mixins import TypeIDPrimaryKey
from activemodel.types import TypeIDType
from sqlmodel import Field
from typeid import TypeID

class Event(BaseModel, table=True):
    id: TypeID = TypeIDPrimaryKey("event")
    originating_id: UUID | None = Field(
        default=None,
        index=True,
        sa_type=TypeIDType.raw(),
    )
```

Because `raw()` fields return a stdlib `UUID` while TypeID objects are not directly comparable to `UUID`, use `.bytes` to compare them reliably:

```python
assert event.originating_id.bytes == some_typeid.uuid_bytes
```
