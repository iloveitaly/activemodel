# TypeID

`activemodel` includes first-class support for [TypeIDs](https://github.com/jetpack-io/typeid) — type-safe, globally unique identifiers with a human-readable prefix (e.g. `user_01h45ytscbebyvny4gc8cr8ma2`).

## Primary Key

Use `TypeIDPrimaryKey` with a `TypeIDField` annotation to define a typed primary key:

```python
from typing import Literal
from typeid import TypeID
from activemodel import BaseModel
from activemodel.mixins import TypeIDField, TypeIDPrimaryKey

class User(BaseModel, table=True):
    id: TypeIDField[Literal["user"]] = TypeIDPrimaryKey("user")
```

The `Literal["user"]` annotation gives static type-checking of the prefix. Each prefix must be unique within a process — defining two models with the same prefix raises an `AssertionError` at class definition time.

## Foreign Keys

Use `Model.foreign_key()` to wire up a FK column. Annotate with `TypeID` (not `TypeIDType`):

```python
from typing import Literal
from typeid import TypeID
from activemodel import BaseModel
from activemodel.mixins import TypeIDField, TypeIDPrimaryKey
from sqlmodel import Relationship

class Distribution(BaseModel, table=True):
    id: TypeIDField[Literal["dst"]] = TypeIDPrimaryKey("dst")
    name: str

class Screening(BaseModel, table=True):
    id: TypeIDField[Literal["scr"]] = TypeIDPrimaryKey("scr")
    distribution_id: TypeID = Distribution.foreign_key(index=True)
    distribution: Distribution = Relationship()
```

`foreign_key()` defaults to `nullable=False` and accepts any `Field` kwargs (`index`, `nullable`, etc.).

## Prefix Enforcement

For FK fields that must carry a specific prefix — such as self-referential foreign keys — use `sa_type=TypeIDType(prefix="...")`. The annotation stays as `TypeID`:

```python
from typeid import TypeID
from activemodel import BaseModel
from activemodel.mixins import TypeIDField, TypeIDPrimaryKey
from activemodel.types import TypeIDType
from sqlmodel import Field

class Screening(BaseModel, table=True):
    id: TypeIDField[Literal["scr"]] = TypeIDPrimaryKey("scr")
    merged_into_screening_id: TypeID | None = Field(
        default=None,
        sa_type=TypeIDType(prefix="scr"),  # type: ignore
    )
```

`TypeIDType` appears only in `sa_type=`, never as the field annotation. Assigning a TypeID with the wrong prefix raises `TypeIDValidationError`.

## Raw Polymorphic References

Use `TypeIDType.raw()` when a field can reference objects of multiple different types (and thus different TypeID prefixes). The field accepts TypeIDs of any prefix on write, but only the underlying UUID is persisted — on read it returns a plain `UUID` with no prefix attached.

```python
from uuid import UUID
from typing import Literal
from typeid import TypeID
from activemodel import BaseModel
from activemodel.mixins import TypeIDPrimaryKey
from activemodel.types import TypeIDType
from sqlmodel import Field

class Event(BaseModel, table=True):
    id: TypeIDField[Literal["event"]] = TypeIDPrimaryKey("event")
    originating_id: UUID | None = Field(
        default=None,
        index=True,
        sa_type=TypeIDType.raw(),
    )
```

The field accepts `TypeID` objects, TypeID strings (`"prefix_xxx"`), stdlib `UUID`, and bare UUID strings on write. Because the field reads back as a stdlib `UUID` while TypeID objects are not directly comparable to `UUID`, use `.bytes` for comparisons:

```python
assert event.originating_id.bytes == some_typeid.uuid_bytes
```

Raw fields emit `{"type": "string", "format": "uuid"}` in the OpenAPI schema (not `typeid`).

## Looking Up Records

`Model.get()` accepts any of these equivalent forms:

```python
User.get(user_id)           # TypeID instance
User.get(str(user_id))      # TypeID string, e.g. "user_01h45y..."
User.get(user_id.uuid)      # uuid_utils.UUID
User.get(uuid_obj)          # stdlib UUID
User.get("01h45y...")       # bare UUID string
```

## Pydantic / OpenAPI

Prefixed TypeID fields emit `{"type": "string", "format": "typeid"}` in the OpenAPI schema. Pydantic accepts both `TypeID` instances and plain strings (coerced via `TypeID.from_string`). In Python mode, `model_dump()` preserves `TypeID` objects; in JSON mode (`model_dump(mode="json")` or `model_dump_json()`), they serialize to their string representation.
