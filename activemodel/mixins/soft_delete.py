from datetime import UTC, datetime
from typing import Protocol, Self

import sqlalchemy as sa
from sqlmodel import Field


class SoftDeleteRecord(Protocol):
    deleted_at: datetime | None

    def save(self) -> Self: ...


class SoftDeletionMixin:
    """
    Soft delete records by setting `deleted_at` instead of removing the row.

    Call `soft_delete()` to timestamp the record and persist that change.
    """

    deleted_at: datetime | None = Field(
        default=None,
        nullable=True,
        # TODO https://github.com/fastapi/sqlmodel/discussions/1228
        sa_type=sa.DateTime(timezone=True),  # type: ignore
    )

    def soft_delete[T: SoftDeleteRecord](self: T) -> T:
        """Timestamp `deleted_at` and persist the record."""

        self.deleted_at = datetime.now(UTC)
        # TODO we should limit the fields updated to just `deleted_at`
        return self.save()
