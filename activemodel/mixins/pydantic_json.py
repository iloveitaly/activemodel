from typing import get_args, get_origin

from pydantic import BaseModel as PydanticBaseModel

from sqlalchemy.orm import reconstructor


class PydanticJSONMixin:
    @reconstructor
    def init_on_load(self):
        # TODO do we need to inspect sa_type
        for field_name, field_info in self.model_fields.items():
            raw_value = getattr(self, field_name, None)

            if raw_value is None:
                continue

            annotation = field_info.annotation
            origin = get_origin(annotation)
            args = get_args(annotation)

            # e.g. list[SomePydanticModel]
            if origin is list and len(args) == 1:
                model_cls = args[0]  # e.g. SomePydanticModel
                if issubclass(model_cls, PydanticBaseModel) and isinstance(
                    raw_value, list
                ):
                    parsed_value = [model_cls(**item) for item in raw_value]
                    setattr(self, field_name, parsed_value)
            # single model
            elif issubclass(annotation, PydanticBaseModel):
                setattr(self, field_name, annotation(**raw_value))
