---
name: upgrade-sqlmodel
description: Upgrade the pinned sqlmodel and typeid-python dependencies and re-verify activemodel's monkeypatches. Use when asked to bump, update, or check SQLModel or TypeID, or when a get_sqlalchemy_type or get_column_from_field hash assertion fails.
---

# Upgrade SQLModel and typeid-python

`sqlmodel` and `typeid-python` are exact pins in `pyproject.toml`. Two SQLModel helpers are monkeypatched under `activemodel/patches/`. Each patch asserts `hash_function_code(...)` against the upstream function. The assert runs before the monkeypatch assignment, so the expected hash is the hash of the installed upstream function.

## Check both packages

Read the pins from `pyproject.toml`. Read the latest version and its upload time from PyPI:

```bash
curl -fsSL https://pypi.org/pypi/sqlmodel/json
curl -fsSL https://pypi.org/pypi/typeid-python/json
```

If a package is already at the latest release, leave it pinned and say so. Continue with the other package. If both are current, stop.

Read the release notes for every version between the pin and latest before editing:

- https://sqlmodel.tiangolo.com/release-notes/
- https://github.com/fastapi/sqlmodel/releases
- https://github.com/fastapi/sqlmodel/compare/<old>...<new>

## Bump

```bash
uv add "sqlmodel==<latest>"
uv add "typeid-python==<latest>"
```

Run only the package that moved. `uv add` updates `uv.lock`.

## The two patches are different

### `get_column_from_field_patch.py` is a copy

`activemodel/patches/get_column_from_field_patch.py` is the upstream `sqlmodel.main.get_column_from_field` body plus `# <Change>` / `# </Change>` blocks. Those blocks copy a field description onto the SQLAlchemy column comment.

Diff `def get_column_from_field` in `sqlmodel/main.py` between the old and new tags on `fastapi/sqlmodel`.

When the body is the same, update the GitHub permalink if the line number moved.

When the body changed, replace the copied function with the new upstream body, then put the `# <Change>` blocks back in the same places. Update the permalink and the expected hash.

As of 0.0.46 the upstream call is `Column(*args, type_=sa_type, **kwargs)`. `sa_type` is a keyword because `Column`'s first positional argument also accepts a name or a `SchemaEventTarget`. Keep that call in the copy.

### `get_sqlalchemy_type_patch.py` is a wrapper

`activemodel/patches/get_sqlalchemy_type_patch.py` does not contain a copy of `get_sqlalchemy_type`. It resolves the annotation, maps `whenever` types to their TypeDecorators, and then calls the original function.

When the upstream body changes, update the permalink and the expected hash. Leave the wrapper in place.

Read the upstream diff and confirm the wrapper still composes with it:

- `whenever` types are handled before the original runs, so they stay on `InstantType`, `PlainDateTimeType`, `ZonedDateTimeType`, `DateType`, and `TimeType`.
- Every other annotation, including plain `datetime`, falls through to the original.
- An explicit `sa_type` is honored by the original, which the wrapper calls.

## Read the changes outside the two functions

A hash update on the wrapper does not record these. Diff them whenever the release touches types, annotations, or datetimes:

- `sqlmodel/main.py` `Field` / `FieldInfo`. `sa_type` accepts a type class or an instance. `type_` inside `sa_column_kwargs` is rejected. This stays in SQLModel's `Field`, which the patches do not replace.
- `sqlmodel/_compat.py` `get_sa_type_from_field` and `get_sa_type_from_type_annotation`. The wrapper calls `get_sa_type_from_field`. As of 0.0.45 that function uses `field.rebuild_annotation()`, and `Annotated[..., AwareDatetime]` / `NaiveDatetime` selects the timezone behavior.
- `sqlmodel/sql/sqltypes.py` `UTCDateTime`. As of 0.0.45, plain `datetime` and `AwareDatetime` map to `UTCDateTime()` (aware UTC, naive values raise on write). `NaiveDatetime` maps to `DateTime(timezone=False)`. As of 0.0.46, `coerce_compared_value` treats a `timedelta` operand as an `Interval`.
- The metaclass decorator is `typing_extensions.dataclass_transform(..., field_specifiers=(Field, FieldInfo))`.

`UTCDateTime.coerce_compared_value` applies to plain `datetime` columns. `whenever` columns use the TypeDecorators in `activemodel/types/whenever/`. Add the same override there only after a test shows timedelta arithmetic on those columns failing.

Search docs and tests for `datetime.now()` stored on a plain `datetime` field. That write raises under `UTCDateTime`. Aware values (`datetime.now(timezone.utc)`) and `whenever` fields keep working. Explicit `sa_type=` keeps its previous column type.

## typeid-python

`activemodel/types/typeid_patch.py` assigns `__get_pydantic_core_schema__` and `__get_pydantic_json_schema__` onto `typeid.TypeID`. It asserts those attributes are missing or already equal to the patch. There is no upstream-function hash.

On a typeid bump, read that package's changelog and compare the methods the patch calls (`TypeID.from_string`, the pydantic hooks). Update the patch when those APIs move. Run the typeid tests.

## Hash and permalink

Compute the hash before importing `activemodel`. Importing it replaces the functions.

```bash
uv run python - <<'PY'
import hashlib
import inspect

import sqlmodel.main as main

for name in ("get_sqlalchemy_type", "get_column_from_field"):
    fn = getattr(main, name)
    digest = hashlib.sha256(inspect.getsource(fn).encode()).hexdigest()
    lineno = inspect.getsourcelines(fn)[1]
    print(f"{name} {digest} line {lineno}")
PY
```

Permalink shape:

```text
https://github.com/fastapi/sqlmodel/blob/<version>/sqlmodel/main.py#L<lineno>
```

## Test

Use the repo commands: `just docker_up` when the database is down, then `just test`.

A missing required environment variable or a database connectivity failure stops the upgrade. Report it. Do not invent a `DATABASE_URL`.

Run `just lint` when the user asked for lint, or when the upgrade edits Python that the linters cover. The lint job is allowed to fail in CI for pre-existing findings. Fix findings introduced by the upgrade.

## Report

- `sqlmodel`: old pin, new pin, or already current
- `typeid-python`: old pin, new pin, or already current
- For each patch: body unchanged, or what was rebased
- Behavior changes outside the patch files, and whether `whenever` fields are affected
- Test results
