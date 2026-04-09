# Automatic JSONB Mutation Tracking

`activemodel` uses a serialize-and-compare strategy to detect in-place JSON mutations.

After SQLAlchemy loads or refreshes a model instance, each tracked JSON field is serialized
to a canonical JSON string and stored as a snapshot. Right before commit, the current value
is serialized again and compared against that snapshot. If the serialized values differ,
`activemodel` calls SQLAlchemy's `flag_modified(...)` so the column is included in the
`UPDATE`.

This gives you ActiveRecord-style dirty tracking for complex JSON objects (either plain old py objects or Pydantic objects) without having to remember `flag_modified()` every time you mutate a nested attribute.

## What Is Tracked

The tracking layer currently covers:

* Pydantic-backed JSON fields such as `SubModel`, `SubModel | None`, `list[SubModel]`, and `list[SubModel] | None`
* raw `dict` fields
* typed `dict[...]` fields
* `list[dict]` fields
* top-level primitive lists such as `list[str]`, `list[int]`, `list[float]`, and `list[bool]`

Rehydration is narrower than mutation tracking.

`PydanticJSONMixin` only rehydrates supported Pydantic annotations back into model objects on
load and refresh. Raw `dict` values and supported raw `list[...]` values stay as plain Python
containers, but they still participate in snapshot-based mutation tracking.

## How It Works

1. a row is loaded or refreshed
2. supported Pydantic fields are rehydrated back into Pydantic objects
3. each tracked JSON field is serialized into a stable JSON string snapshot
4. before commit, the current value is serialized again
5. if the serialized value changed, the field is marked dirty with `flag_modified(...)`

This is why in-place changes like `model.profile.name = "updated"` and
`model.settings["theme"] = "dark"` can persist even though SQLAlchemy would not normally see
those nested mutations.

## Pydantic Example

```python
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from activemodel import BaseModel
from activemodel.mixins import PydanticJSONMixin, TypeIDMixin


class AuditEntry(PydanticBaseModel):
    actor: str
    action: str


class UserRecord(
    BaseModel,
    PydanticJSONMixin,
    TypeIDMixin("usr"),
    table=True,
):
    profile: AuditEntry = Field(sa_type=JSONB)


record = UserRecord.one("usr_123")
record.profile.action = "updated"
record.save()
```

The nested attribute mutation is detected automatically on commit.

## Raw Dict Example

```python
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from activemodel import BaseModel
from activemodel.mixins import PydanticJSONMixin, TypeIDMixin


class FeatureFlags(
    BaseModel,
    PydanticJSONMixin,
    TypeIDMixin("flag"),
    table=True,
):
    settings: dict[str, str] = Field(sa_type=JSONB)


record = FeatureFlags.one("flag_123")
record.settings["theme"] = "dark"
record.save()
```

`settings` stays a plain `dict`, but the in-place key mutation is still detected and persisted.

## List Of Dicts Example

```python
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from activemodel import BaseModel
from activemodel.mixins import PydanticJSONMixin, TypeIDMixin


class WebhookLog(
    BaseModel,
    PydanticJSONMixin,
    TypeIDMixin("wh"),
    table=True,
):
    deliveries: list[dict[str, str]] = Field(sa_type=JSONB)


log = WebhookLog.one("wh_123")
log.deliveries.append({"status": "ok", "provider": "stripe"})
log.save()
```

Top-level `list[dict]` payloads are tracked, including list mutation methods and nested dict
item updates.

## Scope Limits

The current implementation intentionally does not try to support every possible JSON type shape.

Notably out of scope:

* ambiguous unions such as `SubModel | dict | None`
* tuple-shaped JSON payloads
* nested list shapes such as `list[list[SubModel]]`

Those constraints keep rehydration rules predictable and avoid heuristic coercion.

## Key API References

The best entry points are the methods and functions that explain the behavior directly in their
docstrings:

* {py:func}`activemodel.jsonb_snapshot.snapshot_json_fields`
* {py:func}`activemodel.jsonb_snapshot.detect_json_mutations`
* {py:func}`activemodel.jsonb_snapshot.register_before_commit_listener`
* {py:meth}`activemodel.mixins.pydantic_json.PydanticJSONMixin.__transform_dict_to_pydantic__`
* {py:meth}`activemodel.mixins.pydantic_json.PydanticJSONMixin.has_json_mutations`

If you want the exact implementation details, the module-level docs in
{py:mod}`activemodel.jsonb_snapshot` and {py:mod}`activemodel.mixins.pydantic_json` are the
most direct place to read next.
