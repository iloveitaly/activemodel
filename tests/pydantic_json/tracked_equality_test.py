"""
Tests for equality behavior of tracked Pydantic model subclasses.

The __class__ swap used for auto-tracking creates a dynamic subclass (TrackedSubObject)
of the original Pydantic model (SubObject). Pydantic's __eq__ checks type identity via
__pydantic_generic_metadata__['origin'], which we set to the original class so that
tracked instances compare equal to untracked ones.

These tests are intentionally paranoid because:
- Pydantic's __eq__ has a fast path (__dict__) and a slow path (itemgetter on fields)
- Our tracking attrs (_sa_tracking_*) live in __dict__ and must not break either path
- Upstream Pydantic changes to __eq__ could silently break equality
"""

from pydantic import BaseModel as PydanticBaseModel

from activemodel.json.tracked_pydantic import (
    _get_tracked_subclass,
    _attach_pydantic_tracking,
)


class _FakeParent:
    """Minimal weakly-referenceable object standing in for an ORM parent in tests."""

    pass


class Simple(PydanticBaseModel):
    """Baseline model: two required fields, no extras. Used in the majority of equality tests."""

    name: str
    value: int


class WithDefaults(PydanticBaseModel):
    """Exercises Pydantic's fast-path __eq__ when __dict__ keys differ due to defaulted fields."""

    name: str
    count: int = 0
    tag: str | None = None


class WithExtra(PydanticBaseModel):
    """Extra fields land in __pydantic_extra__, a separate dict — tracked attrs must not collide."""

    model_config = {"extra": "allow"}
    name: str


class WithPrivate(PydanticBaseModel):
    """Private attrs live in __private_attributes__, outside __dict__, so should be unaffected."""

    name: str
    _secret: str = "hidden"


class Nested(PydanticBaseModel):
    """Confirms that nested Pydantic models inside a tracked parent still compare by value."""

    child: Simple


# ---------------------------------------------------------------------------
# Basic equality: tracked == untracked
# ---------------------------------------------------------------------------


def test_tracked_equals_untracked_same_fields():
    tracked = Simple(name="a", value=1)
    _swap_to_tracked(tracked)

    assert tracked == Simple(name="a", value=1)
    assert Simple(name="a", value=1) == tracked


def test_tracked_not_equal_untracked_different_fields():
    tracked = Simple(name="a", value=1)
    _swap_to_tracked(tracked)

    assert tracked != Simple(name="a", value=2)
    assert tracked != Simple(name="b", value=1)


def test_two_tracked_instances_equal():
    a = Simple(name="x", value=5)
    b = Simple(name="x", value=5)
    _swap_to_tracked(a)
    _swap_to_tracked(b)

    assert a == b


def test_two_tracked_instances_not_equal():
    a = Simple(name="x", value=5)
    b = Simple(name="x", value=6)
    _swap_to_tracked(a)
    _swap_to_tracked(b)

    assert a != b


# ---------------------------------------------------------------------------
# Symmetry: a == b implies b == a
# ---------------------------------------------------------------------------


def test_equality_is_symmetric():
    tracked = Simple(name="s", value=0)
    _swap_to_tracked(tracked)
    plain = Simple(name="s", value=0)

    assert (tracked == plain) == (plain == tracked)


def test_inequality_is_symmetric():
    tracked = Simple(name="s", value=0)
    _swap_to_tracked(tracked)
    plain = Simple(name="s", value=999)

    assert (tracked != plain) == (plain != tracked)


# ---------------------------------------------------------------------------
# Default field values
# ---------------------------------------------------------------------------


def test_tracked_equals_untracked_with_defaults_explicit():
    tracked = WithDefaults(name="d", count=0, tag=None)
    _swap_to_tracked(tracked)

    assert tracked == WithDefaults(name="d")


def test_tracked_equals_untracked_with_defaults_overridden():
    tracked = WithDefaults(name="d", count=5, tag="yes")
    _swap_to_tracked(tracked)

    assert tracked == WithDefaults(name="d", count=5, tag="yes")
    assert tracked != WithDefaults(name="d", count=5, tag="no")


# ---------------------------------------------------------------------------
# Extra fields (model_config = {"extra": "allow"})
# ---------------------------------------------------------------------------


def test_tracked_equals_untracked_with_extra_fields():
    # model_validate used because pyright doesn't type-check extra fields on dicts
    tracked = WithExtra.model_validate({"name": "e", "bonus": "data"})
    _swap_to_tracked(tracked)

    assert tracked == WithExtra.model_validate({"name": "e", "bonus": "data"})


def test_tracked_not_equal_when_extra_fields_differ():
    tracked = WithExtra.model_validate({"name": "e", "bonus": "data"})
    _swap_to_tracked(tracked)

    assert tracked != WithExtra.model_validate({"name": "e", "bonus": "other"})
    assert tracked != WithExtra(name="e")


# ---------------------------------------------------------------------------
# Private fields
# ---------------------------------------------------------------------------


def test_tracked_equals_untracked_with_private_fields():
    tracked = WithPrivate(name="p")
    _swap_to_tracked(tracked)

    assert tracked == WithPrivate(name="p")


# ---------------------------------------------------------------------------
# Nested Pydantic models
# ---------------------------------------------------------------------------


def test_tracked_equals_untracked_with_nested_model():
    tracked = Nested(child=Simple(name="n", value=1))
    _swap_to_tracked(tracked)

    assert tracked == Nested(child=Simple(name="n", value=1))


def test_tracked_not_equal_when_nested_differs():
    tracked = Nested(child=Simple(name="n", value=1))
    _swap_to_tracked(tracked)

    assert tracked != Nested(child=Simple(name="n", value=2))


# ---------------------------------------------------------------------------
# Cross-type: different model classes should never be equal
# ---------------------------------------------------------------------------


def test_tracked_not_equal_to_different_model_class():
    """Two different model classes with identical field names/values must not compare equal."""

    class AlsoSimple(PydanticBaseModel):
        name: str
        value: int

    tracked = Simple(name="a", value=1)
    _swap_to_tracked(tracked)

    other = AlsoSimple(name="a", value=1)

    assert tracked != other


# ---------------------------------------------------------------------------
# Pydantic's __eq__ fast path vs slow path
#
# Pydantic first compares __dict__ directly (fast path). If that fails AND
# __dict__ contains keys beyond __pydantic_fields__, it filters to field-only
# keys (slow path). Our _sa_tracking_* attrs trigger the slow path.
# ---------------------------------------------------------------------------


def test_fast_path_skipped_due_to_tracking_attrs():
    """Two tracked instances with same fields but different parents must still be equal.

    The fast __dict__ comparison fails because _sa_tracking_parent_ref differs,
    but the slow path filters to pydantic fields only and should return True.
    """
    a = Simple(name="q", value=9)
    b = Simple(name="q", value=9)
    _swap_to_tracked(a)
    _swap_to_tracked(b)

    # Simulate different parent refs (different weakref objects).
    parent_a = _FakeParent()
    parent_b = _FakeParent()
    _attach_pydantic_tracking(a, parent_a, "field_a")
    _attach_pydantic_tracking(b, parent_b, "field_b")

    # __dict__ differs (different weakrefs and field names), but fields are the same.
    assert a.__dict__ != b.__dict__
    assert a == b


def test_fast_path_works_for_unattached_tracked_instances():
    """Without tracking attrs set, __dict__ contains only model fields —
    the fast path should succeed."""
    tracked_cls = _get_tracked_subclass(Simple)
    a = tracked_cls(name="f", value=0)
    b = tracked_cls(name="f", value=0)

    assert a == b


# ---------------------------------------------------------------------------
# list.remove / list.index / `in` operator
# These rely on __eq__ working correctly between tracked and untracked.
# ---------------------------------------------------------------------------


def test_list_remove_finds_tracked_by_untracked_value():
    items = [Simple(name="a", value=1), Simple(name="b", value=2)]
    for item in items:
        _swap_to_tracked(item)

    items.remove(Simple(name="a", value=1))
    assert len(items) == 1
    assert items[0].name == "b"


def test_list_index_finds_tracked_by_untracked_value():
    items = [Simple(name="a", value=1), Simple(name="b", value=2)]
    for item in items:
        _swap_to_tracked(item)

    assert items.index(Simple(name="b", value=2)) == 1


def test_in_operator_finds_tracked_by_untracked_value():
    items = [Simple(name="a", value=1)]
    _swap_to_tracked(items[0])

    assert Simple(name="a", value=1) in items
    assert Simple(name="z", value=99) not in items


# ---------------------------------------------------------------------------
# model_dump / model_dump_json / serialization
# ---------------------------------------------------------------------------


def test_model_dump_excludes_tracking_attrs():
    tracked = Simple(name="s", value=7)
    _swap_to_tracked(tracked)
    _attach_pydantic_tracking(tracked, _FakeParent(), "field")

    dumped = tracked.model_dump()
    assert dumped == {"name": "s", "value": 7}
    assert "_sa_tracking_parent_ref" not in dumped
    assert "_sa_tracking_field_name" not in dumped


def test_model_dump_json_excludes_tracking_attrs():
    tracked = Simple(name="s", value=7)
    _swap_to_tracked(tracked)
    _attach_pydantic_tracking(tracked, _FakeParent(), "field")

    json_str = tracked.model_dump_json()
    assert "_sa_tracking" not in json_str
    assert '"name":"s"' in json_str


# ---------------------------------------------------------------------------
# isinstance checks
# ---------------------------------------------------------------------------


def test_isinstance_original_class():
    tracked = Simple(name="i", value=0)
    _swap_to_tracked(tracked)

    assert isinstance(tracked, Simple)
    assert isinstance(tracked, PydanticBaseModel)


def test_type_is_tracked_subclass_not_original():
    tracked = Simple(name="t", value=0)
    _swap_to_tracked(tracked)

    assert type(tracked) is not Simple
    assert type(tracked).__name__ == "TrackedSimple"


# ---------------------------------------------------------------------------
# __pydantic_generic_metadata__['origin'] is set correctly
# ---------------------------------------------------------------------------


def test_origin_points_to_original_class():
    tracked_cls = _get_tracked_subclass(Simple)
    assert tracked_cls.__pydantic_generic_metadata__["origin"] is Simple


def test_origin_not_set_on_original_class():
    """The original class should not be mutated by tracked subclass creation."""
    _get_tracked_subclass(Simple)
    assert Simple.__pydantic_generic_metadata__["origin"] is None


# ---------------------------------------------------------------------------
# hash behavior: Pydantic models are unhashable by default
# ---------------------------------------------------------------------------


def test_tracked_is_unhashable_like_original():
    """Pydantic models define __eq__ without __hash__, making them unhashable.
    Tracked subclasses should preserve this behavior."""
    tracked = Simple(name="h", value=0)
    _swap_to_tracked(tracked)

    try:
        hash(tracked)
        hashable = True
    except TypeError:
        hashable = False

    try:
        hash(Simple(name="h", value=0))
        original_hashable = True
    except TypeError:
        original_hashable = False

    assert hashable == original_hashable


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _swap_to_tracked(instance: PydanticBaseModel) -> None:
    """Swap __class__ to the tracked subclass without attaching a parent."""
    tracked_cls = _get_tracked_subclass(type(instance))
    instance.__class__ = tracked_cls
