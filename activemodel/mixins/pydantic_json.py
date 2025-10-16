"""
Need to store nested Pydantic models in PostgreSQL using FastAPI and SQLModel.

SQLModel lacks a direct JSONField equivalent (like Tortoise ORM's JSONField), making it tricky to handle nested model data as JSON in the DB.

Extensive discussion on the problem: https://github.com/fastapi/sqlmodel/issues/63
"""

from typing import get_args, get_origin
import typing
import types
from pydantic import BaseModel as PydanticBaseModel
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

    @reconstructor
    def __transform_dict_to_pydantic__(self):
        """
        Transforms dictionary fields into Pydantic models upon loading.

        - Reconstructor only runs once, when the object is loaded.
        - We manually call this method on save(), etc to ensure the pydantic types are maintained
        - `set_committed_value` sets Pydantic models as committed, avoiding `setattr` marking fields as modified
          after loading from the database.
        """
        # TODO do we need to inspect sa_type
        for field_name, field_info in self.model_fields.items():
            raw_value = getattr(self, field_name, None)

            # if the field is not set on the model, we can avoid doing anything with it
            if raw_value is None:
                continue

            annotation = field_info.annotation
            origin = get_origin(annotation)

            # e.g. `dict` or `dict[str, str]`, we don't want to do anything with these
            if origin in (dict, tuple):
                continue

            annotation_args = get_args(annotation)
            is_top_level_list = origin is list
            model_cls = annotation

            # TODO not sure what was going on here...
            # if origin is not None:
            #     assert annotation.__class__ == origin

            # UnionType is only one way of defining an optional. If older typing syntax is used `Tuple[str] | None` the
            # type annotation is different: `typing.Optional[typing.Tuple[float, float]]`. This is why we check both
            # types below.

            # e.g. SomePydanticModel | None or list[SomePydanticModel] | None
            # annotation_args are (type, NoneType) in this case. Remove NoneType.
            if origin in (typing.Union, types.UnionType):
                non_none_types = [t for t in annotation_args if t is not type(None)]

                if len(non_none_types) == 1:
                    model_cls = non_none_types[0]
                else:
                    # if there's more than one non-none type, it isn't meant to be serialized to JSON
                    pass

            model_cls_origin = get_origin(model_cls)

            # e.g. list[SomePydanticModel] | None, we have to unpack it
            # model_cls will print as a list, but it contains a subtype if you dig into it
            if (
                model_cls_origin is list
                and len(list_annotation_args := get_args(model_cls)) == 1
            ):
                model_cls = list_annotation_args[0]
                model_cls_origin = get_origin(model_cls)

                is_top_level_list = True

            # e.g. list[SomePydanticModel] or list[SomePydanticModel] | None
            # iterate through the list and run each item through the pydantic model
            if is_top_level_list:
                if isinstance(raw_value, list) and issubclass(
                    model_cls, PydanticBaseModel
                ):
                    parsed_value = [model_cls(**item) for item in raw_value]
                    attributes.set_committed_value(self, field_name, parsed_value)
                continue

            if model_cls_origin in (list, tuple):
                continue

            # single class
            if issubclass(model_cls, PydanticBaseModel):
                attributes.set_committed_value(self, field_name, model_cls(**raw_value))
