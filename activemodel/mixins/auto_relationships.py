"""
Auto-relationship generation for SQLModel models.

This module provides functionality to automatically create relationship fields from foreign key fields
that have metadata indicating their related model.

Note: Due to SQLModel's type resolution behavior with Annotated types, this mixin currently requires
explicit metadata annotations. A future version may provide deeper integration with the foreign_key() method.
"""

from typing import TYPE_CHECKING, Any, TypeVar

from sqlmodel import Relationship

if TYPE_CHECKING:
    from sqlmodel import SQLModel

T = TypeVar("T")


def auto_relationships(cls: type[T]) -> type[T]:
    """
    Decorator that inspects a model's fields and automatically creates relationship fields
    for any foreign key fields that have 'related_model' metadata.

    Usage pattern with Annotated metadata:

        >>> from typing import Annotated
        >>> @auto_relationships
        >>> class Order(BaseModel, table=True):
        >>>     customer_id: Annotated[
        >>>         int,
        >>>         Field(foreign_key="customer.id"),
        >>>         {"related_model": lambda: Customer}
        >>>     ]
        >>>     # Automatically creates: customer: Customer = Relationship()

    The decorator:
    - Looks for fields ending with '_id' that have 'related_model' in their metadata
    - Derives the relationship field name by removing the '_id' suffix
    - Creates a Relationship() descriptor
    - Adds proper type annotations

    Notes:
    - Metadata must be provided via Annotated type with a dict containing 'related_model'
    - The 'related_model' value can be a class or a callable (lambda) for forward references
    - Optional 'back_populates' key can be included for bidirectional relationships
    - Fields not ending with '_id' are skipped
    - Existing relationship fields are not overwritten
    """

    # Check if the class has model_fields (SQLModel/Pydantic)
    if not hasattr(cls, "model_fields"):
        return cls

    # Process each field to find foreign keys with related_model metadata
    for field_name, field_info in cls.model_fields.items():
        # Skip if this field doesn't end with '_id' (convention for foreign keys)
        if not field_name.endswith("_id"):
            continue

        # Check metadata for related_model (Pydantic v2 stores metadata in a list)
        related_model = None
        back_populates = None

        for meta_item in field_info.metadata:
            if isinstance(meta_item, dict) and "related_model" in meta_item:
                related_model = meta_item.get("related_model")
                back_populates = meta_item.get("back_populates")
                break

        if related_model is None:
            continue

        # Derive the relationship field name by removing '_id' suffix
        relationship_field_name = field_name[:-3]

        # Skip if relationship field already exists
        if hasattr(cls, relationship_field_name):
            continue

        # If it's a callable (lambda/function for forward references), call it
        if callable(related_model):
            related_model = related_model()

        # Create the relationship descriptor
        if back_populates:
            relationship = Relationship(back_populates=back_populates)
        else:
            relationship = Relationship()

        # Add type annotation for the relationship
        if relationship_field_name not in cls.__annotations__:
            cls.__annotations__[relationship_field_name] = related_model

        # Set the attribute on the class
        setattr(cls, relationship_field_name, relationship)

    return cls


class AutoRelationshipsMixin:
    """
    Mixin that uses __init_subclass__ to automatically generate relationship fields
    from foreign key fields with metadata.

    Example:

        >>> from typing import Annotated
        >>> class Order(AutoRelationshipsMixin, BaseModel, table=True):
        >>>     customer_id: Annotated[
        >>>         int,
        >>>         Field(foreign_key="customer.id"),
        >>>         {"related_model": lambda: Customer}
        >>>     ]
        >>>     # The 'customer' relationship field will be created automatically

    The mixin can be used in two ways:

    1. As a mixin class (recommended for consistency):
        >>> class MyModel(AutoRelationshipsMixin, BaseModel, table=True):
        >>>     ...

    2. As a decorator (more explicit control):
        >>> @auto_relationships
        >>> class MyModel(BaseModel, table=True):
        >>>     ...

    Note: Due to SQLModel's type resolution with custom types like TypeIDType,
    you may need to use simpler types (int, str) in the Annotated declaration
    and let the Field's sa_type handle the actual database type.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Called when a class inherits from AutoRelationshipsMixin.
        Automatically applies the auto_relationships logic after the class is defined.
        """
        super().__init_subclass__(**kwargs)

        # Apply the auto_relationships decorator logic
        auto_relationships(cls)
