import inspect
import os
import logging
import sqlmodel as sm
from sqlmodel.sql.expression import SelectOfScalar
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def generate_sqlalchemy_protocol():
    """Generate Protocol type definitions for SQLAlchemy SelectOfScalar methods"""
    logger.info("Starting SQLAlchemy protocol generation")

    # Define the header using a multiline stringT]):
    header = """
# IMPORTANT: This file is auto-generated. Do not edit directly.

from typing import Protocol, TypeVar, Any, Generic
import sqlmodel as sm

T = TypeVar('T', bound=sm.SQLModel, covariant=True)

class SQLAlchemyQueryMethods(Protocol, Generic[T]):
    \"""Protocol defining SQLAlchemy query methods forwarded by QueryWrapper.__getattr__\"""
"""

    # Initialize output list for generated method signatures
    output: list = []

    try:
        # Get all methods from SelectOfScalar
        methods = inspect.getmembers(SelectOfScalar)
        logger.debug(f"Discovered {len(methods)} methods from SelectOfScalar")

        for name, method in methods:
            # Skip private/dunder methods
            if name.startswith("_"):
                continue

            if not inspect.isfunction(method) and not inspect.ismethod(method):
                logger.debug(f"Skipping non-method: {name}")
                continue

            logger.debug(f"Processing method: {name}")
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
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not get signature for {name}: {e}")
                # Some methods might not have proper signatures
                output.append(
                    f'    def {name}(self, *args, **kwargs) -> "SQLAlchemyQueryMethods[T]": ...'
                )

        # Write the output to a file
        protocol_path = (
            Path(__file__).parent.parent / "types" / "sqlalchemy_protocol.py"
        )

        # Ensure directory exists
        os.makedirs(protocol_path.parent, exist_ok=True)

        with open(protocol_path, "w") as f:
            f.write(header + "\n".join(output))

        logger.info(f"Generated SQLAlchemy protocol at {protocol_path}")
    except Exception as e:
        logger.error(f"Error generating SQLAlchemy protocol: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    generate_sqlalchemy_protocol()
