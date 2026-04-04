import weakref
from typing import SupportsIndex
from sqlalchemy.orm.attributes import flag_modified as sa_flag_modified


def _notify_parent(parent_ref: weakref.ref | None, field_name: str | None) -> None:
    if parent_ref is None or field_name is None:
        return
    parent = parent_ref()
    if parent is not None:
        # Tell SQLAlchemy the JSONB column is dirty so it flushes the mutation on next commit.
        sa_flag_modified(parent, field_name)


class TrackedList(list):
    """A list subclass that calls flag_modified on the parent ORM instance when mutated."""

    def __init__(self, items=(), *, parent=None, field_name: str | None = None):
        super().__init__(items)
        # Weak ref avoids a parent → list → parent reference cycle.
        self._sa_tracking_parent_ref: weakref.ref | None = (
            weakref.ref(parent) if parent is not None else None
        )
        self._sa_tracking_field_name = field_name

    def _notify(self) -> None:
        _notify_parent(self._sa_tracking_parent_ref, self._sa_tracking_field_name)

    # Every mutation method calls _notify so SQLAlchemy sees the JSONB field as dirty.

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._notify()

    def __delitem__(self, key):
        super().__delitem__(key)
        self._notify()

    def append(self, value):
        super().append(value)
        self._notify()

    def extend(self, values):
        super().extend(values)
        self._notify()

    def insert(self, index: SupportsIndex, value):
        super().insert(index, value)
        self._notify()

    def pop(self, index: SupportsIndex = -1):
        value = super().pop(index)
        self._notify()
        return value

    def remove(self, value):
        super().remove(value)
        self._notify()

    def clear(self):
        super().clear()
        self._notify()

    def sort(self, *args, **kwargs):
        super().sort(*args, **kwargs)
        self._notify()

    def reverse(self):
        super().reverse()
        self._notify()

    def __iadd__(self, values):
        result = super().__iadd__(values)
        self._notify()
        return result
