from typeid import TypeID
from activemodel.pytest.factories import ActiveModelFactory
from test.models import AnotherExample, ExampleRecord, ExampleWithId


class ExampleRecordFactory(ActiveModelFactory[ExampleRecord]):
    __model__ = ExampleRecord


class AnotherExampleFactory(ActiveModelFactory[AnotherExample]):
    __model__ = AnotherExample


class ExampleWithIdFactory(ActiveModelFactory[ExampleWithId]):
    __model__ = ExampleWithId


def test_factory_save_helper_sets_session_and_persists(create_and_wipe_database):
    """ActiveModelFactory.save should persist model using a global session automatically."""
    rec = ExampleRecordFactory.save(something="abc")
    assert rec.id is not None

    # ensure it was actually committed / visible
    fetched = ExampleRecord.get(rec.id)

    assert fetched is not None
    assert fetched.id == rec.id
    assert fetched.something == "abc"


def test_factory_foreign_key_typeid(create_and_wipe_database):
    """foreign_key_typeid should return a TypeID with the model's prefix (TypeIDMixin)."""
    # ExampleRecord uses TypeIDMixin with prefix EXAMPLE_TABLE_PREFIX (import indirectly)
    fk_value = ExampleRecordFactory.foreign_key_typeid()

    # TypeID string format: <prefix>_<random>
    assert isinstance(fk_value, TypeID)
    assert fk_value.prefix == "test_record"


def test_factory_creates_related_models_via_manual_assignment(create_and_wipe_database):
    """Ensure we can manually wire foreign keys using generated typeids to simulate relationships."""
    # create base objects first
    parent = AnotherExampleFactory.save(note="parent")
    child = ExampleRecordFactory.save(something="child")

    rel = ExampleWithIdFactory.save(
        another_example_id=parent.id,
        example_record_id=child.id,
    )

    assert rel.id is not None
    # fetch and ensure relationships can be traversed
    fetched = ExampleWithId.get(rel.id)
    assert fetched is not None
    assert fetched.another_example_id == parent.id
    assert fetched.example_record_id == child.id
