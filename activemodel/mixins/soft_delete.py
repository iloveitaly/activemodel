from typing import Protocol, Self

from sqlmodel import Field
from whenever import ZonedDateTime


class SoftDeleteRecord(Protocol):
    deleted_at: ZonedDateTime | None

    def save(self) -> Self: ...


class SoftDeletionMixin:
    """
    Soft delete records by setting `deleted_at` instead of removing the row.

    Call `soft_delete()` to timestamp the record and persist that change.
    """

    deleted_at: ZonedDateTime | None = Field(default=None, nullable=True)

    def soft_delete[T: SoftDeleteRecord](self: T) -> T:
        """Timestamp `deleted_at` and persist the record."""

        self.deleted_at = ZonedDateTime.now("UTC")
        # TODO we should limit the fields updated to just `deleted_at`
        return self.save()
