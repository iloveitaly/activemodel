from whenever import Instant, ZonedDateTime

from activemodel import BaseModel
from activemodel.mixins.typeid import TypeIDMixin


class WheneverModel(BaseModel, TypeIDMixin("whenever_model"), table=True):
    triggered_at: Instant | None = None
    scheduled_at: ZonedDateTime | None = None