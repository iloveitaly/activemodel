from activemodel import BaseModel, property_field


class ComputedModel(BaseModel):
    first: str
    last: str

    @property_field
    def full_name(self) -> str:
        return f"{self.first} {self.last}"

    @property_field(alias="display")
    def display_name(self) -> str:
        return f"{self.first} {self.last[0]}."


def test_property_field_attribute_access():
    # decorated method is accessible as an attribute, not a callable
    m = ComputedModel(first="Jane", last="Doe")
    assert m.full_name == "Jane Doe"


def test_property_field_included_in_model_dump():
    # field appears in serialization output
    m = ComputedModel(first="Jane", last="Doe")
    data = m.model_dump()
    assert data["full_name"] == "Jane Doe"


def test_property_field_with_kwargs():
    # kwargs are forwarded to computed_field (e.g. alias)
    m = ComputedModel(first="Jane", last="Doe")
    assert m.display_name == "Jane D."
    assert m.model_dump(by_alias=True)["display"] == "Jane D."
