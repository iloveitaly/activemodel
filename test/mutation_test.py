import pytest
from sqlalchemy.orm.base import instance_state
from test.models import ExampleRecord


def assert_modified(model):
    assert instance_state(model).modified


def assert_clean(model):
    assert not instance_state(model).modified


def test_flag_modified(create_and_wipe_database):
    example = ExampleRecord().save()
    assert_clean(example)

    example.flag_modified("something")
    assert example.modified_fields() == {"something"}


def test_modified_list(create_and_wipe_database):
    example = ExampleRecord().save()
    assert_clean(example)

    example.something = "hi"
    assert example.modified_fields() == {"something"}


def test_error_on_bad_field(create_and_wipe_database):
    example = ExampleRecord().save()
    assert_clean(example)

    with pytest.raises(ValueError, match="bad_field"):
        example.flag_modified("bad_field")
