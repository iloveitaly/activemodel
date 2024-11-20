from activemodel import BaseModel


class TestTable(BaseModel):
    id: int


class TestLLMCache(BaseModel):
    id: int


def test_table_name():
    assert TestTable.__tablename__ == "test_table"
    assert TestLLMCache.__tablename__ == "test_llm_cache"
