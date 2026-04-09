"""Rehydrate JSON-backed SQLModel fields into Pydantic objects after ORM loads.

SQLModel persists JSON columns as plain Python `dict` / `list` values when rows are
loaded from the database. This module restores the annotated Pydantic shapes on the
model instance after SQLAlchemy load and refresh operations.

Supported annotations are intentionally narrow:

- `SubModel`
- `SubModel | None`
- `list[SubModel]`
- `list[SubModel] | None`

Raw `dict` and tuple-shaped fields are left alone during rehydration, and ambiguous
unions are treated as out of scope instead of being coerced heuristically.

Snapshot-based mutation tracking is broader than rehydration and can still detect
in-place changes on raw `dict` and `list[dict]` fields.

Background: https://github.com/fastapi/sqlmodel/issues/63
"""

from typing import get_args, get_origin
import typing
import types
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy import event
from sqlalchemy.orm import attributes
from ..jsonb_snapshot import (
    snapshot_pydantic_fields,
    detect_json_mutations,
    register_before_commit_listener,
)
from ..logger import logger


class PydanticJSONMixin:
    """
    Restore JSON-backed fields to their annotated Pydantic shapes after ORM reloads.

    This mixin is paired with the engine-level JSON serializer so the same field can:

    1. Persist Pydantic models as JSON on write
    2. Automatically convert raw JSON to Pydantic models on load or refresh

    >>> class ExampleWithJSON(BaseModel, PydanticJSONMixin, table=True):
    >>>    list_field: list[SubObject] = Field(sa_type=JSONB())

    Supported field annotations:

    - `SubModel`
    - `SubModel | None`
    - `list[SubModel]`
    - `list[SubModel] | None`

    These are the supported rehydration shapes. Raw `dict` and `list[dict]` fields
    stay as plain Python containers, but snapshot tracking can still detect mutations
    on them.

    Not supported:

    - tuples of Pydantic models
    - nested lists such as `list[list[SubModel]]`
    - ambiguous unions with multiple non-`None` JSON shapes
    """

    def __init_subclass__(cls, **kwargs):
        """Register per-model SQLAlchemy instance events when a mapped subclass is declared.

        `load` fires after SQLAlchemy first constructs an instance from query results.
        `refresh` fires after SQLAlchemy reloads one or more attributes on an existing
        instance, including `session.refresh(...)` and expired-attribute reloads.

        The listeners are attached once per concrete model class so every mapped subclass
        gets the same rehydration behavior automatically.
        """
        super().__init_subclass__(**kwargs)

        if getattr(cls, "_pydantic_json_events_registered", False):
            return

        register_before_commit_listener()

        # `load` runs once for an ORM-created instance, after the initial column values exist.
        # `restore_load_context=True` preserves SQLAlchemy's loader context in case the hook
        # touches unloaded attributes (e.g. lazy relationships) during rehydration.
        event.listen(
            cls,
            "load",
            cls._rehydrate_pydantic_json_on_load,
            restore_load_context=True,
        )

        # `refresh` runs when SQLAlchemy repopulates an existing instance from a query.
        event.listen(
            cls,
            "refresh",
            cls._rehydrate_pydantic_json_on_refresh,
            restore_load_context=True,
        )

        cls._pydantic_json_events_registered = True

    @staticmethod
    def _is_pydantic_model_class(model_cls) -> bool:
        """Return whether the resolved annotation is a concrete Pydantic model class."""
        return isinstance(model_cls, type) and issubclass(model_cls, PydanticBaseModel)

    @classmethod
    def _resolve_pydantic_field_info(cls, annotation):
        """Normalize a supported annotation into list/single-model rehydration metadata.

        This helper only accepts the narrow annotation shapes the mixin promises to
        support. Unsupported or ambiguous annotations return `(False, None)` so the
        caller leaves the raw JSON value untouched.

        Supported annotations return a tuple of:

        - `is_top_level_list`: whether the field is a list of models vs. a single model
        - `model_cls`: the concrete model class to rehydrate to (should be pydantic, but we don't check that here)
        """
        origin = get_origin(annotation)

        if origin in (dict, tuple):
            return False, None

        annotation_args = get_args(annotation)
        is_top_level_list = origin is list
        model_cls = annotation

        if origin in (typing.Union, types.UnionType):
            # Only simple optional unions are eligible for automatic Pydantic coercion.
            non_none_types = [t for t in annotation_args if t is not type(None)]

            if len(non_none_types) != 1:
                return False, None

            model_cls = non_none_types[0]

        model_cls_origin = get_origin(model_cls)

        if (
            model_cls_origin is list
            and len(list_annotation_args := get_args(model_cls)) == 1
        ):
            model_cls = list_annotation_args[0]
            model_cls_origin = get_origin(model_cls)
            is_top_level_list = True

        if model_cls_origin in (list, tuple):
            return False, None

        return is_top_level_list, model_cls

    @classmethod
    def _rehydrate_pydantic_json_on_load(cls, target, context):
        """Handle the SQLAlchemy `load` event for newly materialized ORM instances.

        This is the first chance to replace raw JSON payloads from the result row with
        Pydantic objects on the in-memory model.
        """
        target.__transform_dict_to_pydantic__()

    @classmethod
    def _rehydrate_pydantic_json_on_refresh(cls, target, context, attrs_to_refresh):
        """Handle the SQLAlchemy `refresh` event for existing ORM instances.

        SQLAlchemy passes the refreshed attribute names when it has them, which lets us
        limit the rehydration work to the fields that were just repopulated.

        This is what keeps Pydantic JSON fields stable after expire-on-commit and
        partial `session.refresh(..., attribute_names=[...])` calls.
        """
        # SQLAlchemy tells us which attributes were refreshed, so avoid touching unrelated fields.
        jsonb_field_names = set(attrs_to_refresh) if attrs_to_refresh else None
        target.__transform_dict_to_pydantic__(jsonb_field_names=jsonb_field_names)

    def __transform_dict_to_pydantic__(self, jsonb_field_names: set[str] | None = None):
        """
        Replace raw JSON payloads on the instance with annotated Pydantic objects.

        `@reconstructor` is SQLAlchemy's class-decorator form of the `load` event, so
        this method runs automatically for the initial ORM load. The dedicated refresh
        listener above reuses the same logic for later reloads of an existing instance.

        `set_committed_value` is used so the converted value becomes the instance's
        committed state instead of looking like a user mutation.
        """
        # TODO do we need to inspect sa_type
        model_fields = self.model_fields

        for field_name, field_info in model_fields.items():
            if jsonb_field_names is not None and field_name not in jsonb_field_names:
                continue

            # pull the "raw" (raw dict) value of the JSONB field
            raw_value = getattr(self, field_name, None)

            # if the field is not set on the model, we can avoid doing anything with it
            if raw_value is None:
                continue

            # i.e. `list[SubModel]` or `list[SubModel] | None`
            is_top_level_list, model_cls = self._resolve_pydantic_field_info(
                field_info.annotation
            )

            if model_cls is None:
                logger.debug(
                    f"skipping pydantic json rehydration for unsupported annotation on {type(self).__name__}.{field_name}"
                )
                continue

            if not self._is_pydantic_model_class(model_cls):
                logger.debug(
                    f"skipping pydantic json rehydration for non-pydantic annotation on {type(self).__name__}.{field_name}: {model_cls}"
                )
                continue

            if is_top_level_list:
                # this is a user bug/issue
                if not isinstance(raw_value, list):
                    logger.warning(
                        f"expected a list for field {type(self).__name__}.{field_name} but got {type(raw_value)}; skipping rehydration"
                    )
                    continue

                # TODO I'm very skeptical of this logic, we should test more heavily and see if we can remove + simplify it
                # Preserve already-hydrated items so repeated load/refresh hooks stay idempotent.
                parsed_value = []
                needs_update = False

                for item in raw_value:
                    if isinstance(item, model_cls):
                        parsed_value.append(item)
                        continue

                    needs_update = True
                    parsed_value.append(model_cls(**item))

                if not needs_update:
                    # Reuse the existing list reference for idempotency.
                    parsed_value = raw_value

                if needs_update:
                    attributes.set_committed_value(self, field_name, parsed_value)

                continue

            if isinstance(raw_value, dict):
                raw_value = model_cls(**raw_value)
                attributes.set_committed_value(self, field_name, raw_value)

        snapshot_pydantic_fields(self, jsonb_field_names=jsonb_field_names)

    def has_json_mutations(self) -> bool:
        """Check whether any Pydantic JSON field has been mutated since the last snapshot.

        Eagerly detects mutations by comparing current field values against their
        serialized snapshots, and calls `flag_modified` for any that changed. Returns
        True if at least one field was mutated.

        This is an escape hatch for code that needs to know about pending JSON mutations
        before the automatic `before_flush` detection fires.
        """
        return bool(detect_json_mutations(self))
