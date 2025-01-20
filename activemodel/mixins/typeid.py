from sqlmodel import Column, Field
from typeid import TypeID

from activemodel.types.typeid import TypeIDType

# global list of prefixes to ensure uniqueness
_prefixes = []


def TypeIDMixin(prefix: str):
    assert prefix
    assert prefix not in _prefixes, (
        f"prefix {prefix} already exists, pick a different one"
    )

    class _TypeIDMixin:
        id: TypeIDType = Field(
            sa_column=Column(TypeIDType(prefix), primary_key=True, nullable=False),
            default_factory=lambda: TypeID(prefix),
        )

    _prefixes.append(prefix)

    return _TypeIDMixin


# TODO not sure if I love the idea of a dynamic class for each mixin as used above
#      may give this approach another shot in the future
# class TypeIDMixin2:
#     """
#     Mixin class that adds a TypeID primary key to models.


#     >>>    class MyModel(BaseModel, TypeIDMixin, prefix="xyz", table=True):
#     >>>        name: str

#     Will automatically have an `id` field with prefix "xyz"
#     """

#     def __init_subclass__(cls, *, prefix: str, **kwargs):
#         super().__init_subclass__(**kwargs)

#         cls.id: uuid.UUID = Field(
#             sa_column=Column(TypeIDType(prefix), primary_key=True),
#             default_factory=lambda: TypeID(prefix),
#         )
