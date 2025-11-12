# SQLAlchemy Automap with Snake Case Naming

This module provides helper functions for SQLAlchemy's automap feature to use snake_case naming conventions for relationship attributes, addressing [SQLAlchemy issue #7149](https://github.com/sqlalchemy/sqlalchemy/issues/7149).

## Problem

By default, SQLAlchemy's automap generates relationship names by simply lowercasing class names:

```python
# Default behavior (without this module)
user.processstatus  # ❌ Hard to read
user.httpresponse   # ❌ Doesn't match Python conventions
```

This doesn't match Python's snake_case naming conventions or typical database column naming patterns like `process_status_id`.

## Solution

This module provides naming functions that convert PascalCase class names to snake_case:

```python
# With this module
user.process_status   # ✅ Readable and Pythonic
user.http_response    # ✅ Matches naming conventions
```

## Usage

### Basic Example

Here's a complete example of using automap with snake_case naming:

```python
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.automap import automap_base
from activemodel.automap import (
    name_for_scalar_relationship_snake,
    name_for_collection_relationship_snake,
)

# Create engine and reflect tables
engine = create_engine("sqlite:///example.db")

# First, create some example tables
from sqlalchemy import MetaData, Table

metadata = MetaData()

users_table = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(50)),
)

process_status_table = Table(
    "process_status",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("status", String(50)),
)

metadata.create_all(engine)

# Now use automap with snake_case naming
Base = automap_base()

Base.prepare(
    autoload_with=engine,
    name_for_scalar_relationship=name_for_scalar_relationship_snake,
    name_for_collection_relationship=name_for_collection_relationship_snake,
)

# Access the mapped classes
User = Base.classes.users
ProcessStatus = Base.classes.process_status

# Create a session and query
from sqlalchemy.orm import Session

with Session(engine) as session:
    # Create test data
    user = User(name="Alice")
    status1 = ProcessStatus(status="pending")
    status2 = ProcessStatus(status="completed")

    # Use the snake_case relationship names
    user.process_statuses = [status1, status2]  # ✅ Collection relationship

    session.add(user)
    session.commit()

    # Query and access relationships
    user = session.query(User).first()
    for status in user.process_statuses:  # ✅ Readable!
        print(f"{user.name}: {status.status}")
        print(f"User: {status.user.name}")  # ✅ Scalar relationship
```

### Integration with ActiveModel

If you're using ActiveModel, you can combine automap with manually defined models:

```python
from sqlalchemy.ext.automap import automap_base
from activemodel import get_engine
from activemodel.automap import (
    name_for_scalar_relationship_snake,
    name_for_collection_relationship_snake,
)

engine = get_engine()
Base = automap_base()

# Prepare automap with snake_case naming
Base.prepare(
    autoload_with=engine,
    name_for_scalar_relationship=name_for_scalar_relationship_snake,
    name_for_collection_relationship=name_for_collection_relationship_snake,
)

# Now you can access reflected tables with proper naming
LegacyTable = Base.classes.legacy_table
```

### Advanced: Using inflect for Better Pluralization

For more accurate pluralization (e.g., "person" → "people"), install the `inflect` library:

```bash
pip install inflect
# or
uv add inflect
```

Then use the inflect-based naming function:

```python
from activemodel.automap import (
    name_for_scalar_relationship_snake,
    name_for_collection_relationship_snake_with_inflect,
)

Base.prepare(
    autoload_with=engine,
    name_for_scalar_relationship=name_for_scalar_relationship_snake,
    name_for_collection_relationship=name_for_collection_relationship_snake_with_inflect,
)

# Now irregular plurals work correctly
# Person class -> user.people (not user.persons)
# Child class -> parent.children (not parent.childs)
```

## Examples of Class Name Conversions

### Scalar Relationships (Many-to-One, One-to-One)

| Class Name | Relationship Attribute |
|------------|----------------------|
| `User` | `user` |
| `ProcessStatus` | `process_status` |
| `HTTPResponse` | `http_response` |
| `UserAccountStatus` | `user_account_status` |
| `APIKey` | `api_key` |
| `OAuth2Client` | `o_auth2_client` |

### Collection Relationships (One-to-Many)

| Class Name | Relationship Attribute |
|------------|----------------------|
| `User` | `users` |
| `ProcessStatus` | `process_statuses` |
| `Category` | `categories` |
| `Process` | `processes` |
| `Person` (with inflect) | `people` |
| `Child` (with inflect) | `children` |

## API Reference

### `name_for_scalar_relationship_snake(base, local_cls, referred_cls, constraint)`

Generates a snake_case name for scalar (many-to-one or one-to-one) relationships.

**Parameters:**
- `base`: The automap base
- `local_cls`: The class that will have the relationship property
- `referred_cls`: The class being referred to
- `constraint`: The ForeignKeyConstraint

**Returns:** A snake_case string for the relationship attribute name

**Example:** `ProcessStatus` → `"process_status"`

### `name_for_collection_relationship_snake(base, local_cls, referred_cls, constraint)`

Generates a snake_case, pluralized name for collection (one-to-many) relationships.

**Parameters:** Same as `name_for_scalar_relationship_snake`

**Returns:** A snake_case, pluralized string for the relationship attribute name

**Example:** `ProcessStatus` → `"process_statuses"`

### `name_for_collection_relationship_snake_with_inflect(base, local_cls, referred_cls, constraint)`

Like `name_for_collection_relationship_snake`, but uses the `inflect` library for more accurate pluralization. Falls back to simple pluralization if `inflect` is not installed.

**Requires:** `pip install inflect`

**Example:** `Person` → `"people"` (instead of `"persons"`)

## Testing

The module includes comprehensive tests in `test/automap_test.py`:

```bash
# Run the automap tests
pytest test/automap_test.py -v
```

## Implementation Notes

- Uses the existing `textcase` library (already a dependency) for PascalCase to snake_case conversion
- Includes a built-in simple pluralization function for common cases
- Optional `inflect` integration for more accurate pluralization
- Follows SQLAlchemy's automap naming function signature
- Non-breaking: these are optional functions you can choose to use

## Background

This implementation addresses [SQLAlchemy issue #7149](https://github.com/sqlalchemy/sqlalchemy/issues/7149), where the SQLAlchemy maintainer acknowledged that snake_case naming is "a great idea" but declined to change the default behavior due to backward compatibility concerns. Instead, these helper functions are provided as opt-in alternatives.

## Related Resources

- [SQLAlchemy Automap Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/automap.html)
- [SQLAlchemy Issue #7149](https://github.com/sqlalchemy/sqlalchemy/issues/7149)
- [textcase library](https://pypi.org/project/textcase/)
- [inflect library](https://pypi.org/project/inflect/)
