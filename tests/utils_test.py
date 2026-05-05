import pytest
from activemodel.utils import is_database_empty, to_snake_case
from tests.models import ExampleRecord


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("TableForTesting", "table_for_testing"),
        ("LLMCache", "llm_cache"),
        ("XMLHTTPRequest", "xmlhttp_request"),
        ("HTTPResponseCode", "http_response_code"),
        ("camelCase", "camel_case"),
        ("snake_case", "snake_case"),
        ("UserJSONData", "user_json_data"),
        ("Simple123", "simple123"),
        ("S123Simple", "s123_simple"),
        ("V1Model", "v1_model"),
        ("ModelV1", "model_v1"),
        ("MyAPI", "my_api"),
        ("APIResponse", "api_response"),
        ("JSON", "json"),
        ("a", "a"),
        ("A", "a"),
        ("Already_Snake", "already_snake"),
    ],
)
def test_to_snake_case(input_str, expected):
    assert to_snake_case(input_str) == expected


def test_is_database_empty(create_and_wipe_database):
    # check that the database is initially empty
    assert is_database_empty() is True

    # add a record to one of the tables
    record = ExampleRecord(something="test")
    record.save()

    # check that the database is no longer empty
    assert is_database_empty() is False

    # check that excluding the table returns True
    assert is_database_empty(exclude=[ExampleRecord]) is True
