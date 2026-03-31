from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Session

from activemodel import BaseModel
from activemodel.mixins import PydanticJSONMixin, TypeIDMixin
from activemodel.session_manager import global_session


class NestedPayload(PydanticBaseModel):
    external_id: str
    is_enabled: bool = False


class RecordWithPayloads(
    BaseModel,
    PydanticJSONMixin,
    TypeIDMixin("pydantic_json_record"),
    table=True,
):
    payloads: list[NestedPayload] = Field(sa_type=JSONB)


class TrackerWithObservedValues(
    BaseModel,
    TypeIDMixin("pydantic_json_tracker"),
    table=True,
):
    observed_values: list[str] = Field(sa_type=JSONB, default_factory=list)


def test_sibling_save_preserves_list_of_pydantic_models(create_and_wipe_database):
    record = RecordWithPayloads(
        payloads=[NestedPayload(external_id="payload_123", is_enabled=True)]
    ).save()
    tracker = TrackerWithObservedValues(observed_values=[]).save()

    with global_session():
        record = RecordWithPayloads.get(record.id)
        tracker = TrackerWithObservedValues.get(tracker.id)

        assert record is not None
        assert tracker is not None
        assert Session.object_session(record) is Session.object_session(tracker)
        assert isinstance(record.payloads[0], NestedPayload)

        tracker.observed_values.append("value_1")
        tracker.flag_modified("observed_values")
        tracker.save()

        assert isinstance(record.payloads[0], NestedPayload)