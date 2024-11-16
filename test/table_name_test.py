from activemodel import BaseModel


class TestTable(BaseModel):
    id: int


def test_table_name():
    assert TestTable.__tablename__ == "test_table"
