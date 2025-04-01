from sqlmodel import Column, Field
from typeid import TypeID

from activemodel.types.typeid import TypeIDType

# global list of prefixes to ensure uniqueness
_prefixes: list[str] = []


def TypeIDMixin(prefix: str):
    # make sure duplicate prefixes are not used!
    # NOTE this will cause issues on code reloads
    assert prefix
    assert prefix not in _prefixes, (
        f"prefix {prefix} already exists, pick a different one"
    )

    class _TypeIDMixin:
        __abstract__ = True

        id: TypeIDType = Field(
            sa_column=Column(
                TypeIDType(prefix),
                primary_key=True,
                nullable=False,
                default=lambda: TypeID(prefix),
            ),
            # default_factory=lambda: TypeID(prefix),
        )

    _prefixes.append(prefix)

    return _TypeIDMixin
