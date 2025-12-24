"""
Tests for SQLAlchemy automap with snake_case naming conventions.

These tests verify that the automap naming functions correctly convert
PascalCase class names to snake_case relationship names.
"""

import pytest
from unittest.mock import Mock
from activemodel.automap import (
    name_for_scalar_relationship_snake,
    name_for_collection_relationship_snake,
    name_for_collection_relationship_snake_with_inflect,
    _simple_pluralize,
)


class TestSimplePluralize:
    """Tests for the simple pluralization function."""

    def test_regular_plurals(self):
        """Test regular plural forms."""
        assert _simple_pluralize("cat") == "cats"
        assert _simple_pluralize("dog") == "dogs"
        assert _simple_pluralize("status") == "statuses"
        assert _simple_pluralize("process") == "processes"

    def test_words_ending_in_y(self):
        """Test words ending in 'y' preceded by consonant."""
        assert _simple_pluralize("category") == "categories"
        assert _simple_pluralize("company") == "companies"
        assert _simple_pluralize("entry") == "entries"

    def test_words_ending_in_y_with_vowel(self):
        """Test words ending in 'y' preceded by vowel (just add 's')."""
        assert _simple_pluralize("day") == "days"
        assert _simple_pluralize("key") == "keys"

    def test_words_ending_in_sibilants(self):
        """Test words ending in s, x, z, ch, sh."""
        assert _simple_pluralize("box") == "boxes"
        assert _simple_pluralize("buzz") == "buzzes"
        assert _simple_pluralize("church") == "churches"
        assert _simple_pluralize("dish") == "dishes"

    def test_words_ending_in_f_or_fe(self):
        """Test words ending in 'f' or 'fe'."""
        assert _simple_pluralize("leaf") == "leaves"
        assert _simple_pluralize("knife") == "knives"
        assert _simple_pluralize("life") == "lives"

    def test_irregular_plurals(self):
        """Test irregular plural forms."""
        assert _simple_pluralize("person") == "people"
        assert _simple_pluralize("child") == "children"
        assert _simple_pluralize("man") == "men"
        assert _simple_pluralize("woman") == "women"
        assert _simple_pluralize("tooth") == "teeth"
        assert _simple_pluralize("foot") == "feet"
        assert _simple_pluralize("mouse") == "mice"
        assert _simple_pluralize("goose") == "geese"


class TestScalarRelationshipNaming:
    """Tests for scalar (many-to-one, one-to-one) relationship naming."""

    def test_simple_class_name(self):
        """Test conversion of simple PascalCase class names."""
        referred_cls = Mock()
        referred_cls.__name__ = "User"

        result = name_for_scalar_relationship_snake(
            base=Mock(), local_cls=Mock(), referred_cls=referred_cls, constraint=Mock()
        )
        assert result == "user"

    def test_two_word_class_name(self):
        """Test conversion of two-word PascalCase class names."""
        referred_cls = Mock()
        referred_cls.__name__ = "ProcessStatus"

        result = name_for_scalar_relationship_snake(
            base=Mock(), local_cls=Mock(), referred_cls=referred_cls, constraint=Mock()
        )
        assert result == "process_status"

    def test_three_word_class_name(self):
        """Test conversion of three-word PascalCase class names."""
        referred_cls = Mock()
        referred_cls.__name__ = "UserAccountStatus"

        result = name_for_scalar_relationship_snake(
            base=Mock(), local_cls=Mock(), referred_cls=referred_cls, constraint=Mock()
        )
        assert result == "user_account_status"

    def test_acronym_in_class_name(self):
        """Test conversion with acronyms."""
        referred_cls = Mock()
        referred_cls.__name__ = "HTTPResponse"

        result = name_for_scalar_relationship_snake(
            base=Mock(), local_cls=Mock(), referred_cls=referred_cls, constraint=Mock()
        )
        # textcase should handle this correctly
        assert result == "http_response"

    def test_class_name_with_numbers(self):
        """Test conversion with numbers in class name."""
        referred_cls = Mock()
        referred_cls.__name__ = "OAuth2Client"

        result = name_for_scalar_relationship_snake(
            base=Mock(), local_cls=Mock(), referred_cls=referred_cls, constraint=Mock()
        )
        # textcase should handle this
        assert "oauth" in result.lower()


class TestCollectionRelationshipNaming:
    """Tests for collection (one-to-many) relationship naming."""

    def test_simple_class_name(self):
        """Test pluralization of simple class names."""
        referred_cls = Mock()
        referred_cls.__name__ = "User"

        result = name_for_collection_relationship_snake(
            base=Mock(), local_cls=Mock(), referred_cls=referred_cls, constraint=Mock()
        )
        assert result == "users"

    def test_two_word_class_name(self):
        """Test pluralization of two-word class names."""
        referred_cls = Mock()
        referred_cls.__name__ = "ProcessStatus"

        result = name_for_collection_relationship_snake(
            base=Mock(), local_cls=Mock(), referred_cls=referred_cls, constraint=Mock()
        )
        assert result == "process_statuses"

    def test_three_word_class_name(self):
        """Test pluralization of three-word class names."""
        referred_cls = Mock()
        referred_cls.__name__ = "UserAccountStatus"

        result = name_for_collection_relationship_snake(
            base=Mock(), local_cls=Mock(), referred_cls=referred_cls, constraint=Mock()
        )
        assert result == "user_account_statuses"

    def test_class_name_ending_in_y(self):
        """Test pluralization of class names ending in 'y'."""
        referred_cls = Mock()
        referred_cls.__name__ = "Category"

        result = name_for_collection_relationship_snake(
            base=Mock(), local_cls=Mock(), referred_cls=referred_cls, constraint=Mock()
        )
        assert result == "categories"

    def test_two_word_class_ending_in_y(self):
        """Test pluralization of two-word class names ending in 'y'."""
        referred_cls = Mock()
        referred_cls.__name__ = "CompanyEntry"

        result = name_for_collection_relationship_snake(
            base=Mock(), local_cls=Mock(), referred_cls=referred_cls, constraint=Mock()
        )
        assert result == "company_entries"

    def test_class_name_ending_in_s(self):
        """Test pluralization of class names ending in 's'."""
        referred_cls = Mock()
        referred_cls.__name__ = "Process"

        result = name_for_collection_relationship_snake(
            base=Mock(), local_cls=Mock(), referred_cls=referred_cls, constraint=Mock()
        )
        assert result == "processes"


class TestInflectBasedNaming:
    """Tests for inflect-based collection naming (if available)."""

    def test_with_inflect_available(self):
        """Test that inflect version works when available."""
        pytest.importorskip("inflect")

        referred_cls = Mock()
        referred_cls.__name__ = "Person"

        result = name_for_collection_relationship_snake_with_inflect(
            base=Mock(), local_cls=Mock(), referred_cls=referred_cls, constraint=Mock()
        )
        # inflect should correctly pluralize "person" to "people"
        assert result == "people"

    def test_inflect_two_word_irregular(self):
        """Test inflect with two-word class containing irregular plural."""
        pytest.importorskip("inflect")

        referred_cls = Mock()
        referred_cls.__name__ = "SalesPerson"

        result = name_for_collection_relationship_snake_with_inflect(
            base=Mock(), local_cls=Mock(), referred_cls=referred_cls, constraint=Mock()
        )
        # Should pluralize just the last word: "sales_people"
        assert result == "sales_people"

    def test_without_inflect_fallback(self):
        """Test that fallback works when inflect is not available."""
        # This test will pass regardless of whether inflect is installed
        # because we're testing that the function exists and returns a string
        referred_cls = Mock()
        referred_cls.__name__ = "User"

        result = name_for_collection_relationship_snake_with_inflect(
            base=Mock(), local_cls=Mock(), referred_cls=referred_cls, constraint=Mock()
        )
        assert isinstance(result, str)
        assert result == "users"


class TestRealWorldExamples:
    """Test real-world class names from the SQLAlchemy issue."""

    def test_process_status_scalar(self):
        """Test the main example from SQLAlchemy issue #7149."""
        referred_cls = Mock()
        referred_cls.__name__ = "ProcessStatus"

        result = name_for_scalar_relationship_snake(
            base=Mock(), local_cls=Mock(), referred_cls=referred_cls, constraint=Mock()
        )
        # Should be "process_status", not "processstatus"
        assert result == "process_status"

    def test_process_status_collection(self):
        """Test collection relationship for ProcessStatus."""
        referred_cls = Mock()
        referred_cls.__name__ = "ProcessStatus"

        result = name_for_collection_relationship_snake(
            base=Mock(), local_cls=Mock(), referred_cls=referred_cls, constraint=Mock()
        )
        # Should be "process_statuses", not "processstatuses"
        assert result == "process_statuses"

    def test_common_model_names(self):
        """Test common model names used in applications."""
        test_cases = [
            ("BlogPost", "blog_post", "blog_posts"),
            ("UserProfile", "user_profile", "user_profiles"),
            ("OrderItem", "order_item", "order_items"),
            ("ShoppingCart", "shopping_cart", "shopping_carts"),
            ("PaymentMethod", "payment_method", "payment_methods"),
            ("APIKey", "api_key", "api_keys"),
        ]

        for class_name, expected_scalar, expected_collection in test_cases:
            referred_cls = Mock()
            referred_cls.__name__ = class_name

            scalar_result = name_for_scalar_relationship_snake(
                base=Mock(),
                local_cls=Mock(),
                referred_cls=referred_cls,
                constraint=Mock(),
            )
            assert (
                scalar_result == expected_scalar
            ), f"Expected {expected_scalar}, got {scalar_result} for {class_name}"

            collection_result = name_for_collection_relationship_snake(
                base=Mock(),
                local_cls=Mock(),
                referred_cls=referred_cls,
                constraint=Mock(),
            )
            assert (
                collection_result == expected_collection
            ), f"Expected {expected_collection}, got {collection_result} for {class_name}"
