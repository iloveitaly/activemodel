"""
Test database comments integration
"""

from datetime import datetime

from sqlalchemy import Column, String
from sqlmodel import Field, text

from activemodel import BaseModel
from activemodel.mixins.timestamps import TimestampsMixin
from activemodel.mixins.typeid import TypeIDMixin
from activemodel.session_manager import get_session


class ExampleWithoutComments(
    BaseModel, TimestampsMixin, TypeIDMixin("ex_wo_comments"), table=True
):
    pass


class ExampleWithComments(
    BaseModel, TimestampsMixin, TypeIDMixin("ex_comments"), table=True
):
    # f-strings don't work with docstrings
    """Expected table comment"""

    a_string_field_without_field: str
    "a doc string for a string field without a field"

    a_string_field_with_field: str = Field()
    "a doc string for a string field with a field"

    field_with_sa_column: str = Field(sa_column=Column(String()))
    "a doc string for a string field with a field and a sa_column"

    field_with_sa_column_args: str = Field(
        sa_column_kwargs={"onupdate": datetime.now()}
    )
    "a doc string for a string field with a field and a sa_column_kwargs"

    field_with_empty_sa_column_args: str = Field(sa_column_kwargs={})
    "a doc string for a string field with a field and an empty sa_column_kwargs"


def test_table_comments(create_and_wipe_database):
    assert ExampleWithComments.__doc__
    assert not ExampleWithoutComments.__doc__

    with get_session() as session:
        result = session.execute(
            text("""
            SELECT obj_description('example_with_comments'::regclass, 'pg_class') AS table_comment;
        """)
        )

        table_comment = result.fetchone()[0]
        assert table_comment == "Expected table comment"


def get_column_comment(table_name, column_name):
    with get_session() as session:
        result = session.execute(
            text(
                f"""
            SELECT col_description(({table_name!r}::regclass)::oid, ordinal_position) AS column_comment
            FROM information_schema.columns
            WHERE table_name = {table_name!r} AND column_name = {column_name!r};
            """
            )
        )
        return result.fetchone()[0]


def test_column_comments(create_and_wipe_database):
    fields_to_check = [
        "a_string_field_without_field",
        "a_string_field_with_field",
        "field_with_sa_column",
        "field_with_sa_column_args",
        "field_with_empty_sa_column_args",
    ]

    fields = ExampleWithComments.model_fields

    # is the string added to the description of the field?
    assert (
        fields["a_string_field_without_field"].description
        == "a doc string for a string field without a field"
    )

    assert (
        fields["field_with_sa_column"].description
        == "a doc string for a string field with a field and a sa_column"
    )

    assert (
        fields["field_with_sa_column_args"].description
        == "a doc string for a string field with a field and a sa_column_kwargs"
    )

    assert (
        fields["field_with_empty_sa_column_args"].description
        == "a doc string for a string field with a field and an empty sa_column_kwargs"
    )

    for field_name in fields_to_check:
        assert fields[field_name].description
        assert fields[field_name].description == get_column_comment(
            ExampleWithComments.__tablename__, field_name
        )
