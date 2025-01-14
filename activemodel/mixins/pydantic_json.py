from types import UnionType
from typing import get_args, get_origin

from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.orm import reconstructor


class PydanticJSONMixin:
    """
    By default, SQLModel does not convert JSONB columns into pydantic models when they are loaded from the database.

    This mixin, combined with a custom serializer, fixes that issue.
    """

    @reconstructor
    def init_on_load(self):
        # TODO do we need to inspect sa_type
        for field_name, field_info in self.model_fields.items():
            raw_value = getattr(self, field_name, None)

            if raw_value is None:
                continue

            annotation = field_info.annotation
            origin = get_origin(annotation)

            # e.g. `dict` or `dict[str, str]`, we don't want to do anything with these
            if origin is dict:
                continue

            annotation_args = get_args(annotation)
            is_top_level_list = origin is list

            # if origin is not None:
            #     assert annotation.__class__ == origin

            model_cls = annotation

            # e.g. SomePydanticModel | None or list[SomePydanticModel] | None
            # annotation_args are (type, NoneType) in this case
            if isinstance(annotation, UnionType):
                non_none_types = [t for t in annotation_args if t is not type(None)]

                if len(non_none_types) == 1:
                    model_cls = non_none_types[0]

            # e.g. list[SomePydanticModel] | None, we have to unpack it
            # model_cls will print as a list, but it contains a subtype if you dig into it
            if (
                get_origin(model_cls) is list
                and len(list_annotation_args := get_args(model_cls)) == 1
            ):
                model_cls = list_annotation_args[0]
                is_top_level_list = True

            # e.g. list[SomePydanticModel] or list[SomePydanticModel] | None
            # iterate through the list and run each item through the pydantic model
            if is_top_level_list:
                if isinstance(raw_value, list) and issubclass(
                    model_cls, PydanticBaseModel
                ):
                    parsed_value = [model_cls(**item) for item in raw_value]
                    setattr(self, field_name, parsed_value)

                continue

            # single class
            if issubclass(model_cls, PydanticBaseModel):
                setattr(self, field_name, model_cls(**raw_value))
