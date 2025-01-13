from activemodel import BaseModel
from activemodel.mixins import TypeIDMixin
from activemodel.types.typeid import TypeIDType
from sqlmodel import Relationship

TYPEID_PREFIX = "myid"


class AnotherExample(BaseModel, TypeIDMixin("myotherid"), table=True):
    pass


class ExampleWithId(BaseModel, TypeIDMixin(TYPEID_PREFIX), table=True):
    another_example_id: TypeIDType = AnotherExample.foreign_key(nullable=True)
    another_example: AnotherExample = Relationship()
