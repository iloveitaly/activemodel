from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm.base import instance_state
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
    primary_payload: NestedPayload = Field(sa_type=JSONB)


class TrackerWithObservedValues(
    BaseModel,
    TypeIDMixin("pydantic_json_tracker"),
    table=True,
):
    observed_values: list[str] = Field(sa_type=JSONB, default_factory=list)


def test_sibling_save_preserves_list_of_pydantic_models(create_and_wipe_database):
    record = RecordWithPayloads(
        payloads=[NestedPayload(external_id="payload_123", is_enabled=True)],
        primary_payload=NestedPayload(external_id="primary_123", is_enabled=True),
    ).save()
    tracker = TrackerWithObservedValues(observed_values=[]).save()

    # Use one shared session so the tracker save can expire the already-loaded record.
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


def test_flag_modified_preserves_nested_json_across_sibling_save(
    create_and_wipe_database,
):
    record = RecordWithPayloads(
        payloads=[NestedPayload(external_id="payload_123", is_enabled=True)],
        primary_payload=NestedPayload(external_id="primary_123", is_enabled=True),
    ).save()
    tracker = TrackerWithObservedValues(observed_values=[]).save()

    with global_session():
        record = RecordWithPayloads.get(record.id)
        tracker = TrackerWithObservedValues.get(tracker.id)

        assert record is not None
        assert tracker is not None

        record.payloads[0].external_id = "payload_updated"

        # The sibling save commits the shared session; the before_flush handler detects the
        # in-place mutation on record and flushes it together with tracker's changes.
        # any expiration/reload path and still come back as a Pydantic object.
        tracker.observed_values.append("value_1")
        tracker.flag_modified("observed_values")
        tracker.save()

        assert isinstance(record.payloads[0], NestedPayload)
        assert record.payloads[0].external_id == "payload_updated"
        assert not instance_state(record).modified

    fresh_record = RecordWithPayloads.get(record.id)

    assert fresh_record is not None
    assert isinstance(fresh_record.payloads[0], NestedPayload)
    assert fresh_record.payloads[0].external_id == "payload_updated"


def test_sibling_save_preserves_list_and_scalar_pydantic_mutations(
    create_and_wipe_database,
):
    """
    Saving a sibling record must not wipe pending list or scalar Pydantic JSON mutations.

    This causes a session flush which expires the already-loaded record with pending mutations; the expired record must not lose those mutations and must still come back as a Pydantic object on access after the flush.
    """

    record = RecordWithPayloads(
        payloads=[
            NestedPayload(external_id="payload_123", is_enabled=True),
            NestedPayload(external_id="payload_456", is_enabled=False),
        ],
        primary_payload=NestedPayload(external_id="primary_123", is_enabled=True),
    ).save()
    tracker = TrackerWithObservedValues(observed_values=[]).save()

    with global_session():
        origin_record = RecordWithPayloads.get(record.id)
        tracker = TrackerWithObservedValues.get(tracker.id)

        assert origin_record is not None
        assert tracker is not None

        origin_record.payloads[0].external_id = "payload_updated"
        origin_record.primary_payload.external_id = "primary_updated"

        # Saving a sibling in the shared session expires origin_record and must not wipe either mutation.
        tracker.observed_values.append("value_1")
        tracker.flag_modified("observed_values")
        tracker.save()

        assert isinstance(origin_record.payloads[0], NestedPayload)
        assert isinstance(origin_record.payloads[1], NestedPayload)
        assert isinstance(origin_record.primary_payload, NestedPayload)
        assert origin_record.payloads[0].external_id == "payload_updated"
        assert origin_record.payloads[1].external_id == "payload_456"
        assert origin_record.primary_payload.external_id == "primary_updated"
        assert not instance_state(origin_record).modified

    fresh_record = RecordWithPayloads.get(record.id)

    assert fresh_record is not None
    assert isinstance(fresh_record.payloads[0], NestedPayload)
    assert isinstance(fresh_record.payloads[1], NestedPayload)
    assert isinstance(fresh_record.primary_payload, NestedPayload)
    assert fresh_record.payloads[0].external_id == "payload_updated"
    assert fresh_record.payloads[1].external_id == "payload_456"
    assert fresh_record.primary_payload.external_id == "primary_updated"


def test_sibling_save_preserves_scalar_pydantic_model(create_and_wipe_database):
    record = RecordWithPayloads(
        payloads=[NestedPayload(external_id="payload_123", is_enabled=True)],
        primary_payload=NestedPayload(external_id="primary_123", is_enabled=True),
    ).save()
    tracker = TrackerWithObservedValues(observed_values=[]).save()

    # This is the scalar-object branch of the same sibling-expiration behavior as the list test above.
    with global_session():
        record = RecordWithPayloads.get(record.id)
        tracker = TrackerWithObservedValues.get(tracker.id)

        assert record is not None
        assert tracker is not None
        assert isinstance(record.primary_payload, NestedPayload)

        tracker.observed_values.append("value_1")
        tracker.flag_modified("observed_values")
        tracker.save()

        assert isinstance(record.primary_payload, NestedPayload)
        assert record.primary_payload.external_id == "primary_123"
