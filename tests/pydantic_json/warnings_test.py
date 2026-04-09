from sqlalchemy import Column, MetaData, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import configure_mappers
from sqlmodel import Field

from activemodel import BaseModel
from activemodel.mixins import PydanticJSONMixin, TypeIDMixin


def test_logs_warning_once_for_unsupported_json_fields(caplog):
    with caplog.at_level("WARNING", logger="activemodel.logger"):

        class ExampleWithUnsupportedJSON(
            BaseModel, PydanticJSONMixin, TypeIDMixin("json_warn"), table=True
        ):
            unsupported_list_field: list[tuple[str, str]] = Field(sa_type=JSONB)
            unsupported_json_field: set[str] = Field(
                sa_type=JSONB, default_factory=set
            )

        configure_mappers()

    warning_messages = [record.getMessage() for record in caplog.records]

    assert len(warning_messages) == 2
    assert any(
        "unsupported json field on ExampleWithUnsupportedJSON.unsupported_list_field"
        in message
        for message in warning_messages
    )
    assert any(
        "unsupported json field on ExampleWithUnsupportedJSON.unsupported_json_field"
        in message
        for message in warning_messages
    )


def test_logs_warning_for_field_info_without_sqlmodel_attrs(caplog):
    class DummyFieldInfo:
        annotation = set[str]

    class DummyModel(PydanticJSONMixin):
        __table__ = Table(
            "dummy_model",
            MetaData(),
            Column("unsupported_json_field", JSONB),
        )
        model_fields = {"unsupported_json_field": DummyFieldInfo()}
        _unsupported_json_fields_warned = False

    with caplog.at_level("WARNING", logger="activemodel.logger"):
        DummyModel._warn_for_unsupported_json_fields(None, DummyModel)

    warning_messages = [record.getMessage() for record in caplog.records]

    assert any(
        "unsupported json field on DummyModel.unsupported_json_field" in message
        for message in warning_messages
    )