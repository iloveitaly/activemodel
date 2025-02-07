from typing import Any, Type


class BaseModel(SQLModel):
    """
    Base model class to inherit from so we can hate python less

    https://github.com/woofz/sqlmodel-basecrud/blob/main/sqlmodel_basecrud/basecrud.py

    {before,after} hooks are modeled after Rails.
    """

    @classmethod
    def _apply_comments(cls):
        for field_name, field_obj in cls.model_fields.items():
            description = field_obj.description

            if not description:
                continue

            sa_kw = getattr(field_obj, "sa_column_kwargs", {})

            if "comment" not in field_obj.sa_column_kwargs:
                field_obj.sa_column_kwargs["comment"] = description

            # field_obj.sa_column_kwargs = sa_kw


class ActiveModelMeta(SQLModelMetaclass):
    def __init__(cls, name, bases, namespace, *args, **kwargs):
        super().__init__(name, bases, namespace, *args, **kwargs)
        cls._apply_comments()


class DescriptionMeta(SQLModelMetaclass):
    def __new__(
        cls,
        name: str,
        bases: tuple[Type[Any], ...],
        class_dict: dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        new_class = super().__new__(cls, name, bases, class_dict, **kwargs)
        fields = new_class.model_fields

        for field_name, field in fields.items():
            desc = field.description

            if not desc:
                continue
            if desc:
                # if you don't have a `Field()` definition tied to the field as a default, then sa_column_kwargs cannot
                # be set. This is a limitation of the current implementation of SQLModel.
                if hasattr(field, "sa_column_kwargs"):
                    if field.sa_column_kwargs is not PydanticUndefined:
                        field.sa_column_kwargs["comment"] = desc
                    else:
                        field.sa_column_kwargs = {"comment": desc}

                # deal with sa_column
                if field.sa_column is not PydanticUndefined:
                    if not field.sa_column.comment:
                        field.sa_column.comment = desc

                # deal with attributes of new_class
                # if hasattr(new_class, field_name):
                #     column = getattr(new_class, field_name)
                #     if hasattr(column, "comment") and not column.comment:
                #         column.comment = desc

        return new_class


from pydantic_core import PydanticUndefined
