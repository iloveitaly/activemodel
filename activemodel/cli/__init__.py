"""
This module provides utilities for generating Protocol type definitions for SQLAlchemy's
SelectOfScalar methods, as well as formatting and fixing Python files using ruff.
"""

import inspect
import logging
import os
import subprocess
from pathlib import Path
from typing import Any  # already imported in header of generated file

import sqlmodel as sm
from sqlmodel.sql.expression import SelectOfScalar

from test.test_wrapper import QueryWrapper

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

QUERY_WRAPPER_CLASS_NAME = QueryWrapper.__name__


def format_python_file(file_path: str | Path) -> bool:
    """
    Format a Python file using ruff.

    Args:
        file_path: Path to the Python file to format

    Returns:
        bool: True if formatting was successful, False otherwise
    """
    try:
        subprocess.run(["ruff", "format", str(file_path)], check=True)
        logger.info(f"Formatted file using ruff at {file_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running ruff to format the file: {e}")
        return False


def fix_python_file(file_path: str | Path) -> bool:
    """
    Fix linting issues in a Python file using ruff.

    Args:
        file_path: Path to the Python file to fix

    Returns:
        bool: True if fixing was successful, False otherwise
    """
    try:
        subprocess.run(["ruff", "check", str(file_path), "--fix"], check=True)
        logger.info(f"Fixed linting issues using ruff at {file_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running ruff to fix the file: {e}")
        return False


def generate_sqlalchemy_protocol():
    """Generate Protocol type definitions for SQLAlchemy SelectOfScalar methods"""
    logger.info("Starting SQLAlchemy protocol generation")

    header = """
# IMPORTANT: This file is auto-generated. Do not edit directly.

from typing import Protocol, TypeVar, Any, Generic
import sqlmodel as sm
from sqlalchemy.sql.base import _NoArg

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

                # Process parameters, skipping 'self'
                for param_name, param in list(signature.parameters.items())[1:]:
                    if param.kind == param.VAR_POSITIONAL:
                        params.append(f"*{param_name}: Any")
                    elif param.kind == param.VAR_KEYWORD:
                        params.append(f"**{param_name}: Any")
                    else:
                        if param.default is inspect.Parameter.empty:
                            params.append(f"{param_name}: Any")
                        else:
                            default_repr = repr(param.default)
                            params.append(f"{param_name}: Any = {default_repr}")

                params_str = ", ".join(params)
                output.append(
                    f'    def {name}(self, {params_str}) -> "{QUERY_WRAPPER_CLASS_NAME}[T]": ...'
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not get signature for {name}: {e}")
                # Some methods might not have proper signatures
                output.append(
                    f'    def {name}(self, *args: Any, **kwargs: Any) -> "{QUERY_WRAPPER_CLASS_NAME}[T]": ...'
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

        # Format and fix the generated file with ruff
        format_python_file(protocol_path)
        fix_python_file(protocol_path)
    except Exception as e:
        logger.error(f"Error generating SQLAlchemy protocol: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    generate_sqlalchemy_protocol()
