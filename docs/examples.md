# Examples

This section provides practical examples of how to use `activemodel` in your projects, demonstrating common patterns for structured data, lifecycle management, testing, and complex schema definitions.

## Advanced Field Types and Configuration

`activemodel` leverages `SQLModel` and `SQLAlchemy` to support complex column types, constraints, and schema configurations.

### Custom SQLAlchemy Types and Datetimes

You can map specific fields to underlying SQLAlchemy types using `sa_type`. This is especially useful for timezone-aware datetimes and advanced PostgreSQL types.

```python
import sqlalchemy as sa
from typing import Tuple
from datetime import datetime
from sqlmodel import Field
from activemodel import BaseModel
from sqlalchemy_postgres_point import PointType

class LocationEvent(BaseModel, table=True):
    # Timezone-aware datetimes using sa_type
    booked_datetime: datetime = Field(
        sa_type=sa.DateTime(timezone=True)  # type: ignore
    )
    
    # Custom PostgreSQL Types (e.g. Point)
    location: Tuple[float, float] | None = Field(
        default=None, 
        sa_type=PointType
    )
```

### Defaults, Exclusions, and Constraints

Control schema visibility and enforce constraints directly within the `Field` definition.

```python
from sqlmodel import Field
from activemodel import BaseModel

class Product(BaseModel, table=True):
    # Require values greater than zero
    price_cents: int = Field(gt=0)
    
    # Exclude internal fields from Pydantic schemas (e.g. FastAPI responses)
    stripe_account_id: str | None = Field(default=None, exclude=True)
    
    # Define max lengths and index the column
    status: str = Field(default="active", max_length=100, index=True)
```

### Advanced TypeID Usage

While `TypeIDMixin` handles the primary key, you can use `TypeIDType` and the `.foreign_key()` helper to manage related IDs securely, and even enforce prefixes.

```python
from activemodel import BaseModel
from activemodel.mixins import TypeIDMixin
from activemodel.types import TypeIDType
from sqlmodel import Field, Relationship

class Distribution(BaseModel, TypeIDMixin("dst"), table=True):
    name: str

class Screening(BaseModel, TypeIDMixin("scr"), table=True):
    # Standard Foreign Key relationship definition helper
    distribution_id: TypeIDType = Distribution.foreign_key(index=True)
    distribution: Distribution = Relationship()

    # Enforce a specific TypeID prefix on a field
    merged_into_screening_id: TypeIDType | None = Field(
        default=None, 
        sa_type=TypeIDType(prefix="scr")  # type: ignore
    )
```

## Structured JSON with Pydantic Models

Using the `PydanticJSONMixin`, you can store complex Pydantic models or lists of models in PostgreSQL `JSONB` columns. The mixin handles serialization and deserialization automatically.

### Single Model Column

```python
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field
from activemodel import BaseModel
from activemodel.mixins import PydanticJSONMixin, TypeIDMixin, TimestampsMixin

class UserActionAuditData(PydanticBaseModel):
    ip_address: str
    build_version: str
    timestamp: str

class RefundChoice(
    BaseModel,
    TimestampsMixin,
    PydanticJSONMixin,
    TypeIDMixin("rc"),
    table=True,
):
    chosen_info: UserActionAuditData | None = Field(default=None, sa_type=JSONB)
    "audit data about the user's choice stored as structured JSON"
```

### List of Models Column

You can also store a list of Pydantic models. This is useful for things like transcripts, audit logs, or line items.

```python
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field
from activemodel import BaseModel
from activemodel.mixins import PydanticJSONMixin, TypeIDMixin

class TranscriptEntry(PydanticBaseModel):
    speaker: str
    content: str
    startTime: int  # in milliseconds
    endTime: int    # in milliseconds

class AIVisitTranscript(
    BaseModel,
    PydanticJSONMixin,
    TypeIDMixin("ai_vt"),
    table=True,
):
    # The mixin will convert this list of dicts to a list of TranscriptEntry objects
    transcript_data: list[TranscriptEntry] = Field(sa_type=JSONB)
```

## Lifecycle Hooks

`activemodel` supports several lifecycle hooks that allow you to execute logic at specific points in a model's lifecycle.

### Basic Validation and Defaults

```python
from datetime import datetime, timedelta
from activemodel import BaseModel
from activemodel.mixins import TypeIDMixin, TimestampsMixin
from sqlmodel import Field

class Screening(BaseModel, TimestampsMixin, TypeIDMixin("scr"), table=True):
    funding_goal: int = Field(default=0)
    funding_ending_at: datetime | None = Field(default=None)

    def before_create(self):
        """Set a default ending date only on creation."""
        if self.funding_ending_at is None:
            self.funding_ending_at = datetime.now() + timedelta(days=30)

    def before_save(self):
        """Prevent saving invalid data."""
        if self.funding_goal < 0:
            raise ValueError("Funding goal must be non-negative.")
```

### Advanced Hooks: Immutable Fields

You can use `before_save` to enforce immutability or perform complex validations.

```python
import hashlib
from activemodel import BaseModel
from activemodel.mixins import TypeIDMixin
from sqlmodel import Field

def hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()

class LLMResponse(BaseModel, TypeIDMixin("llr"), table=True):
    prompt: str
    prompt_hash: str | None = Field(default=None, nullable=False)

    def before_save(self):
        new_hash = hash_prompt(self.prompt)
        
        # Enforce that the prompt cannot be changed once saved
        if self.prompt_hash and self.prompt_hash != new_hash:
            raise ValueError("Prompts should never be modified once they are cached")

        self.prompt_hash = new_hash
```

## Factories with Polyfactory

`activemodel` integrates with [polyfactory](https://polyfactory.litestar.dev/) via `ActiveModelFactory`. This is powerful for generating complex, related test data automatically.

### Complex Data Generation and Datetimes

Factories can use `BaseFactory.__faker__` for generating rich mock data and dynamic values using `Use`. We also recommend utilizing robust datetime libraries like `whenever` for generating timestamps.

```python
from polyfactory import BaseFactory, Use
from whenever import Instant
from activemodel.pytest.factories import ActiveModelFactory
from app.models.user import User

class UserFactory(ActiveModelFactory[User]):
    # Static defaults
    status = "active"

    # Using Faker for random structured data
    name = BaseFactory.__faker__.name
    email = BaseFactory.__faker__.email
    
    # Using Use() to execute a function dynamically for each build
    # Combining with `whenever` for timezone-aware datetimes
    last_active_at = Use(
        lambda: Instant.now().to_system_tz().add(days=-5).py_datetime()
    )
```

### Recursive Factory Dependencies

You can use `post_build` to automatically create and associate related models if they aren't provided.

```python
from activemodel.pytest.factories import ActiveModelFactory
from app.models.order import TicketReservationOrder

class TicketReservationOrderFactory(ActiveModelFactory[TicketReservationOrder]):
    """
    Advanced factory that automatically handles recursive dependencies.
    """
    ticket_count = 1

    @classmethod
    def post_build(cls, model):
        """
        Automatically ensure the order has a Distribution and a Screening.
        """
        if not model.distribution_id:
            # Recursively use another factory
            from .distribution import DistributionFactory
            model.distribution = DistributionFactory.save()
            model.distribution_id = model.distribution.id

        if not model.screening_id:
            # Create a screening associated with the same distribution
            from .screening import ScreeningFactory
            model.screening = ScreeningFactory.save(
                distribution_id=model.distribution_id
            )
            model.screening_id = model.screening.id

        # Always save the model at the end of post_build in an ActiveModelFactory
        return model.save()
```

### Complex Post-Save Logic

Use `post_save` for actions that require the record to already have an ID or for complex side effects.

```python
class FullyFundedScreeningFactory(ActiveModelFactory[Screening]):
    @classmethod
    def post_save(cls, model):
        """
        After creating a screening, automatically create enough 
        paid orders to reach the funding goal.
        """
        from .order import TicketReservationOrderFactory
        
        ticket_count = 10 
        for _ in range(ticket_count):
            TicketReservationOrderFactory.save(
                screening_id=model.id,
                status="paid"
            )
        
        # Refresh to ensure any computed fields/relationships are updated
        return model.refresh()
```

## Standard Model Example

A typical model combining common mixins:

```python
from activemodel import BaseModel
from activemodel.mixins import (
    PydanticJSONMixin,
    SoftDeletionMixin,
    TimestampsMixin,
    TypeIDMixin,
)
from activemodel.types import TypeIDType
from sqlmodel import Field, Relationship

class Partner(
    BaseModel,
    TimestampsMixin,
    SoftDeletionMixin,
    TypeIDMixin("prt"),
    table=True,
):
    """
    Comprehensive model example with TypeID, Timestamps, and Soft Delete.
    """
    name: str = Field(nullable=False)
    slug: str = Field(nullable=False, unique=True)
    
    # Using foreign_key() helper for clean relationship definitions
    doctor_id: TypeIDType = Doctor.foreign_key()
    doctor: Doctor = Relationship()
```