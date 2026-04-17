from typing import Any
from warnings import deprecated

from sqlmodel import Column, Field
from typeid import TypeID, typeid_factory

from activemodel.types import typeid_patch  # noqa: F401
from activemodel.types.typeid import (
    TypeIDType,  # noqa: F401 (re-exported for sa_column usage)
)

# global list of prefixes to ensure uniqueness
# NOTE this will cause issues on code reloads
_prefixes: list[str] = []


def TypeIDPrimaryKey(prefix: str) -> Any:
    """
    Field factory for the declarative form:

        id: TypeIDField[Literal["user"]] = TypeIDPrimaryKey("user")

    Use this when you want static type-checking of the prefix.

    Returns Any so that type checkers accept it as a default value for any
    annotation (e.g. TypeIDField[Literal["user"]]), matching the same pattern
    used by pydantic's own Field() factory.

    Unfortunately, py typing is not advanced enough to automatically add a TypeIDField[Literal[prefix]]
    so you must add a specific type and input the prefix twice.
    """

    # make sure duplicate prefixes are not used!
    # NOTE this will cause issues on code reloads

    assert prefix
    assert prefix not in _prefixes, (
        f"TypeID prefix '{prefix}' already exists, pick a different one"
    )

    ret = Field(
        sa_column=Column(
            TypeIDType(prefix),
            primary_key=True,
            nullable=False,
            # default on the sa_column level ensures that an ID is generated when creating a new record, even when
            # raw SQLAlchemy operations are used instead of activemodel operations
            default=typeid_factory(prefix),
        ),
        description=f"TypeID with prefix: {prefix}",
    )

    _prefixes.append(prefix)

    return ret


@deprecated("Use TypeIDPrimaryKey(prefix) on the id field instead.")
def TypeIDMixin(prefix: str):
    """
    Mixin that adds a TypeID primary key field to a SQLModel. Specify the prefix to use for the TypeID.
    """

    class _TypeIDMixin:
        __abstract__ = True

        id: TypeID = TypeIDPrimaryKey(prefix)

    return _TypeIDMixin
