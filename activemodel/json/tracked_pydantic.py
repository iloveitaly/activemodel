"""
Automatic mutation tracking for Pydantic models stored in JSONB columns.

After PydanticJSONMixin rehydrates JSON fields, this module attaches lightweight
wrappers that call SQLAlchemy's flag_modified when field values are mutated in place,
eliminating the need for manual flag_modified("field_name") calls.
"""

import weakref
import functools
from sqlalchemy.orm.attributes import flag_modified as sa_flag_modified
from pydantic import BaseModel as PydanticBaseModel
from .tracked_list import TrackedList


@functools.lru_cache(maxsize=None)
def _get_tracked_subclass(
    model_cls: type[PydanticBaseModel],
) -> type[PydanticBaseModel]:
    """Return a cached dynamic subclass that auto-calls flag_modified on attribute mutation."""

    class TrackedModel(model_cls):  # type: ignore[valid-type]
        # Marker so _attach_pydantic_tracking can detect already-tracked instances.
        _is_tracked_pydantic = True

        def __setattr__(self, name: str, value) -> None:
            super().__setattr__(name, value)
            # Skip private/dunder attributes set during Pydantic's own internals.
            if name.startswith("_"):
                return
            try:
                # object.__getattribute__ bypasses Pydantic's descriptor so we read
                # the raw tracking ref without triggering field validation.
                parent_ref = object.__getattribute__(self, "_sa_tracking_parent_ref")
            except AttributeError:
                # Tracking refs not yet set (e.g. during initial __init__ before attach).
                return
            parent = parent_ref()
            if parent is not None:
                field_name: str = object.__getattribute__(
                    self, "_sa_tracking_field_name"
                )
                sa_flag_modified(parent, field_name)

    TrackedModel.__name__ = f"Tracked{model_cls.__name__}"
    TrackedModel.__qualname__ = f"Tracked{model_cls.__name__}"
    # Pydantic's __eq__ checks __pydantic_generic_metadata__['origin'] (falling back to
    # __class__) as the type identity token before comparing field values. Setting 'origin'
    # to the original class makes TrackedSubObject == SubObject when field values match,
    # so the __class__ swap is invisible to equality checks without overriding __eq__.
    TrackedModel.__pydantic_generic_metadata__["origin"] = model_cls
    return TrackedModel


def _attach_pydantic_tracking(
    instance: PydanticBaseModel, parent, field_name: str
) -> None:
    """Swap the instance's class to a tracked subclass and register parent tracking refs."""
    current_cls = type(instance)

    if not getattr(current_cls, "_is_tracked_pydantic", False):
        tracked_cls = _get_tracked_subclass(current_cls)
        # __class__ swap is an in-place rebind: the object identity and all data are
        # preserved; isinstance checks against the original class still pass since
        # TrackedModel is a subclass.
        instance.__class__ = tracked_cls

    # object.__setattr__ writes directly to __dict__, bypassing Pydantic's field
    # validation so tracking attrs don't appear in model_dump() or trigger __setattr__.
    object.__setattr__(instance, "_sa_tracking_parent_ref", weakref.ref(parent))
    object.__setattr__(instance, "_sa_tracking_field_name", field_name)


def attach_tracking(value, parent, field_name: str, model_cls, *, is_list: bool):
    """
    Attach ORM dirty-state tracking to a rehydrated Pydantic field value.

    For list fields, converts plain lists to TrackedList (or refreshes refs on an
    existing TrackedList). For scalar fields, swaps the Pydantic instance's __class__
    to a tracked subclass in place.

    Returns the (possibly new) value -- callers must use set_committed_value if the
    returned value is a different object than what was passed in.
    """
    if is_list:
        if isinstance(value, TrackedList):
            # Already tracked -- just refresh the weakref in case the parent was re-bound
            # (e.g. after expunge/merge across sessions).
            value._sa_tracking_parent_ref = weakref.ref(parent)
            value._sa_tracking_field_name = field_name
            for item in value:
                if isinstance(item, PydanticBaseModel):
                    _attach_pydantic_tracking(item, parent, field_name)
            return value

        tracked = TrackedList(value, parent=parent, field_name=field_name)
        if isinstance(model_cls, type) and issubclass(model_cls, PydanticBaseModel):
            # Also track individual Pydantic items so mutations like list[0].field = x
            # propagate flag_modified up to the ORM parent.
            for item in tracked:
                if isinstance(item, PydanticBaseModel):
                    _attach_pydantic_tracking(item, parent, field_name)
        return tracked

    if isinstance(value, PydanticBaseModel):
        _attach_pydantic_tracking(value, parent, field_name)

    return value
