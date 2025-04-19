"""
Notes on polyfactory:

1. is_supported_type validates that the class can be used to generate a factory
https://github.com/litestar-org/polyfactory/issues/655#issuecomment-2727450854
"""

from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.field_meta import FieldMeta
import typing as t

# TODO not currently used
# def type_id_provider(cls, field_meta):
#     # TODO this doesn't work well with __ args:
#     # https://github.com/litestar-org/polyfactory/pull/666/files
#     return str(TypeID("hi"))


# BaseFactory.add_provider(TypeIDType, type_id_provider)


class SQLModelFactory[T](ModelFactory[T]):
    """
    Base factory for SQLModel models:

    1. Ability to ignore all relationship fks
    2. Option to ignore all pks
    """

    __is_base_factory__ = True

    @classmethod
    def should_set_field_value(cls, field_meta: FieldMeta, **kwargs: t.Any) -> bool:
        has_object_override = hasattr(cls, field_meta.name)

        # TODO this should be more intelligent
        if not has_object_override and (
            field_meta.name == "id" or field_meta.name.endswith("_id")
        ):
            return False

        return super().should_set_field_value(field_meta, **kwargs)


class ActiveModelFactory[T](SQLModelFactory[T]):
    __is_base_factory__ = True

    @classmethod
    def should_set_field_value(cls, field_meta: FieldMeta, **kwargs: t.Any) -> bool:
        # do not default deleted at mixin to deleted!
        # TODO should be smarter about detecting if the mixin is in place
        if field_meta.name in ["deleted_at", "updated_at", "created_at"]:
            return False

        return super().should_set_field_value(field_meta, **kwargs)

    # @classmethod
    # def build(
    #     cls,
    #     factory_use_construct: bool | None = None,
    #     sqlmodel_save: bool = False,
    #     **kwargs: t.Any,
    # ) -> T:
    #     result = super().build(factory_use_construct=factory_use_construct, **kwargs)

    #     # TODO allow magic dunder method here
    #     if sqlmodel_save:
    #         result.save()

    #     return result
