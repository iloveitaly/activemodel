"""
Notes on polyfactory:

1. is_supported_type validates that the class can be used to generate a factory
https://github.com/litestar-org/polyfactory/issues/655#issuecomment-2727450854
"""

import typing as t

from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.field_meta import FieldMeta
from typeid import TypeID

from activemodel.session_manager import global_session

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
        # TODO what is this checking for?
        has_object_override = hasattr(cls, field_meta.name)

        # TODO this should be more intelligent, it's goal is to detect all of the relationship field and avoid settings them
        if not has_object_override and (
            field_meta.name == "id" or field_meta.name.endswith("_id")
        ):
            return False

        return super().should_set_field_value(field_meta, **kwargs)


# TODO we need to think through how to handle relationships and autogenerate them
class ActiveModelFactory[T](SQLModelFactory[T]):
    __is_base_factory__ = True
    __sqlalchemy_session__ = None

    # TODO we shouldn't have to type this, but `save()` typing is not working
    @classmethod
    def save(cls, *args, **kwargs) -> T:
        """
        Where this gets tricky, is this can be called multiple times within the same callstack. This can happen when
        a factory uses other factories to create relationships.

        In a truncation strategy, the __sqlalchemy_session__ is set to None.
        """
        with global_session(cls.__sqlalchemy_session__):
            return cls.build(*args, **kwargs).save()

    @classmethod
    def foreign_key_typeid(cls):
        """
        Return a random type id for the foreign key on this model.

        This is helpful for generating TypeIDs for testing 404s, parsing, manually settings, etc
        """
        # TODO right now assumes the model is typeid, maybe we should assert against this?
        primary_key_name = cls.__model__.primary_key_column().name
        return TypeID(
            cls.__model__.model_fields[primary_key_name].sa_column.type.prefix
        )

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
