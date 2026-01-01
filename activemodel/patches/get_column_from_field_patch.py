"""
Pydantic has a great DX for adding docstrings to fields. This allows devs to easily document the fields of a model.

Making sure these docstrings make their way to the DB schema is helpful for a bunch of reasons (LLM understanding being one of them).

This patch mutates a core sqlmodel function which translates pydantic FieldInfo objects into sqlalchemy Column objects. It adds the field description as a comment to the column.

Note that FieldInfo *from pydantic* is used when a "bare" field is defined. This can be confusing, because when inspecting model fields, the class name looks exactly the same.

Some ideas for this originally sourced from: https://github.com/fastapi/sqlmodel/issues/492#issuecomment-2489858633
"""

from typing import (
    TYPE_CHECKING,
    Any,
    Sequence,
    cast,
)

import sqlmodel
from sqlalchemy import (
    Column,
    ForeignKey,
)
from sqlmodel._compat import (  # type: ignore[attr-defined]
    ModelMetaclass,
    Representation,
    Undefined,
    UndefinedType,
    is_field_noneable,
)
from sqlmodel.main import get_sqlalchemy_type

from activemodel.utils import hash_function_code

if TYPE_CHECKING:
    from pydantic._internal._model_construction import ModelMetaclass as ModelMetaclass
    from pydantic._internal._repr import Representation as Representation
    from pydantic_core import PydanticUndefined as Undefined
    from pydantic_core import PydanticUndefinedType as UndefinedType


# https://github.com/fastapi/sqlmodel/blob/5c2dbe419edc2d15200eee5269c9508987944ed8/sqlmodel/main.py#L691
assert (
    hash_function_code(sqlmodel.main.get_column_from_field)
    == "ab3cdd5d20079358911b6aef76b3916ba3890b20eb07e970a0f35bd63e1713d9"
), (
    f"get_column_from_field has changed, please verify the patch is still valid: {hash_function_code(sqlmodel.main.get_column_from_field)}"
)


def get_column_from_field(field: Any) -> Column:  # type: ignore
    field_info = field
    sa_column = getattr(field_info, "sa_column", Undefined)
    if isinstance(sa_column, Column):
        # <Change>
        if not sa_column.comment and (field_comment := field_info.description):
            sa_column.comment = field_comment
        # </Change>
        return sa_column
    sa_type = get_sqlalchemy_type(field)
    primary_key = getattr(field_info, "primary_key", Undefined)
    if primary_key is Undefined:
        primary_key = False
    index = getattr(field_info, "index", Undefined)
    if index is Undefined:
        index = False
    nullable = not primary_key and is_field_noneable(field)
    # Override derived nullability if the nullable property is set explicitly
    # on the field
    field_nullable = getattr(field_info, "nullable", Undefined)  # noqa: B009
    if field_nullable is not Undefined:
        assert not isinstance(field_nullable, UndefinedType)
        nullable = field_nullable
    args = []
    foreign_key = getattr(field_info, "foreign_key", Undefined)
    if foreign_key is Undefined:
        foreign_key = None
    unique = getattr(field_info, "unique", Undefined)
    if unique is Undefined:
        unique = False
    if foreign_key:
        if field_info.ondelete == "SET NULL" and not nullable:
            raise RuntimeError('ondelete="SET NULL" requires nullable=True')
        assert isinstance(foreign_key, str)
        ondelete = getattr(field_info, "ondelete", Undefined)
        if ondelete is Undefined:
            ondelete = None
        assert isinstance(ondelete, (str, type(None)))  # for typing
        args.append(ForeignKey(foreign_key, ondelete=ondelete))
    kwargs = {
        "primary_key": primary_key,
        "nullable": nullable,
        "index": index,
        "unique": unique,
    }
    sa_default = Undefined
    if field_info.default_factory:
        sa_default = field_info.default_factory
    elif field_info.default is not Undefined:
        sa_default = field_info.default
    if sa_default is not Undefined:
        kwargs["default"] = sa_default
    sa_column_args = getattr(field_info, "sa_column_args", Undefined)
    if sa_column_args is not Undefined:
        args.extend(list(cast(Sequence[Any], sa_column_args)))
    sa_column_kwargs = getattr(field_info, "sa_column_kwargs", Undefined)

    # <Change>
    if field_info.description:
        if sa_column_kwargs is Undefined:
            sa_column_kwargs = {}

        assert isinstance(sa_column_kwargs, dict)

        # only update comments if not already set
        if "comment" not in sa_column_kwargs:
            sa_column_kwargs["comment"] = field_info.description
    # </Change>

    if sa_column_kwargs is not Undefined:
        kwargs.update(cast(dict[Any, Any], sa_column_kwargs))
    return Column(sa_type, *args, **kwargs)  # type: ignore


sqlmodel.main.get_column_from_field = get_column_from_field
