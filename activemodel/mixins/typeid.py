from warnings import deprecated

from typeid import TypeID

from activemodel.types import typeid_patch  # noqa: F401
from activemodel.types.typeid import (
    TypeIDPrimaryKey,  # noqa: F401 (re-exported for backward compat)
    TypeIDType,  # noqa: F401 (re-exported for sa_column usage)
)


@deprecated("Use TypeIDPrimaryKey(prefix) on the id field instead.")
def TypeIDMixin(prefix: str):
    """
    Mixin that adds a TypeID primary key field to a SQLModel. Specify the prefix to use for the TypeID.
    """

    class _TypeIDMixin:
        __abstract__ = True

        id: TypeID = TypeIDPrimaryKey(prefix)

    return _TypeIDMixin
