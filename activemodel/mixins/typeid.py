from sqlmodel import Column, Field
from typeid import TypeID

from activemodel.types import typeid_patch  # noqa: F401
from activemodel.types.typeid import TypeIDType

# global list of prefixes to ensure uniqueness
_prefixes: list[str] = []


def TypeIDMixin(prefix: str):
    """
    Mixin that adds a TypeID primary key field to a SQLModel. Specify the prefix to use for the TypeID.
    """

    # make sure duplicate prefixes are not used!
    # NOTE this will cause issues on code reloads
    assert prefix
    assert prefix not in _prefixes, (
        f"TypeID prefix '{prefix}' already exists, pick a different one"
    )

    class _TypeIDMixin:
        __abstract__ = True

        id: TypeIDType = Field(
            sa_column=Column(
                TypeIDType(prefix),
                primary_key=True,
                nullable=False,
                # default on the sa_column level ensures that an ID is generated when creating a new record, even when
                # raw SQLAlchemy operations are used instead of activemodel operations
                default=lambda: TypeID(prefix),
            ),
            # add a database comment to document the prefix, since it's not stored in the DB otherwise
            description=f"TypeID with prefix: {prefix}",
        )

    _prefixes.append(prefix)

    return _TypeIDMixin
