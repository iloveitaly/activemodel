# whenever Integration

`activemodel` has built-in support for the [`whenever`](https://github.com/ariebovenberg/whenever) datetime library. Three types are supported:

| whenever type   | SQLAlchemy column type        | Notes                                         |
|-----------------|-------------------------------|-----------------------------------------------|
| `Instant`       | `TIMESTAMP WITH TIME ZONE`    | UTC-normalized point in time                  |
| `ZonedDateTime` | `TIMESTAMP WITH TIME ZONE`    | IANA timezone name is not preserved in the DB |
| `PlainDateTime` | `TIMESTAMP WITHOUT TIME ZONE` | No timezone; matches SQLite/naive datetime    |

## Defining fields on a model

Import and annotate fields with the bare `whenever` type. The SQLAlchemy column type is resolved automatically via the `get_sqlalchemy_type` patch that `activemodel` applies on import.

```python
from whenever import Instant, PlainDateTime, ZonedDateTime
from activemodel import BaseModel
from activemodel.mixins import TypeIDPrimaryKey

class Event(BaseModel, table=True):
    id: str = TypeIDPrimaryKey("event")
    occurred_at: Instant
    scheduled_at: ZonedDateTime | None = None
    local_time: PlainDateTime | None = None
```

`Instant` and `ZonedDateTime` both map to `TIMESTAMP WITH TIME ZONE` on Postgres. The difference is that `Instant` is always UTC-normalized whereas `ZonedDateTime` carries a timezone at the application level. Neither preserves the original IANA timezone name in the database — on read, `ZonedDateTime` is reconstructed from the stored UTC offset.

`PlainDateTime` maps to `TIMESTAMP WITHOUT TIME ZONE` and has no timezone at all, matching the behavior of SQLite and Postgres naive datetimes.

## Reading and writing

Values round-trip transparently through SQLAlchemy:

```python
from whenever import Instant, ZonedDateTime

event = Event(
    occurred_at=Instant.now(),
    scheduled_at=ZonedDateTime.now_in_system_tz(),
).save()

fetched = Event.get(event.id)
assert isinstance(fetched.occurred_at, Instant)
assert isinstance(fetched.scheduled_at, ZonedDateTime)
```

## Factories

`ActiveModelFactory` registers providers for all three types automatically, so any factory subclass generates valid values without extra configuration:

```python
from activemodel.pytest.factories import ActiveModelFactory
from my_app.models import Event

class EventFactory(ActiveModelFactory[Event]):
    __model__ = Event

event = EventFactory.build()
assert isinstance(event.occurred_at, Instant)
```

Generated values use the system timezone:

- `Instant` → `Instant.now()`
- `ZonedDateTime` → `ZonedDateTime.now_in_system_tz()`
- `PlainDateTime` → `ZonedDateTime.now_in_system_tz().to_plain()`

To override a field with a specific value, pass it as a keyword argument:

```python
from whenever import Instant

past_event = EventFactory.build(occurred_at=Instant.now().subtract(hours=24))
```
