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