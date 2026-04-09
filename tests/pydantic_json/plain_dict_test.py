from sqlalchemy.orm.base import instance_state

from activemodel.jsonb_snapshot import detect_json_mutations
from activemodel.session_manager import global_session
from tests.models import ExampleRecord
from tests.pydantic_json.helpers import ExampleWithJSONB, make_example


def test_dict_setitem_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.unstructured_field["updated"] = "value"
    example.save()

    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.unstructured_field == {"k": "v", "updated": "value"}


def test_list_of_dict_item_mutation_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.generic_list_field[0]["extra"] = "item"
    example.save()

    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.generic_list_field == [{"key": "val", "extra": "item"}]


def test_list_of_dict_append_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.generic_list_field.append({"another": "entry"})
    example.save()

    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.generic_list_field == [{"key": "val"}, {"another": "entry"}]


def test_list_of_dict_assign_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.generic_list_field = [{"another": "entry"}]
    example.save()

    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.generic_list_field == [{"another": "entry"}]


def test_list_of_strings_append_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.list_of_strings_field.append("d")
    example.save()

    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.list_of_strings_field == ["a", "b", "c", "d"]


def test_list_of_bools_append_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.list_of_bools_field.append(True)
    example.save()

    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.list_of_bools_field == [True, False, True]


def test_list_of_bools_setitem_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.list_of_bools_field[1] = True
    example.save()

    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.list_of_bools_field == [True, True]


def test_list_of_floats_append_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.list_of_floats_field.append(4.5)
    example.save()

    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.list_of_floats_field == [1.5, 2.5, 3.5, 4.5]


def test_list_of_floats_setitem_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.list_of_floats_field[0] = 9.5
    example.save()

    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.list_of_floats_field == [9.5, 2.5, 3.5]


def test_list_of_strings_setitem_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.list_of_strings_field[1] = "updated"
    example.save()

    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.list_of_strings_field == ["a", "updated", "c"]


def test_list_of_ints_append_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.list_of_ints_field.append(4)
    example.save()

    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.list_of_ints_field == [1, 2, 3, 4]


def test_list_of_ints_setitem_persists(create_and_wipe_database):
    example = make_example()
    assert not instance_state(example).modified

    example.list_of_ints_field[0] = 9
    example.save()

    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.list_of_ints_field == [9, 2, 3]


def test_refresh_discards_unflushed_dict_mutation(create_and_wipe_database):
    example = make_example()

    example.unstructured_field["k"] = "updated"
    example.refresh()

    assert example.unstructured_field == {"k": "v"}
    assert not instance_state(example).modified


def test_single_field_dict_update(create_and_wipe_database):
    example = make_example()
    example.unstructured_field = {"special": "value"}
    example.save()

    assert example.unstructured_field == {"special": "value"}
    assert not instance_state(example).modified
    assert not example.has_json_mutations()

    example.unstructured_field["special"] = "new_value"

    assert example.unstructured_field == {"special": "new_value"}
    assert example.has_json_mutations()
    assert instance_state(example).modified

    example.save()

    assert example.unstructured_field == {"special": "new_value"}
    assert not instance_state(example).modified
    assert not example.has_json_mutations()

    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.unstructured_field == {"special": "new_value"}
    assert not fresh.has_json_mutations()


def test_has_json_mutations_returns_true_for_dict_field(create_and_wipe_database):
    example = make_example()
    assert not example.has_json_mutations()

    example.unstructured_field["updated"] = "value"
    assert example.has_json_mutations()


def test_has_json_mutations_returns_true_for_list_of_strings_field(
    create_and_wipe_database,
):
    example = make_example()
    assert not example.has_json_mutations()

    example.list_of_strings_field.append("d")
    assert example.has_json_mutations()


def test_has_json_mutations_returns_true_for_list_of_bools_field(
    create_and_wipe_database,
):
    example = make_example()
    assert not example.has_json_mutations()

    example.list_of_bools_field[1] = True
    assert example.has_json_mutations()


def test_detect_json_mutations_returns_dict_field_names(create_and_wipe_database):
    example = make_example()
    assert detect_json_mutations(example) == []

    example.semi_structured_field["updated"] = "value"
    assert detect_json_mutations(example) == ["semi_structured_field"]


def test_detect_json_mutations_returns_list_of_ints_field_name(
    create_and_wipe_database,
):
    example = make_example()
    assert detect_json_mutations(example) == []

    example.list_of_ints_field.append(4)
    assert detect_json_mutations(example) == ["list_of_ints_field"]


def test_detect_json_mutations_returns_list_of_floats_field_name(
    create_and_wipe_database,
):
    example = make_example()
    assert detect_json_mutations(example) == []

    example.list_of_floats_field.append(4.5)
    assert detect_json_mutations(example) == ["list_of_floats_field"]


def test_equivalent_dict_reassignment_does_not_produce_spurious_update(
    create_and_wipe_database,
):
    example = make_example()

    example.unstructured_field = {"k": "v"}
    assert instance_state(example).modified
    assert not example.has_json_mutations()

    example.save()
    assert not instance_state(example).modified
    assert not example.has_json_mutations()


def test_dict_mutation_persists_across_sibling_save(create_and_wipe_database):
    example = make_example()
    sibling_record = ExampleRecord(something="before").save()

    with global_session():
        example = ExampleWithJSONB.get(example.id)
        sibling_record = ExampleRecord.get(sibling_record.id)

        assert example is not None
        assert sibling_record is not None

        # shared-session commits must not wipe pending in-place dict mutations
        example.unstructured_field["updated"] = "value"

        sibling_record.something = "after"
        sibling_record.save()

        assert example.unstructured_field == {"k": "v", "updated": "value"}
        assert not instance_state(example).modified

    fresh = ExampleWithJSONB.one(example.id)
    assert fresh.unstructured_field == {"k": "v", "updated": "value"}
