"""
Need to store nested Pydantic models in PostgreSQL using FastAPI and SQLModel.

SQLModel lacks a direct JSONField equivalent (like Tortoise ORM's JSONField), making it tricky to handle nested model data as JSON in the DB.

Extensive discussion on the problem: https://github.com/fastapi/sqlmodel/issues/63
"""

from typing import get_args, get_origin
import typing
import types
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy import event
from sqlalchemy.orm import reconstructor, attributes


class PydanticJSONMixin:
    """
    By default, SQLModel does not convert JSONB columns into pydantic models when they are loaded from the database.

    This mixin, combined with a custom serializer (`_serialize_pydantic_model`), fixes that issue.

    >>> class ExampleWithJSON(BaseModel, PydanticJSONMixin, table=True):
    >>>    list_field: list[SubObject] = Field(sa_type=JSONB()

    Notes:

    - Tuples of pydantic models are not supported, only lists.
    - Nested lists of pydantic models are not supported, e.g. list[list[SubObject]]
    """

    def __init_subclass__(cls, **kwargs):
        """Register per-model SQLAlchemy instance events when a mapped subclass is declared.

        `load` fires after SQLAlchemy first constructs an instance from query results.
        `refresh` fires after SQLAlchemy reloads one or more attributes on an existing
        instance, including `session.refresh(...)` and expired-attribute reloads.
        """
        super().__init_subclass__(**kwargs)

        if getattr(cls, "_pydantic_json_events_registered", False):
            return

        # `load` runs once for an ORM-created instance, after the initial column values exist.
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

        # Preserve SQLAlchemy's loader context in case the hook touches unloaded state.

        cls._pydantic_json_events_registered = True

    @staticmethod
    def _is_pydantic_model_class(model_cls) -> bool:
        """Return whether the resolved annotation is a concrete Pydantic model class."""
        return isinstance(model_cls, type) and issubclass(model_cls, PydanticBaseModel)

    @classmethod
    def _resolve_pydantic_field_info(cls, annotation):
        """Normalize a field annotation into list/single-model metadata for rehydration."""
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
        """Handle the SQLAlchemy `load` event for newly materialized ORM instances."""
        target.__transform_dict_to_pydantic__()

    @classmethod
    def _rehydrate_pydantic_json_on_refresh(cls, target, context, attrs_to_refresh):
        """Handle the SQLAlchemy `refresh` event for existing ORM instances.

        SQLAlchemy passes the refreshed attribute names when it has them, which lets us
        limit the rehydration work to the fields that were just repopulated.
        """
        # SQLAlchemy tells us which attributes were refreshed, so avoid touching unrelated fields.
        field_names = set(attrs_to_refresh) if attrs_to_refresh else None
        target.__transform_dict_to_pydantic__(field_names=field_names)

    @reconstructor
    def __transform_dict_to_pydantic__(self, field_names: set[str] | None = None):
        """
        Transforms dictionary fields into Pydantic models upon loading.

                - Reconstructor is SQLAlchemy's class-decorator form of the `load` event.
                - It only runs for the initial ORM load, not for later `refresh` events.
                - The dedicated `refresh` listener above covers reloads of existing instances.
                - We manually call this method on save(), etc to ensure the pydantic types are maintained
        - `set_committed_value` sets Pydantic models as committed, avoiding `setattr` marking fields as modified
          after loading from the database.
        """
        # TODO do we need to inspect sa_type
        model_fields = getattr(type(self), "model_fields")

        for field_name, field_info in model_fields.items():
            if field_names is not None and field_name not in field_names:
                continue

            raw_value = getattr(self, field_name, None)

            # if the field is not set on the model, we can avoid doing anything with it
            if raw_value is None:
                continue

            is_top_level_list, model_cls = self._resolve_pydantic_field_info(
                field_info.annotation
            )

            if model_cls is None:
                continue

            if is_top_level_list:
                if not isinstance(raw_value, list) or not self._is_pydantic_model_class(
                    model_cls
                ):
                    continue

                # Preserve already-hydrated items so repeated load/refresh hooks stay idempotent.
                parsed_value = []
                needs_update = False

                for item in raw_value:
                    if isinstance(item, model_cls):
                        parsed_value.append(item)
                        continue

                    needs_update = True
                    parsed_value.append(model_cls(**item))

                if needs_update:
                    attributes.set_committed_value(self, field_name, parsed_value)

                continue

            if not self._is_pydantic_model_class(model_cls):
                continue

            if isinstance(raw_value, model_cls):
                continue

            if isinstance(raw_value, dict):
                attributes.set_committed_value(self, field_name, model_cls(**raw_value))
