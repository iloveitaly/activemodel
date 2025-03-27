import inspect
import os
import sqlmodel as sm
from sqlmodel.sql.expression import SelectOfScalar
from pathlib import Path


def generate_sqlalchemy_protocol():
    """Generate Protocol type definitions for SQLAlchemy SelectOfScalar methods"""

    # Define the header using a multiline string
    header = """from typing import Protocol, TypeVar, Any, List, Optional, Union, Generic
import sqlmodel as sm

T = TypeVar('T', bound=sm.SQLModel)

class SQLAlchemyQueryMethods(Protocol, Generic[T]):
    \"""Protocol defining SQLAlchemy query methods forwarded by QueryWrapper.__getattr__\"""
"""

    # Initialize output list for generated method signatures
    output: list = []

    # Get all methods from SelectOfScalar
    methods = inspect.getmembers(SelectOfScalar, predicate=inspect.ismethod)

    for name, method in methods:
        # Skip private/dunder methods
        if name.startswith("_"):
            continue

        try:
            signature = inspect.signature(method)
            params = []

            # Process parameters
            for param_name, param in list(signature.parameters.items())[
                1:
            ]:  # Skip 'self'
                if param.default is inspect.Parameter.empty:
                    params.append(f"{param_name}")
                else:
                    # Handle default values safely
                    default_repr = repr(param.default).replace('"', '\\"')
                    params.append(f"{param_name}={default_repr}")

            params_str = ", ".join(params)
            output.append(
                f'    def {name}(self, {params_str}) -> "SQLAlchemyQueryMethods[T]": ...'
            )
        except (ValueError, TypeError):
            # Some methods might not have proper signatures
            output.append(
                f'    def {name}(self, *args, **kwargs) -> "SQLAlchemyQueryMethods[T]": ...'
            )

    # Write the output to a file
    protocol_path = Path(__file__).parent.parent / "types" / "sqlalchemy_protocol.py"

    # Ensure directory exists
    os.makedirs(protocol_path.parent, exist_ok=True)

    with open(protocol_path, "w") as f:
        f.write(header + "\n".join(output))

    print(f"Generated SQLAlchemy protocol at {protocol_path}")


if __name__ == "__main__":
    generate_sqlalchemy_protocol()
