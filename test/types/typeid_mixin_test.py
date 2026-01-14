
import pytest


from activemodel.mixins import TypeIDMixin


def test_enforces_unique_prefixes():
    TypeIDMixin("hi")

    with pytest.raises(AssertionError):
        TypeIDMixin("hi")


def test_no_empty_prefixes_test():
    with pytest.raises(AssertionError):
        TypeIDMixin("")
