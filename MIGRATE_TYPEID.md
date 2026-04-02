# TypeID Migration Guide

Field annotations no longer need to use `TypeIDType`. You can now annotate with the plain `TypeID` type from the `typeid` library, which is consistent with how other types like `whenever.Instant` work.

`TypeIDType` continues to work as a type annotation, so this migration is optional and fully backwards compatible.

## What to change

### Primary key fields (via TypeIDMixin)

These are handled automatically by `TypeIDMixin` and require no changes.

### Foreign key fields

```python
# Before
from activemodel.types import TypeIDType

class Appointment(BaseModel, TypeIDMixin("appointment"), table=True):
    doctor_id: TypeIDType = Doctor.foreign_key()
    doctor: Doctor = Relationship()

# After
from typeid import TypeID

class Appointment(BaseModel, TypeIDMixin("appointment"), table=True):
    doctor_id: TypeID = Doctor.foreign_key()
    doctor: Doctor = Relationship()
```

### Plain Pydantic response models

```python
# Before
from activemodel.types import TypeIDType

class AppointmentResponse(PydanticBaseModel):
    id: TypeIDType

# After
from typeid import TypeID

class AppointmentResponse(PydanticBaseModel):
    id: TypeID
```

### FastAPI path/query parameters

```python
# Before
from activemodel.types import TypeIDType

async def get_appointment(appointment_id: Annotated[TypeIDType, Path()]):
    ...

# After
from typeid import TypeID

async def get_appointment(appointment_id: Annotated[TypeID, Path()]):
    ...
```

## What does NOT change

- `TypeIDType` still exists and is still used internally — it is the SQLAlchemy `TypeDecorator` that handles DB serialization. You still see it in `sa_column` and `sa_type` arguments, but never need it as a type annotation.
- `TypeIDMixin` works identically.
- `Model.foreign_key()` works identically — it sets `sa_type` internally.
- All DB behavior, serialization, and prefix validation are unchanged.
