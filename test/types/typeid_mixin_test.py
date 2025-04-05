import json

import pytest
from pydantic import BaseModel as PydanticBaseModel
from typeid import TypeID

from test.models import TYPEID_PREFIX, ExampleWithId
from test.utils import temporary_tables

from activemodel.mixins import TypeIDMixin


def test_enforces_unique_prefixes():
    TypeIDMixin("hi")

    with pytest.raises(AssertionError):
        TypeIDMixin("hi")


def test_no_empty_prefixes_test():
    with pytest.raises(AssertionError):
        TypeIDMixin("")
