from typeid import TypeID
from activemodel.pytest.factories import ActiveModelFactory
from test.models import (
    AnotherExample,
    ExampleRecord,
    ExampleRelatedModel,
    ExampleWithId,
)


class ExampleRecordFactory(ActiveModelFactory[ExampleRecord]):
    __model__ = ExampleRecord


class AnotherExampleFactory(ActiveModelFactory[AnotherExample]):
    __model__ = AnotherExample


class ExampleWithIdFactory(ActiveModelFactory[ExampleWithId]):
    __model__ = ExampleWithId


class ExampleRecordWithPostSaveFactory(ActiveModelFactory[ExampleRecord]):
    """Factory that uses post_save to modify the model after saving."""

    __model__ = ExampleRecord

    @classmethod
    def post_save(cls, model: ExampleRecord) -> ExampleRecord:
        # Modify the model after it's been saved
        model.something = f"post_save:{model.something}"
        model.save()
        return model


class ExampleWithTrackingFactory(ActiveModelFactory[ExampleRecord]):
    """Factory that tracks post_save calls for testing."""

    __model__ = ExampleRecord
    post_save_called = False
    post_save_model_id = None

    @classmethod
    def post_save(cls, model: ExampleRecord) -> ExampleRecord:
        cls.post_save_called = True
        cls.post_save_model_id = model.id
        return model

    @classmethod
    def reset_tracking(cls):
        cls.post_save_called = False
        cls.post_save_model_id = None


class ExampleRelatedModelFactory(ActiveModelFactory[ExampleRelatedModel]):
    __model__ = ExampleRelatedModel


class CreateRelatedModelOnPostSaveExampleRecordFactory(
    ActiveModelFactory[ExampleRecord]
):
    """
    Creates a related ExampleRelatedModel in the post_save hook after saving the ExampleRecord.
    to test that related models can be created after the main model is saved.
    """

    __model__ = ExampleRecord

    @classmethod
    def post_save(cls, model: ExampleRecord) -> ExampleRecord:
        # Create a related ExampleRelatedModel in the post_save hook
        ExampleRelatedModelFactory.save(example_record_id=model.id)
        return model


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


def test_post_save_hook_is_called(create_and_wipe_database):
    """post_save hook should be called after the model is saved."""
    ExampleWithTrackingFactory.reset_tracking()

    rec = ExampleWithTrackingFactory.save(something="test")

    assert ExampleWithTrackingFactory.post_save_called is True
    assert ExampleWithTrackingFactory.post_save_model_id == rec.id


def test_post_save_hook_can_modify_model(create_and_wipe_database):
    """post_save hook should be able to modify and re-save the model."""
    rec = ExampleRecordWithPostSaveFactory.save(something="original")

    assert rec.something == "post_save:original"

    # Verify the modification was persisted
    fetched = ExampleRecord.get(rec.id)
    assert fetched is not None
    assert fetched.something == "post_save:original"


def test_post_save_receives_persisted_model(create_and_wipe_database):
    """post_save should receive a model that has already been persisted (has an id)."""
    ExampleWithTrackingFactory.reset_tracking()

    rec = ExampleWithTrackingFactory.save(something="check_id")

    # The model should have had an id when post_save was called
    assert ExampleWithTrackingFactory.post_save_model_id is not None
    assert rec.id == ExampleWithTrackingFactory.post_save_model_id


def test_post_save_default_returns_model_unchanged(create_and_wipe_database):
    """Default post_save implementation should return the model unchanged."""
    rec = ExampleRecordFactory.save(something="unchanged")

    assert rec.something == "unchanged"
    fetched = ExampleRecord.get(rec.id)
    assert fetched.something == "unchanged"


def test_post_save_can_create_related_models(create_and_wipe_database):
    """post_save should be able to create related models that reference the main model."""
    rec = CreateRelatedModelOnPostSaveExampleRecordFactory.save(something="main")

    # Fetch related model to ensure it was created and linked properly
    related = ExampleRelatedModel.get(ExampleRelatedModel.example_record_id == rec.id)
    assert related is not None
    assert related.example_record_id == rec.id
