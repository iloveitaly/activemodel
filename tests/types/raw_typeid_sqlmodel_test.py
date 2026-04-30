from uuid import UUID

import pytest
from sqlmodel import Field
from typeid import TypeID

from activemodel import BaseModel
from activemodel.types.typeid import TypeIDPrimaryKey, TypeIDType


class RawTypeIDExample(BaseModel, table=True):
    id: TypeID = TypeIDPrimaryKey("raw_typeid_example")
    originating_id: UUID | None = Field(
        default=None,
        index=True,
        sa_type=TypeIDType.raw(),
    )


def _typeid_uuid(value: TypeID) -> UUID:
    return UUID(bytes=value.uuid.bytes)


def test_raw_typeid_must_use_raw_constructor():
    with pytest.raises(AssertionError):
        TypeIDType(None)


def test_raw_typeid_accepts_multiple_prefixes(create_and_wipe_database):
    user_id = TypeID(prefix="raw_user")
    organization_id = TypeID(prefix="raw_organization")

    user_event = RawTypeIDExample()
    setattr(user_event, "originating_id", user_id)
    user_event = user_event.save()

    organization_event = RawTypeIDExample()
    setattr(organization_event, "originating_id", organization_id)
    organization_event = organization_event.save()

    assert isinstance(user_event.originating_id, UUID)
    assert user_event.originating_id == _typeid_uuid(user_id)
    assert isinstance(organization_event.originating_id, UUID)
    assert organization_event.originating_id == _typeid_uuid(organization_id)


def test_raw_typeid_queries_by_typeid_and_string(create_and_wipe_database):
    user_id = TypeID(prefix="raw_query_user")
    organization_id = TypeID(prefix="raw_query_organization")

    user_event = RawTypeIDExample()
    setattr(user_event, "originating_id", user_id)
    user_event = user_event.save()

    organization_event = RawTypeIDExample()
    setattr(organization_event, "originating_id", organization_id)
    organization_event = organization_event.save()

    fetched_user_event = RawTypeIDExample.where(
        RawTypeIDExample.originating_id == user_id
    ).one()
    fetched_organization_event = RawTypeIDExample.where(
        RawTypeIDExample.originating_id == str(organization_id)
    ).one()

    assert fetched_user_event.id == user_event.id
    assert fetched_user_event.originating_id == _typeid_uuid(user_id)
    assert fetched_organization_event.id == organization_event.id
    assert fetched_organization_event.originating_id == _typeid_uuid(organization_id)


def test_raw_typeid_allows_null_originating_id(create_and_wipe_database):
    event = RawTypeIDExample().save()

    fetched_event = RawTypeIDExample.get(event.id)

    assert fetched_event is not None
    assert fetched_event.originating_id is None


def test_raw_typeid_json_schema_uses_uuid_format():
    schema = RawTypeIDExample.model_json_schema()
    originating_id_schema = schema["properties"]["originating_id"]

    assert {"type": "string", "format": "uuid"} in originating_id_schema["anyOf"]
