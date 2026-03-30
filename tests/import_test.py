import activemodel


def test_import() -> None:
    assert isinstance(activemodel.__name__, str)
