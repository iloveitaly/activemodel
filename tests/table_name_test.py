from activemodel import BaseModel


class TableForTesting(BaseModel):
    id: int


# this one is especially tricky...
class LLMCache(BaseModel):
    id: int


def test_table_name():
    assert TableForTesting.__tablename__ == "table_for_testing"
    assert LLMCache.__tablename__ == "llm_cache"
