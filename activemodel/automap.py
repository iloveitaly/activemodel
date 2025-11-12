"""
SQLAlchemy automap utilities with snake_case naming conventions.

This module provides helper functions for SQLAlchemy's automap feature to use
snake_case naming conventions for relationship attributes, addressing the issue
described in https://github.com/sqlalchemy/sqlalchemy/issues/7149

Instead of generating lowercase relationship names (e.g., `user.processstatus`),
these functions generate snake_case names (e.g., `user.process_status`) that
match Python and database naming conventions.

Example usage with automap_base:

    from sqlalchemy.ext.automap import automap_base
    from sqlalchemy import create_engine
    from activemodel.automap import (
        name_for_scalar_relationship_snake,
        name_for_collection_relationship_snake,
    )

    engine = create_engine("sqlite:///database.db")
    Base = automap_base()

    # Configure automap to use snake_case naming
    Base.prepare(
        autoload_with=engine,
        name_for_scalar_relationship=name_for_scalar_relationship_snake,
        name_for_collection_relationship=name_for_collection_relationship_snake,
    )

    # Now relationships will use snake_case:
    # - ProcessStatus -> user.process_status (scalar)
    # - ProcessStatus -> user.process_statuses (collection)
"""

import re
import textcase
from sqlalchemy.ext.automap import (
    name_for_scalar_relationship as default_scalar,
    name_for_collection_relationship as default_collection,
)


def _simple_pluralize(word: str) -> str:
    """
    Simple pluralization for English words.

    This is a basic implementation that handles common cases. For production use,
    consider using a library like `inflect` for more comprehensive pluralization.

    Args:
        word: The word to pluralize

    Returns:
        The pluralized form of the word
    """
    # Handle common irregular plurals
    irregulars = {
        "person": "people",
        "child": "children",
        "man": "men",
        "woman": "women",
        "tooth": "teeth",
        "foot": "feet",
        "mouse": "mice",
        "goose": "geese",
    }

    word_lower = word.lower()
    if word_lower in irregulars:
        return irregulars[word_lower]

    # Words ending in 'y' preceded by a consonant -> change 'y' to 'ies'
    if len(word) > 1 and word[-1] == "y" and word[-2] not in "aeiou":
        return word[:-1] + "ies"

    # Words ending in s, x, z, ch, sh -> add 'es'
    if word.endswith(("s", "x", "z")) or word.endswith(("ch", "sh")):
        return word + "es"

    # Words ending in 'f' or 'fe' -> change to 'ves'
    if word.endswith("f"):
        return word[:-1] + "ves"
    if word.endswith("fe"):
        return word[:-2] + "ves"

    # Default: just add 's'
    return word + "s"


def name_for_scalar_relationship_snake(
    base, local_cls, referred_cls, constraint
) -> str:
    """
    Generate a snake_case name for a scalar (many-to-one or one-to-one) relationship.

    This function is designed to be passed to `automap_base().prepare()` as the
    `name_for_scalar_relationship` parameter.

    Args:
        base: The automap base
        local_cls: The class that will have the relationship property
        referred_cls: The class being referred to
        constraint: The ForeignKeyConstraint

    Returns:
        A snake_case name for the relationship attribute

    Example:
        ProcessStatus class -> "process_status" attribute
    """
    # Get the class name and convert to snake_case
    class_name = referred_cls.__name__
    return textcase.snake(class_name)


def name_for_collection_relationship_snake(
    base, local_cls, referred_cls, constraint
) -> str:
    """
    Generate a snake_case, pluralized name for a collection (one-to-many) relationship.

    This function is designed to be passed to `automap_base().prepare()` as the
    `name_for_collection_relationship` parameter.

    Args:
        base: The automap base
        local_cls: The class that will have the relationship property
        referred_cls: The class being referred to
        constraint: The ForeignKeyConstraint

    Returns:
        A snake_case, pluralized name for the relationship attribute

    Example:
        ProcessStatus class -> "process_statuses" attribute
    """
    # Get the class name and convert to snake_case
    class_name = referred_cls.__name__
    snake_name = textcase.snake(class_name)

    # Split the snake_case name to get individual words
    # We'll pluralize the last word
    parts = snake_name.split("_")
    if parts:
        parts[-1] = _simple_pluralize(parts[-1])

    return "_".join(parts)


def name_for_scalar_relationship_snake_with_inflect(
    base, local_cls, referred_cls, constraint
) -> str:
    """
    Generate a snake_case name for a scalar relationship (alias for compatibility).

    This function has the same behavior as `name_for_scalar_relationship_snake`
    but is named to pair with the inflect-based collection naming function.
    """
    return name_for_scalar_relationship_snake(
        base, local_cls, referred_cls, constraint
    )


# Optional: If inflect is available, provide a more robust pluralization
try:
    import inflect

    _inflect_engine = inflect.engine()

    def name_for_collection_relationship_snake_with_inflect(
        base, local_cls, referred_cls, constraint
    ) -> str:
        """
        Generate a snake_case, pluralized name for a collection relationship using inflect.

        This version uses the `inflect` library for more accurate pluralization.
        To use this function, install inflect: `pip install inflect` or `uv add inflect`

        Args:
            base: The automap base
            local_cls: The class that will have the relationship property
            referred_cls: The class being referred to
            constraint: The ForeignKeyConstraint

        Returns:
            A snake_case, pluralized name for the relationship attribute

        Example:
            ProcessStatus class -> "process_statuses" attribute
            Person class -> "people" attribute (correct irregular plural)
        """
        # Get the class name and convert to snake_case
        class_name = referred_cls.__name__
        snake_name = textcase.snake(class_name)

        # Split the snake_case name to get individual words
        # We'll pluralize the last word using inflect
        parts = snake_name.split("_")
        if parts:
            parts[-1] = _inflect_engine.plural(parts[-1])

        return "_".join(parts)

except ImportError:
    # If inflect is not available, provide a fallback that uses the simple version
    def name_for_collection_relationship_snake_with_inflect(
        base, local_cls, referred_cls, constraint
    ) -> str:
        """
        Fallback to simple pluralization when inflect is not installed.

        To use more accurate pluralization, install inflect: `pip install inflect`
        """
        return name_for_collection_relationship_snake(
            base, local_cls, referred_cls, constraint
        )
