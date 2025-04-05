from test.models import TYPEID_PREFIX, ExampleWithId


def test_json_schema(create_and_wipe_database):
    "json schema generation shouldn't be meaningfully different than json rendering, but let's check it anyway"

    example = ExampleWithId().save()
    example.model_json_schema()
