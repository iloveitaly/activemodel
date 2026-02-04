"""Test activemodel."""

import activemodel


def test_import() -> None:
    """Test that the  can be imported."""
    assert isinstance(activemodel.__name__, str)