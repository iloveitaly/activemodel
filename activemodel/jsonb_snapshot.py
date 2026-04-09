"""Serialize-and-compare snapshot tracking for JSON-backed fields.

After each ORM load/refresh, each tracked JSON field is serialized to a canonical JSON
string and stored as a snapshot. Before commit, the current value is re-serialized and
compared; if the strings differ, `flag_modified` is called so SQLAlchemy includes the
column in the UPDATE.

This mirrors how Rails' ActiveRecord handles JSON column dirty-tracking: compare the
serialized form of the current value against the serialized form of the original, rather
than intercepting every mutation with proxy objects.
"""

import json
import types
import typing
from typing import get_args, get_origin

from pydantic_core import to_jsonable_python
from sqlalchemy import event
from sqlalchemy.orm import Session, attributes as sa_attributes


def _value_to_json_string(value) -> str | None:
    """Serialize a Pydantic model, list of models, or raw dict to a canonical JSON string.

    `to_jsonable_python` (pydantic-core, Rust) converts the value to a JSON-serializable
    form before dumping. `sort_keys=True` ensures stable output when a Pydantic-annotated
    field is assigned a raw dict with arbitrary key ordering rather than a Pydantic model.

    Uses orjson when available (2-10x faster, Rust-based); falls back to stdlib json.
    orjson returns bytes, so .decode() is required when it is available. The serializer
    is resolved once on first call and cached on the function object.
    """
    if value is None:
        return None

    if not hasattr(_value_to_json_string, "_impl"):
        try:
            import orjson

            _value_to_json_string._impl = lambda o: orjson.dumps(
                o, option=orjson.OPT_SORT_KEYS
            ).decode()
        except ImportError:
            _value_to_json_string._impl = lambda o: json.dumps(o, sort_keys=True)

    return _value_to_json_string._impl(to_jsonable_python(value))


def _is_plain_json_container_annotation(annotation) -> bool:
    origin = get_origin(annotation)

    if origin in (typing.Union, types.UnionType):
        # optional dict/list[dict] fields should still participate in snapshot tracking
        non_none_types = [
            item for item in get_args(annotation) if item is not type(None)
        ]

        if len(non_none_types) != 1:
            return False

        return _is_plain_json_container_annotation(non_none_types[0])

    if annotation is dict or origin is dict:
        return True

    if annotation is list or origin is list:
        # only top-level list[dict] is tracked here; nested list shapes remain unsupported
        list_item_types = get_args(annotation)

        if len(list_item_types) != 1:
            return False

        list_item_type = list_item_types[0]

        return list_item_type is dict or get_origin(list_item_type) is dict

    return False


def _supports_snapshot_tracking(instance, annotation) -> bool:
    # reuse the mixin's pydantic classifier so rehydrated shapes and tracked shapes stay aligned
    _, model_cls = instance._resolve_pydantic_field_info(annotation)

    if model_cls is not None and instance._is_pydantic_model_class(model_cls):
        return True

    # plain dict containers are tracked even though load/refresh leaves them as raw python values
    return _is_plain_json_container_annotation(annotation)


def snapshot_json_fields(instance, jsonb_field_names: set[str] | None = None) -> None:
    """Store a serialized snapshot of each tracked JSON field on the instance.

    Called after rehydration so the snapshot reflects the committed database state.
    When `jsonb_field_names` is provided (partial refresh), only those fields are
    re-snapshotted; existing snapshots for other fields are preserved.
    """
    if jsonb_field_names is not None and not jsonb_field_names:
        return

    # copy so a partial refresh only overwrites the refreshed fields, leaving others intact
    existing = getattr(instance, "_json_field_snapshots", {})
    snapshots = dict(existing)

    for field_name, field_info in type(instance).model_fields.items():
        # partial refresh: only re-snapshot the fields that were just reloaded from DB
        if jsonb_field_names is not None and field_name not in jsonb_field_names:
            continue

        raw_value = getattr(instance, field_name, None)

        # None means the field isn't present / was cleared; drop any existing snapshot
        if raw_value is None:
            snapshots.pop(field_name, None)
            continue

        if not _supports_snapshot_tracking(instance, field_info.annotation):
            continue

        snapshots[field_name] = _value_to_json_string(raw_value)

    # bypass Pydantic's __setattr__ so this private dict is invisible to model_dump/validation
    object.__setattr__(instance, "_json_field_snapshots", snapshots)


def detect_json_mutations(instance) -> list[str]:
    """Compare current field values against snapshots, flagging any that changed.

    Returns a list of field names that were mutated since the last snapshot.
    Side effect: calls `flag_modified` on the SQLAlchemy instance for each changed field.
    """

    # store a map of field name to serialized json string for that field
    snapshots: dict[str, str | None] = getattr(instance, "_json_field_snapshots", {})

    # new instances (never loaded from DB) have no snapshot; nothing to compare
    if not snapshots:
        return []

    mutated_fields: list[str] = []
    model_fields = type(instance).model_fields

    for field_name, snapshot_str in snapshots.items():
        field_info = model_fields.get(field_name)
        if field_info is None:
            continue

        if not _supports_snapshot_tracking(instance, field_info.annotation):
            continue

        current_value = getattr(instance, field_name, None)
        current_str = _value_to_json_string(current_value)

        if current_str != snapshot_str:
            # tell SQLAlchemy this column is dirty so it's included in the UPDATE
            sa_attributes.flag_modified(instance, field_name)
            mutated_fields.append(field_name)
        else:
            # serialized value is unchanged; if SQLAlchemy already marked the field
            # modified (e.g. direct assignment of an equivalent value), reset its
            # history to prevent a spurious UPDATE.
            #
            # set_committed_value is the only public API for this — SQLAlchemy has no
            # flag_clean/unflag_modified. The alternatives are worse: expire() forces a
            # DB reload on next access; _commit() is internal. set_committed_value does
            # slightly more than we need (it also updates the committed baseline to
            # current_value), but since the serialized forms are equal the DB value is
            # the same, so the baseline shift is harmless.

            sa_attributes.set_committed_value(instance, field_name, current_value)

    return mutated_fields


_before_commit_registered = False


def register_before_commit_listener() -> None:
    """Register a session-level before_commit handler to detect in-place JSON mutations.

    Uses before_commit (not before_flush) because SQLAlchemy skips the flush entirely
    when it sees no pending changes -- meaning before_flush never fires for in-place
    mutations that haven't been explicitly flagged. before_commit fires unconditionally,
    giving us the chance to call flag_modified before the flush decision is made.

    Safe to call multiple times -- the listener is only registered once.
    """
    global _before_commit_registered

    if _before_commit_registered:
        return

    # avoid circular imports
    from .mixins.pydantic_json import PydanticJSONMixin

    # applies to all Session subclasses (including sqlmodel.Session) via SQLAlchemy propagation
    @event.listens_for(Session, "before_commit")
    def _detect_tracked_json_mutations(session):
        # snapshot is only set on persistent instances that came through our load/refresh hooks
        for instance in list(session.identity_map.values()):
            if isinstance(instance, PydanticJSONMixin):
                detect_json_mutations(instance)

    _before_commit_registered = True
