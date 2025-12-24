"""
Tests for SQLAlchemy constraint naming conventions.

This ensures that unique constraints (both single and compound) follow
the expected naming pattern defined in POSTGRES_INDEXES_NAMING_CONVENTION.
"""

from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from activemodel import BaseModel
from activemodel.mixins import TypeIDMixin


class SingleUniqueModel(BaseModel, TypeIDMixin("single_uq"), table=True):
    """Test model with a single unique constraint"""

    email: str = Field(unique=True)
    name: str = Field(default="test")


class CompoundUniqueModel(BaseModel, TypeIDMixin("compound_uq"), table=True):
    """Test model with a compound unique constraint"""

    tenant_id: str
    user_email: str
    status: str = Field(default="active")

    __table_args__ = (UniqueConstraint("tenant_id", "user_email"),)


class CompoundUniqueThreeColumnsModel(
    BaseModel, TypeIDMixin("compound_uq_three"), table=True
):
    """Test model with a three-column compound unique constraint"""

    org_id: str
    project_id: str
    resource_name: str

    __table_args__ = (UniqueConstraint("org_id", "project_id", "resource_name"),)


def test_single_unique_constraint_naming():
    """Test that single column unique constraints follow the naming convention"""
    # Get the table from the model
    table = SingleUniqueModel.__table__

    # Find the unique constraint on the email column
    unique_constraints = [c for c in table.constraints if isinstance(c, UniqueConstraint)]

    # Should have at least one unique constraint
    assert len(unique_constraints) > 0, "Expected at least one unique constraint"

    # Find the constraint on the email column
    email_constraint = None
    for constraint in unique_constraints:
        column_names = [col.name for col in constraint.columns]
        if "email" in column_names:
            email_constraint = constraint
            break

    assert email_constraint is not None, "Expected to find unique constraint on email"

    # The naming convention should be: %(table_name)s_%(column_0_N_name)s_key
    # For a single column, this should be: single_unique_model_email_key
    expected_name = "single_unique_model_email_key"
    assert (
        email_constraint.name == expected_name
    ), f"Expected constraint name '{expected_name}', got '{email_constraint.name}'"


def test_compound_unique_constraint_naming():
    """Test that compound unique constraints include all column names"""
    table = CompoundUniqueModel.__table__

    # Find unique constraints
    unique_constraints = [c for c in table.constraints if isinstance(c, UniqueConstraint)]

    # Find the compound constraint on tenant_id and user_email
    compound_constraint = None
    for constraint in unique_constraints:
        column_names = sorted([col.name for col in constraint.columns])
        if column_names == ["tenant_id", "user_email"]:
            compound_constraint = constraint
            break

    assert (
        compound_constraint is not None
    ), "Expected to find compound unique constraint on tenant_id and user_email"

    # The naming convention should include both column names
    # Expected: compound_unique_model_tenant_id_user_email_key
    expected_name = "compound_unique_model_tenant_id_user_email_key"
    assert (
        compound_constraint.name == expected_name
    ), f"Expected constraint name '{expected_name}', got '{compound_constraint.name}'"


def test_compound_unique_constraint_three_columns_naming():
    """Test that compound unique constraints with three columns include all names"""
    table = CompoundUniqueThreeColumnsModel.__table__

    # Find unique constraints
    unique_constraints = [c for c in table.constraints if isinstance(c, UniqueConstraint)]

    # Find the three-column compound constraint
    compound_constraint = None
    for constraint in unique_constraints:
        column_names = sorted([col.name for col in constraint.columns])
        if column_names == ["org_id", "project_id", "resource_name"]:
            compound_constraint = constraint
            break

    assert (
        compound_constraint is not None
    ), "Expected to find compound unique constraint on org_id, project_id, and resource_name"

    # The naming convention should include all three column names
    # Expected: compound_unique_three_columns_model_org_id_project_id_resource_name_key
    expected_name = (
        "compound_unique_three_columns_model_org_id_project_id_resource_name_key"
    )
    assert (
        compound_constraint.name == expected_name
    ), f"Expected constraint name '{expected_name}', got '{compound_constraint.name}'"


def test_existing_upsert_model_constraint():
    """Test that the existing UpsertTestModel constraint is named correctly"""
    from test.models import UpsertTestModel

    table = UpsertTestModel.__table__

    # Find the manually named constraint
    unique_constraints = [c for c in table.constraints if isinstance(c, UniqueConstraint)]

    # The UpsertTestModel has a manually named constraint "compound_constraint"
    compound_constraint = None
    for constraint in unique_constraints:
        if constraint.name == "compound_constraint":
            compound_constraint = constraint
            break

    # Verify it exists and has the expected columns
    assert (
        compound_constraint is not None
    ), "Expected to find manually named 'compound_constraint'"

    column_names = sorted([col.name for col in compound_constraint.columns])
    assert column_names == [
        "category",
        "name",
    ], f"Expected columns ['category', 'name'], got {column_names}"

    # When manually named, it should keep the manual name
    assert compound_constraint.name == "compound_constraint"
