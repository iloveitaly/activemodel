from contextlib import contextmanager

from sqlalchemy import Column, MetaData, Table
from sqlalchemy.dialects.postgresql import JSONB

from activemodel.logger import logger
from activemodel.mixins import PydanticJSONMixin
from tests.pydantic_json.helpers import ExampleWithUnsupportedJSON


@contextmanager
def capture_activemodel_warnings(caplog):
    previous_disabled = logger.disabled

    logger.disabled = False

    try:
        with caplog.at_level("WARNING", logger=logger.name):
            yield
    finally:
        logger.disabled = previous_disabled


def test_logs_warning_once_for_unsupported_json_fields(caplog):
    previous_warned = getattr(
        ExampleWithUnsupportedJSON, "_unsupported_json_fields_warned", False
    )

    try:
        with capture_activemodel_warnings(caplog):
            ExampleWithUnsupportedJSON._unsupported_json_fields_warned = False

            ExampleWithUnsupportedJSON._warn_for_unsupported_json_fields(
                None, ExampleWithUnsupportedJSON
            )
            ExampleWithUnsupportedJSON._warn_for_unsupported_json_fields(
                None, ExampleWithUnsupportedJSON
            )
    finally:
        ExampleWithUnsupportedJSON._unsupported_json_fields_warned = previous_warned

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
    class MinimalFieldInfo:
        annotation = set[str]

    class DummyModel(PydanticJSONMixin):
        __table__ = Table(
            "dummy_model",
            MetaData(),
            Column("unsupported_json_field", JSONB),
        )
        model_fields = {"unsupported_json_field": MinimalFieldInfo()}
        _unsupported_json_fields_warned = False

    with capture_activemodel_warnings(caplog):
        DummyModel._warn_for_unsupported_json_fields(None, DummyModel)

    warning_messages = [record.getMessage() for record in caplog.records]

    assert any(
        "unsupported json field on DummyModel.unsupported_json_field" in message
        for message in warning_messages
    )
