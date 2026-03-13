# activemodel.cli

This module provides utilities for generating Protocol type definitions for SQLAlchemy’s
SelectOfScalar methods, as well as formatting and fixing Python files using ruff.

## Attributes

| [`logger`](#activemodel.cli.logger)                                     |    |
|-------------------------------------------------------------------------|----|
| [`QUERY_WRAPPER_CLASS_NAME`](#activemodel.cli.QUERY_WRAPPER_CLASS_NAME) |    |

## Functions

| [`format_python_file`](#activemodel.cli.format_python_file)(→ bool)               | Format a Python file using ruff.                                         |
|-----------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| [`fix_python_file`](#activemodel.cli.fix_python_file)(→ bool)                     | Fix linting issues in a Python file using ruff.                          |
| [`generate_sqlalchemy_protocol`](#activemodel.cli.generate_sqlalchemy_protocol)() | Generate Protocol type definitions for SQLAlchemy SelectOfScalar methods |

## Package Contents

### activemodel.cli.logger

### activemodel.cli.QUERY_WRAPPER_CLASS_NAME

### activemodel.cli.format_python_file(file_path: [str](https://docs.python.org/3/library/stdtypes.html#str) | [pathlib.Path](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) → [bool](https://docs.python.org/3/library/functions.html#bool)

Format a Python file using ruff.

* **Parameters:**
  **file_path** – Path to the Python file to format
* **Returns:**
  True if formatting was successful, False otherwise
* **Return type:**
  [bool](https://docs.python.org/3/library/functions.html#bool)

### activemodel.cli.fix_python_file(file_path: [str](https://docs.python.org/3/library/stdtypes.html#str) | [pathlib.Path](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) → [bool](https://docs.python.org/3/library/functions.html#bool)

Fix linting issues in a Python file using ruff.

* **Parameters:**
  **file_path** – Path to the Python file to fix
* **Returns:**
  True if fixing was successful, False otherwise
* **Return type:**
  [bool](https://docs.python.org/3/library/functions.html#bool)

### activemodel.cli.generate_sqlalchemy_protocol()

Generate Protocol type definitions for SQLAlchemy SelectOfScalar methods
