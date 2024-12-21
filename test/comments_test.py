"""
Test database comments integration
"""

from activemodel import BaseModel
from activemodel.mixins.timestamps import TimestampsMixin
from activemodel.mixins.typeid import TypeIDMixin
from activemodel.session_manager import get_session
from sqlmodel import text


class ExampleWithoutComments(
    BaseModel, TimestampsMixin, TypeIDMixin("ex2"), table=True
):
    pass


TABLE_COMMENT = "Expected table comment"


class ExampleWithComments(BaseModel, TimestampsMixin, TypeIDMixin("ex"), table=True):
    """Expected table comment"""


def test_comment(create_and_wipe_database):
    assert ExampleWithComments.__doc__
    assert not ExampleWithoutComments.__doc__

    connection = create_and_wipe_database
    with get_session() as session:
        result = session.execute(
            text("""
            SELECT obj_description('example_with_comments'::regclass, 'pg_class') AS table_comment;
        """)
        )
        table_comment = result.fetchone()[0]
        assert table_comment == "Expected table comment"

        # session.exec(
        #     text("""
        #     SELECT col_description('example_with_comments'::regclass, ordinal_position) AS column_comment
        #     FROM information_schema.columns
        #     WHERE table_name = 'example_with_comments' AND column_name = 'your_column';
        # """)
        # )
        # column_comment = cursor.fetchone()[0]
        # assert column_comment == "Expected column comment"
