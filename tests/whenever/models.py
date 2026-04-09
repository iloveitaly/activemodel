from pydantic import BaseModel as PydanticBaseModel
from whenever import Instant, PlainDateTime, ZonedDateTime

from activemodel import BaseModel
from activemodel.mixins.typeid import TypeIDMixin


class WheneverModel(BaseModel, TypeIDMixin("whenever_model"), table=True):
    plain_datetime: PlainDateTime | None = None
    triggered_at: Instant | None = None
    scheduled_at: ZonedDateTime | None = None


class WheneverSchema(PydanticBaseModel):
    instant: Instant
    plain_datetime: PlainDateTime
    zoned_datetime: ZonedDateTime