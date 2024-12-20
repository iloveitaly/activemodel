from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Field


class SoftDeletionMixin:
    deleted_at: datetime = Field(
        default=None,
        nullable=True,
        # TODO https://github.com/fastapi/sqlmodel/discussions/1228
        sa_type=sa.DateTime(timezone=True),  # type: ignore
    )

    def soft_delete(self):
        self.deleted_at = datetime.now()
        raise NotImplementedError("Soft deletion is not implemented")
