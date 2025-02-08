"""
Pydantic has a great DX for adding docstrings to class attributes.

Making sure these docstrings make their way to the DB schema is helpful for a bunch of reasons (LLM understanding being one of them)
"""

from typing import Any, Type

from pydantic_core import PydanticUndefined
from sqlmodel.main import SQLModelMetaclass

# this line is very important: it patches FieldInfo to support comments
from . import (
    field_info_patch,  # noqa: F401
    get_column_from_field_patch,  # noqa: F401
)
from .utils import logger


class FieldDescriptionMeta(SQLModelMetaclass):
    def __new__(
        cls,
        name: str,
        bases: tuple[Type[Any], ...],
        class_dict: dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        """
        This metaclass exists to take the field-level docstrings and copy them to the sa_column_kwargs. A class only has a single metaclass.

        When the Python interpreter reads and executes the class definition, it uses the metaclass's new method to create the new class object.
        This is before any instances of the class are created. Thus, any field modifications (such as setting comments) done in new happen as soon as the class is defined.
        """

        class_with_docstrings = super().__new__(cls, name, bases, class_dict, **kwargs)
        mutated_field = False

        for field_name, field in class_with_docstrings.model_fields.items():
            field_description = field.description

            if not field_description:
                continue

            has_column_definition = (
                hasattr(field, "sa_column") and field.sa_column is not PydanticUndefined
            )

            # if you don't have a `Field()` definition tied to the field as a default, then sa_column_kwargs cannot
            # be set. This is a limitation of the current implementation of SQLModel.
            if not has_column_definition and hasattr(field, "sa_column_kwargs"):
                if field.sa_column_kwargs is not PydanticUndefined:
                    field.sa_column_kwargs["comment"] = field_description
                else:
                    field.sa_column_kwargs = {"comment": field_description}

                mutated_field = True
                continue

            # if sa_column is set on the field definition, then we can set the comment on that directly
            # also occurs when no `Field` is set (bare field with type annotation)
            if has_column_definition and not field.sa_column.comment:
                field.sa_column.comment = field_description
                mutated_field = True
                continue

            logger.warning(
                "field comment found, but no sa_column_kwargs or sa_column found. %s",
                field_name,
            )

            # breakpoint()

            # TODO not sure what I was thinking here?
            # deal with attributes of new_class
            # if hasattr(new_class, field_name):
            #     column = getattr(new_class, field_name)
            #     if hasattr(column, "comment") and not column.comment:
            #         column.comment = desc

            class_dict[field_name] = field

        if not mutated_field:
            return class_with_docstrings

        class_with_comments = super().__new__(cls, name, bases, class_dict, **kwargs)
        return class_with_comments
